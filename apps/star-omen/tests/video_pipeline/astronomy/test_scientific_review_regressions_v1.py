from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.video_pipeline.astronomy import (
    EphemerisFileSpecV1,
    MoonPhaseEventV1,
    ScientificObservationV1,
    SkyfieldEphemerisProvider,
    load_scientific_conventions,
    verify_ephemeris_file,
)
from src.video_pipeline.asterisms import load_asterism_catalog


APP_ROOT = Path(__file__).resolve().parents[3]
CONVENTIONS_PATH = APP_ROOT / "data" / "video_pipeline" / "scientific_conventions_v1.yaml"
CATALOG_PATH = APP_ROOT / "data" / "video_pipeline" / "asterism_catalog_v1.yaml"


def write_fake_bsp(path: Path, payload: bytes = b"DAF/SPK review fixture") -> str:
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def verified_fake_ephemeris(path: Path):
    sha256 = write_fake_bsp(path)
    return verify_ephemeris_file(
        path,
        EphemerisFileSpecV1(
            logical_name=path.name,
            expected_sha256=sha256,
            expected_size_bytes=path.stat().st_size,
            max_size_bytes=1024,
        ),
    )


def test_verified_ephemeris_detects_content_mutation_before_load(tmp_path: Path) -> None:
    path = tmp_path / "review.bsp"
    verified = verified_fake_ephemeris(path)
    path.write_bytes(b"DAF/SPK changed bytes")

    with pytest.raises(ValueError, match="changed"):
        verified.assert_unchanged()


def test_verified_ephemeris_detects_inode_replacement_even_with_same_bytes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "review.bsp"
    verified = verified_fake_ephemeris(path)
    original = path.read_bytes()
    replacement = tmp_path / "replacement.bsp"
    replacement.write_bytes(original)
    replacement.replace(path)

    with pytest.raises(ValueError, match="identity"):
        verified.assert_unchanged()


def test_provider_rechecks_verified_ephemeris_before_skyfield_load(
    tmp_path: Path,
) -> None:
    path = tmp_path / "review.bsp"
    verified = verified_fake_ephemeris(path)
    path.write_bytes(b"DAF/SPK changed bytes")

    with pytest.raises(ValueError, match="changed"):
        SkyfieldEphemerisProvider(
            verified_ephemeris=verified,
            conventions=load_scientific_conventions(CONVENTIONS_PATH),
            catalog=load_asterism_catalog(CATALOG_PATH),
        )


@pytest.mark.parametrize(
    "value",
    [
        datetime(2026, 7, 21, 11),
        datetime(2026, 7, 21, 19, tzinfo=timezone(timedelta(hours=8))),
    ],
)
def test_scientific_observation_requires_explicit_utc(value: datetime) -> None:
    with pytest.raises(ValidationError):
        ScientificObservationV1(
            object_id="moon",
            at_utc=value,
            identity_ra_deg=1.0,
            identity_dec_deg=1.0,
            apparent_ra_deg=1.0,
            apparent_dec_deg=1.0,
            ecliptic_longitude_deg=1.0,
            ecliptic_latitude_deg=1.0,
        )


@pytest.mark.parametrize(
    "value",
    [
        datetime(2026, 7, 21, 11),
        datetime(2026, 7, 21, 19, tzinfo=timezone(timedelta(hours=8))),
    ],
)
def test_moon_phase_event_requires_explicit_utc(value: datetime) -> None:
    with pytest.raises(ValidationError):
        MoonPhaseEventV1(
            phase_index=0,
            phase_name="new-moon",
            utc=value,
        )


def test_observation_altaz_is_all_or_none() -> None:
    with pytest.raises(ValidationError):
        ScientificObservationV1(
            object_id="moon",
            at_utc=datetime(2026, 7, 21, 11, tzinfo=timezone.utc),
            identity_ra_deg=1.0,
            identity_dec_deg=1.0,
            apparent_ra_deg=1.0,
            apparent_dec_deg=1.0,
            ecliptic_longitude_deg=1.0,
            ecliptic_latitude_deg=1.0,
            topocentric_altitude_deg=10.0,
            topocentric_azimuth_deg=None,
        )
