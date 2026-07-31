from __future__ import annotations

from typing import Any, Literal, Mapping

from pydantic import ConfigDict, Field, ValidationError, model_validator

from .rule_candidate_v2 import (
    NonEmptyText,
    RuleProposalV2,
    Sha256Hex,
    StableId,
    StrictRuleModel,
    UtcDateTime,
    _canonical_json_bytes,
    _require_sorted,
    _require_unique,
    proposal_sha256,
)


class CitableEvidenceV2(StrictRuleModel):
    evidence_id: StableId
    status: Literal["citable", "candidate_only", "ambiguous", "missing_evidence"]
    passage_id: StableId
    kb_book_id: StableId
    source_locator: str = Field(min_length=1, max_length=512)
    page_marker: str = Field(min_length=1, max_length=160)
    heading_path: list[NonEmptyText] = Field(min_length=1)
    paragraph_index: int = Field(strict=True, ge=0)
    raw_start: int = Field(strict=True, ge=0)
    raw_end: int = Field(strict=True, gt=0)
    raw_content_hash: Sha256Hex
    normalized_content_hash: Sha256Hex
    source_fingerprint: Sha256Hex
    quote: str = Field(min_length=1, max_length=20_000)

    @model_validator(mode="after")
    def validate_binding(self) -> "CitableEvidenceV2":
        if self.raw_end <= self.raw_start:
            raise ValueError("raw_end must be greater than raw_start")
        return self


class RuleApprovalV2(StrictRuleModel):
    status: Literal["approved"]
    reviewer_id: StableId
    approved_at: UtcDateTime
    annotation_guide_version: StableId
    decision_reason: str = Field(min_length=1, max_length=4000)


class RuleProvenanceV2(StrictRuleModel):
    rule_id_assigned_by: Literal["human_review"]
    created_from_candidate_ids: list[StableId] = Field(min_length=1)
    created_at: UtcDateTime
    source_release_head: str = Field(strict=True, pattern=r"^[0-9a-f]{40}$")

    @model_validator(mode="after")
    def validate_candidates(self) -> "RuleProvenanceV2":
        _require_unique(
            self.created_from_candidate_ids,
            "provenance.created_from_candidate_ids",
        )
        _require_sorted(
            self.created_from_candidate_ids,
            "provenance.created_from_candidate_ids",
        )
        return self


class RuleVersionHistoryEntryV2(StrictRuleModel):
    rule_version: int = Field(strict=True, ge=1)
    content_sha256: Sha256Hex
    reviewer_id: StableId
    recorded_at: UtcDateTime
    reason: str = Field(min_length=1, max_length=2000)


class OmenRuleV2(StrictRuleModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:omen-rule/v2"},
    )

    schema_version: Literal["omen-rule/v2"]
    rule_id: StableId
    rule_version: int = Field(strict=True, ge=1)
    supersedes_rule_version: int | None = Field(default=None, strict=True, ge=1)
    source_candidate_ids: list[StableId] = Field(min_length=1)
    source_passage_ids: list[StableId] = Field(min_length=1)
    content: RuleProposalV2
    evidence: list[CitableEvidenceV2] = Field(min_length=1)
    review: RuleApprovalV2
    provenance: RuleProvenanceV2
    version_history: list[RuleVersionHistoryEntryV2] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_rule(self) -> "OmenRuleV2":
        for field_name in ("source_candidate_ids", "source_passage_ids"):
            values = list(getattr(self, field_name))
            _require_unique(values, field_name)
            _require_sorted(values, field_name)
        if self.source_candidate_ids != self.provenance.created_from_candidate_ids:
            raise ValueError(
                "provenance candidate identity must match source_candidate_ids"
            )
        evidence_ids = [item.evidence_id for item in self.evidence]
        _require_unique(evidence_ids, "evidence")
        if any(item.status != "citable" for item in self.evidence):
            raise ValueError("formal rule evidence must be citable")
        if any(
            item.passage_id not in self.source_passage_ids for item in self.evidence
        ):
            raise ValueError("evidence passage must reference source_passage_ids")

        if self.rule_version == 1:
            if self.supersedes_rule_version is not None:
                raise ValueError("version 1 cannot supersede a prior version")
        elif self.supersedes_rule_version != self.rule_version - 1:
            raise ValueError(
                "supersedes_rule_version must identify the immediately prior version"
            )

        expected_versions = list(range(1, self.rule_version + 1))
        actual_versions = [item.rule_version for item in self.version_history]
        if actual_versions != expected_versions:
            raise ValueError("version_history must preserve every version in order")
        if any(
            current.recorded_at <= previous.recorded_at
            for previous, current in zip(
                self.version_history, self.version_history[1:]
            )
        ):
            raise ValueError("version_history timestamps must be strictly increasing")
        if self.version_history[-1].content_sha256 != proposal_sha256(self.content):
            raise ValueError("latest content_sha256 must match current content")
        if self.version_history[-1].reviewer_id != self.review.reviewer_id:
            raise ValueError("latest history reviewer must match approval reviewer")
        if self.version_history[-1].recorded_at != self.review.approved_at:
            raise ValueError("latest history timestamp must match approval timestamp")
        if self.provenance.created_at > self.review.approved_at:
            raise ValueError("provenance creation cannot occur after approval")
        return self


class LegacyTriggerV1(StrictRuleModel):
    body: str
    event_type: str
    target: str | None = None
    qualifiers: list[str] = Field(default_factory=list)


class LegacyOmenRuleV1(StrictRuleModel):
    id: str
    source_text: str
    source_book: str
    trigger: LegacyTriggerV1
    effect_domain: list[str]
    validation_status: Literal[
        "unverified",
        "partially_verified",
        "historically_attested",
        "disputed",
    ]
    source_chapter: str | None = None
    evidence: Mapping[str, Any] | None = None
    severity: Literal["low", "medium", "high", "critical"] | None = None
    time_window: str | None = None
    interpretation: str | None = None
    modern_translation: str | None = None
    linked_cases: list[str] = Field(default_factory=list)
    notes: str | None = None


class OmenRuleV1MigrationReport(StrictRuleModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:omen-rule-migration/v1-to-v2"},
    )

    source_schema_version: Literal["omen-rule/v1"]
    target_schema_version: Literal["omen-rule/v2"]
    status: Literal["needs_review", "rejected", "migrated"]
    legacy_rule_id: str | None = None
    issue_codes: list[str] = Field(min_length=1)
    diagnostics: list[str] = Field(default_factory=list)
    migrated_rule: OmenRuleV2 | None = None

    @model_validator(mode="after")
    def validate_report(self) -> "OmenRuleV1MigrationReport":
        _require_unique(self.issue_codes, "issue_codes")
        if self.status == "migrated" and self.migrated_rule is None:
            raise ValueError("migrated status requires migrated_rule")
        if self.status != "migrated" and self.migrated_rule is not None:
            raise ValueError("non-migrated report cannot contain migrated_rule")
        return self


def migrate_omen_rule_v1(
    payload: Mapping[str, Any],
) -> OmenRuleV1MigrationReport:
    try:
        legacy = LegacyOmenRuleV1.model_validate(payload)
    except ValidationError as exc:
        return OmenRuleV1MigrationReport(
            source_schema_version="omen-rule/v1",
            target_schema_version="omen-rule/v2",
            status="rejected",
            legacy_rule_id=(
                payload.get("id") if isinstance(payload.get("id"), str) else None
            ),
            issue_codes=["invalid_v1_shape"],
            diagnostics=[str(exc)],
            migrated_rule=None,
        )

    issue_codes = [
        "candidate_identity_required",
        "passage_binding_required",
        "approval_history_required",
    ]
    if legacy.evidence is None:
        issue_codes.append("missing_citable_evidence")
    else:
        issue_codes.append("v1_evidence_revalidation_required")
    return OmenRuleV1MigrationReport(
        source_schema_version="omen-rule/v1",
        target_schema_version="omen-rule/v2",
        status="needs_review",
        legacy_rule_id=legacy.id,
        issue_codes=issue_codes,
        diagnostics=[
            "v1 content was read successfully but cannot be promoted without "
            "stable passages, candidate identity, citable evidence and human approval"
        ],
        migrated_rule=None,
    )


def canonical_omen_rule_bytes(
    value: OmenRuleV2 | OmenRuleV1MigrationReport,
) -> bytes:
    return _canonical_json_bytes(value)


__all__ = [
    "CitableEvidenceV2",
    "OmenRuleV1MigrationReport",
    "OmenRuleV2",
    "RuleApprovalV2",
    "RuleProvenanceV2",
    "RuleVersionHistoryEntryV2",
    "canonical_omen_rule_bytes",
    "migrate_omen_rule_v1",
]
