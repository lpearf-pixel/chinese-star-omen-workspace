from __future__ import annotations

from pathlib import Path

import pytest

from src.video_pipeline.asterisms import load_asterism_catalog
from src.video_pipeline.asterisms.mansion_regions import (
    AngularThresholdV1,
    EquatorialPositionV1,
    MansionRegionAssessmentV1,
    assess_mansion_region,
    assess_single_time_relation,
)


APP_ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = APP_ROOT / "data" / "video_pipeline" / "asterism_catalog_v1.yaml"


def position(object_id: str, ra_deg: float, dec_deg: float = 0.0) -> EquatorialPositionV1:
    return EquatorialPositionV1(
        object_id=object_id,
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        reference_frame="apparent-equatorial-of-date",
    )


def definitions():
    catalog = load_asterism_catalog(CATALOG_PATH).catalog
    return catalog.asterism("bi-xiu"), catalog.mansion("bi-xiu")


def member_positions(*, nearest_ra: float = 74.0) -> list[EquatorialPositionV1]:
    asterism, _ = definitions()
    ras = [nearest_ra, 66.0, 65.0, 64.0, 69.0, 67.0, 66.5, 60.0]
    return [
        position(object_id, ra_deg)
        for object_id, ra_deg in zip(asterism.member_object_ids, ras, strict=True)
    ]


@pytest.mark.parametrize(
    ("target_ra", "expected"),
    [(67.0, True), (83.999, True), (84.0, False), (66.999, False)],
)
def test_region_only_assessment_is_west_inclusive_and_east_exclusive(
    target_ra: float,
    expected: bool,
) -> None:
    _, mansion = definitions()

    assessment = assess_mansion_region(
        mansion=mansion,
        target=position("mars", target_ra),
        west_boundary=position("hip:20889", 67.0, 19.0),
        east_boundary=position("hip:26207", 84.0, 10.0),
    )

    assert isinstance(assessment, MansionRegionAssessmentV1)
    assert assessment.mansion_id == "bi-xiu"
    assert assessment.in_mansion_region is expected
    assert assessment.target_position == position("mars", target_ra)
    assert assessment.west_boundary_position.object_id == "hip:20889"
    assert assessment.east_boundary_position.object_id == "hip:26207"
    assert not hasattr(assessment, "nearest_member_object_id")


def test_region_only_assessment_handles_the_shi_to_bi_wall_zero_degree_wrap() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog
    mansion = catalog.mansion("shi-xiu")

    inside = assess_mansion_region(
        mansion=mansion,
        target=position("mars", 1.0),
        west_boundary=position("hip:113963", 346.0),
        east_boundary=position("hip:1067", 3.0),
    )
    outside = assess_mansion_region(
        mansion=mansion,
        target=position("mars", 180.0),
        west_boundary=position("hip:113963", 346.0),
        east_boundary=position("hip:1067", 3.0),
    )

    assert inside.in_mansion_region is True
    assert outside.in_mansion_region is False


def test_member_proximity_accepts_complete_non_gold_asterism_catalogs() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog
    asterism = catalog.asterism("jiao-xiu")
    mansion = catalog.mansion("jiao-xiu")

    assessment = assess_single_time_relation(
        relation_term="临",
        asterism=asterism,
        mansion=mansion,
        target=position("mars", 203.5),
        west_boundary=position("hip:65474", 201.0),
        east_boundary=position("hip:69427", 213.0),
        members=[
            position("hip:65474", 201.0),
            position("hip:66249", 203.6),
        ],
    )

    assert assessment.nearest_member_object_id == "hip:66249"
    assert assessment.interpretation_status == "ambiguous_relation"


def test_member_proximity_rejects_ambiguous_asterism_catalogs() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog
    asterism = catalog.asterism("yi-xiu")
    mansion = catalog.mansion("yi-xiu")

    with pytest.raises(ValueError, match="verified complete member catalog.*region-only"):
        assess_single_time_relation(
            relation_term="临",
            asterism=asterism,
            mansion=mansion,
            target=position("mars", 170.0),
            west_boundary=position("hip:53740", 165.0),
            east_boundary=position("hip:59803", 183.0),
            members=[],
        )


def test_single_time_lin_bi_returns_measurements_without_classical_inference() -> None:
    asterism, mansion = definitions()

    assessment = assess_single_time_relation(
        relation_term="临",
        asterism=asterism,
        mansion=mansion,
        target=position("mars", 75.0),
        west_boundary=position("hip:20889", 67.0, 19.0),
        east_boundary=position("hip:26207", 84.0, 10.0),
        members=member_positions(),
    )

    assert assessment.mansion_id == "bi-xiu"
    assert assessment.target_position == position("mars", 75.0)
    assert assessment.west_boundary_position == position("hip:20889", 67.0, 19.0)
    assert assessment.east_boundary_position == position("hip:26207", 84.0, 10.0)
    assert assessment.nearest_member_position == position("hip:20889", 74.0)
    assert assessment.in_mansion_region is True
    assert assessment.interpretation_status == "ambiguous_relation"
    assert assessment.inferred_classical_relation is None
    assert assessment.nearest_member_object_id == "hip:20889"
    assert assessment.nearest_member_angular_separation_deg == pytest.approx(1.0)
    assert assessment.near_asterism_status == "not_evaluated"
    assert assessment.threshold_id is None


@pytest.mark.parametrize(
    ("target_ra", "expected"),
    [(67.0, True), (83.999, True), (84.0, False), (66.999, False)],
)
def test_mansion_interval_is_west_inclusive_and_east_exclusive(
    target_ra: float,
    expected: bool,
) -> None:
    asterism, mansion = definitions()

    assessment = assess_single_time_relation(
        relation_term="临",
        asterism=asterism,
        mansion=mansion,
        target=position("mars", target_ra),
        west_boundary=position("hip:20889", 67.0),
        east_boundary=position("hip:26207", 84.0),
        members=member_positions(),
    )

    assert assessment.in_mansion_region is expected


def test_mansion_interval_handles_zero_degree_wrap() -> None:
    asterism, mansion = definitions()

    inside = assess_single_time_relation(
        relation_term="临",
        asterism=asterism,
        mansion=mansion,
        target=position("mars", 5.0),
        west_boundary=position("hip:20889", 350.0),
        east_boundary=position("hip:26207", 10.0),
        members=member_positions(nearest_ra=4.0),
    )
    outside = assess_single_time_relation(
        relation_term="临",
        asterism=asterism,
        mansion=mansion,
        target=position("mars", 180.0),
        west_boundary=position("hip:20889", 350.0),
        east_boundary=position("hip:26207", 10.0),
        members=member_positions(nearest_ra=4.0),
    )

    assert inside.in_mansion_region is True
    assert outside.in_mansion_region is False


def test_near_asterism_requires_an_explicit_versioned_threshold() -> None:
    asterism, mansion = definitions()

    assessment = assess_single_time_relation(
        relation_term="临",
        asterism=asterism,
        mansion=mansion,
        target=position("mars", 75.0),
        west_boundary=position("hip:20889", 67.0),
        east_boundary=position("hip:26207", 84.0),
        members=member_positions(),
        near_threshold=AngularThresholdV1(
            threshold_id="research-near-asterism-v1",
            max_separation_deg=1.5,
        ),
    )

    assert assessment.near_asterism_status == "within_threshold"
    assert assessment.threshold_id == "research-near-asterism-v1"


@pytest.mark.parametrize("relation_term", ["犯", "入", "守", "留"])
def test_single_time_sample_never_infers_temporal_or_contact_relations(
    relation_term: str,
) -> None:
    asterism, mansion = definitions()

    assessment = assess_single_time_relation(
        relation_term=relation_term,
        asterism=asterism,
        mansion=mansion,
        target=position("mars", 75.0),
        west_boundary=position("hip:20889", 67.0),
        east_boundary=position("hip:26207", 84.0),
        members=member_positions(),
    )

    assert assessment.interpretation_status == "unsupported_single_time_relation"
    assert assessment.inferred_classical_relation is None


def test_assessment_rejects_frame_and_member_identity_mismatches() -> None:
    asterism, mansion = definitions()
    mismatched_target = EquatorialPositionV1(
        object_id="mars",
        ra_deg=75.0,
        dec_deg=0.0,
        reference_frame="icrs-j2000",
    )

    with pytest.raises(ValueError, match="same reference frame"):
        assess_single_time_relation(
            relation_term="临",
            asterism=asterism,
            mansion=mansion,
            target=mismatched_target,
            west_boundary=position("hip:20889", 67.0),
            east_boundary=position("hip:26207", 84.0),
            members=member_positions(),
        )

    with pytest.raises(ValueError, match="member object IDs"):
        assess_single_time_relation(
            relation_term="临",
            asterism=asterism,
            mansion=mansion,
            target=position("mars", 75.0),
            west_boundary=position("hip:20889", 67.0),
            east_boundary=position("hip:26207", 84.0),
            members=member_positions()[:-1],
        )
