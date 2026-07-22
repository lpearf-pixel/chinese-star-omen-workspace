from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ._common import FiniteFloat, Sha256Hex, StableId, StrictContractModel, ensure_unique


ConditionState = Literal["pass", "fail", "unknown"]
RuleMatchStatus = Literal[
    "matched",
    "candidate_only",
    "insufficient_data",
    "partial_match",
    "not_matched",
]


class RuleMatchV1(StrictContractModel):
    rule_id: StableId
    status: RuleMatchStatus
    score: FiniteFloat = Field(ge=0.0, le=1.0)


class EvidenceReferenceV1(StrictContractModel):
    evidence_id: StableId
    status: Literal["citable", "candidate_only", "ambiguous", "missing_evidence"]
    source_locator: str | None = Field(default=None, min_length=1, max_length=256)
    content_hash: Sha256Hex | None = None

    @model_validator(mode="after")
    def validate_citable_fields(self) -> "EvidenceReferenceV1":
        if self.status == "citable" and (
            self.source_locator is None or self.content_hash is None
        ):
            raise ValueError("citable evidence requires source_locator and content_hash")
        return self


class RuleAssessmentV1(StrictContractModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:rule-assessment/v1"},
    )

    schema_version: Literal["rule-assessment/v1"]
    assessment_id: StableId
    event_id: StableId
    rule_set_version: StableId
    matched_rules: list[RuleMatchV1]
    condition_states: dict[StableId, ConditionState]
    match_status: RuleMatchStatus
    conflict_summary: list[str] = Field(default_factory=list)
    recommended_rule_id: StableId | None = None
    provisional_rule_id: StableId | None = None
    evidence_references: list[EvidenceReferenceV1]
    narration_eligibility: Literal["eligible", "blocked"]
    uncertainty_reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_assessment(self) -> "RuleAssessmentV1":
        rule_ids = [item.rule_id for item in self.matched_rules]
        rules_by_id = {item.rule_id: item for item in self.matched_rules}
        ensure_unique(rule_ids, "matched_rules")
        ensure_unique(
            [item.evidence_id for item in self.evidence_references],
            "evidence_references",
        )
        if self.match_status == "matched" and not any(
            item.status == "matched" for item in self.matched_rules
        ):
            raise ValueError("matched assessment requires a matched rule")
        if self.recommended_rule_id is not None:
            recommended = rules_by_id.get(self.recommended_rule_id)
            if recommended is None:
                raise ValueError("recommended_rule_id must reference matched_rules")
            if self.match_status != "matched" or recommended.status != "matched":
                raise ValueError("formal recommendation must reference a matched rule")
        if self.provisional_rule_id is not None and self.provisional_rule_id not in rule_ids:
            raise ValueError("provisional_rule_id must reference matched_rules")
        if self.narration_eligibility == "eligible":
            if self.match_status != "matched":
                raise ValueError("only matched assessments can be narration eligible")
            if not any(item.status == "citable" for item in self.evidence_references):
                raise ValueError("eligible narration requires citable evidence")
        return self
