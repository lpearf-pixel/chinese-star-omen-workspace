from __future__ import annotations

from pathlib import Path
from copy import deepcopy

import pytest
import yaml
from pydantic import ValidationError

from src.video_pipeline.asterisms import (
    AsterismNarrationPolicy,
    AsterismStatus,
    load_asterism_catalog,
)


APP_ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = APP_ROOT / "data" / "video_pipeline" / "asterism_catalog_v1.yaml"


def test_committed_catalog_resolves_spica_by_exact_id_and_alias() -> None:
    snapshot = load_asterism_catalog(CATALOG_PATH)
    catalog = snapshot.catalog

    by_id = catalog.resolve("hip:65474")
    by_alias = catalog.resolve("  SPICA  ")

    assert by_id.status is AsterismStatus.VERIFIED_IDENTITY
    assert by_id.modern_object_id == "hip:65474"
    assert by_id.traditional_star_id == "jiao-xiu-1"
    assert by_id.asterism_id == "jiao-xiu"
    assert by_id.canonical_chinese_name == "角宿一"
    assert by_id.reference_coordinates.ra_deg == pytest.approx(201.298247375, abs=1e-9)
    assert by_id.reference_coordinates.dec_deg == pytest.approx(-11.1613194722, abs=1e-9)
    assert by_id.narration_policy is AsterismNarrationPolicy.EXPLICIT_STAR_NAME
    assert by_alias == by_id
    assert len(snapshot.sha256) == 64
    assert str(CATALOG_PATH.resolve()) not in snapshot.model_dump_json()


def test_committed_catalog_contains_complete_bi_asterism_and_mansion() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog

    definition = catalog.asterism("bi-xiu")
    mansion = catalog.mansion("bi-xiu")

    assert definition.canonical_chinese_name == "毕宿"
    assert definition.aliases == ["畢宿"]
    assert definition.completeness_status == "complete_gold_sample"
    assert definition.member_object_ids == [
        "hip:20889",
        "hip:20648",
        "hip:20455",
        "hip:20205",
        "hip:21421",
        "hip:20885",
        "hip:20713",
        "hip:18724",
    ]
    assert definition.related_object_ids == ["hip:21683"]
    assert definition.defining_star_object_id == "hip:20889"
    assert mansion.sequence_index == 19
    assert mansion.west_boundary_object_id == "hip:20889"
    assert mansion.east_boundary_object_id == "hip:26207"
    assert mansion.boundary_model == "polar-great-circles"
    assert mansion.coordinate_system == "apparent-equatorial-of-date"
    assert mansion.provenance_class == "derived_region"


def test_committed_catalog_resolves_bi_members_by_traditional_name() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog

    simplified = catalog.resolve("毕宿五")
    traditional = catalog.resolve("畢宿五")

    assert simplified.modern_object_id == "hip:21421"
    assert traditional == simplified
    assert simplified.asterism_id == "bi-xiu"
    assert simplified.status is AsterismStatus.VERIFIED_IDENTITY

    related = catalog.resolve("附耳")
    assert related.modern_object_id == "hip:21683"
    assert related.asterism_id == "fu-er"
    assert related.status is AsterismStatus.AMBIGUOUS


def test_asterism_definitions_reject_unknown_and_overlapping_members(
    tmp_path: Path,
) -> None:
    text = CATALOG_PATH.read_text(encoding="utf-8")

    unknown = tmp_path / "unknown-member.yaml"
    unknown.write_text(
        text.replace(
            "member_object_ids:\n",
            "member_object_ids:\n      - hip:99999\n",
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown member object"):
        load_asterism_catalog(unknown)

    overlap = tmp_path / "overlapping-member.yaml"
    overlap.write_text(
        text.replace(
            "related_object_ids: [hip:21683]",
            "related_object_ids: [hip:21683, hip:20889]",
            1,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="member and related object IDs must be disjoint"):
        load_asterism_catalog(overlap)


def test_unknown_objects_remain_unresolved_without_nearest_star_guessing() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog

    result = catalog.resolve("near:201.298:-11.161")

    assert result.status is AsterismStatus.UNRESOLVED
    assert result.narration_policy is AsterismNarrationPolicy.BLOCKED
    assert result.modern_object_id is None
    assert result.canonical_chinese_name is None
    assert result.source_refs == []


def test_catalog_source_is_pinned_to_exact_stellarium_and_simbad_records() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog
    entry = catalog.entry("hip:65474")
    sources = {source.source_id: source for source in catalog.sources}

    stellarium = sources[entry.source_refs[0]]
    simbad = sources[entry.source_refs[1]]

    assert stellarium.revision == "3972e97101e4321079279b5e5660b074fafc030a"
    assert stellarium.content_hash_algorithm == "sha256"
    assert stellarium.content_hash == "d036a7f37e3c27ca1197d93739d922808e2a0d60e57b96b7692e7d60ca711229"
    assert stellarium.upstream_content_id_algorithm == "git-sha1"
    assert stellarium.upstream_content_id == "fe8761576dc6c5cd4a65e3551a81ead6122c895f"
    assert stellarium.locator == '65474|_("角宿一") 1'
    assert simbad.locator == "HIP 65474 / Spica"
    assert simbad.reference_frame == "ICRS J2000"


def test_duplicate_ids_and_aliases_fail_closed(tmp_path: Path) -> None:
    payload = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    duplicate_id = tmp_path / "duplicate-id.yaml"
    duplicate_id_payload = deepcopy(payload)
    duplicate_id_payload["entries"].append(deepcopy(payload["entries"][0]))
    duplicate_id.write_text(yaml.safe_dump(duplicate_id_payload, allow_unicode=True), encoding="utf-8")
    with pytest.raises((ValidationError, ValueError)):
        load_asterism_catalog(duplicate_id)

    duplicate_alias = tmp_path / "duplicate-alias.yaml"
    duplicate_alias_payload = deepcopy(payload)
    synthetic = deepcopy(payload["entries"][0])
    synthetic.update(
        {
            "modern_object_id": "hip:99999",
            "traditional_star_id": "synthetic-test",
            "asterism_id": "synthetic",
            "canonical_chinese_name": "测试星",
            "aliases": ["spica"],
        }
    )
    duplicate_alias_payload["entries"].append(synthetic)
    duplicate_alias.write_text(
        yaml.safe_dump(duplicate_alias_payload, allow_unicode=True),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="alias"):
        load_asterism_catalog(duplicate_alias)


def test_catalog_rejects_unpinned_sources_and_unsafe_status_claims(tmp_path: Path) -> None:
    text = CATALOG_PATH.read_text(encoding="utf-8")
    unpinned = tmp_path / "unpinned.yaml"
    unpinned.write_text(
        text.replace(
            "revision: 3972e97101e4321079279b5e5660b074fafc030a",
            "revision: latest",
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_asterism_catalog(unpinned)

    low_confidence = tmp_path / "low-confidence.yaml"
    low_confidence.write_text(
        text.replace("confidence: 1.0", "confidence: 0.5"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="verified_identity"):
        load_asterism_catalog(low_confidence)
