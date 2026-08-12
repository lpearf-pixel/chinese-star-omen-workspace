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

EXPECTED_MANSION_CYCLE = [
    (1, "jiao-xiu", "角宿", "hip:65474", "hip:69427"),
    (2, "kang-xiu", "亢宿", "hip:69427", "hip:72622"),
    (3, "di-xiu", "氐宿", "hip:72622", "hip:78265"),
    (4, "fang-xiu", "房宿", "hip:78265", "hip:80112"),
    (5, "xin-xiu", "心宿", "hip:80112", "hip:82514"),
    (6, "wei-tail-xiu", "尾宿", "hip:82514", "hip:88635"),
    (7, "ji-xiu", "箕宿", "hip:88635", "hip:92041"),
    (8, "dou-xiu", "斗宿", "hip:92041", "hip:100345"),
    (9, "niu-xiu", "牛宿", "hip:100345", "hip:102618"),
    (10, "nu-xiu", "女宿", "hip:102618", "hip:106278"),
    (11, "xu-xiu", "虚宿", "hip:106278", "hip:109074"),
    (12, "wei-danger-xiu", "危宿", "hip:109074", "hip:113963"),
    (13, "shi-xiu", "室宿", "hip:113963", "hip:1067"),
    (14, "bi-wall-xiu", "壁宿", "hip:1067", "hip:4463"),
    (15, "kui-xiu", "奎宿", "hip:4463", "hip:8903"),
    (16, "lou-xiu", "娄宿", "hip:8903", "hip:12719"),
    (17, "wei-stomach-xiu", "胃宿", "hip:12719", "hip:17499"),
    (18, "mao-xiu", "昴宿", "hip:17499", "hip:20889"),
    (19, "bi-xiu", "毕宿", "hip:20889", "hip:26207"),
    (20, "zi-xiu", "觜宿", "hip:26207", "hip:26727"),
    (21, "shen-xiu", "参宿", "hip:26727", "hip:30343"),
    (22, "jing-xiu", "井宿", "hip:30343", "hip:41822"),
    (23, "gui-xiu", "鬼宿", "hip:41822", "hip:42313"),
    (24, "liu-xiu", "柳宿", "hip:42313", "hip:46390"),
    (25, "xing-xiu", "星宿", "hip:46390", "hip:48356"),
    (26, "zhang-xiu", "张宿", "hip:48356", "hip:53740"),
    (27, "yi-xiu", "翼宿", "hip:53740", "hip:59803"),
    (28, "zhen-xiu", "轸宿", "hip:59803", "hip:65474"),
]


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


def test_committed_catalog_contains_the_exact_closed_twenty_eight_mansion_cycle() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog

    assert catalog.lunar_mansion_cycle_status == "complete"
    ordered = sorted(catalog.lunar_mansions, key=lambda item: item.sequence_index)
    actual = [
        (
            mansion.sequence_index,
            mansion.mansion_id,
            catalog.asterism(mansion.mansion_id).canonical_chinese_name,
            mansion.west_boundary_object_id,
            mansion.east_boundary_object_id,
        )
        for mansion in ordered
    ]

    assert actual == EXPECTED_MANSION_CYCLE
    assert len({item.west_boundary_object_id for item in ordered}) == 28
    assert all(
        current.east_boundary_object_id == following.west_boundary_object_id
        for current, following in zip(ordered, ordered[1:] + ordered[:1], strict=True)
    )


def test_partial_mansion_asterism_exposes_only_verified_defining_star() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog

    definition = catalog.asterism("角宿")

    assert definition.asterism_id == "jiao-xiu"
    assert definition.member_object_ids == ["hip:65474"]
    assert definition.defining_star_object_id == "hip:65474"
    assert definition.line_segments == []
    assert definition.completeness_status == "partial"


def test_complete_mansion_cycle_rejects_missing_sequence_and_broken_edges(
    tmp_path: Path,
) -> None:
    payload = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    assert payload["lunar_mansion_cycle_status"] == "complete"
    assert len(payload["lunar_mansions"]) == 28

    missing = deepcopy(payload)
    missing["lunar_mansions"] = [
        item for item in missing["lunar_mansions"] if item["sequence_index"] != 12
    ]
    missing_path = tmp_path / "missing-sequence.yaml"
    missing_path.write_text(yaml.safe_dump(missing, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError, match="sequence indices 1 through 28"):
        load_asterism_catalog(missing_path)

    duplicate = deepcopy(payload)
    duplicate["lunar_mansions"][12]["sequence_index"] = 12
    duplicate_path = tmp_path / "duplicate-sequence.yaml"
    duplicate_path.write_text(
        yaml.safe_dump(duplicate, allow_unicode=True),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="sequence indices must be unique"):
        load_asterism_catalog(duplicate_path)

    broken = deepcopy(payload)
    broken["lunar_mansions"][18]["east_boundary_object_id"] = "hip:26727"
    broken_path = tmp_path / "broken-edge.yaml"
    broken_path.write_text(yaml.safe_dump(broken, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError, match="cycle is broken"):
        load_asterism_catalog(broken_path)

    open_cycle = deepcopy(payload)
    open_cycle["lunar_mansions"][27]["east_boundary_object_id"] = "hip:69427"
    open_cycle_path = tmp_path / "open-cycle.yaml"
    open_cycle_path.write_text(
        yaml.safe_dump(open_cycle, allow_unicode=True),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="cycle is broken"):
        load_asterism_catalog(open_cycle_path)


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
