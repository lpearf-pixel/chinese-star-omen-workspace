from __future__ import annotations

import json

from src.video_pipeline.feedback_loop.comparison import compare_external_audit
from src.video_pipeline.feedback_loop.planner import (
    build_initial_publication_handoff,
    build_video_production_request,
    plan_improvement_candidates,
)
from tests.video_pipeline.feedback_loop.test_comparison_v1 import (
    episode_22_probes,
    load_episode_22_audit,
)


def episode_22_observations():
    return compare_external_audit(
        audit_bundle=load_episode_22_audit(), local_probes=episode_22_probes()
    )


def test_episode_22_plans_only_bounded_non_applying_candidates() -> None:
    """Catches a planner that applies, omits, or creates ungrounded candidates."""
    candidates = plan_improvement_candidates(observations=episode_22_observations())

    assert [candidate.candidate_id for candidate in candidates] == sorted(
        candidate.candidate_id for candidate in candidates
    )
    assert {candidate.owner_subsystem for candidate in candidates} == {
        "corpus_research",
        "retrieval",
        "semantic_policy",
        "video_editorial",
    }
    assert all(candidate.apply_allowed is False for candidate in candidates)
    assert all(candidate.verification_steps for candidate in candidates)
    assert all(candidate.rollback_requirements for candidate in candidates)
    assert all(
        candidate.supporting_observation_ids
        or candidate.contradicting_observation_ids
        for candidate in candidates
    )
    assert all(
        not set(candidate.supporting_observation_ids)
        & set(candidate.contradicting_observation_ids)
        for candidate in candidates
    )


def test_episode_22_candidates_have_fixed_canonical_identity_and_order() -> None:
    """Catches changed candidate IDs, confidence, or caller-order-dependent output."""
    observations = episode_22_observations()
    first = plan_improvement_candidates(observations=observations)
    repeated = plan_improvement_candidates(observations=observations)
    reversed_input = plan_improvement_candidates(
        observations=tuple(reversed(observations))
    )

    assert len(first) == 4
    assert [(candidate.candidate_id, candidate.confidence) for candidate in first] == [
        (
            "candidate:vfl:corpus_research:"
            "observation:audit:douyin:zushan:episode-22:"
            "claim:douyin:zushan:episode-22:01",
            0.85,
        ),
        (
            "candidate:vfl:retrieval:"
            "observation:audit:douyin:zushan:episode-22:"
            "claim:douyin:zushan:episode-22:01",
            0.60,
        ),
        (
            "candidate:vfl:semantic_policy:"
            "observation:audit:douyin:zushan:episode-22:"
            "claim:douyin:zushan:episode-22:02",
            0.90,
        ),
        (
            "candidate:vfl:video_editorial:"
            "observation:audit:douyin:zushan:episode-22:"
            "claim:douyin:zushan:episode-22:01",
            0.90,
        ),
    ]

    def serialized(candidates) -> bytes:
        return json.dumps(
            [candidate.model_dump(mode="json") for candidate in candidates],
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    assert serialized(repeated) == serialized(first)
    assert serialized(reversed_input) == serialized(first)


def test_candidate_policy_is_keyed_to_typed_dispositions() -> None:
    """Catches candidate generation based on source or creator display-name text."""
    observations = episode_22_observations()

    source_only = plan_improvement_candidates(observations=observations[:1])
    assert {candidate.owner_subsystem for candidate in source_only} == {
        "corpus_research",
        "retrieval",
        "video_editorial",
    }

    unknown_only = observations[1].model_copy(
        update={"operational_disposition": "not_searched"}
    )
    assert plan_improvement_candidates(observations=(unknown_only,)) == ()


def test_episode_22_production_request_preserves_safe_claim_boundaries() -> None:
    """Catches an absent classical quote or a weather-system equivalence in B9 input."""
    audit = load_episode_22_audit()
    observations = episode_22_observations()
    request = build_video_production_request(
        audit_bundle=audit, observations=observations
    )

    assert request.request_id == (
        "video-request:vfl:audit:douyin:zushan:episode-22:source-audit-explainer"
    )
    assert request.format == "source_audit_explainer"
    assert request.output_contract == "video-package/v1"
    assert request.requires_human_review is True
    assert "classical_quote" not in {claim.claim_class for claim in request.claims}
    assert all("classical quotation" not in claim.text.lower() for claim in request.claims)
    assert any("absent classical quotation" in claim for claim in request.forbidden_claims)
    assert any(
        "烈风" in claim
        and "typhoon" in claim
        and "tropical cyclone" in claim
        and "maritime storm" in claim
        for claim in request.forbidden_claims
    )
    assert any("no classical source" in claim.text.lower() for claim in request.claims)
    assert any("modern context only" in claim.text.lower() for claim in request.claims)
    assert request.evidence_ref_ids == [
        "evidence-link:douyin:zushan:episode-22:wmo-context"
    ]

    renamed_audit = audit.model_copy(
        update={
            "source": audit.source.model_copy(
                update={"creator_display_name": "unrelated display name"}
            )
        }
    )
    assert build_video_production_request(
        audit_bundle=renamed_audit, observations=observations
    ).model_dump(mode="json") == request.model_dump(mode="json")


def test_initial_handoff_blocks_publication_pending_b9_artifact_and_review() -> None:
    """Catches a handoff that permits publishing before a package and human review."""
    request = build_video_production_request(
        audit_bundle=load_episode_22_audit(), observations=episode_22_observations()
    )
    handoff = build_initial_publication_handoff(production_request=request)

    assert handoff.request_id == request.request_id
    assert handoff.state == "awaiting_video_package"
    assert handoff.auto_publish_allowed is False
    assert any("video-package/v1" in item for item in handoff.requirements)
    assert any("human review" in item.lower() for item in handoff.requirements)
    assert any("no video package" in item.lower() for item in handoff.blocked_reasons)
