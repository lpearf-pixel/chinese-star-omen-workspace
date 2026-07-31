#!/usr/bin/env python3
"""Create a version-bound, privacy-safe B9-G6 evidence handoff archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import plistlib
import re
import sys
import tarfile
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import BinaryIO


_REQUIRED_SOURCE_FILES = (
    "local-capability-evidence.json",
    "renderer-review-input.json",
    "renderer-hard-gate.json",
    "ai-assisted-visual-review.json",
    "human-experience-confirmation.json",
    "assisted-renderer-review.json",
    "ocr-observations.json",
    "ffprobe-preview.json",
    "preview.mp4",
    "scene.ssc",
    "preview-command.json",
    "package-manifest.json",
)
_VERSION_RE = re.compile(r"^([0-9]+)\.([0-9]+)(?:\.([0-9]+))?$")
_MAX_SCREENSHOTS = 30
_MAX_METADATA_BYTES = 1024 * 1024


class HandoffError(RuntimeError):
    """A fail-closed B9-G6 handoff construction error."""


@dataclass(frozen=True)
class _Source:
    path: Path
    archive_name: str
    size: int
    identity: tuple[int, int, int, int]
    content: bytes | None = None


def _canonical_archive_name(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or "\x00" in value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != value
    ):
        raise HandoffError(f"unsafe archive member path: {value!r}")
    return value


def _regular_source(path: Path, *, archive_name: str) -> _Source:
    if path.is_symlink() or not path.is_file():
        raise HandoffError(f"{archive_name} must be a regular non-symlink file")
    stat = path.stat()
    return _Source(
        path=path,
        archive_name=_canonical_archive_name(archive_name),
        size=stat.st_size,
        identity=(stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns),
    )


def _require_stable(source: _Source) -> None:
    if source.path.is_symlink() or not source.path.is_file():
        raise HandoffError(f"{source.archive_name} changed while archiving")
    stat = source.path.stat()
    identity = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
    if identity != source.identity:
        raise HandoffError(f"{source.archive_name} changed while archiving")


def _bounded_source_bytes(source: _Source) -> bytes:
    if source.size > _MAX_METADATA_BYTES:
        raise HandoffError(
            f"{source.archive_name} exceeds the metadata size limit"
        )
    with source.path.open("rb") as handle:
        value = handle.read(_MAX_METADATA_BYTES + 1)
    _require_stable(source)
    if len(value) > _MAX_METADATA_BYTES:
        raise HandoffError(
            f"{source.archive_name} exceeds the metadata size limit"
        )
    return value


def _bounded_bytes(path: Path, *, label: str) -> bytes:
    return _bounded_source_bytes(_regular_source(path, archive_name=label))


def normalize_stellarium_version(value: str) -> str:
    if not isinstance(value, str):
        raise HandoffError("Stellarium application version must be a string")
    match = _VERSION_RE.fullmatch(value.strip())
    if match is None:
        raise HandoffError("Stellarium application version is invalid")
    major, minor, patch = match.groups()
    normalized = f"{int(major)}.{int(minor)}.{int(patch or '0')}"
    if int(major) != 26:
        raise HandoffError("Stellarium version must be in supported series 26.x")
    return normalized


def read_stellarium_version(app: Path) -> str:
    if app.is_symlink() or not app.is_dir() or app.suffix != ".app":
        raise HandoffError("Stellarium app must be an existing real .app bundle")
    info_path = app / "Contents" / "Info.plist"
    raw = _bounded_bytes(info_path, label="Stellarium Info.plist")
    try:
        payload = plistlib.loads(raw)
    except (plistlib.InvalidFileException, ValueError) as exc:
        raise HandoffError("Stellarium Info.plist is invalid") from exc
    if not isinstance(payload, dict):
        raise HandoffError("Stellarium Info.plist must contain a dictionary")
    return normalize_stellarium_version(payload.get("CFBundleShortVersionString"))


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise HandoffError(f"duplicate capability JSON key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise HandoffError(f"non-finite capability JSON value: {value}")


def _bind_capability_source(source: _Source) -> tuple[str, _Source]:
    raw = _bounded_source_bytes(source)
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise HandoffError("local-capability-evidence.json is invalid") from exc
    if not isinstance(payload, dict):
        raise HandoffError("local-capability-evidence.json must contain an object")
    if payload.get("schema_version") != "local-capability-evidence/v1":
        raise HandoffError("local capability evidence schema is invalid")
    version = normalize_stellarium_version(payload.get("stellarium_version"))
    return version, replace(source, content=raw)


def _sha256_file(source: _Source) -> str:
    digest = hashlib.sha256()
    with source.path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    _require_stable(source)
    return digest.hexdigest()


def build_screenshot_inventory(
    evidence_dir: Path,
) -> tuple[bytes, list[_Source]]:
    screenshot_dir = evidence_dir / "screenshots"
    if screenshot_dir.is_symlink() or not screenshot_dir.is_dir():
        raise HandoffError("screenshots must be an existing real directory")
    paths = sorted(
        path
        for path in screenshot_dir.glob("*.png")
        if not path.name.startswith("._")
    )
    if not paths:
        raise HandoffError("evidence requires at least one screenshot")
    if len(paths) > _MAX_SCREENSHOTS:
        raise HandoffError("evidence supports at most 30 screenshots")
    sources = [
        _regular_source(
            path,
            archive_name=f"screenshots/{path.name}",
        )
        for path in paths
    ]
    inventory = "".join(
        f"{_sha256_file(source)}  {source.archive_name}\n"
        for source in sources
    ).encode("utf-8")
    return inventory, sources


def _tar_info(name: str, *, size: int, directory: bool = False) -> tarfile.TarInfo:
    info = tarfile.TarInfo(_canonical_archive_name(name))
    info.size = 0 if directory else size
    info.mode = 0o755 if directory else 0o644
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    if directory:
        info.type = tarfile.DIRTYPE
    return info


def _add_source(archive: tarfile.TarFile, source: _Source) -> None:
    if source.content is not None:
        archive.addfile(
            _tar_info(source.archive_name, size=len(source.content)),
            fileobj=_BytesReader(source.content),
        )
        return
    with source.path.open("rb") as handle:
        archive.addfile(
            _tar_info(source.archive_name, size=source.size),
            fileobj=handle,
        )
    _require_stable(source)


def _write_archive(
    handle: BinaryIO,
    *,
    sources: list[_Source],
    inventory: bytes,
    screenshots: list[_Source],
) -> None:
    with gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0) as compressed:
        with tarfile.open(
            mode="w",
            fileobj=compressed,
            format=tarfile.PAX_FORMAT,
        ) as archive:
            for source in sources:
                _add_source(archive, source)
            archive.addfile(
                _tar_info("screenshot-sha256.txt", size=len(inventory)),
                fileobj=_BytesReader(inventory),
            )
            archive.addfile(_tar_info("screenshots", size=0, directory=True))
            for screenshot in screenshots:
                _add_source(archive, screenshot)


class _BytesReader:
    def __init__(self, value: bytes) -> None:
        self._value = value
        self._offset = 0

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self._value) - self._offset
        start = self._offset
        self._offset = min(len(self._value), start + size)
        return self._value[start : self._offset]


def create_handoff_archive(
    *,
    evidence_dir: Path,
    stellarium_app: Path,
    output: Path,
) -> Path:
    if evidence_dir.is_symlink() or not evidence_dir.is_dir():
        raise HandoffError("evidence directory must be an existing real directory")
    if output.suffixes[-2:] != [".tar", ".gz"]:
        raise HandoffError("archive output must end with .tar.gz")
    if output.exists() or output.is_symlink():
        raise HandoffError(f"archive output already exists: {output}")
    if output.parent.is_symlink() or not output.parent.is_dir():
        raise HandoffError("archive output parent must be an existing real directory")

    sources = [
        _regular_source(evidence_dir / name, archive_name=name)
        for name in _REQUIRED_SOURCE_FILES
    ]
    installed_version = read_stellarium_version(stellarium_app)
    capability_version, sources[0] = _bind_capability_source(sources[0])
    if capability_version != installed_version:
        raise HandoffError(
            f"capability Stellarium version {capability_version} does not match "
            f"the installed Stellarium version {installed_version}"
        )

    inventory, screenshots = build_screenshot_inventory(evidence_dir)

    descriptor, temporary_name = tempfile.mkstemp(
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w+b") as handle:
            _write_archive(
                handle,
                sources=sources,
                inventory=inventory,
                screenshots=screenshots,
            )
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, output)
        except FileExistsError as exc:
            raise HandoffError(f"archive output already exists: {output}") from exc
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create one version-bound B9-G6 evidence handoff archive.",
    )
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--stellarium-app", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--print-stellarium-version",
        action="store_true",
        help="print the normalized actual app version without creating an archive",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        installed_version = read_stellarium_version(args.stellarium_app)
        if args.print_stellarium_version:
            if args.evidence_dir is not None or args.output is not None:
                raise HandoffError(
                    "version-only mode does not accept evidence or output paths"
                )
            print(installed_version)
            return 0
        if args.evidence_dir is None or args.output is None:
            raise HandoffError(
                "--evidence-dir and --output are required for archive creation"
            )
        output = create_handoff_archive(
            evidence_dir=args.evidence_dir,
            stellarium_app=args.stellarium_app,
            output=args.output,
        )
    except (HandoffError, OSError) as exc:
        print(f"B9 G6 handoff failed: {exc}", file=sys.stderr)
        return 1
    print(f"Stellarium version: {installed_version}")
    print(f"B9 G6 handoff archive: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
