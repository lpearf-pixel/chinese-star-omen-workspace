from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.video_pipeline.astronomy import load_scientific_conventions


APP_ROOT = Path(__file__).resolve().parents[3]
CONVENTIONS_PATH = APP_ROOT / "data" / "video_pipeline" / "scientific_conventions_v1.yaml"


def test_committed_scientific_conventions_are_strict_and_versioned() -> None:
    snapshot = load_scientific_conventions(CONVENTIONS_PATH)
    model = snapshot.conventions

    assert model.schema_version == "scientific-conventions/v1"
    assert model.time.persisted_scale == "utc"
    assert model.time.input_format == "rfc3339-z"
    assert model.time.skyfield_internal_scales == ["tt", "tdb"]
    assert model.coordinates.identity_frame == "icrs"
    assert model.coordinates.apparent_frame == "gcrs"
    assert model.coordinates.ecliptic_frame == "ecliptic-of-date"
    assert model.coordinates.topocentric_frame == "wgs84-altaz"
    assert model.coordinates.longitude_sign == "east-positive"
    assert model.coordinates.latitude_sign == "north-positive"
    assert model.refraction.scientific_geometry == "disabled"
    assert model.ephemeris.runtime_download == "forbidden"
    assert model.ephemeris.verification == "sha256-required"
    assert len(snapshot.sha256) == 64
    assert snapshot.byte_size == CONVENTIONS_PATH.stat().st_size
    assert str(CONVENTIONS_PATH.resolve()) not in snapshot.model_dump_json()


def test_unknown_convention_fields_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "scientific.yaml"
    path.write_text(
        CONVENTIONS_PATH.read_text(encoding="utf-8") + "\nunexpected: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_scientific_conventions(path)


def test_invalid_sign_and_download_policy_are_rejected(tmp_path: Path) -> None:
    text = CONVENTIONS_PATH.read_text(encoding="utf-8")
    invalid_sign = tmp_path / "invalid-sign.yaml"
    invalid_sign.write_text(
        text.replace("longitude_sign: east-positive", "longitude_sign: west-positive"),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_scientific_conventions(invalid_sign)

    invalid_download = tmp_path / "invalid-download.yaml"
    invalid_download.write_text(
        text.replace("runtime_download: forbidden", "runtime_download: allowed"),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_scientific_conventions(invalid_download)


def test_convention_loader_rejects_missing_non_yaml_and_oversized_files(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_scientific_conventions(tmp_path / "missing.yaml")

    wrong_suffix = tmp_path / "conventions.json"
    wrong_suffix.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="yaml"):
        load_scientific_conventions(wrong_suffix)

    oversized = tmp_path / "oversized.yaml"
    oversized.write_bytes(b"x" * (256 * 1024 + 1))
    with pytest.raises(ValueError, match="too large"):
        load_scientific_conventions(oversized)
