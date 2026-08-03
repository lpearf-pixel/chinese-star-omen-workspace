from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

from research_sources.core14_index import load_core14_target_index
from research_sources.projector import project_compatibility, project_source_bundle
from research_sources.source_inventory import load_source_inventory


REPO_ROOT = Path(
    os.environ.get(
        "B10_R04_REPO_ROOT",
        Path(__file__).resolve().parents[4],
    )
)
PACKAGE = REPO_ROOT / "corpus/research_sources/related-wikisource"


def _load() -> tuple[dict[str, object], dict[str, object], str, str]:
    manifest_bytes = (PACKAGE / "accession-manifest.json").read_bytes()
    mapping_bytes = (PACKAGE / "core14-mapping.json").read_bytes()
    return (
        json.loads(manifest_bytes),
        json.loads(mapping_bytes),
        hashlib.sha256(manifest_bytes).hexdigest(),
        hashlib.sha256(mapping_bytes).hexdigest(),
    )


def _assert_same_shape_and_order(actual: object, expected: object) -> None:
    assert type(actual) is type(expected)
    if isinstance(expected, dict):
        assert list(actual) == list(expected)
        for key in expected:
            _assert_same_shape_and_order(actual[key], expected[key])
    elif isinstance(expected, list):
        assert len(actual) == len(expected)
        for got, wanted in zip(actual, expected, strict=True):
            _assert_same_shape_and_order(got, wanted)
    else:
        assert actual == expected


def _bundle():
    manifest, mapping, manifest_sha, mapping_sha = _load()
    return (
        project_source_bundle(
            load_source_inventory(REPO_ROOT),
            manifest,
            mapping,
            source_manifest_sha=manifest_sha,
            source_mapping_sha=mapping_sha,
            core14_index=load_core14_target_index(REPO_ROOT),
        ),
        manifest,
        mapping,
    )


def test_roundtrip_is_deep_exact_and_reads_nothing(monkeypatch) -> None:
    bundle, manifest, mapping = _bundle()
    expected_manifest = copy.deepcopy(manifest)
    expected_mapping = copy.deepcopy(mapping)
    manifest.clear()
    mapping.clear()

    def forbidden_read(*_args, **_kwargs):
        raise AssertionError("project_compatibility must not read files")

    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    monkeypatch.setattr(Path, "read_text", forbidden_read)
    projection = project_compatibility(bundle)

    _assert_same_shape_and_order(projection.manifest_document, expected_manifest)
    _assert_same_shape_and_order(projection.mapping_document, expected_mapping)
    mutated = projection.manifest_document
    mutated.clear()
    _assert_same_shape_and_order(projection.manifest_document, expected_manifest)


def test_projection_records_exact_inputs_and_source_order() -> None:
    bundle, manifest, mapping = _bundle()

    assert bundle.generated_from_accession_ids == tuple(
        sorted(item["accession_id"] for item in manifest["accessions"])
    )
    assert bundle.generated_from_mapping_ids == tuple(
        f"B10-R03-M{i:02d}" for i in range(1, 21)
    )
    assert bundle.pilot_case_ids == ("C14", "C45", "C47")
    assert bundle.source_package_metadata.source_capture == manifest["source_capture"]
    assert {item.ordinal for item in bundle.source_objects} == set(range(31))
    assert {item.ordinal for item in bundle.evidence_links} == set(range(20))
    assert bundle.source_object_count == 31
    assert bundle.evidence_link_count == 20


def test_canonical_bytes_ignore_bundle_collection_input_order() -> None:
    bundle, _, _ = _bundle()
    reversed_bundle = bundle.model_copy(
        update={
            "nodes": tuple(reversed(bundle.nodes)),
            "bibliographic_edges": tuple(reversed(bundle.bibliographic_edges)),
            "assertions": tuple(reversed(bundle.assertions)),
            "source_objects": tuple(reversed(bundle.source_objects)),
            "evidence_links": tuple(reversed(bundle.evidence_links)),
        }
    )

    assert reversed_bundle.canonical_json_bytes() == bundle.canonical_json_bytes()


def test_real_stress_cases_preserve_evidence_without_collapsing() -> None:
    bundle, _, _ = _bundle()
    by_case = {}
    for link in bundle.evidence_links:
        by_case.setdefault(link.target_case_id, []).append(link)

    assert {link.relation_type for link in by_case["C14"]} == {
        "material_variant",
        "historical_note_parallel",
        "locator_support",
        "citation_source",
    }
    c45 = by_case["C45"]
    assert len({link.source_object_id for link in c45}) == 2
    assert {link.source_accession_id for link in c45} == {
        "zhws-houhanshu-83-r1458140",
        "zhws-houhanshu-100-r1753568",
    }
    assert any("御坐" in link.evidence_excerpt for link in c45)
    assert any("帝坐" in link.evidence_excerpt for link in c45)

    c47_text = "\n".join(
        link.evidence_excerpt + "\n" + link.research_note for link in by_case["C47"]
    )
    assert "誅" in c47_text and "謀" in c47_text
    assert "時" in c47_text and "absence" in c47_text


def test_rebuild_from_same_layer_a_bytes_is_identical() -> None:
    first, _, _ = _bundle()
    second, _, _ = _bundle()

    assert first.source_manifest_sha == second.source_manifest_sha
    assert first.source_mapping_sha == second.source_mapping_sha
    assert first.canonical_json_bytes() == second.canonical_json_bytes()
