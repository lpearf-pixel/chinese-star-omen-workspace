from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from .core14_index import Core14TargetIndexV0
from .source_graph import (
    AssertionStatus,
    CompatibilityProjectionV0,
    ConfidenceLevel,
    FamilyDescriptorV0,
    ForbiddenSideEffectsV0,
    GraphRelation,
    MappingPackageMetadataV0,
    NodeKind,
    ResearchAssertionV0,
    ResearchEvidenceLinkV0,
    SourceGraphEdgeV0,
    SourceGraphNodeV0,
    SourceObjectRefV0,
    SourcePackageMetadataV0,
    SourceProjectionBundleV0,
)
from .source_inventory import SourceInventory


MANIFEST_KEYS = (
    "manifest_id",
    "status",
    "access_date",
    "working_contract_path",
    "mapping_path",
    "source_capture",
    "family_count",
    "accession_count",
    "raw_file_count",
    "total_raw_byte_count",
    "core14_cases",
    "families",
    "accessions",
    "forbidden_side_effects",
)
FAMILY_KEYS = (
    "family_id",
    "label",
    "accession_count",
    "accession_metadata_path",
    "notes_path",
)
ACCESSION_KEYS = (
    "accession_id",
    "family_id",
    "page_title",
    "oldid",
    "raw_path",
    "raw_sha256",
    "raw_byte_count",
    "capture_status",
)
MAPPING_DOCUMENT_KEYS = (
    "mapping_id",
    "status",
    "access_date",
    "direction",
    "relation_types",
    "scope_note",
    "mappings",
)
MAPPING_KEYS = (
    "mapping_id",
    "direction",
    "source_accession_id",
    "target_case_id",
    "target_atom_ids",
    "relation_type",
    "mapping_scope",
    "evidence_locator",
    "evidence_excerpt",
    "target_whole_row_citation_eligible",
    "research_note",
)
IMPORT_CONFIDENCE_NOTE = (
    "Compatibility import from an unfrozen research mapping; no new "
    "adjudication performed."
)


class SourceProjectionError(ValueError):
    """Deterministic failure while projecting Layer A into research Layer B."""


def _fail(code: str, detail: str = "") -> None:
    unsafe = (
        detail.startswith("/")
        or "/workspace/" in detail
        or "/tmp/" in detail
        or "/Users/" in detail
        or "\\" in detail
    )
    safe_detail = "<invalid>" if unsafe else detail
    suffix = f":{safe_detail}" if safe_detail else ""
    raise SourceProjectionError(f"source-projection:{code}{suffix}")


def _exact_keys(document: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    if tuple(document.keys()) != keys:
        _fail("invalid-key-shape", label)


def _require_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail("invalid-shape", label)
    return value


def _require_list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        _fail("invalid-shape", label)
    return value


def _source_json_bytes(document: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def _carrier_node_id(page_title: str) -> str:
    payload = json.dumps(
        {"page_title": page_title, "provider": "zh.wikisource.org"},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"carrier:zhws:sha256:{hashlib.sha256(payload).hexdigest()}"


def _edge_id(relation: GraphRelation, source: str, target: str) -> str:
    payload = f"{relation.value}\0{source}\0{target}".encode("utf-8")
    return f"edge:sha256:{hashlib.sha256(payload).hexdigest()}"


def _validate_inventory_join(
    inventory: SourceInventory, source_objects: tuple[SourceObjectRefV0, ...]
) -> None:
    if len(source_objects) != len(inventory.accessions):
        _fail("accession-count-mismatch")
    by_id = {item.accession_id: item for item in inventory.accessions}
    if set(by_id) != {item.accession_id for item in source_objects}:
        _fail("accession-id-set-mismatch")
    for source in source_objects:
        detailed = by_id[source.accession_id]
        expected = (
            detailed.family_id,
            detailed.page_title,
            detailed.oldid,
            detailed.raw_path,
            detailed.raw_sha256,
            detailed.raw_byte_count,
            detailed.capture_status.value,
        )
        actual = (
            source.family_id,
            source.page_title,
            source.oldid,
            source.raw_path,
            source.raw_sha256,
            source.raw_byte_count,
            source.capture_status,
        )
        if any(type(left) is not type(right) or left != right for left, right in zip(actual, expected, strict=True)):
            _fail("inventory-join-mismatch", source.accession_id)


def _build_graph(
    inventory: SourceInventory,
    families: tuple[FamilyDescriptorV0, ...],
    sources: tuple[SourceObjectRefV0, ...],
) -> tuple[
    tuple[SourceGraphNodeV0, ...],
    tuple[SourceGraphEdgeV0, ...],
    tuple[ResearchAssertionV0, ...],
]:
    detailed_by_id = {item.accession_id: item for item in inventory.accessions}
    sources_by_family: dict[str, list[SourceObjectRefV0]] = {
        family.family_id: [] for family in families
    }
    for source in sources:
        if source.family_id not in sources_by_family:
            _fail("unknown-family", source.family_id)
        sources_by_family[source.family_id].append(source)

    nodes: dict[str, SourceGraphNodeV0] = {}
    edges: dict[str, SourceGraphEdgeV0] = {}
    assertions: list[ResearchAssertionV0] = []
    for family in families:
        family_sources = tuple(
            sorted(sources_by_family[family.family_id], key=lambda item: item.accession_id)
        )
        evidence_ids = tuple(item.accession_id for item in family_sources)
        if len(family_sources) != family.accession_count:
            _fail("family-count-mismatch", family.family_id)
        work_id = f"work-candidate:family:{family.family_id}"
        version_id = f"text-version-candidate:family:{family.family_id}:v0"
        nodes[work_id] = SourceGraphNodeV0(
            node_id=work_id,
            kind=NodeKind.WORK_CANDIDATE,
            family_id=family.family_id,
        )
        nodes[version_id] = SourceGraphNodeV0(
            node_id=version_id,
            kind=NodeKind.TEXT_VERSION_CANDIDATE,
            family_id=family.family_id,
        )
        relation = GraphRelation.WORK_HAS_TEXT_VERSION_CANDIDATE
        edge_id = _edge_id(relation, work_id, version_id)
        edges[edge_id] = SourceGraphEdgeV0(
            edge_id=edge_id,
            relation_type=relation,
            source_node_id=work_id,
            target_node_id=version_id,
            status=AssertionStatus.HYPOTHESIZED,
            confidence_level=ConfidenceLevel.UNKNOWN,
            confidence_note="Imported family grouping is a research hypothesis, not an accepted genealogy.",
            supporting_accession_ids=evidence_ids,
        )

        for source in family_sources:
            detail = detailed_by_id[source.accession_id]
            carrier_id = _carrier_node_id(source.page_title)
            source_id = f"source-object:{source.accession_id}"
            nodes.setdefault(
                carrier_id,
                SourceGraphNodeV0(
                    node_id=carrier_id,
                    kind=NodeKind.CARRIER,
                    provider="zh.wikisource.org",
                    page_title=source.page_title,
                ),
            )
            nodes[source_id] = SourceGraphNodeV0(
                node_id=source_id,
                kind=NodeKind.SOURCE_OBJECT,
                accession_id=source.accession_id,
            )
            relation = GraphRelation.VERSION_HAS_CARRIER
            edge_id = _edge_id(relation, version_id, carrier_id)
            if edge_id in edges:
                existing = edges[edge_id]
                edges[edge_id] = existing.model_copy(
                    update={
                        "supporting_accession_ids": tuple(
                            sorted(
                                set(existing.supporting_accession_ids)
                                | {source.accession_id}
                            )
                        )
                    }
                )
            else:
                edges[edge_id] = SourceGraphEdgeV0(
                    edge_id=edge_id,
                    relation_type=relation,
                    source_node_id=version_id,
                    target_node_id=carrier_id,
                    status=AssertionStatus.DEFERRED,
                    confidence_level=ConfidenceLevel.UNKNOWN,
                    confidence_note="Carrier-to-version placement is retained as a deferred research assertion.",
                    supporting_accession_ids=(source.accession_id,),
                )
            relation = GraphRelation.CARRIER_HAS_SOURCE_OBJECT
            edge_id = _edge_id(relation, carrier_id, source_id)
            edges[edge_id] = SourceGraphEdgeV0(
                edge_id=edge_id,
                relation_type=relation,
                source_node_id=carrier_id,
                target_node_id=source_id,
                status=AssertionStatus.OBSERVED,
                confidence_level=ConfidenceLevel.HIGH,
                confidence_note="The fixed oldid source object was captured from this exact Wikisource page title.",
                supporting_accession_ids=(source.accession_id,),
            )

            assertion_specs = (
                ("printed_label", detail.work_printed, AssertionStatus.OBSERVED, work_id),
                (
                    "normalized_label_candidate",
                    detail.work_normalized_candidate,
                    AssertionStatus.HYPOTHESIZED,
                    work_id,
                ),
                ("edition_identity", detail.version_family, AssertionStatus.DEFERRED, version_id),
                ("genealogy", detail.author_or_compiler, AssertionStatus.DEFERRED, version_id),
                (
                    "independent_witness",
                    detail.independent_witness_note,
                    AssertionStatus.DEFERRED,
                    source_id,
                ),
            )
            for predicate, value, status, subject in assertion_specs:
                assertions.append(
                    ResearchAssertionV0(
                        assertion_id=(
                            f"assertion:{source.accession_id}:{predicate}"
                        ),
                        subject_node_id=subject,
                        predicate=predicate,
                        value=value,
                        status=status,
                        confidence_level=(
                            ConfidenceLevel.HIGH
                            if status is AssertionStatus.OBSERVED
                            else ConfidenceLevel.UNKNOWN
                        ),
                        confidence_note=(
                            "Verbatim Layer-A field; observation is limited to the preserved record."
                            if status is AssertionStatus.OBSERVED
                            else "Legacy research wording preserved verbatim without human adjudication."
                        ),
                        supporting_accession_ids=(source.accession_id,),
                        rationale="Preserve source metadata while separating observation, hypothesis, and deferral.",
                        verification_method="Exact field projection from the validated immutable accession.",
                    )
                )

    return (
        tuple(sorted(nodes.values(), key=lambda item: item.node_id)),
        tuple(sorted(edges.values(), key=lambda item: item.edge_id)),
        tuple(sorted(assertions, key=lambda item: item.assertion_id)),
    )


def project_source_bundle(
    inventory: SourceInventory,
    manifest_document: Mapping[str, Any],
    mapping_document: Mapping[str, Any],
    source_manifest_sha: str,
    source_mapping_sha: str,
    core14_index: Core14TargetIndexV0,
) -> SourceProjectionBundleV0:
    """Project immutable source records into a reversible research-only graph."""

    manifest = _require_mapping(manifest_document, "manifest")
    mapping = _require_mapping(mapping_document, "mapping")
    _exact_keys(manifest, MANIFEST_KEYS, "manifest")
    _exact_keys(mapping, MAPPING_DOCUMENT_KEYS, "mapping")
    if hashlib.sha256(_source_json_bytes(manifest)).hexdigest() != source_manifest_sha:
        _fail("source-manifest-sha256-mismatch")
    if hashlib.sha256(_source_json_bytes(mapping)).hexdigest() != source_mapping_sha:
        _fail("source-mapping-sha256-mismatch")

    family_rows = _require_list(manifest["families"], "families")
    compact_rows = _require_list(manifest["accessions"], "accessions")
    mapping_rows = _require_list(mapping["mappings"], "mappings")
    try:
        families = tuple(
            FamilyDescriptorV0.model_validate(
                {**_require_mapping(row, f"family:{ordinal}"), "ordinal": ordinal}
            )
            for ordinal, row in enumerate(family_rows)
        )
        source_objects = tuple(
            SourceObjectRefV0.model_validate(
                {**_require_mapping(row, f"accession:{ordinal}"), "ordinal": ordinal}
            )
            for ordinal, row in enumerate(compact_rows)
        )
    except ValidationError as exc:
        _fail("invalid-source-model", exc.errors(include_url=False)[0]["msg"])
    for row in family_rows:
        _exact_keys(_require_mapping(row, "family"), FAMILY_KEYS, "family")
    for row in compact_rows:
        _exact_keys(_require_mapping(row, "accession"), ACCESSION_KEYS, "accession")

    _validate_inventory_join(inventory, source_objects)
    if (
        manifest["family_count"] != inventory.family_count
        or manifest["accession_count"] != len(inventory.accessions)
        or manifest["raw_file_count"] != inventory.raw_file_count
        or manifest["total_raw_byte_count"] != inventory.total_raw_byte_count
    ):
        _fail("inventory-count-mismatch")

    try:
        source_metadata = SourcePackageMetadataV0(
            manifest_id=manifest["manifest_id"],
            status=manifest["status"],
            access_date=manifest["access_date"],
            working_contract_path=manifest["working_contract_path"],
            mapping_path=manifest["mapping_path"],
            source_capture=manifest["source_capture"],
            family_count=manifest["family_count"],
            accession_count=manifest["accession_count"],
            raw_file_count=manifest["raw_file_count"],
            total_raw_byte_count=manifest["total_raw_byte_count"],
            core14_cases=tuple(_require_list(manifest["core14_cases"], "core14_cases")),
            families=tuple(sorted(families, key=lambda item: item.family_id)),
            forbidden_side_effects=ForbiddenSideEffectsV0.model_validate(
                manifest["forbidden_side_effects"]
            ),
        )
        mapping_metadata = MappingPackageMetadataV0(
            mapping_id=mapping["mapping_id"],
            status=mapping["status"],
            access_date=mapping["access_date"],
            direction=mapping["direction"],
            relation_types=tuple(
                _require_list(mapping["relation_types"], "relation_types")
            ),
            scope_note=mapping["scope_note"],
        )
    except (KeyError, TypeError, ValidationError) as exc:
        _fail("invalid-package-metadata", type(exc).__name__)

    nodes, edges, assertions = _build_graph(inventory, families, source_objects)
    accession_ids = {item.accession_id for item in source_objects}
    relation_types = set(mapping_metadata.relation_types)
    links: list[ResearchEvidenceLinkV0] = []
    seen_mapping_ids: set[str] = set()
    for ordinal, raw_row in enumerate(mapping_rows):
        row = _require_mapping(raw_row, f"mapping:{ordinal}")
        _exact_keys(row, MAPPING_KEYS, "mapping-entry")
        mapping_id = row.get("mapping_id")
        if not isinstance(mapping_id, str) or mapping_id in seen_mapping_ids:
            _fail("duplicate-or-invalid-mapping-id", str(mapping_id))
        seen_mapping_ids.add(mapping_id)
        source_accession_id = row.get("source_accession_id")
        if source_accession_id not in accession_ids:
            _fail("unknown-source-accession", str(source_accession_id))
        case_id = row.get("target_case_id")
        if not isinstance(case_id, str) or not core14_index.contains_case(case_id):
            _fail("unknown-target-case", str(case_id))
        atom_ids = row.get("target_atom_ids")
        if not isinstance(atom_ids, list):
            _fail("invalid-target-atoms", mapping_id)
        for atom_id in atom_ids:
            if not isinstance(atom_id, str) or not core14_index.contains_atom(
                case_id, atom_id
            ):
                _fail("unknown-target-atom", str(atom_id))
        if row.get("direction") != mapping_metadata.direction:
            _fail("mapping-direction-mismatch", mapping_id)
        if row.get("relation_type") not in relation_types:
            _fail("unknown-relation-type", mapping_id)
        if row.get("target_whole_row_citation_eligible") != "NO":
            _fail("citation-boundary-violation", mapping_id)
        try:
            links.append(
                ResearchEvidenceLinkV0.model_validate(
                    {
                        **row,
                        "source_object_id": f"source-object:{source_accession_id}",
                        "status": AssertionStatus.HYPOTHESIZED,
                        "confidence_level": ConfidenceLevel.UNKNOWN,
                        "confidence_note": IMPORT_CONFIDENCE_NOTE,
                        "supporting_accession_ids": (source_accession_id,),
                        "contradicting_accession_ids": (),
                        "ordinal": ordinal,
                    }
                )
            )
        except ValidationError as exc:
            _fail("invalid-evidence-link", exc.errors(include_url=False)[0]["msg"])

    try:
        return SourceProjectionBundleV0(
            schema_version="source-projection-bundle/pilot-v0",
            research_only=True,
            source_manifest_sha=source_manifest_sha,
            source_mapping_sha=source_mapping_sha,
            core14_index=core14_index,
            source_package_metadata=source_metadata,
            mapping_package_metadata=mapping_metadata,
            source_objects=tuple(
                sorted(source_objects, key=lambda item: item.accession_id)
            ),
            nodes=nodes,
            bibliographic_edges=edges,
            assertions=assertions,
            evidence_links=tuple(sorted(links, key=lambda item: item.mapping_id)),
            generated_from_accession_ids=tuple(sorted(accession_ids)),
            generated_from_mapping_ids=tuple(sorted(seen_mapping_ids)),
            pilot_case_ids=("C14", "C45", "C47"),
            title_based_merges=(),
            validation_report=None,
        )
    except ValidationError as exc:
        _fail("invalid-bundle", exc.errors(include_url=False)[0]["msg"])


def _family_document(family: FamilyDescriptorV0) -> dict[str, Any]:
    return {key: getattr(family, key) for key in FAMILY_KEYS}


def _source_document(source: SourceObjectRefV0) -> dict[str, Any]:
    return {key: getattr(source, key) for key in ACCESSION_KEYS}


def _mapping_document(link: ResearchEvidenceLinkV0) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in MAPPING_KEYS:
        value = getattr(link, key)
        result[key] = list(value) if key == "target_atom_ids" else value
    return result


def project_compatibility(
    bundle: SourceProjectionBundleV0,
) -> CompatibilityProjectionV0:
    """Pure reverse projection back to the two legacy Layer-A documents."""

    source = bundle.source_package_metadata
    manifest: dict[str, Any] = {
        "manifest_id": source.manifest_id,
        "status": source.status,
        "access_date": source.access_date,
        "working_contract_path": source.working_contract_path,
        "mapping_path": source.mapping_path,
        "source_capture": source.source_capture,
        "family_count": source.family_count,
        "accession_count": source.accession_count,
        "raw_file_count": source.raw_file_count,
        "total_raw_byte_count": source.total_raw_byte_count,
        "core14_cases": list(source.core14_cases),
        "families": [
            _family_document(item)
            for item in sorted(source.families, key=lambda item: item.ordinal)
        ],
        "accessions": [
            _source_document(item)
            for item in sorted(bundle.source_objects, key=lambda item: item.ordinal)
        ],
        "forbidden_side_effects": source.forbidden_side_effects.model_dump(),
    }
    mapping_metadata = bundle.mapping_package_metadata
    mapping: dict[str, Any] = {
        "mapping_id": mapping_metadata.mapping_id,
        "status": mapping_metadata.status,
        "access_date": mapping_metadata.access_date,
        "direction": mapping_metadata.direction,
        "relation_types": list(mapping_metadata.relation_types),
        "scope_note": mapping_metadata.scope_note,
        "mappings": [
            _mapping_document(item)
            for item in sorted(bundle.evidence_links, key=lambda item: item.ordinal)
        ],
    }
    return CompatibilityProjectionV0.from_documents(manifest, mapping)


__all__ = [
    "SourceProjectionError",
    "project_compatibility",
    "project_source_bundle",
]
