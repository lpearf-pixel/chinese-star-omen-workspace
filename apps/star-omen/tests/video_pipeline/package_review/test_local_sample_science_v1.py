from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from skyfield_data import get_skyfield_data_path

from src.video_pipeline.asterisms import load_asterism_catalog
from src.video_pipeline.astronomy import (
    EphemerisFileSpecV1,
    SkyfieldEphemerisProvider,
    load_scientific_conventions,
)
from src.video_pipeline.contracts import AstronomyEventV1, ObserverV1
from src.video_pipeline.local_sample import build_july_21_event


APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parents[1]
JULY_FIXTURE = (
    WORKSPACE_ROOT / "tests" / "fixtures" / "evidence" / "v1" / "july-21-event.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def provider(monkeypatch: pytest.MonkeyPatch) -> SkyfieldEphemerisProvider:
    def forbid_download(*args: object, **kwargs: object) -> None:
        raise AssertionError("local sample attempted a network download")

    monkeypatch.setattr("skyfield.iokit.download", forbid_download)
    ephemeris_path = Path(get_skyfield_data_path()) / "de421.bsp"
    return SkyfieldEphemerisProvider.from_local_ephemeris(
        ephemeris_path=ephemeris_path,
        ephemeris_spec=EphemerisFileSpecV1(
            logical_name="de421.bsp",
            expected_sha256=sha256_file(ephemeris_path),
            expected_size_bytes=ephemeris_path.stat().st_size,
            max_size_bytes=32 * 1024 * 1024,
        ),
        conventions=load_scientific_conventions(
            APP_ROOT / "data" / "video_pipeline" / "scientific_conventions_v1.yaml"
        ),
        catalog=load_asterism_catalog(
            APP_ROOT / "data" / "video_pipeline" / "asterism_catalog_v1.yaml"
        ),
    )


def shanghai_observer() -> ObserverV1:
    return ObserverV1(
        latitude_deg=31.2304,
        longitude_deg=121.4737,
        elevation_m=4.0,
        timezone="Asia/Shanghai",
    )


def test_july_fixture_equals_verified_offline_provider_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated = build_july_21_event(
        provider=provider(monkeypatch),
        observer=shanghai_observer(),
        at_utc=datetime(2026, 7, 21, 11, tzinfo=timezone.utc),
    )
    fixture = AstronomyEventV1.model_validate_json(
        JULY_FIXTURE.read_text(encoding="utf-8")
    )

    assert fixture == generated
    measurement = generated.measurements[0]
    assert measurement.value == pytest.approx(5.40412185407934, abs=1e-12)
    assert measurement.reference_frame == "topocentric-apparent"
    assert (
        generated.calculation_provenance.ephemeris_sha256
        == "a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc"
    )


def test_july_sample_uses_fixed_target_and_explicit_utc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built = build_july_21_event(
        provider=provider(monkeypatch),
        observer=shanghai_observer(),
        at_utc=datetime(2026, 7, 21, 11, tzinfo=timezone.utc),
    )

    assert built.primary_body == "moon"
    assert built.target_body_or_region == "hip:65474"
    assert built.peak_utc.isoformat() == "2026-07-21T11:00:00+00:00"

    with pytest.raises(ValueError, match="UTC"):
        build_july_21_event(
            provider=provider(monkeypatch),
            observer=shanghai_observer(),
            at_utc=datetime(2026, 7, 21, 11),
        )
