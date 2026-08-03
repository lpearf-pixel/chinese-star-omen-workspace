from __future__ import annotations

import json
import hashlib
import re
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .core14_index import Core14TargetIndexV0


class StrictResearchModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    @model_validator(mode="after")
    def reject_blank_string_fields(self) -> "StrictResearchModel":
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"{name} must not be blank")
        return self


_ASCII_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9:._-]*$"


class NodeKind(str, Enum):
    WORK_CANDIDATE = "work_candidate"
    TEXT_VERSION_CANDIDATE = "text_version_candidate"
    CARRIER = "carrier"
    SOURCE_OBJECT = "source_object"


class AssertionStatus(str, Enum):
    OBSERVED = "observed"
    HYPOTHESIZED = "hypothesized"
    DEFERRED = "deferred"


class ConfidenceLevel(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GraphRelation(str, Enum):
    WORK_HAS_TEXT_VERSION_CANDIDATE = "work_has_text_version_candidate"
    VERSION_HAS_CARRIER = "version_has_carrier"
    CARRIER_HAS_SOURCE_OBJECT = "carrier_has_source_object"


class FamilyDescriptorV0(StrictResearchModel):
    family_id: str = Field(strict=True, min_length=1, pattern=_ASCII_ID_PATTERN)
    label: str = Field(strict=True, min_length=1)
    accession_count: int = Field(strict=True, gt=0)
    accession_metadata_path: str = Field(strict=True, min_length=1)
    notes_path: str = Field(strict=True, min_length=1)
    ordinal: int = Field(strict=True, ge=0)

    @field_validator("family_id", "label", "accession_metadata_path", "notes_path")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class SourceObjectRefV0(StrictResearchModel):
    accession_id: str = Field(strict=True, min_length=1, pattern=_ASCII_ID_PATTERN)
    family_id: str = Field(strict=True, min_length=1, pattern=_ASCII_ID_PATTERN)
    page_title: str = Field(strict=True, min_length=1)
    oldid: int = Field(strict=True, gt=0)
    raw_path: str = Field(strict=True, min_length=1)
    raw_sha256: str = Field(strict=True, pattern=r"^[0-9a-f]{64}$")
    raw_byte_count: int = Field(strict=True, ge=0)
    capture_status: str = Field(strict=True, min_length=1)
    ordinal: int = Field(strict=True, ge=0)

    @field_validator(
        "accession_id", "family_id", "page_title", "raw_path", "capture_status"
    )
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class ForbiddenSideEffectsV0(StrictResearchModel):
    production_schema_freeze: Literal["NOT_RUN"]
    official_kb_ingest: Literal["NOT_RUN"]
    qdrant_access: Literal["NOT_RUN"]
    local_kb_default_access: Literal["NOT_RUN"]
    reviewer_a_b_modification: Literal["NOT_RUN"]


class SourcePackageMetadataV0(StrictResearchModel):
    manifest_id: str = Field(strict=True, min_length=1)
    status: str = Field(strict=True, min_length=1)
    access_date: str = Field(strict=True, min_length=1)
    working_contract_path: str = Field(strict=True, min_length=1)
    mapping_path: str = Field(strict=True, min_length=1)
    source_capture: str = Field(strict=True, min_length=1)
    family_count: int = Field(strict=True, ge=0)
    accession_count: int = Field(strict=True, ge=0)
    raw_file_count: int = Field(strict=True, ge=0)
    total_raw_byte_count: int = Field(strict=True, ge=0)
    core14_cases: tuple[str, ...]
    families: tuple[FamilyDescriptorV0, ...]
    forbidden_side_effects: ForbiddenSideEffectsV0

    @field_validator("core14_cases")
    @classmethod
    def validate_core14_cases(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if (
            not value
            or value != tuple(sorted(set(value)))
            or any(re.fullmatch(r"C[0-9]{2}", item) is None for item in value)
        ):
            raise ValueError("core14_cases must be non-empty, sorted, unique case IDs")
        return value


class MappingPackageMetadataV0(StrictResearchModel):
    mapping_id: str = Field(strict=True, min_length=1)
    status: str = Field(strict=True, min_length=1)
    access_date: str = Field(strict=True, min_length=1)
    direction: str = Field(strict=True, min_length=1)
    relation_types: tuple[str, ...]
    scope_note: str = Field(strict=True, min_length=1)

    @field_validator("relation_types")
    @classmethod
    def validate_relation_types(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or len(value) != len(set(value)) or any(not item.strip() for item in value):
            raise ValueError("relation_types must be non-empty and unique")
        return value


class SourceGraphNodeV0(StrictResearchModel):
    """Graph-local identity only; descriptive claims live in assertions."""

    node_id: str = Field(strict=True, min_length=1, pattern=_ASCII_ID_PATTERN)
    kind: NodeKind
    family_id: str | None = Field(default=None, strict=True, pattern=_ASCII_ID_PATTERN)
    provider: str | None = Field(default=None, strict=True)
    page_title: str | None = Field(default=None, strict=True)
    accession_id: str | None = Field(
        default=None, strict=True, pattern=_ASCII_ID_PATTERN
    )

    @model_validator(mode="after")
    def validate_kind_identity(self) -> "SourceGraphNodeV0":
        identities = {
            "family_id": self.family_id,
            "provider": self.provider,
            "page_title": self.page_title,
            "accession_id": self.accession_id,
        }
        if self.kind in {NodeKind.WORK_CANDIDATE, NodeKind.TEXT_VERSION_CANDIDATE}:
            valid = self.family_id is not None and all(
                identities[key] is None for key in ("provider", "page_title", "accession_id")
            )
        elif self.kind is NodeKind.CARRIER:
            valid = (
                self.provider is not None
                and self.page_title is not None
                and self.family_id is None
                and self.accession_id is None
            )
        else:
            valid = self.accession_id is not None and all(
                identities[key] is None for key in ("family_id", "provider", "page_title")
            )
        if not valid:
            raise ValueError("node identity fields do not match kind")
        return self


class SourceGraphEdgeV0(StrictResearchModel):
    edge_id: str = Field(strict=True, min_length=1, pattern=_ASCII_ID_PATTERN)
    relation_type: GraphRelation
    source_node_id: str = Field(strict=True, min_length=1)
    target_node_id: str = Field(strict=True, min_length=1)
    status: AssertionStatus
    confidence_level: ConfidenceLevel
    confidence_note: str = Field(strict=True, min_length=1)
    supporting_accession_ids: tuple[str, ...]

    @field_validator("supporting_accession_ids")
    @classmethod
    def validate_support(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or value != tuple(sorted(set(value))):
            raise ValueError("supporting accession IDs must be non-empty, sorted, unique")
        return value


class ResearchAssertionV0(StrictResearchModel):
    assertion_id: str = Field(strict=True, min_length=1, pattern=_ASCII_ID_PATTERN)
    subject_node_id: str = Field(strict=True, min_length=1)
    predicate: str = Field(strict=True, min_length=1)
    value: str = Field(strict=True, min_length=1)
    status: AssertionStatus
    confidence_level: ConfidenceLevel
    confidence_note: str = Field(strict=True, min_length=1)
    supporting_accession_ids: tuple[str, ...]
    contradicting_accession_ids: tuple[str, ...] = ()
    rationale: str = Field(strict=True, min_length=1)
    verification_method: str = Field(strict=True, min_length=1)

    @field_validator("supporting_accession_ids")
    @classmethod
    def validate_support(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or value != tuple(sorted(set(value))):
            raise ValueError("supporting accession IDs must be non-empty, sorted, unique")
        return value

    @field_validator("contradicting_accession_ids")
    @classmethod
    def validate_contradictions(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != tuple(sorted(set(value))):
            raise ValueError("contradicting accession IDs must be sorted and unique")
        return value


class ResearchEvidenceLinkV0(StrictResearchModel):
    mapping_id: str = Field(strict=True, min_length=1)
    direction: str = Field(strict=True, min_length=1)
    source_accession_id: str = Field(strict=True, min_length=1)
    target_case_id: str = Field(strict=True, pattern=r"^C[0-9]{2}$")
    target_atom_ids: tuple[str, ...]
    relation_type: str = Field(strict=True, min_length=1)
    mapping_scope: str = Field(strict=True, min_length=1)
    evidence_locator: str = Field(strict=True, min_length=1)
    evidence_excerpt: str = Field(strict=True, min_length=1)
    target_whole_row_citation_eligible: Literal["NO"]
    research_note: str = Field(strict=True, min_length=1)
    source_object_id: str = Field(strict=True, min_length=1)
    status: AssertionStatus
    confidence_level: ConfidenceLevel
    confidence_note: str = Field(strict=True, min_length=1)
    supporting_accession_ids: tuple[str, ...]
    contradicting_accession_ids: tuple[str, ...] = ()
    ordinal: int = Field(strict=True, ge=0)

    @field_validator("supporting_accession_ids")
    @classmethod
    def validate_support(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or value != tuple(sorted(set(value))):
            raise ValueError("supporting accession IDs must be non-empty, sorted, unique")
        return value

    @field_validator("contradicting_accession_ids")
    @classmethod
    def validate_contradictions(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != tuple(sorted(set(value))):
            raise ValueError("contradicting accession IDs must be sorted and unique")
        return value


class CompatibilityProjectionV0(StrictResearchModel):
    manifest_json_bytes: bytes = Field(repr=False)
    mapping_json_bytes: bytes = Field(repr=False)

    @classmethod
    def from_documents(
        cls, manifest_document: dict[str, Any], mapping_document: dict[str, Any]
    ) -> "CompatibilityProjectionV0":
        def encode(value: dict[str, Any]) -> bytes:
            return json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8")

        return cls(
            manifest_json_bytes=encode(manifest_document),
            mapping_json_bytes=encode(mapping_document),
        )

    @property
    def manifest_document(self) -> dict[str, Any]:
        return json.loads(self.manifest_json_bytes)

    @property
    def mapping_document(self) -> dict[str, Any]:
        return json.loads(self.mapping_json_bytes)


class FileDigestV0(StrictResearchModel):
    path: str = Field(strict=True, min_length=1)
    sha256: str = Field(strict=True, pattern=r"^[0-9a-f]{64}$")


class SnapshotDigestV0(StrictResearchModel):
    file_count: int = Field(strict=True, ge=0)
    total_byte_count: int = Field(strict=True, ge=0)
    sha256: str = Field(strict=True, pattern=r"^[0-9a-f]{64}$")


class PilotCaseCheckV0(StrictResearchModel):
    case_id: Literal["C14", "C45", "C47"]
    status: Literal["PASS"]
    checks: tuple[str, ...]

    @field_validator("checks")
    @classmethod
    def validate_checks(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or value != tuple(sorted(set(value))):
            raise ValueError("pilot checks must be non-empty, sorted, and unique")
        return value


def build_pilot_case_checks(
    evidence_links: tuple[ResearchEvidenceLinkV0, ...],
    source_objects: tuple[SourceObjectRefV0, ...],
    assertions: tuple[ResearchAssertionV0, ...],
) -> tuple[PilotCaseCheckV0, ...]:
    """Validate the exact C14/C45/C47 stress denominators and label only facts checked."""

    by_id = {link.mapping_id: link for link in evidence_links}
    c14_expected = {
        "B10-R03-M07": ("material_variant", "case_historical_context"),
        "B10-R03-M09": ("historical_note_parallel", "case_historical_context"),
        "B10-R03-M12": ("locator_support", "case_context"),
        "B10-R03-M16": ("material_variant", "case_historical_context"),
        "B10-R03-M18": ("citation_source", "case_historical_source"),
    }
    c14_ids = {link.mapping_id for link in evidence_links if link.target_case_id == "C14"}
    if c14_ids != set(c14_expected):
        raise ValueError("C14 must contain exactly mappings M07/M09/M12/M16/M18")
    for mapping_id, (relation, scope) in c14_expected.items():
        link = by_id[mapping_id]
        if (
            link.relation_type != relation
            or link.mapping_scope != scope
            or link.target_atom_ids != ()
        ):
            raise ValueError("C14 relation, scope, or case-level boundary is invalid")

    c45_ids = {link.mapping_id for link in evidence_links if link.target_case_id == "C45"}
    if c45_ids != {"B10-R03-M19", "B10-R03-M20"}:
        raise ValueError("C45 must contain exactly mappings M19/M20")
    c45 = (by_id["B10-R03-M19"], by_id["B10-R03-M20"])
    if any(
        link.relation_type != "material_variant"
        or link.mapping_scope != "atomic_parallel"
        or link.target_atom_ids != ("C45-H2",)
        for link in c45
    ):
        raise ValueError("C45 relation, scope, or atom target is invalid")
    c45_source_ids = {link.source_accession_id for link in c45}
    if c45_source_ids != {
        "zhws-houhanshu-83-r1458140",
        "zhws-houhanshu-100-r1753568",
    }:
        raise ValueError("C45 source denominator is invalid")
    source_family = {item.accession_id: item.family_id for item in source_objects}
    if {source_family.get(source_id) for source_id in c45_source_ids} != {"houhanshu"}:
        raise ValueError("C45 sources must remain in one houhanshu family")
    c45_text = "\n".join(link.evidence_excerpt for link in c45)
    if "御坐" not in c45_text or "帝坐" not in c45_text:
        raise ValueError("C45 material readings are incomplete")
    deferred_witness_sources = {
        assertion.supporting_accession_ids[0]
        for assertion in assertions
        if assertion.predicate == "independent_witness"
        and assertion.status is AssertionStatus.DEFERRED
        and len(assertion.supporting_accession_ids) == 1
    }
    if not c45_source_ids <= deferred_witness_sources:
        raise ValueError("C45 independent-witness state must remain deferred")

    c47_expected = {
        "B10-R03-M03": (("C47-R3",), "material_variant", "atomic_parallel"),
        "B10-R03-M04": (("C47-R7",), "material_variant", "atomic_parallel"),
        "B10-R03-M15": ((), "locator_support", "case_terminology"),
        "B10-R03-M17": ((), "locator_support", "case_context"),
    }
    c47_ids = {link.mapping_id for link in evidence_links if link.target_case_id == "C47"}
    if c47_ids != set(c47_expected):
        raise ValueError("C47 must contain exactly mappings M03/M04/M15/M17")
    for mapping_id, (atom_ids, relation, scope) in c47_expected.items():
        link = by_id[mapping_id]
        if (
            link.target_atom_ids != atom_ids
            or link.relation_type != relation
            or link.mapping_scope != scope
        ):
            raise ValueError("C47 relation, scope, or atom boundary is invalid")
    c47_text = "\n".join(
        link.evidence_excerpt + "\n" + link.research_note
        for link in (by_id[mapping_id] for mapping_id in sorted(c47_expected))
    )
    if not all(token in c47_text for token in ("誅", "謀", "時", "absence")):
        raise ValueError("C47 material readings are incomplete")

    return (
        PilotCaseCheckV0(
            case_id="C14",
            status="PASS",
            checks=(
                "five_distinct_case_level_links",
                "four_relation_types_preserved",
                "no_atom_scope_inflation",
            ),
        ),
        PilotCaseCheckV0(
            case_id="C45",
            status="PASS",
            checks=(
                "di_zuo_and_yu_zuo_preserved",
                "same_received_history_family_not_independent",
                "two_source_objects_preserved",
            ),
        ),
        PilotCaseCheckV0(
            case_id="C47",
            status="PASS",
            checks=(
                "case_level_locators_preserved",
                "mou_and_zhu_preserved",
                "shi_and_absence_preserved",
            ),
        ),
    )


class ProjectionValidationReportV0(StrictResearchModel):
    schema_version: Literal["projection-validation-report/pilot-v0"]
    status: Literal["PASS"]
    source_manifest_sha256: str = Field(strict=True, pattern=r"^[0-9a-f]{64}$")
    source_mapping_sha256: str = Field(strict=True, pattern=r"^[0-9a-f]{64}$")
    source_replay_expected: int = Field(strict=True, ge=0)
    source_replay_actual: int = Field(strict=True, ge=0)
    reverse_accession_expected: int = Field(strict=True, ge=0)
    reverse_accession_actual: int = Field(strict=True, ge=0)
    reverse_mapping_expected: int = Field(strict=True, ge=0)
    reverse_mapping_actual: int = Field(strict=True, ge=0)
    graph_node_count: int = Field(strict=True, ge=0)
    bibliographic_edge_count: int = Field(strict=True, ge=0)
    evidence_link_count: int = Field(strict=True, ge=0)
    orphan_graph_node_count: int = Field(strict=True, ge=0)
    orphan_graph_edge_count: int = Field(strict=True, ge=0)
    orphan_assertion_count: int = Field(strict=True, ge=0)
    orphan_evidence_link_count: int = Field(strict=True, ge=0)
    title_based_merge_count: int = Field(strict=True, ge=0)
    accepted_independent_witness_count: int = Field(strict=True, ge=0)
    deferred_independent_witness_count: int = Field(strict=True, ge=0)
    pilot_cases: tuple[PilotCaseCheckV0, ...]
    core14_manifest_sha256: str = Field(strict=True, pattern=r"^[0-9a-f]{64}$")
    core14_audit_digests: tuple[FileDigestV0, ...]
    layer_a_before: SnapshotDigestV0
    layer_a_after: SnapshotDigestV0
    rule_identity_fixture_status: Literal[
        "NO_VERSIONED_RULE_FIXTURE_IN_STABLE_BASELINE"
    ]
    rule_identity_fixture_before: tuple[FileDigestV0, ...]
    rule_identity_fixture_after: tuple[FileDigestV0, ...]
    forbidden_side_effects: ForbiddenSideEffectsV0

    @model_validator(mode="after")
    def validate_pass_evidence(self) -> "ProjectionValidationReportV0":
        if self.source_replay_expected != self.source_replay_actual:
            raise ValueError("source replay denominator does not close")
        if self.reverse_accession_expected != self.reverse_accession_actual:
            raise ValueError("reverse accession denominator does not close")
        if self.reverse_mapping_expected != self.reverse_mapping_actual:
            raise ValueError("reverse mapping denominator does not close")
        if any(
            value != 0
            for value in (
                self.orphan_graph_node_count,
                self.orphan_graph_edge_count,
                self.orphan_assertion_count,
                self.orphan_evidence_link_count,
                self.title_based_merge_count,
                self.accepted_independent_witness_count,
            )
        ):
            raise ValueError("PASS report cannot contain orphan, merge, or accepted counts")
        if self.deferred_independent_witness_count <= 0:
            raise ValueError("PASS report must retain deferred independent-witness state")
        if tuple(item.case_id for item in self.pilot_cases) != ("C14", "C45", "C47"):
            raise ValueError("pilot cases must be C14, C45, and C47 in order")
        if self.layer_a_before != self.layer_a_after:
            raise ValueError("Layer-A snapshot changed during build")
        if self.rule_identity_fixture_before != self.rule_identity_fixture_after:
            raise ValueError("rule identity fixture snapshot changed during build")
        if self.rule_identity_fixture_before or self.rule_identity_fixture_after:
            raise ValueError("no-fixture status requires empty fixture hash denominators")
        return self


class SourceProjectionBundleV0(StrictResearchModel):
    schema_version: Literal["source-projection-bundle/pilot-v0"]
    research_only: Literal[True]
    source_manifest_sha: str = Field(strict=True, pattern=r"^[0-9a-f]{64}$")
    source_mapping_sha: str = Field(strict=True, pattern=r"^[0-9a-f]{64}$")
    core14_index: Core14TargetIndexV0
    source_package_metadata: SourcePackageMetadataV0
    mapping_package_metadata: MappingPackageMetadataV0
    source_objects: tuple[SourceObjectRefV0, ...]
    nodes: tuple[SourceGraphNodeV0, ...]
    bibliographic_edges: tuple[SourceGraphEdgeV0, ...]
    assertions: tuple[ResearchAssertionV0, ...]
    evidence_links: tuple[ResearchEvidenceLinkV0, ...]
    generated_from_accession_ids: tuple[str, ...]
    generated_from_mapping_ids: tuple[str, ...]
    pilot_case_ids: tuple[Literal["C14", "C45", "C47"], ...]
    title_based_merges: tuple[str, ...] = ()
    validation_report: ProjectionValidationReportV0 | None = None

    @model_validator(mode="after")
    def validate_closed_research_graph(self) -> "SourceProjectionBundleV0":
        node_by_id = {node.node_id: node for node in self.nodes}
        if len(node_by_id) != len(self.nodes):
            raise ValueError("graph nodes must have unique IDs")
        edge_ids = {edge.edge_id for edge in self.bibliographic_edges}
        if len(edge_ids) != len(self.bibliographic_edges):
            raise ValueError("bibliographic edges must have unique IDs")
        assertion_ids = {item.assertion_id for item in self.assertions}
        if len(assertion_ids) != len(self.assertions):
            raise ValueError("assertions must have unique IDs")
        mapping_ids = {item.mapping_id for item in self.evidence_links}
        if len(mapping_ids) != len(self.evidence_links):
            raise ValueError("evidence links must have unique mapping IDs")
        family_ordinals = {
            item.ordinal for item in self.source_package_metadata.families
        }
        source_ordinals = {item.ordinal for item in self.source_objects}
        mapping_ordinals = {item.ordinal for item in self.evidence_links}
        if family_ordinals != set(range(len(self.source_package_metadata.families))):
            raise ValueError("family ordinals must be a complete sequence")
        if source_ordinals != set(range(len(self.source_objects))):
            raise ValueError("source ordinals must be a complete sequence")
        if mapping_ordinals != set(range(len(self.evidence_links))):
            raise ValueError("mapping ordinals must be a complete sequence")
        if self.title_based_merges:
            raise ValueError("title-based merges are forbidden in pilot-v0")

        family_ids = [item.family_id for item in self.source_package_metadata.families]
        source_ids = [item.accession_id for item in self.source_objects]
        if len(family_ids) != len(set(family_ids)):
            raise ValueError("family descriptors must have unique IDs")
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source object references must have unique accession IDs")
        if self.source_package_metadata.family_count != len(family_ids):
            raise ValueError("source metadata family count is inconsistent")
        if self.source_package_metadata.accession_count != len(source_ids):
            raise ValueError("source metadata accession count is inconsistent")
        if self.source_package_metadata.raw_file_count != len(source_ids):
            raise ValueError("source metadata raw-file count is inconsistent")
        if self.source_package_metadata.total_raw_byte_count != sum(
            item.raw_byte_count for item in self.source_objects
        ):
            raise ValueError("source metadata raw-byte total is inconsistent")
        source_family_counts = {family_id: 0 for family_id in family_ids}
        for source in self.source_objects:
            if source.family_id not in source_family_counts:
                raise ValueError("source object reference has unknown family")
            source_family_counts[source.family_id] += 1
        for family in self.source_package_metadata.families:
            if family.accession_count != source_family_counts[family.family_id]:
                raise ValueError("family accession count is inconsistent")

        endpoint_kinds = {
            GraphRelation.WORK_HAS_TEXT_VERSION_CANDIDATE: (
                NodeKind.WORK_CANDIDATE,
                NodeKind.TEXT_VERSION_CANDIDATE,
            ),
            GraphRelation.VERSION_HAS_CARRIER: (
                NodeKind.TEXT_VERSION_CANDIDATE,
                NodeKind.CARRIER,
            ),
            GraphRelation.CARRIER_HAS_SOURCE_OBJECT: (
                NodeKind.CARRIER,
                NodeKind.SOURCE_OBJECT,
            ),
        }
        for node in self.nodes:
            if node.kind is NodeKind.WORK_CANDIDATE:
                expected_node_id = f"work-candidate:family:{node.family_id}"
            elif node.kind is NodeKind.TEXT_VERSION_CANDIDATE:
                expected_node_id = f"text-version-candidate:family:{node.family_id}:v0"
            elif node.kind is NodeKind.CARRIER:
                if node.provider != "zh.wikisource.org":
                    raise ValueError("pilot carrier provider is invalid")
                carrier_payload = json.dumps(
                    {"page_title": node.page_title, "provider": node.provider},
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                expected_node_id = (
                    "carrier:zhws:sha256:" + hashlib.sha256(carrier_payload).hexdigest()
                )
            else:
                expected_node_id = f"source-object:{node.accession_id}"
            if node.node_id != expected_node_id:
                raise ValueError("graph node ID does not match identity derivation")
        for edge in self.bibliographic_edges:
            source = node_by_id.get(edge.source_node_id)
            target = node_by_id.get(edge.target_node_id)
            if source is None or target is None:
                raise ValueError("bibliographic edge endpoint is missing")
            if (source.kind, target.kind) != endpoint_kinds[edge.relation_type]:
                raise ValueError("bibliographic edge endpoint kind is invalid")
            edge_payload = (
                f"{edge.relation_type.value}\0{edge.source_node_id}\0{edge.target_node_id}"
            ).encode("utf-8")
            expected_edge_id = "edge:sha256:" + hashlib.sha256(edge_payload).hexdigest()
            if edge.edge_id != expected_edge_id:
                raise ValueError("bibliographic edge ID is invalid")
        if any(item.subject_node_id not in node_by_id for item in self.assertions):
            raise ValueError("assertion subject is missing")

        object_nodes = {
            node.node_id: node.accession_id
            for node in self.nodes
            if node.kind is NodeKind.SOURCE_OBJECT
        }
        object_refs = {item.accession_id for item in self.source_objects}
        if len(object_nodes) != len(object_refs) or len(object_nodes.values()) != len(
            set(object_nodes.values())
        ):
            raise ValueError("source-object nodes must map one-to-one to accessions")
        if set(object_nodes.values()) != object_refs:
            raise ValueError("source-object nodes and references must close exactly")
        if self.generated_from_accession_ids != tuple(sorted(object_refs)):
            raise ValueError("generated accession IDs do not match source objects")
        if self.generated_from_mapping_ids != tuple(sorted(mapping_ids)):
            raise ValueError("generated mapping IDs do not match evidence links")
        mapped_case_ids = {item.target_case_id for item in self.evidence_links}
        declared_case_ids = set(self.source_package_metadata.core14_cases)
        if declared_case_ids != mapped_case_ids:
            raise ValueError("source metadata Core14 cases must equal mapped cases")
        if not declared_case_ids <= set(self.core14_index.case_ids):
            raise ValueError("source metadata contains unknown Core14 case")
        for edge in self.bibliographic_edges:
            if not set(edge.supporting_accession_ids) <= object_refs:
                raise ValueError("edge evidence contains unknown accession")
        for assertion in self.assertions:
            if not set(assertion.supporting_accession_ids) <= object_refs:
                raise ValueError("assertion support contains unknown accession")
            if not set(assertion.contradicting_accession_ids) <= object_refs:
                raise ValueError("assertion contradiction contains unknown accession")
            if len(assertion.supporting_accession_ids) != 1:
                raise ValueError("pilot assertion must bind one source accession")
            expected_assertion_id = (
                f"assertion:{assertion.supporting_accession_ids[0]}:{assertion.predicate}"
            )
            if assertion.assertion_id != expected_assertion_id:
                raise ValueError("assertion ID does not match identity derivation")
        for link in self.evidence_links:
            if object_nodes.get(link.source_object_id) != link.source_accession_id:
                raise ValueError("evidence link source object is invalid")
            if not self.core14_index.contains_case(link.target_case_id):
                raise ValueError("evidence link case target is unknown")
            if any(
                not self.core14_index.contains_atom(link.target_case_id, atom_id)
                for atom_id in link.target_atom_ids
            ):
                raise ValueError("evidence link atom target is unknown")
            if not set(link.supporting_accession_ids) <= object_refs:
                raise ValueError("evidence-link support contains unknown accession")
            if not set(link.contradicting_accession_ids) <= object_refs:
                raise ValueError("evidence-link contradiction contains unknown accession")
            if link.direction != self.mapping_package_metadata.direction:
                raise ValueError("evidence-link direction is inconsistent")
            if link.relation_type not in self.mapping_package_metadata.relation_types:
                raise ValueError("evidence-link relation is not declared")
            if link.source_accession_id not in link.supporting_accession_ids:
                raise ValueError("evidence-link support must contain its source accession")
        if self.validation_report is not None:
            report = self.validation_report
            if report.source_manifest_sha256 != self.source_manifest_sha:
                raise ValueError("validation report source manifest hash is inconsistent")
            if report.source_mapping_sha256 != self.source_mapping_sha:
                raise ValueError("validation report source mapping hash is inconsistent")
            if report.source_replay_actual != len(self.source_objects):
                raise ValueError("validation report source replay count is inconsistent")
            if report.reverse_accession_actual != len(self.source_objects):
                raise ValueError("validation report reverse accession count is inconsistent")
            if report.reverse_mapping_actual != len(self.evidence_links):
                raise ValueError("validation report reverse mapping count is inconsistent")
            if report.graph_node_count != len(self.nodes):
                raise ValueError("validation report graph node count is inconsistent")
            if report.bibliographic_edge_count != len(self.bibliographic_edges):
                raise ValueError("validation report edge count is inconsistent")
            if report.evidence_link_count != len(self.evidence_links):
                raise ValueError("validation report evidence-link count is inconsistent")
            if report.core14_manifest_sha256 != self.core14_index.manifest_sha256:
                raise ValueError("validation report Core14 manifest hash is inconsistent")
            expected_audits = tuple(
                FileDigestV0(path=item.path, sha256=item.sha256)
                for item in self.core14_index.audits
            )
            if report.core14_audit_digests != expected_audits:
                raise ValueError("validation report Core14 audit hashes are inconsistent")
            if tuple(item.case_id for item in report.pilot_cases) != self.pilot_case_ids:
                raise ValueError("validation report pilot cases are inconsistent")
            if report.forbidden_side_effects != self.source_package_metadata.forbidden_side_effects:
                raise ValueError("validation report forbidden side effects are inconsistent")
            if report.accepted_independent_witness_count != len(
                self.accepted_independent_witness_assertions
            ):
                raise ValueError("validation report accepted-witness count is inconsistent")
            if report.deferred_independent_witness_count != (
                self.deferred_independent_witness_assertion_count
            ):
                raise ValueError("validation report deferred-witness count is inconsistent")
            expected_pilot_checks = build_pilot_case_checks(
                self.evidence_links,
                self.source_objects,
                self.assertions,
            )
            if report.pilot_cases != expected_pilot_checks:
                raise ValueError("validation report pilot checks are inconsistent")
        return self

    @property
    def source_object_count(self) -> int:
        return len(self.source_objects)

    @property
    def evidence_link_count(self) -> int:
        return len(self.evidence_links)

    @property
    def accepted_independent_witness_assertions(
        self,
    ) -> tuple[ResearchAssertionV0, ...]:
        return ()

    @property
    def deferred_independent_witness_assertion_count(self) -> int:
        return sum(
            assertion.predicate == "independent_witness"
            and assertion.status is AssertionStatus.DEFERRED
            for assertion in self.assertions
        )

    def canonical_json_bytes(self) -> bytes:
        payload = self.model_dump(mode="json", exclude_none=False)
        payload["source_objects"] = sorted(
            payload["source_objects"], key=lambda item: item["accession_id"]
        )
        payload["nodes"] = sorted(payload["nodes"], key=lambda item: item["node_id"])
        payload["bibliographic_edges"] = sorted(
            payload["bibliographic_edges"], key=lambda item: item["edge_id"]
        )
        payload["assertions"] = sorted(
            payload["assertions"], key=lambda item: item["assertion_id"]
        )
        payload["evidence_links"] = sorted(
            payload["evidence_links"], key=lambda item: item["mapping_id"]
        )
        return json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")


__all__ = [
    "AssertionStatus",
    "CompatibilityProjectionV0",
    "FileDigestV0",
    "ConfidenceLevel",
    "FamilyDescriptorV0",
    "ForbiddenSideEffectsV0",
    "GraphRelation",
    "MappingPackageMetadataV0",
    "NodeKind",
    "ResearchAssertionV0",
    "ResearchEvidenceLinkV0",
    "SourceGraphEdgeV0",
    "SourceGraphNodeV0",
    "SourceObjectRefV0",
    "SourcePackageMetadataV0",
    "SourceProjectionBundleV0",
    "SnapshotDigestV0",
    "PilotCaseCheckV0",
    "ProjectionValidationReportV0",
    "build_pilot_case_checks",
]
