from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from src.video_pipeline.contracts.external_media_v1 import ExternalAuditBundleV1
from src.video_pipeline.feedback_loop.contracts_v1 import (
    FeedbackObservationV1,
    ImprovementCandidateV1,
    ManualPublicationHandoffV1,
    OwnerSubsystem,
    VideoClaimCandidateV1,
    VideoProductionRequestV1,
)


@dataclass(frozen=True, slots=True)
class _CandidatePolicy:
    owner_subsystem: OwnerSubsystem
    confidence: float
    hypothesis: str
    verification_steps: tuple[str, ...]
    rollback_requirements: tuple[str, ...]


_CANDIDATE_POLICY_BY_DISPOSITION: dict[str, tuple[_CandidatePolicy, ...]] = {
    "source_missing": (
        _CandidatePolicy(
            owner_subsystem="corpus_research",
            confidence=0.85,
            hypothesis=(
                "A citable classical source locus is needed before the captured "
                "historical correspondence can be assessed."
            ),
            verification_steps=(
                "Locate and review a citable classical locus in a separately approved corpus-research task.",
            ),
            rollback_requirements=(
                "Discard the candidate if no citable locus can be verified; do not promote external metadata.",
            ),
        ),
        _CandidatePolicy(
            owner_subsystem="retrieval",
            confidence=0.60,
            hypothesis=(
                "The unresolved source query should be evaluated for retrievable "
                "classical-locus coverage before any retrieval change is proposed."
            ),
            verification_steps=(
                "Evaluate the reviewed source-locus query against a fixture in a separately approved retrieval task.",
            ),
            rollback_requirements=(
                "Revert any later owning-module change if reviewed retrieval evidence does not improve.",
            ),
        ),
        _CandidatePolicy(
            owner_subsystem="video_editorial",
            confidence=0.90,
            hypothesis=(
                "The source gap requires an editorial source-audit explanation "
                "rather than a promoted historical claim."
            ),
            verification_steps=(
                "Review the source-audit explanation and disclaimers before accepting a video package.",
            ),
            rollback_requirements=(
                "Withhold the package if its wording promotes the missing source as classical evidence.",
            ),
        ),
    ),
    "modern_context_only": (
        _CandidatePolicy(
            owner_subsystem="semantic_policy",
            confidence=0.90,
            hypothesis=(
                "Modern storm-system context must remain distinct from the captured "
                "historical terminology."
            ),
            verification_steps=(
                "Review the terminology boundary in a separately approved semantic-policy task.",
            ),
            rollback_requirements=(
                "Reject any later policy change that equates historical terminology with a modern storm system.",
            ),
        ),
    ),
}


def plan_improvement_candidates(
    *, observations: Sequence[FeedbackObservationV1]
) -> tuple[ImprovementCandidateV1, ...]:
    """Map typed comparison dispositions to bounded, non-applying candidates."""
    validated_observations = _validated_observations(observations)
    candidates: list[ImprovementCandidateV1] = []
    for observation in validated_observations:
        for policy in _CANDIDATE_POLICY_BY_DISPOSITION.get(
            observation.operational_disposition, ()
        ):
            candidates.append(
                ImprovementCandidateV1(
                    candidate_id=(
                        f"candidate:vfl:{policy.owner_subsystem}:"
                        f"{observation.observation_id}"
                    ),
                    owner_subsystem=policy.owner_subsystem,
                    supporting_observation_ids=[observation.observation_id],
                    contradicting_observation_ids=[],
                    confidence=policy.confidence,
                    hypothesis=policy.hypothesis,
                    verification_steps=list(policy.verification_steps),
                    rollback_requirements=list(policy.rollback_requirements),
                    apply_allowed=False,
                )
            )
    return tuple(sorted(candidates, key=lambda candidate: candidate.candidate_id))


def build_video_production_request(
    *,
    audit_bundle: ExternalAuditBundleV1,
    observations: Sequence[FeedbackObservationV1],
) -> VideoProductionRequestV1:
    """Build the safe, source-audit-only B9 request from typed observations."""
    audit = ExternalAuditBundleV1.model_validate(audit_bundle.model_dump(mode="python"))
    validated_observations = _validated_observations(observations)
    _validate_request_observations(audit=audit, observations=validated_observations)

    observations_by_disposition = {
        observation.operational_disposition: observation
        for observation in validated_observations
    }
    source_missing = observations_by_disposition.get("source_missing")
    modern_context = observations_by_disposition.get("modern_context_only")
    if source_missing is None or modern_context is None:
        raise ValueError(
            "source-audit request requires source_missing and modern_context_only observations"
        )

    claims = [
        VideoClaimCandidateV1(
            video_claim_id=f"video-claim:vfl:{source_missing.observation_id}",
            claim_class="historical_context",
            text=(
                "Captured metadata raises a possible historical correspondence, but "
                "no classical source locus was captured."
            ),
            observation_ids=[source_missing.observation_id],
        ),
        VideoClaimCandidateV1(
            video_claim_id=f"video-claim:vfl:{modern_context.observation_id}",
            claim_class="modern_interpretation",
            text=(
                "The WMO material supplies modern context only and does not establish "
                "a storm-system equivalence."
            ),
            observation_ids=[modern_context.observation_id],
        ),
    ]
    return VideoProductionRequestV1(
        request_id=(
            f"video-request:vfl:{audit.audit.audit_id}:source-audit-explainer"
        ),
        source_id=audit.source.source_id,
        audit_id=audit.audit.audit_id,
        topic=f"Source-audit explainer for {audit.audit.audit_id}",
        format="source_audit_explainer",
        claims=claims,
        forbidden_claims=[
            "Do not quote an absent classical quotation.",
            "Do not equate 烈风 with a typhoon, tropical cyclone, maritime storm, or any storm system.",
        ],
        evidence_ref_ids=sorted(
            {
                evidence_ref_id
                for observation in validated_observations
                for evidence_ref_id in observation.external_evidence_link_ids
            }
        ),
        required_disclaimers=[
            "Captured external metadata is research-only and does not establish classical authority or a rule.",
            "No classical source locus was captured for the historical correspondence claim.",
            "The WMO reference supplies modern context only and does not establish a storm-system equivalence.",
        ],
        output_contract="video-package/v1",
        requires_human_review=True,
    )


def build_initial_publication_handoff(
    *, production_request: VideoProductionRequestV1
) -> ManualPublicationHandoffV1:
    """Create the initial blocked handoff without a publisher or account adapter."""
    request = VideoProductionRequestV1.model_validate(
        production_request.model_dump(mode="python")
    )
    return ManualPublicationHandoffV1(
        handoff_id=f"handoff:vfl:{request.request_id}",
        request_id=request.request_id,
        state="awaiting_video_package",
        requirements=[
            "Provide a validated video-package/v1 B9 artifact for this request.",
            "Complete documented human review of the video package and its claims.",
            "Keep publication disabled until the package and human review requirements are met.",
        ],
        blocked_reasons=[
            "No video package has been supplied.",
            "Human review has not been completed.",
            "Automatic publication is prohibited by feedback-loop/v1.",
        ],
        auto_publish_allowed=False,
    )


def _validated_observations(
    observations: Sequence[FeedbackObservationV1],
) -> tuple[FeedbackObservationV1, ...]:
    validated = tuple(
        FeedbackObservationV1.model_validate(observation.model_dump(mode="python"))
        for observation in observations
    )
    observation_ids = [observation.observation_id for observation in validated]
    if len(observation_ids) != len(set(observation_ids)):
        raise ValueError("duplicate observation_id")
    return tuple(sorted(validated, key=lambda observation: observation.observation_id))


def _validate_request_observations(
    *, audit: ExternalAuditBundleV1, observations: Sequence[FeedbackObservationV1]
) -> None:
    expected_claim_ids = set(audit.audit.claim_ids)
    observations_by_claim_id = {
        observation.claim_id: observation for observation in observations
    }
    if set(observations_by_claim_id) != expected_claim_ids:
        raise ValueError("request observations must exactly cover audit claim_ids")
    if len(observations_by_claim_id) != len(observations):
        raise ValueError("duplicate request observation claim_id")

    assessments_by_claim_id = {
        assessment.claim_id: assessment for assessment in audit.audit.assessments
    }
    for observation in observations:
        if observation.source_id != audit.source.source_id:
            raise ValueError("request observation source_id must equal audit source_id")
        if observation.audit_id != audit.audit.audit_id:
            raise ValueError("request observation audit_id must equal audit audit_id")
        assessment = assessments_by_claim_id[observation.claim_id]
        if observation.external_disposition != assessment.disposition:
            raise ValueError(
                "request observation external_disposition must equal audit assessment"
            )
