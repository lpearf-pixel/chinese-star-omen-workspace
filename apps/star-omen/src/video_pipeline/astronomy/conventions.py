from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

_MAX_ASSET_BYTES = 256 * 1024


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


class TimeConventionsV1(_StrictModel):
    persisted_scale: Literal["utc"]
    input_format: Literal["rfc3339-z"]
    skyfield_internal_scales: list[Literal["tt", "tdb"]]
    timescale_source: Literal["skyfield-builtin"]


class CoordinateConventionsV1(_StrictModel):
    identity_frame: Literal["icrs"]
    apparent_frame: Literal["gcrs"]
    ecliptic_frame: Literal["ecliptic-of-date"]
    topocentric_frame: Literal["wgs84-altaz"]
    longitude_sign: Literal["east-positive"]
    latitude_sign: Literal["north-positive"]


class RefractionConventionsV1(_StrictModel):
    scientific_geometry: Literal["disabled"]
    display_refraction: Literal["explicit-only"]


class EphemerisConventionsV1(_StrictModel):
    runtime_download: Literal["forbidden"]
    verification: Literal["sha256-required"]
    accepted_suffixes: list[Literal[".bsp"]]
    timescale_builtin: Literal[True]


class ScientificConventionsV1(_StrictModel):
    schema_version: Literal["scientific-conventions/v1"]
    conventions_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._:/-]{0,159}$")
    time: TimeConventionsV1
    coordinates: CoordinateConventionsV1
    refraction: RefractionConventionsV1
    ephemeris: EphemerisConventionsV1


class ScientificConventionsSnapshotV1(_StrictModel):
    schema_version: Literal["scientific-conventions-snapshot/v1"] = (
        "scientific-conventions-snapshot/v1"
    )
    logical_name: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}\.ya?ml$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(gt=0, le=_MAX_ASSET_BYTES)
    conventions: ScientificConventionsV1


def _read_yaml_asset(path: Path, *, max_bytes: int = _MAX_ASSET_BYTES) -> tuple[bytes, object]:
    if path.is_symlink():
        raise ValueError("scientific convention asset must not be a symlink")
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_file():
        raise ValueError("scientific convention asset must be a regular file")
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("scientific convention asset must use yaml")
    size = path.stat().st_size
    if size <= 0:
        raise ValueError("scientific convention asset is empty")
    if size > max_bytes:
        raise ValueError("scientific convention asset is too large")
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("scientific convention asset must be strict UTF-8") from exc
    try:
        payload = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError("scientific convention asset is invalid YAML") from exc
    if not isinstance(payload, dict):
        raise ValueError("scientific convention asset root must be a mapping")
    return raw, payload


def load_scientific_conventions(path: str | Path) -> ScientificConventionsSnapshotV1:
    asset_path = Path(path)
    raw, payload = _read_yaml_asset(asset_path)
    model = ScientificConventionsV1.model_validate(payload)
    return ScientificConventionsSnapshotV1(
        logical_name=asset_path.name,
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_size=len(raw),
        conventions=model,
    )
