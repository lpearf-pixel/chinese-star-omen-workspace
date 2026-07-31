from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import Annotated, Any, Literal, Mapping

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

_STABLE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:/-]{0,159}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _validate_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must include an explicit UTC offset")
    if value.utcoffset() != timedelta(0):
        raise ValueError("datetime must be expressed in UTC")
    return value


UtcDateTime = Annotated[datetime, AfterValidator(_validate_utc)]
StableId = Annotated[
    str,
    Field(strict=True, min_length=1, max_length=160, pattern=_STABLE_ID_RE.pattern),
]
Sha256Hex = Annotated[str, Field(strict=True, pattern=_SHA256_RE.pattern)]
NonEmptyText = Annotated[
    str,
    Field(strict=True, min_length=1, max_length=4000),
]


class StrictRuleModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


def _canonical_json_bytes(value: BaseModel | Mapping[str, Any]) -> bytes:
    payload: Any
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude_none=False)
    else:
        payload = dict(value)
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _require_unique(values: list[str], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must contain unique identifiers")


def _require_sorted(values: list[str], field_name: str) -> None:
    if values != sorted(values):
        raise ValueError(f"{field_name} must be sorted")


EffectDomain = Literal[
    "politics",
    "leadership",
    "military",
    "agriculture",
    "climate",
    "economy",
    "public_health",
    "ritual",
    "border",
    "general_omen",
    "other",
]


class TriggerV2(StrictRuleModel):
    body_or_actor: list[NonEmptyText] = Field(min_length=1)
    event_type: str = Field(min_length=1, max_length=120)
    target_object_or_region: list[NonEmptyText] = Field(default_factory=list)
    relation_terms: list[NonEmptyText] = Field(min_length=1)
    required_measurements: list[NonEmptyText] = Field(default_factory=list)
    sequence_conditions: list[NonEmptyText] = Field(default_factory=list)
    visibility_conditions: list[NonEmptyText] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_lists(self) -> "TriggerV2":
        for field_name in (
            "body_or_actor",
            "target_object_or_region",
            "relation_terms",
            "required_measurements",
            "sequence_conditions",
            "visibility_conditions",
        ):
            _require_unique(getattr(self, field_name), f"trigger.{field_name}")
        return self


class ConditionV2(StrictRuleModel):
    condition_id: StableId
    kind: Literal[
        "target_region",
        "angular_relation",
        "direction",
        "sequence",
        "duration",
        "calendar",
        "visibility",
        "other",
    ]
    operator: Literal[
        "equals",
        "within",
        "outside",
        "before",
        "after",
        "during",
        "present",
        "absent",
        "other",
    ]
    value: str = Field(min_length=1, max_length=512)


class ObservationalPropertyV2(StrictRuleModel):
    property_id: StableId
    kind: Literal[
        "color",
        "size",
        "brightness",
        "motion",
        "rays",
        "shape",
        "other",
    ]
    value: str = Field(min_length=1, max_length=512)


class EffectV2(StrictRuleModel):
    effect_domain: list[EffectDomain] = Field(min_length=1)
    subject_scope: list[NonEmptyText] = Field(min_length=1)
    polarity: Literal["favorable", "adverse", "mixed", "neutral", "unknown"]
    description: str = Field(min_length=1, max_length=4000)
    historical_context: list[NonEmptyText] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_lists(self) -> "EffectV2":
        _require_unique(self.effect_domain, "effect.effect_domain")
        _require_unique(self.subject_scope, "effect.subject_scope")
        return self


class ComputabilityV2(StrictRuleModel):
    status: Literal[
        "computable",
        "partially_computable",
        "not_computable",
        "unknown",
    ]
    required_measurements: list[NonEmptyText] = Field(default_factory=list)
    reasons: list[NonEmptyText] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_reason(self) -> "ComputabilityV2":
        _require_unique(self.required_measurements, "computability.required_measurements")
        if self.status != "computable" and not self.reasons:
            raise ValueError("non-computable or uncertain status requires reasons")
        return self


class RuleProposalV2(StrictRuleModel):
    tradition: str = Field(min_length=1, max_length=120)
    trigger: TriggerV2
    actors: list[NonEmptyText] = Field(min_length=1)
    relation: str = Field(min_length=1, max_length=120)
    spatial_conditions: list[ConditionV2] = Field(default_factory=list)
    temporal_conditions: list[ConditionV2] = Field(default_factory=list)
    observational_properties: list[ObservationalPropertyV2] = Field(default_factory=list)
    effect: EffectV2
    severity: Literal["low", "medium", "high", "critical", "unknown"]
    time_window: str | None = Field(default=None, min_length=1, max_length=512)
    exceptions: list[NonEmptyText] = Field(default_factory=list)
    conflict_group: StableId | None = None
    rule_priority: int = Field(strict=True, ge=0, le=1_000_000)
    resolution_policy: Literal[
        "manual_adjudication",
        "specific_over_general",
        "tradition_scoped",
        "unresolved",
    ]
    computability: ComputabilityV2
    uncertainty: list[NonEmptyText] = Field(default_factory=list)
    editorial_notes: list[NonEmptyText] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_collections(self) -> "RuleProposalV2":
        _require_unique(self.actors, "actors")
        for field_name in (
            "spatial_conditions",
            "temporal_conditions",
            "observational_properties",
        ):
            values = [
                item.condition_id
                if isinstance(item, ConditionV2)
                else item.property_id
                for item in getattr(self, field_name)
            ]
            _require_unique(values, field_name)
        return self


class ExtractorIdentityV2(StrictRuleModel):
    extractor_type: Literal["deterministic", "model", "manual"]
    extractor_name: str = Field(min_length=1, max_length=160)
    extractor_version: str = Field(min_length=1, max_length=80)
    pattern_version: str | None = Field(default=None, min_length=1, max_length=160)
    model_provider: str | None = Field(default=None, min_length=1, max_length=160)
    model_name: str | None = Field(default=None, min_length=1, max_length=160)
    prompt_hash: Sha256Hex | None = None

    @model_validator(mode="after")
    def validate_extractor_boundary(self) -> "ExtractorIdentityV2":
        if self.extractor_type == "deterministic":
            if self.pattern_version is None:
                raise ValueError("deterministic extractor requires pattern_version")
            if any((self.model_provider, self.model_name, self.prompt_hash)):
                raise ValueError("deterministic extractor cannot declare model identity")
        elif self.extractor_type == "model":
            if not all((self.model_provider, self.model_name, self.prompt_hash)):
                raise ValueError("model extractor requires provider, model and prompt hash")
            if self.pattern_version is not None:
                raise ValueError("model extractor cannot declare pattern_version")
        elif any(
            (
                self.pattern_version,
                self.model_provider,
                self.model_name,
                self.prompt_hash,
            )
        ):
            raise ValueError("manual extractor cannot declare pattern or model identity")
        return self


class RawSpanV2(StrictRuleModel):
    passage_id: StableId
    raw_start: int = Field(strict=True, ge=0)
    raw_end: int = Field(strict=True, gt=0)
    raw_text: str = Field(min_length=1, max_length=20_000)
    raw_content_hash: Sha256Hex

    @model_validator(mode="after")
    def validate_offsets(self) -> "RawSpanV2":
        if self.raw_end <= self.raw_start:
            raise ValueError("raw_end must be greater than raw_start")
        return self


CandidateEventType = Literal[
    "created",
    "edited",
    "merged",
    "split",
    "rejected",
    "deferred",
    "approved",
]


class CandidateHistoryEventV2(StrictRuleModel):
    event_id: StableId
    sequence: int = Field(strict=True, ge=1)
    event_type: CandidateEventType
    actor_type: Literal["extractor", "model", "reviewer", "system"]
    actor_id: StableId
    recorded_at: UtcDateTime
    reason: str = Field(min_length=1, max_length=2000)
    proposal_sha256: Sha256Hex
    source_candidate_ids: list[StableId] = Field(default_factory=list)
    resulting_candidate_ids: list[StableId] = Field(default_factory=list)
    resulting_rule_id: StableId | None = None

    @model_validator(mode="after")
    def validate_event(self) -> "CandidateHistoryEventV2":
        _require_unique(self.source_candidate_ids, "history.source_candidate_ids")
        _require_unique(self.resulting_candidate_ids, "history.resulting_candidate_ids")
        if self.event_type == "approved" and self.resulting_rule_id is None:
            raise ValueError("approved event requires resulting_rule_id")
        if self.event_type == "approved" and self.actor_type != "reviewer":
            raise ValueError("approved event requires a reviewer actor")
        if self.event_type != "approved" and self.resulting_rule_id is not None:
            raise ValueError("only approved event may assign resulting_rule_id")
        if self.event_type == "merged" and len(self.source_candidate_ids) < 2:
            raise ValueError("merged event requires at least two source candidates")
        if self.event_type == "split" and len(self.resulting_candidate_ids) < 2:
            raise ValueError("split event requires at least two resulting candidates")
        return self


def proposal_sha256(proposal: RuleProposalV2 | Mapping[str, Any]) -> str:
    validated = (
        proposal
        if isinstance(proposal, RuleProposalV2)
        else RuleProposalV2.model_validate(proposal)
    )
    return hashlib.sha256(_canonical_json_bytes(validated)).hexdigest()


def derive_candidate_id(
    *,
    extractor: ExtractorIdentityV2 | Mapping[str, Any],
    source_passage_ids: list[str],
    raw_spans: list[RawSpanV2 | Mapping[str, Any]],
    proposal: RuleProposalV2 | Mapping[str, Any],
) -> str:
    validated_extractor = (
        extractor
        if isinstance(extractor, ExtractorIdentityV2)
        else ExtractorIdentityV2.model_validate(extractor)
    )
    validated_spans = [
        item if isinstance(item, RawSpanV2) else RawSpanV2.model_validate(item)
        for item in raw_spans
    ]
    validated_proposal = (
        proposal
        if isinstance(proposal, RuleProposalV2)
        else RuleProposalV2.model_validate(proposal)
    )
    identity = {
        "extractor": validated_extractor.model_dump(mode="json", exclude_none=False),
        "source_passage_ids": source_passage_ids,
        "raw_spans": [
            item.model_dump(mode="json", exclude_none=False) for item in validated_spans
        ],
        "proposal_sha256": proposal_sha256(validated_proposal),
    }
    digest = hashlib.sha256(_canonical_json_bytes(identity)).hexdigest()
    return f"candidate:sha256:{digest}"


CandidateStatus = Literal[
    "needs_review",
    "deferred_with_reason",
    "rejected",
    "merged",
    "split",
    "approved",
]


class RuleCandidateV2(StrictRuleModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:rule-candidate/v2"},
    )

    schema_version: Literal["rule-candidate/v2"]
    candidate_id: StableId
    extractor: ExtractorIdentityV2
    source_passage_ids: list[StableId] = Field(min_length=1)
    raw_spans: list[RawSpanV2] = Field(min_length=1)
    proposal: RuleProposalV2
    proposal_sha256: Sha256Hex
    status: CandidateStatus
    history: list[CandidateHistoryEventV2] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_candidate(self) -> "RuleCandidateV2":
        _require_unique(self.source_passage_ids, "source_passage_ids")
        _require_sorted(self.source_passage_ids, "source_passage_ids")
        span_order = [
            (item.passage_id, item.raw_start, item.raw_end) for item in self.raw_spans
        ]
        if span_order != sorted(span_order):
            raise ValueError("raw_spans must be sorted by passage and offsets")
        if len(span_order) != len(set(span_order)):
            raise ValueError("raw_spans must not contain duplicate spans")
        if any(item.passage_id not in self.source_passage_ids for item in self.raw_spans):
            raise ValueError("raw_spans must reference source_passage_ids")
        if self.proposal_sha256 != proposal_sha256(self.proposal):
            raise ValueError("proposal_sha256 does not match proposal")
        expected_id = derive_candidate_id(
            extractor=self.extractor,
            source_passage_ids=list(self.source_passage_ids),
            raw_spans=list(self.raw_spans),
            proposal=self.proposal,
        )
        if self.candidate_id != expected_id:
            raise ValueError("candidate_id does not match bound identity inputs")

        event_ids = [item.event_id for item in self.history]
        _require_unique(event_ids, "history event_id")
        if [item.sequence for item in self.history] != list(
            range(1, len(self.history) + 1)
        ):
            raise ValueError("history sequence must be contiguous from 1")
        if self.history[0].event_type != "created":
            raise ValueError("history must begin with created")
        if any(
            current.recorded_at <= previous.recorded_at
            for previous, current in zip(self.history, self.history[1:])
        ):
            raise ValueError("history timestamps must be strictly increasing")
        if self.candidate_id not in self.history[0].resulting_candidate_ids:
            raise ValueError("created history event must emit candidate_id")
        if self.history[-1].proposal_sha256 != self.proposal_sha256:
            raise ValueError("latest history proposal_sha256 must match proposal")

        terminal_event = {
            "deferred_with_reason": "deferred",
            "rejected": "rejected",
            "merged": "merged",
            "split": "split",
            "approved": "approved",
        }.get(self.status)
        if terminal_event is not None and self.history[-1].event_type != terminal_event:
            raise ValueError("terminal candidate status requires matching history event")
        if self.status == "needs_review" and self.history[-1].event_type in {
            "deferred",
            "rejected",
            "merged",
            "split",
            "approved",
        }:
            raise ValueError("needs_review cannot end in terminal history event")
        return self


def canonical_rule_candidate_bytes(candidate: RuleCandidateV2) -> bytes:
    validated = RuleCandidateV2.model_validate(
        candidate.model_dump(mode="json", exclude_none=False)
    )
    return _canonical_json_bytes(validated)


__all__ = [
    "CandidateHistoryEventV2",
    "ComputabilityV2",
    "ConditionV2",
    "EffectV2",
    "ExtractorIdentityV2",
    "ObservationalPropertyV2",
    "NonEmptyText",
    "RawSpanV2",
    "RuleCandidateV2",
    "RuleProposalV2",
    "Sha256Hex",
    "StableId",
    "StrictRuleModel",
    "TriggerV2",
    "UtcDateTime",
    "canonical_rule_candidate_bytes",
    "derive_candidate_id",
    "proposal_sha256",
]
