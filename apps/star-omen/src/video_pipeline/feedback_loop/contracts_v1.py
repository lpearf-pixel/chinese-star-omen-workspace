from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from src.video_pipeline.contracts._common import (
    FiniteFloat,
    Sha256Hex,
    StableId,
    StrictContractModel,
    ensure_unique,
)
from src.video_pipeline.contracts.external_media_v1 import AuditDisposition


LocalProbeState = Literal[
    "corroborated",
    "contradicted",
    "unresolved",
    "not_searched",
]
OperationalDisposition = Literal[
    "supported",
    "source_missing",
    "ambiguous",
    "contradicted",
    "modern_context_only",
    "unresolved",
    "not_searched",
]
OwnerSubsystem = Literal[
    "corpus_research",
    "retrieval",
    "semantic_policy",
    "video_editorial",
]


class LocalEvidenceReferenceV1(StrictContractModel):
    evidence_ref_id: StableId
    evidence_class: Literal[
        "citable_passage",
        "historical_source",
        "modern_authority",
        "retrieval_record",
    ]
    evidence_locator: str = Field(min_length=1, max_length=2048)
    evidence_sha256: Sha256Hex
    relationship: Literal["supports", "qualifies", "contradicts", "context_only"]
    note: str = Field(min_length=1, max_length=4000)


class LocalEvidenceProbeV1(StrictContractModel):
    schema_version: Literal["local-evidence-probe/v1"]
    probe_id: StableId
    source_id: StableId
    claim_id: StableId
    query: str = Field(min_length=1, max_length=4000)
    corpus_version: str = Field(min_length=1, max_length=256)
    retrieval_version: str = Field(min_length=1, max_length=256)
    result_state: LocalProbeState
    evidence_references: list[LocalEvidenceReferenceV1] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_probe_state(self) -> "LocalEvidenceProbeV1":
        evidence_ids = [item.evidence_ref_id for item in self.evidence_references]
        ensure_unique(evidence_ids, "evidence_references")
        if self.result_state in {"corroborated", "contradicted"} and not evidence_ids:
            raise ValueError(f"{self.result_state} probes require evidence_references")
        if self.result_state == "not_searched" and evidence_ids:
            raise ValueError("not_searched probes cannot contain evidence_references")
        if self.result_state == "corroborated" and not any(
            item.relationship in {"supports", "qualifies"}
            for item in self.evidence_references
        ):
            raise ValueError("corroborated probes require supporting evidence")
        if self.result_state == "contradicted" and not any(
            item.relationship == "contradicts" for item in self.evidence_references
        ):
            raise ValueError("contradicted probes require contradicting evidence")
        return self


class FeedbackObservationV1(StrictContractModel):
    observation_id: StableId
    source_id: StableId
    audit_id: StableId
    claim_id: StableId
    probe_id: StableId
    external_disposition: AuditDisposition
    local_result_state: LocalProbeState
    operational_disposition: OperationalDisposition
    external_evidence_link_ids: list[StableId] = Field(default_factory=list)
    local_evidence_ref_ids: list[StableId] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="after")
    def validate_evidence_ids(self) -> "FeedbackObservationV1":
        ensure_unique(
            list(self.external_evidence_link_ids), "external_evidence_link_ids"
        )
        ensure_unique(list(self.local_evidence_ref_ids), "local_evidence_ref_ids")
        return self


class ImprovementCandidateV1(StrictContractModel):
    candidate_id: StableId
    owner_subsystem: OwnerSubsystem
    supporting_observation_ids: list[StableId] = Field(default_factory=list)
    contradicting_observation_ids: list[StableId] = Field(default_factory=list)
    confidence: FiniteFloat = Field(ge=0.0, le=1.0)
    hypothesis: str = Field(min_length=1, max_length=4000)
    verification_steps: list[str] = Field(min_length=1)
    rollback_requirements: list[str] = Field(min_length=1)
    apply_allowed: Literal[False]

    @model_validator(mode="after")
    def validate_observation_references(self) -> "ImprovementCandidateV1":
        supporting = list(self.supporting_observation_ids)
        contradicting = list(self.contradicting_observation_ids)
        ensure_unique(supporting, "supporting_observation_ids")
        ensure_unique(contradicting, "contradicting_observation_ids")
        if set(supporting) & set(contradicting):
            raise ValueError("candidate observation references cannot both support and contradict")
        if not supporting and not contradicting:
            raise ValueError("candidate requires an observation reference")
        return self


class VideoClaimCandidateV1(StrictContractModel):
    video_claim_id: StableId
    claim_class: Literal[
        "astronomy_fact",
        "historical_context",
        "modern_interpretation",
        "production_instruction",
    ]
    text: str = Field(min_length=1, max_length=4000)
    observation_ids: list[StableId] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_observations(self) -> "VideoClaimCandidateV1":
        ensure_unique(list(self.observation_ids), "video claim observation_ids")
        return self


class VideoProductionRequestV1(StrictContractModel):
    request_id: StableId
    source_id: StableId
    audit_id: StableId
    topic: str = Field(min_length=1, max_length=1000)
    format: Literal["source_audit_explainer"]
    claims: list[VideoClaimCandidateV1] = Field(min_length=1)
    forbidden_claims: list[str] = Field(min_length=1)
    evidence_ref_ids: list[StableId] = Field(default_factory=list)
    required_disclaimers: list[str] = Field(min_length=1)
    output_contract: Literal["video-package/v1"]
    requires_human_review: Literal[True]

    @model_validator(mode="after")
    def validate_request_references(self) -> "VideoProductionRequestV1":
        ensure_unique([claim.video_claim_id for claim in self.claims], "video claims")
        ensure_unique(list(self.evidence_ref_ids), "request evidence_ref_ids")
        return self


class ManualPublicationHandoffV1(StrictContractModel):
    handoff_id: StableId
    request_id: StableId
    state: Literal[
        "awaiting_video_package",
        "awaiting_human_review",
        "learning_proposal_ready",
    ]
    requirements: list[str] = Field(min_length=1)
    blocked_reasons: list[str] = Field(min_length=1)
    auto_publish_allowed: Literal[False]


class FeedbackMetricV1(StrictContractModel):
    metric_id: StableId
    metric_name: str = Field(min_length=1, max_length=256)
    value: FiniteFloat
    unit: str = Field(min_length=1, max_length=128)


class FeedbackOutcomeV1(StrictContractModel):
    outcome_id: StableId
    handoff_id: StableId
    decision: Literal["human_reviewed", "rejected", "publication_observed"]
    reviewer_id: StableId
    notes: list[str] = Field(default_factory=list)
    metrics: list[FeedbackMetricV1] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_metric_ids(self) -> "FeedbackOutcomeV1":
        ensure_unique([metric.metric_id for metric in self.metrics], "metrics")
        return self


class LearningUpdateProposalV1(StrictContractModel):
    proposal_id: StableId
    outcome_id: StableId
    owner_subsystem: OwnerSubsystem
    evidence_observation_ids: list[StableId] = Field(min_length=1)
    expected_benefit: str = Field(min_length=1, max_length=4000)
    verification_steps: list[str] = Field(min_length=1)
    rollback_requirements: list[str] = Field(min_length=1)
    apply_allowed: Literal[False]

    @model_validator(mode="after")
    def validate_observations(self) -> "LearningUpdateProposalV1":
        ensure_unique(
            list(self.evidence_observation_ids), "proposal evidence_observation_ids"
        )
        return self


class FeedbackLoopRunV1(StrictContractModel):
    schema_version: Literal["feedback-loop-run/v1"]
    run_id: StableId
    policy_version: str = Field(min_length=1, max_length=256)
    source_id: StableId
    audit_id: StableId
    local_probes: list[LocalEvidenceProbeV1]
    observations: list[FeedbackObservationV1]
    improvement_candidates: list[ImprovementCandidateV1] = Field(default_factory=list)
    video_production_request: VideoProductionRequestV1
    manual_publication_handoff: ManualPublicationHandoffV1
    outcome: FeedbackOutcomeV1 | None = None
    learning_update_proposal: LearningUpdateProposalV1 | None = None
    metrics: list[FeedbackMetricV1] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "FeedbackLoopRunV1":
        probes_by_id = {probe.probe_id: probe for probe in self.local_probes}
        observations_by_id = {
            observation.observation_id: observation for observation in self.observations
        }
        ensure_unique([probe.probe_id for probe in self.local_probes], "local_probes")
        ensure_unique(
            [observation.observation_id for observation in self.observations],
            "observations",
        )
        ensure_unique(
            [candidate.candidate_id for candidate in self.improvement_candidates],
            "improvement_candidates",
        )
        ensure_unique([metric.metric_id for metric in self.metrics], "metrics")

        for probe in self.local_probes:
            if probe.source_id != self.source_id:
                raise ValueError("probe source_id must equal run source_id")
        for observation in self.observations:
            if observation.source_id != self.source_id:
                raise ValueError("observation source_id must equal run source_id")
            if observation.audit_id != self.audit_id:
                raise ValueError("observation audit_id must equal run audit_id")
            probe = probes_by_id.get(observation.probe_id)
            if probe is None:
                raise ValueError("observation references an unknown probe")
            if observation.claim_id != probe.claim_id:
                raise ValueError("observation claim_id must equal probe claim_id")
            probe_evidence_ids = {
                reference.evidence_ref_id for reference in probe.evidence_references
            }
            if not set(observation.local_evidence_ref_ids) <= probe_evidence_ids:
                raise ValueError("observation local evidence must belong to its probe")
        for candidate in self.improvement_candidates:
            candidate_observation_ids = set(candidate.supporting_observation_ids) | set(
                candidate.contradicting_observation_ids
            )
            if not candidate_observation_ids <= observations_by_id.keys():
                raise ValueError("candidate observation references must belong to the run")

        request = self.video_production_request
        if request.source_id != self.source_id:
            raise ValueError("request source_id must equal run source_id")
        if request.audit_id != self.audit_id:
            raise ValueError("request audit_id must equal run audit_id")
        for claim in request.claims:
            if not set(claim.observation_ids) <= observations_by_id.keys():
                raise ValueError("video claim observation_ids must belong to the run")
        known_evidence_ids = {
            evidence_id
            for probe in self.local_probes
            for evidence_id in [
                reference.evidence_ref_id for reference in probe.evidence_references
            ]
        } | {
            evidence_id
            for observation in self.observations
            for evidence_id in observation.external_evidence_link_ids
        }
        if not set(request.evidence_ref_ids) <= known_evidence_ids:
            raise ValueError("request evidence_ref_ids must belong to the run")

        handoff = self.manual_publication_handoff
        if handoff.request_id != request.request_id:
            raise ValueError("handoff request_id must equal video production request")
        if (self.outcome is None) != (self.learning_update_proposal is None):
            raise ValueError("outcome and learning_update_proposal must be paired")
        if self.outcome is None:
            if handoff.state == "learning_proposal_ready":
                raise ValueError("learning_proposal_ready requires an outcome and proposal")
            return self

        assert self.learning_update_proposal is not None
        if handoff.state != "learning_proposal_ready":
            raise ValueError("outcome and proposal require learning_proposal_ready")
        if self.outcome.handoff_id != handoff.handoff_id:
            raise ValueError("outcome handoff_id must equal manual publication handoff")
        if self.learning_update_proposal.outcome_id != self.outcome.outcome_id:
            raise ValueError("proposal outcome_id must equal outcome")
        if not set(self.learning_update_proposal.evidence_observation_ids) <= observations_by_id.keys():
            raise ValueError("proposal observation references must belong to the run")
        return self
