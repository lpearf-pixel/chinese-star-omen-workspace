from __future__ import annotations

import hashlib
import json
from typing import Literal, Sequence

from pydantic import Field, model_validator

from src.video_pipeline.contracts._common import (
    Sha256Hex,
    StableId,
    StrictContractModel,
    ensure_unique,
)
from src.video_pipeline.contracts.rule_assessment_v1 import RuleAssessmentV1

EvidenceStatus = Literal["citable", "candidate_only", "ambiguous", "missing_evidence"]
RetrievalSource = Literal[
    "embedded_rule",
    "official_primary",
    "filesystem_fallback",
    "none",
]


def stable_lineage_id(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return f"{prefix}:{hashlib.sha256(payload).hexdigest()[:32]}"


class EvidenceProjectionRecordV1(StrictContractModel):
    schema_version: Literal["evidence-projection-record/v1"] = (
        "evidence-projection-record/v1"
    )
    evidence_id: StableId
    rule_id: StableId
    status: EvidenceStatus
    source_locator: str | None = Field(default=None, min_length=1, max_length=256)
    content_hash: Sha256Hex | None = None
    resolver_status: str = Field(min_length=1, max_length=96)
    resolver_version: str | None = Field(default=None, min_length=1, max_length=96)
    validation_version: str | None = Field(default=None, min_length=1, max_length=96)
    retrieval_source: RetrievalSource
    blocking_reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_record(self) -> "EvidenceProjectionRecordV1":
        if self.status == "citable":
            if self.source_locator is None or self.content_hash is None:
                raise ValueError("citable evidence projection requires locator and hash")
            if self.blocking_reasons:
                raise ValueError("citable evidence projection cannot have blocking reasons")
        elif not self.blocking_reasons:
            raise ValueError("non-citable evidence projection requires blocking reasons")
        return self


class RuleRetrievalReportV1(StrictContractModel):
    schema_version: Literal["rule-evidence-retrieval-report/v1"] = (
        "rule-evidence-retrieval-report/v1"
    )
    rule_id: StableId
    status: Literal[
        "embedded_citable",
        "embedded_non_citable",
        "hydrated_citable",
        "candidate_overlay_only",
        "ambiguous_exact_primary",
        "no_exact_primary",
        "resolver_rejected",
        "missing_evidence",
    ]
    exact_primary_count: int = Field(ge=0)
    candidate_overlay_count: int = Field(ge=0)
    official_primary_used: bool
    fallback_used: bool
    retrieval_source: RetrievalSource
    resolver_status: str | None = Field(default=None, min_length=1, max_length=96)


class EvidenceLineageEntryV1(StrictContractModel):
    schema_version: Literal["evidence-lineage-entry/v1"] = (
        "evidence-lineage-entry/v1"
    )
    lineage_id: StableId
    assessment_id: StableId
    event_id: StableId
    rule_id: StableId
    evidence_id: StableId
    status: EvidenceStatus
    claim_class: Literal["classical_quote"] = "classical_quote"
    source_locator: str | None = Field(default=None, min_length=1, max_length=256)
    content_hash: Sha256Hex | None = None
    retrieval_source: RetrievalSource
    resolver_status: str = Field(min_length=1, max_length=96)
    validation_version: str | None = Field(default=None, min_length=1, max_length=96)
    narration_allowed: bool
    blocking_reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_lineage(self) -> "EvidenceLineageEntryV1":
        if self.narration_allowed:
            if self.status != "citable":
                raise ValueError("narration lineage requires citable evidence")
            if self.blocking_reasons:
                raise ValueError("allowed narration lineage cannot be blocked")
        elif not self.blocking_reasons:
            raise ValueError("blocked narration lineage requires reasons")
        return self


class EvidenceBundleV1(StrictContractModel):
    schema_version: Literal["evidence-bundle/v1"] = "evidence-bundle/v1"
    bundle_id: StableId
    assessment_id: StableId
    event_id: StableId
    rule_set_version: StableId
    entries: list[EvidenceLineageEntryV1]

    @model_validator(mode="after")
    def validate_bundle(self) -> "EvidenceBundleV1":
        ensure_unique([entry.lineage_id for entry in self.entries], "lineage entries")
        ensure_unique([entry.evidence_id for entry in self.entries], "evidence entries")
        for entry in self.entries:
            if entry.assessment_id != self.assessment_id:
                raise ValueError("lineage assessment_id does not match bundle")
            if entry.event_id != self.event_id:
                raise ValueError("lineage event_id does not match bundle")
        return self

    def canonical_bytes(self) -> bytes:
        return canonical_evidence_bundle_bytes(self)


def canonical_evidence_bundle_bytes(bundle: EvidenceBundleV1) -> bytes:
    payload = bundle.model_dump(mode="json", exclude_none=False)
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def build_evidence_bundle(
    assessment: RuleAssessmentV1,
    records: Sequence[EvidenceProjectionRecordV1],
) -> EvidenceBundleV1:
    records_by_rule = {record.rule_id: record for record in records}
    if len(records_by_rule) != len(records):
        raise ValueError("evidence projection records must have unique rule IDs")
    match_rule_ids = [match.rule_id for match in assessment.matched_rules]
    if set(records_by_rule) != set(match_rule_ids):
        raise ValueError("evidence projection records must cover matched rules exactly")

    entries: list[EvidenceLineageEntryV1] = []
    for rule_id in match_rule_ids:
        record = records_by_rule[rule_id]
        allowed = (
            assessment.narration_eligibility == "eligible"
            and assessment.recommended_rule_id == rule_id
            and record.status == "citable"
        )
        blocking = [] if allowed else list(record.blocking_reasons)
        if not allowed and not blocking:
            blocking = ["not_formal_recommendation"]
        entries.append(
            EvidenceLineageEntryV1(
                lineage_id=stable_lineage_id(
                    "lineage",
                    assessment.assessment_id,
                    rule_id,
                    record.evidence_id,
                ),
                assessment_id=assessment.assessment_id,
                event_id=assessment.event_id,
                rule_id=rule_id,
                evidence_id=record.evidence_id,
                status=record.status,
                source_locator=record.source_locator,
                content_hash=record.content_hash,
                retrieval_source=record.retrieval_source,
                resolver_status=record.resolver_status,
                validation_version=record.validation_version,
                narration_allowed=allowed,
                blocking_reasons=blocking,
            )
        )

    bundle_id = stable_lineage_id(
        "evidence-bundle",
        assessment.assessment_id,
        *(entry.evidence_id for entry in entries),
    )
    return EvidenceBundleV1(
        bundle_id=bundle_id,
        assessment_id=assessment.assessment_id,
        event_id=assessment.event_id,
        rule_set_version=assessment.rule_set_version,
        entries=entries,
    )


__all__ = [
    "EvidenceBundleV1",
    "EvidenceLineageEntryV1",
    "EvidenceProjectionRecordV1",
    "RuleRetrievalReportV1",
    "build_evidence_bundle",
    "canonical_evidence_bundle_bytes",
    "stable_lineage_id",
]
