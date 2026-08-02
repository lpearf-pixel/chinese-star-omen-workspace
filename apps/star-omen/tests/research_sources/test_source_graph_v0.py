from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from research_sources.core14_index import Core14IndexError, load_core14_target_index
from research_sources.source_graph import (
    AssertionStatus,
    FamilyDescriptorV0,
    NodeKind,
    SourceGraphNodeV0,
    SourceObjectRefV0,
    SourceProjectionBundleV0,
)
from research_sources.projector import SourceProjectionError, project_source_bundle
from research_sources.source_inventory import load_source_inventory


REPO_ROOT = Path(
    os.environ.get(
        "B10_R04_REPO_ROOT",
        Path(__file__).resolve().parents[4],
    )
)
PACKAGE = REPO_ROOT / "corpus/research_sources/related-wikisource"


def _documents() -> tuple[dict[str, object], dict[str, object]]:
    return (
        json.loads((PACKAGE / "accession-manifest.json").read_text("utf-8")),
        json.loads((PACKAGE / "core14-mapping.json").read_text("utf-8")),
    )


def _document_sha(document: dict[str, object]) -> str:
    raw = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def _bundle():
    manifest, mapping = _documents()
    return project_source_bundle(
        load_source_inventory(REPO_ROOT),
        manifest,
        mapping,
        source_manifest_sha=hashlib.sha256((PACKAGE / "accession-manifest.json").read_bytes()).hexdigest(),
        source_mapping_sha=hashlib.sha256((PACKAGE / "core14-mapping.json").read_bytes()).hexdigest(),
        core14_index=load_core14_target_index(REPO_ROOT),
    )


def test_core14_index_binds_real_manifest_and_exact_targets() -> None:
    index = load_core14_target_index(REPO_ROOT)

    assert len(index.case_ids) == 14
    assert len(index.atom_ids) == 130
    assert index.case_ids == tuple(sorted(index.case_ids))
    assert index.atom_ids == tuple(sorted(index.atom_ids))
    assert set(index.audit_sha256) == {"early", "middle", "late"}
    manifest_path = REPO_ROOT / "corpus/research_sources/b10-core14/accession-manifest.json"
    assert index.manifest_sha256 == hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def test_core14_index_rejects_declared_hash_mismatch(tmp_path: Path) -> None:
    target = tmp_path / "corpus/research_sources/b10-core14"
    target.mkdir(parents=True)
    source = REPO_ROOT / "corpus/research_sources/b10-core14"
    for name in ("accession-manifest.json", "audit-early.json", "audit-middle.json", "audit-late.json"):
        (target / name).write_bytes((source / name).read_bytes())
    (target / "audit-early.json").write_bytes((target / "audit-early.json").read_bytes() + b" ")

    with pytest.raises(Core14IndexError, match="audit-sha256-mismatch"):
        load_core14_target_index(tmp_path)


@pytest.mark.parametrize("duplicate_kind", ["case", "atom"])
def test_core14_index_rejects_duplicate_targets_after_hash_replay(
    tmp_path: Path, duplicate_kind: str
) -> None:
    target = tmp_path / "corpus/research_sources/b10-core14"
    source = REPO_ROOT / "corpus/research_sources/b10-core14"
    shutil.copytree(source, target)
    audit_path = target / "audit-early.json"
    audit = json.loads(audit_path.read_text("utf-8"))
    if duplicate_kind == "case":
        audit["cases"].append(copy.deepcopy(audit["cases"][0]))
    else:
        audit["cases"][0]["atomic_rules"].append(
            copy.deepcopy(audit["cases"][0]["atomic_rules"][0])
        )
    audit_bytes = (json.dumps(audit, ensure_ascii=False, indent=2) + "\n").encode()
    audit_path.write_bytes(audit_bytes)
    manifest_path = target / "accession-manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    for item in manifest["files"]:
        if item["path"].endswith("audit-early.json"):
            item["sha256"] = hashlib.sha256(audit_bytes).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )

    with pytest.raises(Core14IndexError, match="core14-manifest-sha256-mismatch"):
        load_core14_target_index(tmp_path)


def test_core14_index_rejects_symlinked_fixed_audit(tmp_path: Path) -> None:
    target = tmp_path / "corpus/research_sources/b10-core14"
    source = REPO_ROOT / "corpus/research_sources/b10-core14"
    shutil.copytree(source, target)
    audit_path = target / "audit-early.json"
    real_path = target / "audit-early-real.json"
    audit_path.rename(real_path)
    audit_path.symlink_to(real_path.name)

    with pytest.raises(Core14IndexError, match="symlink-forbidden"):
        load_core14_target_index(tmp_path)


def test_core14_index_wraps_malicious_target_without_leaking_path(tmp_path: Path) -> None:
    target = tmp_path / "corpus/research_sources/b10-core14"
    source = REPO_ROOT / "corpus/research_sources/b10-core14"
    shutil.copytree(source, target)
    audit_path = target / "audit-early.json"
    audit = json.loads(audit_path.read_text("utf-8"))
    audit["cases"][0]["atomic_rules"][0]["id"] = "/workspace/private"
    audit_bytes = (json.dumps(audit, ensure_ascii=False, indent=2) + "\n").encode()
    audit_path.write_bytes(audit_bytes)
    manifest_path = target / "accession-manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    for item in manifest["files"]:
        if item["path"].endswith("audit-early.json"):
            item["sha256"] = hashlib.sha256(audit_bytes).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )

    with pytest.raises(Core14IndexError) as caught:
        load_core14_target_index(tmp_path)
    assert "core14-manifest-sha256-mismatch" in str(caught.value)
    assert "/workspace/private" not in str(caught.value)


def test_graph_has_expected_layer_counts_and_valid_references() -> None:
    bundle = _bundle()
    counts = Counter(node.kind for node in bundle.nodes)

    assert len(bundle.nodes) == 46
    assert counts == {
        NodeKind.WORK_CANDIDATE: 7,
        NodeKind.TEXT_VERSION_CANDIDATE: 7,
        NodeKind.CARRIER: 16,
        NodeKind.SOURCE_OBJECT: 16,
    }
    assert len(bundle.bibliographic_edges) == 39
    assert len(bundle.evidence_links) == 20

    node_ids = {node.node_id for node in bundle.nodes}
    accession_ids = {item.accession_id for item in bundle.source_objects}
    for edge in bundle.bibliographic_edges:
        assert edge.source_node_id in node_ids
        assert edge.target_node_id in node_ids
    for link in bundle.evidence_links:
        assert link.source_object_id in node_ids
        assert link.source_accession_id in accession_ids
        assert link.target_case_id in bundle.core14_index.case_ids
        assert set(link.target_atom_ids) <= set(bundle.core14_index.atom_ids)


def test_projection_is_family_id_based_not_normalized_title_based() -> None:
    inventory = load_source_inventory(REPO_ROOT)
    manifest, mapping = _documents()
    manifest = copy.deepcopy(manifest)
    manifest["families"][1]["label"] = manifest["families"][0]["label"]

    bundle = project_source_bundle(
        inventory,
        manifest,
        mapping,
        source_manifest_sha=_document_sha(manifest),
        source_mapping_sha=hashlib.sha256((PACKAGE / "core14-mapping.json").read_bytes()).hexdigest(),
        core14_index=load_core14_target_index(REPO_ROOT),
    )

    work_nodes = [n for n in bundle.nodes if n.kind is NodeKind.WORK_CANDIDATE]
    assert len(work_nodes) == 7
    assert len({n.node_id for n in work_nodes}) == 7
    assert bundle.title_based_merges == ()


def test_carrier_identity_excludes_oldid_and_can_be_reused() -> None:
    bundle = _bundle()
    carrier_nodes = {n.node_id: n for n in bundle.nodes if n.kind is NodeKind.CARRIER}
    carrier_edges = [e for e in bundle.bibliographic_edges if e.relation_type == "carrier_has_source_object"]
    source_by_node = {f"source-object:{s.accession_id}": s for s in bundle.source_objects}

    for edge in carrier_edges:
        source = source_by_node[edge.target_node_id]
        assert str(source.oldid) not in edge.source_node_id
        assert edge.source_node_id in carrier_nodes


def test_models_preserve_strings_oldid_is_strict_and_family_shape_is_exact() -> None:
    family = FamilyDescriptorV0(
        family_id="f1",
        label="  《原样》  ",
        accession_count=1,
        accession_metadata_path="corpus/x.json",
        notes_path="corpus/n.md",
        ordinal=0,
    )
    assert family.label == "  《原样》  "
    assert list(family.model_dump()) == [
        "family_id",
        "label",
        "accession_count",
        "accession_metadata_path",
        "notes_path",
        "ordinal",
    ]

    manifest, _ = _documents()
    row = dict(manifest["accessions"][0])
    row["ordinal"] = 0
    SourceObjectRefV0.model_validate(row)
    row["oldid"] = str(row["oldid"])
    with pytest.raises(ValidationError):
        SourceObjectRefV0.model_validate(row)
    with pytest.raises(ValidationError):
        FamilyDescriptorV0(
            family_id="phantom",
            label="phantom",
            accession_count=0,
            accession_metadata_path="corpus/x.json",
            notes_path="corpus/n.md",
            ordinal=0,
        )


def test_only_research_statuses_exist_and_approval_fields_are_forbidden() -> None:
    assert {item.value for item in AssertionStatus} == {"observed", "hypothesized", "deferred"}
    with pytest.raises(ValueError):
        AssertionStatus("accepted")
    with pytest.raises(ValueError):
        AssertionStatus("rejected")

    with pytest.raises(ValidationError):
        SourceGraphNodeV0(
            node_id="work--x",
            kind="work_candidate",
            family_id="x",
            human_review_status="accepted",
        )
    with pytest.raises(ValidationError):
        SourceGraphNodeV0(
            node_id="work--x",
            kind="work_candidate",
            family_id="x",
            printed_label="must-live-in-an-assertion",
        )


def test_assertions_keep_observation_hypothesis_and_deferral_distinct() -> None:
    bundle = _bundle()
    by_predicate = {}
    for assertion in bundle.assertions:
        by_predicate.setdefault(assertion.predicate, set()).add(assertion.status)

    assert by_predicate["printed_label"] == {AssertionStatus.OBSERVED}
    assert by_predicate["normalized_label_candidate"] == {AssertionStatus.HYPOTHESIZED}
    assert by_predicate["edition_identity"] == {AssertionStatus.DEFERRED}
    assert by_predicate["genealogy"] == {AssertionStatus.DEFERRED}
    assert by_predicate["independent_witness"] == {AssertionStatus.DEFERRED}
    assert bundle.accepted_independent_witness_assertions == ()
    assert bundle.deferred_independent_witness_assertion_count > 0


def test_unknown_case_or_atom_is_rejected() -> None:
    inventory = load_source_inventory(REPO_ROOT)
    manifest, mapping = _documents()
    mapping = copy.deepcopy(mapping)
    mapping["mappings"][0]["target_atom_ids"] = ["NOT-AN-ATOM"]

    with pytest.raises(SourceProjectionError, match="unknown-target-atom"):
        project_source_bundle(
            inventory,
            manifest,
            mapping,
            source_manifest_sha=hashlib.sha256((PACKAGE / "accession-manifest.json").read_bytes()).hexdigest(),
            source_mapping_sha=_document_sha(mapping),
            core14_index=load_core14_target_index(REPO_ROOT),
        )


def test_unknown_case_and_production_input_field_are_rejected() -> None:
    inventory = load_source_inventory(REPO_ROOT)
    manifest, mapping = _documents()
    mapping = copy.deepcopy(mapping)
    mapping["mappings"][0]["target_case_id"] = "C99"
    with pytest.raises(SourceProjectionError, match="unknown-target-case"):
        project_source_bundle(
            inventory,
            manifest,
            mapping,
            source_manifest_sha=_document_sha(manifest),
            source_mapping_sha=_document_sha(mapping),
            core14_index=load_core14_target_index(REPO_ROOT),
        )

    manifest, mapping = _documents()
    manifest = copy.deepcopy(manifest)
    manifest["reviewer_decision"] = "accepted"
    with pytest.raises(SourceProjectionError, match="invalid-key-shape"):
        project_source_bundle(
            inventory,
            manifest,
            mapping,
            source_manifest_sha=_document_sha(manifest),
            source_mapping_sha=_document_sha(mapping),
            core14_index=load_core14_target_index(REPO_ROOT),
        )

    manifest, mapping = _documents()
    manifest = copy.deepcopy(manifest)
    manifest["core14_cases"] = "C03"
    with pytest.raises(SourceProjectionError, match="invalid-shape"):
        project_source_bundle(
            inventory,
            manifest,
            mapping,
            source_manifest_sha=_document_sha(manifest),
            source_mapping_sha=_document_sha(mapping),
            core14_index=load_core14_target_index(REPO_ROOT),
        )


def test_projection_binds_declared_hashes_and_manifest_case_denominator() -> None:
    inventory = load_source_inventory(REPO_ROOT)
    manifest, mapping = _documents()
    with pytest.raises(SourceProjectionError, match="source-manifest-sha256-mismatch"):
        project_source_bundle(
            inventory,
            manifest,
            mapping,
            source_manifest_sha="0" * 64,
            source_mapping_sha=_document_sha(mapping),
            core14_index=load_core14_target_index(REPO_ROOT),
        )
    with pytest.raises(SourceProjectionError, match="source-mapping-sha256-mismatch"):
        project_source_bundle(
            inventory,
            manifest,
            mapping,
            source_manifest_sha=_document_sha(manifest),
            source_mapping_sha="1" * 64,
            core14_index=load_core14_target_index(REPO_ROOT),
        )

    manifest = copy.deepcopy(manifest)
    manifest["core14_cases"].append("C99")
    with pytest.raises(SourceProjectionError, match="Core14 cases"):
        project_source_bundle(
            inventory,
            manifest,
            mapping,
            source_manifest_sha=_document_sha(manifest),
            source_mapping_sha=_document_sha(mapping),
            core14_index=load_core14_target_index(REPO_ROOT),
        )


def test_bundle_model_rejects_orphan_graph_endpoint() -> None:
    bundle = _bundle()
    payload = bundle.model_dump(mode="json")
    payload["bibliographic_edges"][0]["target_node_id"] = "source-object:missing"

    with pytest.raises(ValidationError, match="endpoint"):
        SourceProjectionBundleV0.model_validate(payload)


def test_bundle_model_rejects_unknown_support_and_duplicate_source_ref() -> None:
    bundle = _bundle()
    payload = bundle.model_dump(mode="json")
    payload["bibliographic_edges"][0]["supporting_accession_ids"] = ["missing"]
    with pytest.raises(ValidationError, match="unknown accession"):
        SourceProjectionBundleV0.model_validate(payload)

    payload = bundle.model_dump(mode="json")
    duplicate = copy.deepcopy(payload["source_objects"][0])
    duplicate["ordinal"] = len(payload["source_objects"])
    payload["source_objects"].append(duplicate)
    with pytest.raises(ValidationError, match="unique accession"):
        SourceProjectionBundleV0.model_validate(payload)


def test_serialized_core14_index_cannot_diverge_from_bound_audits() -> None:
    bundle = _bundle()
    payload = bundle.core14_index.model_dump(mode="json")
    payload["cases"][0]["atom_ids"][-1] = "ZZ-C02-FAKE"

    with pytest.raises(ValidationError, match="audit atom targets"):
        type(bundle.core14_index).model_validate(payload)
