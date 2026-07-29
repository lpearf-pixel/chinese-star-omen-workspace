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
from src.video_pipeline.contracts import ObserverV1


APP_ROOT = Path(__file__).resolve().parents[3]
CONVENTIONS_PATH = APP_ROOT / "data" / "video_pipeline" / "scientific_conventions_v1.yaml"
CATALOG_PATH = APP_ROOT / "data" / "video_pipeline" / "asterism_catalog_v1.yaml"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_provider(monkeypatch: pytest.MonkeyPatch) -> SkyfieldEphemerisProvider:
    def forbid_download(*args: object, **kwargs: object) -> None:
        raise AssertionError("scientific provider attempted a network download")

    monkeypatch.setattr("skyfield.iokit.download", forbid_download)
    ephemeris_path = Path(get_skyfield_data_path()) / "de421.bsp"
    spec = EphemerisFileSpecV1(
        logical_name="de421.bsp",
        expected_sha256=sha256_file(ephemeris_path),
        expected_size_bytes=ephemeris_path.stat().st_size,
        max_size_bytes=32 * 1024 * 1024,
    )
    return SkyfieldEphemerisProvider.from_local_ephemeris(
        ephemeris_path=ephemeris_path,
        ephemeris_spec=spec,
        conventions=load_scientific_conventions(CONVENTIONS_PATH),
        catalog=load_asterism_catalog(CATALOG_PATH),
    )


def test_published_skyfield_moon_phase_example_is_reproduced_offline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = build_provider(monkeypatch)

    degrees = provider.moon_phase_degrees(
        datetime(2020, 11, 19, tzinfo=timezone.utc)
    )

    assert degrees == pytest.approx(51.3, abs=0.05)


def test_published_moon_phase_transition_times_are_reproduced_offline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = build_provider(monkeypatch)

    events = provider.find_moon_phases(
        datetime(2018, 9, 1, tzinfo=timezone.utc),
        datetime(2018, 9, 10, tzinfo=timezone.utc),
    )

    assert [(item.phase_name, item.utc.isoformat()) for item in events] == [
        ("last-quarter", "2018-09-03T02:37:24+00:00"),
        ("new-moon", "2018-09-09T18:01:28+00:00"),
    ]


def test_spica_identity_uses_catalog_coordinates_not_nearest_star(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = build_provider(monkeypatch)
    observer = ObserverV1(
        latitude_deg=31.2304,
        longitude_deg=121.4737,
        elevation_m=4.0,
        timezone="Asia/Shanghai",
    )

    observation = provider.observe_catalog_star(
        modern_object_id="hip:65474",
        at_utc=datetime(2026, 7, 21, 11, tzinfo=timezone.utc),
        observer=observer,
    )

    assert observation.object_id == "hip:65474"
    assert observation.identity_ra_deg == pytest.approx(201.298247375, abs=1e-9)
    assert observation.identity_dec_deg == pytest.approx(-11.1613194722, abs=1e-9)
    assert observation.mapping_status == "verified_identity"
    assert observation.topocentric_altitude_deg is not None
    assert observation.topocentric_azimuth_deg is not None


def test_geocentric_coordinates_are_observer_invariant_but_altaz_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = build_provider(monkeypatch)
    at = datetime(2026, 7, 21, 11, tzinfo=timezone.utc)
    shanghai = ObserverV1(
        latitude_deg=31.2304,
        longitude_deg=121.4737,
        elevation_m=4.0,
        timezone="Asia/Shanghai",
    )
    london = ObserverV1(
        latitude_deg=51.5074,
        longitude_deg=-0.1278,
        elevation_m=11.0,
        timezone="Europe/London",
    )

    first = provider.observe_body(body_id="moon", at_utc=at, observer=shanghai)
    second = provider.observe_body(body_id="moon", at_utc=at, observer=london)

    assert first.identity_ra_deg == pytest.approx(second.identity_ra_deg, abs=1e-12)
    assert first.identity_dec_deg == pytest.approx(second.identity_dec_deg, abs=1e-12)
    assert first.ecliptic_longitude_deg == pytest.approx(
        second.ecliptic_longitude_deg, abs=1e-12
    )
    assert first.topocentric_altitude_deg != pytest.approx(
        second.topocentric_altitude_deg, abs=1e-6
    )
    assert first.topocentric_azimuth_deg != pytest.approx(
        second.topocentric_azimuth_deg, abs=1e-6
    )


def test_scientific_event_builders_emit_frozen_astronomy_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = build_provider(monkeypatch)
    observer = ObserverV1(
        latitude_deg=31.2304,
        longitude_deg=121.4737,
        elevation_m=4.0,
        timezone="Asia/Shanghai",
    )
    at = datetime(2026, 7, 21, 11, tzinfo=timezone.utc)

    separation = provider.calculate_angular_separation_event(
        primary_body="moon",
        target_modern_object_id="hip:65474",
        at_utc=at,
        observer=observer,
    )
    phase = provider.calculate_moon_phase_event(at_utc=at, observer=observer)

    assert separation.schema_version == "astronomy-event/v1"
    assert separation.event_type == "angular-separation"
    assert separation.target_body_or_region == "hip:65474"
    assert separation.quality_status == "verified"
    assert any(
        item.kind == "angular-separation-deg" for item in separation.measurements
    )
    assert phase.event_type == "moon-phase-angle"
    assert phase.primary_body == "moon"
    assert phase.target_body_or_region == "sun"
    assert any(item.kind == "moon-phase-angle-deg" for item in phase.measurements)


def test_provider_rejects_naive_time_and_unknown_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = build_provider(monkeypatch)
    observer = ObserverV1(
        latitude_deg=31.2304,
        longitude_deg=121.4737,
        elevation_m=4.0,
        timezone="Asia/Shanghai",
    )

    with pytest.raises(ValueError, match="UTC"):
        provider.observe_body(
            body_id="moon",
            at_utc=datetime(2026, 7, 21, 11),
            observer=observer,
        )
    with pytest.raises(ValueError, match="unsupported body"):
        provider.observe_body(
            body_id="pluto",
            at_utc=datetime(2026, 7, 21, 11, tzinfo=timezone.utc),
            observer=observer,
        )
