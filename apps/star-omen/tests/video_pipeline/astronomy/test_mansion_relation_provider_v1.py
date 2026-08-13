from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from skyfield_data import get_skyfield_data_path

from src.video_pipeline.asterisms import (
    AngularThresholdV1,
    MansionRegionObservationV1,
    load_asterism_catalog,
)
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


def shanghai_observer() -> ObserverV1:
    return ObserverV1(
        latitude_deg=31.2304,
        longitude_deg=121.4737,
        elevation_m=4.0,
        timezone="Asia/Shanghai",
    )


def test_provider_binds_mars_bi_assessment_to_time_and_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = build_provider(monkeypatch)
    at = datetime(2026, 8, 12, 0, tzinfo=timezone.utc)

    observation = provider.assess_mansion_relation(
        body_id="mars",
        mansion_id="bi-xiu",
        relation_term="临",
        at_utc=at,
        observer=shanghai_observer(),
    )

    assert observation.schema_version == "mansion-relation-observation/v1"
    assert observation.body_id == "mars"
    assert observation.at_utc == at
    assert observation.asterism_catalog_sha256 == provider.catalog.sha256
    assert observation.assessment.mansion_id == "bi-xiu"
    assert observation.assessment.target_position.object_id == "mars"
    assert observation.assessment.west_boundary_position.object_id == "hip:20889"
    assert observation.assessment.east_boundary_position.object_id == "hip:26207"
    assert observation.assessment.nearest_member_object_id in {
        "hip:20889",
        "hip:20648",
        "hip:20455",
        "hip:20205",
        "hip:21421",
        "hip:20885",
        "hip:20713",
        "hip:18724",
    }
    assert observation.assessment.interpretation_status == "ambiguous_relation"
    assert observation.assessment.inferred_classical_relation is None
    assert observation.assessment.near_asterism_status == "not_evaluated"


@pytest.mark.parametrize(
    ("mansion_id", "west_id", "east_id"),
    [
        ("jiao-xiu", "hip:65474", "hip:69427"),
        ("shi-xiu", "hip:113963", "hip:1067"),
    ],
)
def test_provider_binds_region_only_assessment_without_member_proximity(
    monkeypatch: pytest.MonkeyPatch,
    mansion_id: str,
    west_id: str,
    east_id: str,
) -> None:
    provider = build_provider(monkeypatch)
    at = datetime(2026, 8, 12, 0, tzinfo=timezone.utc)

    observation = provider.assess_mansion_region(
        body_id="mars",
        mansion_id=mansion_id,
        at_utc=at,
        observer=shanghai_observer(),
    )

    assert isinstance(observation, MansionRegionObservationV1)
    assert observation.schema_version == "mansion-region-observation/v1"
    assert observation.body_id == "mars"
    assert observation.at_utc == at
    assert observation.asterism_catalog_sha256 == provider.catalog.sha256
    assert observation.assessment.mansion_id == mansion_id
    assert observation.assessment.target_position.object_id == "mars"
    assert observation.assessment.west_boundary_position.object_id == west_id
    assert observation.assessment.east_boundary_position.object_id == east_id
    assert observation.assessment.reference_frame == "apparent-equatorial-of-date"
    assert not hasattr(observation.assessment, "nearest_member_object_id")


def test_provider_applies_only_an_explicit_versioned_near_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = build_provider(monkeypatch)

    observation = provider.assess_mansion_relation(
        body_id="mars",
        mansion_id="bi-xiu",
        relation_term="临",
        at_utc=datetime(2026, 8, 12, 0, tzinfo=timezone.utc),
        observer=shanghai_observer(),
        near_threshold=AngularThresholdV1(
            threshold_id="research-near-asterism-v1",
            max_separation_deg=180.0,
        ),
    )

    assert observation.assessment.near_asterism_status == "within_threshold"
    assert observation.assessment.threshold_id == "research-near-asterism-v1"


def test_provider_assesses_complete_non_gold_mansion_members(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = build_provider(monkeypatch)

    observation = provider.assess_mansion_relation(
        body_id="mars",
        mansion_id="jiao-xiu",
        relation_term="临",
        at_utc=datetime(2026, 8, 12, 0, tzinfo=timezone.utc),
        observer=shanghai_observer(),
    )

    assert observation.assessment.nearest_member_object_id in {
        "hip:65474",
        "hip:66249",
    }
    assert observation.assessment.interpretation_status == "ambiguous_relation"
    assert observation.assessment.inferred_classical_relation is None


def test_provider_preserves_hipparcos_epoch_and_proper_motion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = build_provider(monkeypatch)
    resolution = provider.catalog.catalog.resolve("hip:21421")

    star = provider._star_from_catalog_resolution(resolution)

    assert star.epoch == pytest.approx(2448349.0625)
    assert star.ra_mas_per_year == pytest.approx(62.78)
    assert star.dec_mas_per_year == pytest.approx(-189.36)


def test_provider_rejects_unknown_or_ambiguous_mansions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = build_provider(monkeypatch)

    with pytest.raises(KeyError):
        provider.assess_mansion_relation(
            body_id="mars",
            mansion_id="not-a-mansion",
            relation_term="临",
            at_utc=datetime(2026, 8, 12, 0, tzinfo=timezone.utc),
            observer=shanghai_observer(),
        )

    with pytest.raises(ValueError, match="verified complete member catalog.*region-only"):
        provider.assess_mansion_relation(
            body_id="mars",
            mansion_id="yi-xiu",
            relation_term="临",
            at_utc=datetime(2026, 8, 12, 0, tzinfo=timezone.utc),
            observer=shanghai_observer(),
        )
