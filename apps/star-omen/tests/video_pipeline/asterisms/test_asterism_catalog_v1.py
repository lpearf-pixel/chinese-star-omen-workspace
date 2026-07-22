from __future__ import annotations

from pathlib import Path

import pytest
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
    assert stellarium.content_sha == "fe8761576dc6c5cd4a65e3551a81ead6122c895f"
    assert stellarium.locator == '65474|_("角宿一") 1'
    assert simbad.locator == "HIP 65474 / Spica"
    assert simbad.reference_frame == "ICRS J2000"


def test_duplicate_ids_and_aliases_fail_closed(tmp_path: Path) -> None:
    text = CATALOG_PATH.read_text(encoding="utf-8")
    duplicate_id = tmp_path / "duplicate-id.yaml"
    duplicate_id.write_text(
        text + "\n" + text.split("entries:\n", 1)[1],
        encoding="utf-8",
    )
    with pytest.raises((ValidationError, ValueError)):
        load_asterism_catalog(duplicate_id)

    duplicate_alias = tmp_path / "duplicate-alias.yaml"
    duplicate_alias.write_text(
        text.replace(
            "entries:\n",
            "entries:\n"
            "  - modern_object_id: hip:99999\n"
            "    traditional_star_id: synthetic-test\n"
            "    asterism_id: synthetic\n"
            "    canonical_chinese_name: 测试星\n"
            "    aliases: [spica]\n"
            "    catalog_epoch: J2000\n"
            "    reference_coordinates:\n"
            "      frame: icrs\n"
            "      epoch: J2000\n"
            "      ra_deg: 0.0\n"
            "      dec_deg: 0.0\n"
            "    source_refs:\n"
            "      - source:stellarium-chinese-skyculture\n"
            "      - source:simbad-spica\n"
            "    mapping_method: catalog-identity\n"
            "    confidence: 1.0\n"
            "    editorial_status: verified_identity\n",
        ),
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
