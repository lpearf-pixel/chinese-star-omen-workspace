from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.video_pipeline.feedback_loop.contracts_v1 import (
    FeedbackLoopRunV1,
    FeedbackMetricV1,
    FeedbackObservationV1,
    FeedbackOutcomeV1,
    ImprovementCandidateV1,
    LearningUpdateProposalV1,
    LocalEvidenceProbeV1,
    LocalEvidenceReferenceV1,
    ManualPublicationHandoffV1,
    VideoClaimCandidateV1,
    VideoProductionRequestV1,
)
from tests.video_pipeline.feedback_loop.helpers import (
    valid_candidate_payload,
    valid_handoff_payload,
    valid_local_evidence_reference_payload,
    valid_local_probe_payload,
    valid_metric_payload,
    valid_observation_payload,
    valid_outcome_payload,
    valid_proposal_payload,
    valid_run_payload,
    valid_video_claim_candidate_payload,
    valid_video_production_request_payload,
)


@pytest.mark.parametrize(
    ("model", "payload_factory"),
    [
        (LocalEvidenceReferenceV1, valid_local_evidence_reference_payload),
        (LocalEvidenceProbeV1, valid_local_probe_payload),
        (FeedbackObservationV1, valid_observation_payload),
        (ImprovementCandidateV1, valid_candidate_payload),
        (VideoClaimCandidateV1, valid_video_claim_candidate_payload),
        (VideoProductionRequestV1, valid_video_production_request_payload),
        (ManualPublicationHandoffV1, valid_handoff_payload),
        (FeedbackMetricV1, valid_metric_payload),
        (FeedbackOutcomeV1, valid_outcome_payload),
        (LearningUpdateProposalV1, valid_proposal_payload),
        (FeedbackLoopRunV1, valid_run_payload),
    ],
)
def test_contract_models_are_strict_and_accept_valid_lifecycle_records(
    model: type, payload_factory
) -> None:
    """Catches a contract made permissive by dropping the strict model base."""
    instance = model.model_validate(payload_factory())
    field_name = next(iter(type(instance).model_fields))
    with pytest.raises(ValidationError):
        setattr(instance, field_name, "caller-mutation")

    payload = payload_factory()
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_stable_ids_reject_invalid_lifecycle_identifiers() -> None:
    """Catches an ID field weakened to arbitrary text."""
    payload = valid_local_probe_payload()
    payload["probe_id"] = "probe id with spaces"
    with pytest.raises(ValidationError):
        LocalEvidenceProbeV1.model_validate(payload)


def test_confidence_and_metrics_reject_non_finite_numbers() -> None:
    """Catches confidence or outcome metrics accepting NaN or infinity."""
    candidate = valid_candidate_payload()
    candidate["confidence"] = float("nan")
    with pytest.raises(ValidationError):
        ImprovementCandidateV1.model_validate(candidate)

    metric = valid_metric_payload()
    metric["value"] = float("inf")
    with pytest.raises(ValidationError):
        FeedbackMetricV1.model_validate(metric)


def test_probe_state_must_agree_with_its_local_evidence() -> None:
    """Catches a probe that calls absent evidence corroboration or searched evidence."""
    corroborated_without_evidence = valid_local_probe_payload()
    corroborated_without_evidence["evidence_references"] = []
    with pytest.raises(ValidationError, match="corroborated"):
        LocalEvidenceProbeV1.model_validate(corroborated_without_evidence)

    not_searched_with_evidence = valid_local_probe_payload()
    not_searched_with_evidence["result_state"] = "not_searched"
    with pytest.raises(ValidationError, match="not_searched"):
        LocalEvidenceProbeV1.model_validate(not_searched_with_evidence)


def test_reference_collections_reject_duplicate_identifiers() -> None:
    """Catches duplicate evidence, observation, and metric references being accepted."""
    probe = valid_local_probe_payload()
    probe["evidence_references"].append(deepcopy(probe["evidence_references"][0]))
    with pytest.raises(ValidationError, match="evidence_references"):
        LocalEvidenceProbeV1.model_validate(probe)

    outcome = valid_outcome_payload()
    outcome["metrics"].append(deepcopy(outcome["metrics"][0]))
    with pytest.raises(ValidationError, match="metrics"):
        FeedbackOutcomeV1.model_validate(outcome)


def test_run_rejects_broken_lifecycle_references_and_identity() -> None:
    """Catches candidates, requests, and handoffs disconnected from this run."""
    missing_observation = valid_run_payload()
    missing_observation["improvement_candidates"][0]["supporting_observation_ids"] = [
        "observation:fixture:missing"
    ]
    with pytest.raises(ValidationError, match="candidate observation"):
        FeedbackLoopRunV1.model_validate(missing_observation)

    wrong_request_source = valid_run_payload()
    wrong_request_source["video_production_request"]["source_id"] = "media:fixture:other"
    with pytest.raises(ValidationError, match="request source_id"):
        FeedbackLoopRunV1.model_validate(wrong_request_source)

    wrong_handoff_request = valid_run_payload()
    wrong_handoff_request["manual_publication_handoff"]["request_id"] = (
        "video-request:fixture:other"
    )
    with pytest.raises(ValidationError, match="handoff request_id"):
        FeedbackLoopRunV1.model_validate(wrong_handoff_request)


def test_run_observation_state_must_equal_its_authoritative_probe_state() -> None:
    """Catches an observation copying a local result that differs from its probe."""
    payload = valid_run_payload()
    payload["observations"][0]["local_result_state"] = "contradicted"
    with pytest.raises(ValidationError, match="local_result_state"):
        FeedbackLoopRunV1.model_validate(payload)


def test_run_rejects_duplicate_evidence_ids_across_distinct_probes() -> None:
    """Catches flattened evidence identity collapsing two different local references."""
    payload = valid_run_payload()
    second_probe = deepcopy(payload["local_probes"][0])
    second_probe["probe_id"] = "probe:fixture:002"
    second_probe["claim_id"] = "claim:fixture:002"
    second_probe["evidence_references"][0]["evidence_locator"] = (
        "fixture://local/citation-002"
    )
    second_probe["evidence_references"][0]["evidence_sha256"] = "b" * 64
    payload["local_probes"].append(second_probe)

    second_observation = deepcopy(payload["observations"][0])
    second_observation["observation_id"] = "observation:fixture:002"
    second_observation["claim_id"] = "claim:fixture:002"
    second_observation["probe_id"] = "probe:fixture:002"
    payload["observations"].append(second_observation)

    with pytest.raises(ValidationError, match="run evidence_references"):
        FeedbackLoopRunV1.model_validate(payload)


def test_outcome_and_proposal_are_paired_and_match_the_handoff() -> None:
    """Catches a proposal without a human outcome or an outcome in the wrong stage."""
    proposal_without_outcome = valid_run_payload()
    proposal_without_outcome["learning_update_proposal"] = valid_proposal_payload()
    with pytest.raises(ValidationError, match="outcome and learning_update_proposal"):
        FeedbackLoopRunV1.model_validate(proposal_without_outcome)

    outcome_before_video_package = valid_run_payload(with_outcome=True)
    outcome_before_video_package["manual_publication_handoff"]["state"] = (
        "awaiting_video_package"
    )
    with pytest.raises(ValidationError, match="learning_proposal_ready"):
        FeedbackLoopRunV1.model_validate(outcome_before_video_package)

    wrong_outcome_handoff = valid_run_payload(with_outcome=True)
    wrong_outcome_handoff["outcome"]["handoff_id"] = "handoff:fixture:other"
    with pytest.raises(ValidationError, match="outcome handoff_id"):
        FeedbackLoopRunV1.model_validate(wrong_outcome_handoff)


@pytest.mark.parametrize(
    ("field_path", "value"),
    [
        (("improvement_candidates", 0, "apply_allowed"), True),
        (("learning_update_proposal", "apply_allowed"), True),
        (("manual_publication_handoff", "auto_publish_allowed"), True),
    ],
)
def test_callers_cannot_enable_apply_or_auto_publish_authority(
    field_path: tuple[str | int, ...], value: bool
) -> None:
    """Catches any literal-false authority flag changed to a caller-controlled bool."""
    payload = valid_run_payload(with_outcome=True)
    target: dict = payload
    for part in field_path[:-1]:
        target = target[part]  # type: ignore[index]
    target[field_path[-1]] = value  # type: ignore[index]
    with pytest.raises(ValidationError):
        FeedbackLoopRunV1.model_validate(payload)
