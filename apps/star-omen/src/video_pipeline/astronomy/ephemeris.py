from __future__ import annotations

import hashlib
import os
import platform
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..asterisms.catalog import AsterismCatalogSnapshotV1
from .conventions import ScientificConventionsSnapshotV1

_LOGICAL_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}\.bsp$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


class EphemerisFileSpecV1(_StrictModel):
    schema_version: Literal["ephemeris-file-spec/v1"] = "ephemeris-file-spec/v1"
    logical_name: str = Field(pattern=_LOGICAL_NAME_RE.pattern)
    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_size_bytes: int | None = Field(default=None, strict=True, gt=0)
    max_size_bytes: int = Field(strict=True, gt=0, le=1024 * 1024 * 1024)

    @model_validator(mode="after")
    def validate_sizes(self) -> "EphemerisFileSpecV1":
        if (
            self.expected_size_bytes is not None
            and self.expected_size_bytes > self.max_size_bytes
        ):
            raise ValueError("expected_size_bytes exceeds max_size_bytes")
        return self


class EphemerisProvenanceV1(_StrictModel):
    schema_version: Literal["ephemeris-provenance/v1"] = "ephemeris-provenance/v1"
    logical_name: str = Field(pattern=_LOGICAL_NAME_RE.pattern)
    byte_size: int = Field(strict=True, gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class VerifiedEphemerisFile:
    path: Path
    logical_name: str
    byte_size: int
    sha256: str

    def safe_provenance(self) -> EphemerisProvenanceV1:
        return EphemerisProvenanceV1(
            logical_name=self.logical_name,
            byte_size=self.byte_size,
            sha256=self.sha256,
        )


class AstronomyToolchainManifestV1(_StrictModel):
    schema_version: Literal["astronomy-toolchain/v1"] = "astronomy-toolchain/v1"
    python_version: str = Field(min_length=1, max_length=64)
    skyfield_version: str = Field(min_length=1, max_length=64)
    skyfield_data_version: str | None = Field(default=None, min_length=1, max_length=64)
    ephemeris: EphemerisProvenanceV1
    timescale_source: Literal["skyfield-builtin"]
    conventions_schema_version: Literal["scientific-conventions/v1"]
    conventions_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    asterism_catalog_schema_version: Literal["asterism-catalog/v1"]
    asterism_catalog_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_ephemeris_file(
    path: str | Path,
    spec: EphemerisFileSpecV1,
) -> VerifiedEphemerisFile:
    candidate = Path(path)
    if candidate.is_symlink():
        raise ValueError("ephemeris file must not be a symlink")
    if not candidate.exists():
        raise FileNotFoundError(candidate)
    if not candidate.is_file():
        raise ValueError("ephemeris path must be a regular file")
    if candidate.suffix.lower() != ".bsp":
        raise ValueError("ephemeris file must use the .bsp suffix")
    stat = candidate.stat()
    if stat.st_size <= 0:
        raise ValueError("ephemeris file is empty")
    if stat.st_size > spec.max_size_bytes:
        raise ValueError("ephemeris file is too large")
    if spec.expected_size_bytes is not None and stat.st_size != spec.expected_size_bytes:
        raise ValueError("ephemeris file size mismatch")
    digest = _sha256_file(candidate)
    if digest != spec.expected_sha256:
        raise ValueError("ephemeris file sha256 mismatch")
    resolved = candidate.resolve(strict=True)
    if not os.path.samefile(candidate, resolved):
        raise ValueError("ephemeris file identity changed while verifying")
    return VerifiedEphemerisFile(
        path=resolved,
        logical_name=spec.logical_name,
        byte_size=stat.st_size,
        sha256=digest,
    )


def build_toolchain_manifest(
    *,
    verified_ephemeris: VerifiedEphemerisFile,
    conventions: ScientificConventionsSnapshotV1,
    catalog: AsterismCatalogSnapshotV1,
    skyfield_version: str,
    skyfield_data_version: str | None = None,
) -> AstronomyToolchainManifestV1:
    return AstronomyToolchainManifestV1(
        python_version=platform.python_version(),
        skyfield_version=skyfield_version,
        skyfield_data_version=skyfield_data_version,
        ephemeris=verified_ephemeris.safe_provenance(),
        timescale_source=conventions.conventions.time.timescale_source,
        conventions_schema_version=conventions.conventions.schema_version,
        conventions_sha256=conventions.sha256,
        asterism_catalog_schema_version=catalog.catalog.schema_version,
        asterism_catalog_sha256=catalog.sha256,
    )
