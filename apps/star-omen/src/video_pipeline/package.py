from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Literal, Mapping

from pydantic import Field, model_validator

from src.video_pipeline.contracts._common import StableId, StrictContractModel, ensure_unique

_MAX_STRUCTURED_BYTES = 10 * 1024 * 1024
_MAX_MEMBER_COUNT = 256


class PackageMemberV1(StrictContractModel):
    schema_version: Literal["package-member/v1"] = "package-member/v1"
    path: str = Field(min_length=1, max_length=256)
    byte_size: int = Field(strict=True, ge=0, le=_MAX_STRUCTURED_BYTES)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_path(self) -> "PackageMemberV1":
        _validate_member_path(self.path)
        return self


class PackageManifestV1(StrictContractModel):
    schema_version: Literal["package-manifest/v1"] = "package-manifest/v1"
    package_id: StableId
    members: list[PackageMemberV1]
    total_structured_bytes: int = Field(
        strict=True,
        ge=0,
        le=_MAX_STRUCTURED_BYTES,
    )

    @model_validator(mode="after")
    def validate_manifest(self) -> "PackageManifestV1":
        if not self.members:
            raise ValueError("package manifest requires members")
        if len(self.members) > _MAX_MEMBER_COUNT:
            raise ValueError("package manifest has too many members")
        paths = [entry.path for entry in self.members]
        ensure_unique(paths, "package member paths")
        if paths != sorted(paths):
            raise ValueError("package members must use canonical path order")
        total = sum(entry.byte_size for entry in self.members)
        if total != self.total_structured_bytes:
            raise ValueError("package total size does not match member inventory")
        return self


def _validate_member_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise ValueError("package member path is unsafe")
    path = PurePosixPath(value)
    if path.is_absolute() or value in {".", ".."}:
        raise ValueError("package member path must be relative")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("package member path contains traversal")
    if path.name == "manifest.json":
        raise ValueError("manifest.json is reserved")
    if any(ord(character) < 32 for character in value):
        raise ValueError("package member path contains control characters")
    return path


def _canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def canonical_manifest_bytes(manifest: PackageManifestV1) -> bytes:
    validated = PackageManifestV1.model_validate(manifest.model_dump(mode="json"))
    return _canonical_json_bytes(validated.model_dump(mode="json"))


def _normalize_members(members: Mapping[str, bytes]) -> dict[str, bytes]:
    if not isinstance(members, Mapping) or not members:
        raise ValueError("package members must be a non-empty mapping")
    if len(members) > _MAX_MEMBER_COUNT:
        raise ValueError("package has too many members")
    normalized: dict[str, bytes] = {}
    total = 0
    for raw_path, raw_bytes in members.items():
        path = _validate_member_path(raw_path).as_posix()
        if path in normalized:
            raise ValueError("package member path is duplicated")
        if not isinstance(raw_bytes, bytes):
            raise TypeError("package member content must be bytes")
        total += len(raw_bytes)
        if total > _MAX_STRUCTURED_BYTES:
            raise ValueError("structured package exceeds 10 MiB")
        normalized[path] = raw_bytes
    return normalized


def build_package_manifest(
    *,
    package_id: str,
    members: Mapping[str, bytes],
) -> PackageManifestV1:
    normalized = _normalize_members(members)
    entries = [
        PackageMemberV1(
            path=path,
            byte_size=len(normalized[path]),
            sha256=hashlib.sha256(normalized[path]).hexdigest(),
        )
        for path in sorted(normalized)
    ]
    return PackageManifestV1(
        package_id=package_id,
        members=entries,
        total_structured_bytes=sum(entry.byte_size for entry in entries),
    )


def verify_package_members(
    manifest: PackageManifestV1,
    members: Mapping[str, bytes],
) -> bool:
    manifest = PackageManifestV1.model_validate(manifest.model_dump(mode="json"))
    normalized = _normalize_members(members)
    expected_paths = [entry.path for entry in manifest.members]
    if sorted(normalized) != expected_paths:
        raise ValueError("package member set does not match manifest")
    for entry in manifest.members:
        content = normalized[entry.path]
        if len(content) != entry.byte_size:
            raise ValueError(f"package member size mismatch: {entry.path}")
        if hashlib.sha256(content).hexdigest() != entry.sha256:
            raise ValueError(f"package member hash mismatch: {entry.path}")
    return True


def write_package_atomic(
    *,
    output_dir: str | Path,
    manifest: PackageManifestV1,
    members: Mapping[str, bytes],
) -> Path:
    manifest = PackageManifestV1.model_validate(manifest.model_dump(mode="json"))
    normalized = _normalize_members(members)
    verify_package_members(manifest, normalized)

    output = Path(output_dir)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    parent = output.parent
    if not parent.exists() or not parent.is_dir() or parent.is_symlink():
        raise ValueError("package output parent must be an existing real directory")

    staging = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.", dir=str(parent))
    )
    try:
        for relative_path, content in sorted(normalized.items()):
            target = staging.joinpath(*PurePosixPath(relative_path).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        manifest_path = staging / "manifest.json"
        with manifest_path.open("xb") as handle:
            handle.write(canonical_manifest_bytes(manifest))
            handle.flush()
            os.fsync(handle.fileno())

        staged_members = {
            entry.path: staging.joinpath(*PurePosixPath(entry.path).parts).read_bytes()
            for entry in manifest.members
        }
        verify_package_members(manifest, staged_members)
        if output.exists() or output.is_symlink():
            raise FileExistsError(output)
        os.rename(staging, output)
        return output
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


__all__ = [
    "PackageManifestV1",
    "PackageMemberV1",
    "build_package_manifest",
    "canonical_manifest_bytes",
    "verify_package_members",
    "write_package_atomic",
]
