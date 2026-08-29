from __future__ import annotations

def valid_local_evidence_reference_payload() -> dict:
    return {
        "evidence_ref_id": "local-evidence:fixture:001",
        "evidence_class": "citable_passage",
        "evidence_locator": "fixture://local/citation-001",
        "evidence_sha256": "a" * 64,
        "relationship": "supports",
        "note": "Synthetic citable local evidence for the contract boundary.",
    }


def valid_local_probe_payload() -> dict:
    return {
        "schema_version": "local-evidence-probe/v1",
        "probe_id": "probe:fixture:001",
        "source_id": "media:fixture:001",
        "claim_id": "claim:fixture:001",
        "query": "fixture classical correspondence",
        "corpus_version": "corpus-fixture/1",
        "retrieval_version": "retrieval-fixture/1",
        "result_state": "corroborated",
        "evidence_references": [valid_local_evidence_reference_payload()],
        "notes": ["Synthetic probe result."],
    }


def valid_observation_payload() -> dict:
    return {
        "observation_id": "observation:fixture:001",
        "source_id": "media:fixture:001",
        "audit_id": "audit:fixture:001",
        "claim_id": "claim:fixture:001",
        "probe_id": "probe:fixture:001",
        "external_disposition": "source_missing",
        "local_result_state": "corroborated",
        "operational_disposition": "source_missing",
        "external_evidence_link_ids": [],
        "local_evidence_ref_ids": ["local-evidence:fixture:001"],
        "rationale": "The external source remains missing despite local evidence.",
    }


def valid_candidate_payload() -> dict:
    return {
        "candidate_id": "candidate:fixture:001",
        "owner_subsystem": "corpus_research",
        "supporting_observation_ids": ["observation:fixture:001"],
        "contradicting_observation_ids": [],
        "confidence": 0.75,
        "hypothesis": "Locate and review the relevant classical source.",
        "verification_steps": ["Review a citable locus through the owning task."],
        "rollback_requirements": ["Discard the proposal if the locus cannot be verified."],
        "apply_allowed": False,
    }


def valid_video_claim_candidate_payload() -> dict:
    return {
        "video_claim_id": "video-claim:fixture:001",
        "claim_class": "historical_context",
        "text": "The captured material requires a source audit before promotion.",
        "observation_ids": ["observation:fixture:001"],
    }


def valid_video_production_request_payload() -> dict:
    return {
        "request_id": "video-request:fixture:001",
        "source_id": "media:fixture:001",
        "audit_id": "audit:fixture:001",
        "topic": "Fixture source-audit explainer",
        "format": "source_audit_explainer",
        "claims": [valid_video_claim_candidate_payload()],
        "forbidden_claims": ["Do not invent an absent classical quotation."],
        "evidence_ref_ids": ["local-evidence:fixture:001"],
        "required_disclaimers": ["External material remains research-only."],
        "output_contract": "video-package/v1",
        "requires_human_review": True,
    }


def valid_handoff_payload() -> dict:
    return {
        "handoff_id": "handoff:fixture:001",
        "request_id": "video-request:fixture:001",
        "state": "awaiting_video_package",
        "requirements": ["A valid VideoPackage/v1 artifact is required."],
        "blocked_reasons": ["No video package has been supplied."],
        "auto_publish_allowed": False,
    }


def valid_metric_payload() -> dict:
    return {
        "metric_id": "metric:fixture:001",
        "metric_name": "claim_count",
        "value": 1.0,
        "unit": "count",
    }


def valid_outcome_payload() -> dict:
    return {
        "outcome_id": "outcome:fixture:001",
        "handoff_id": "handoff:fixture:001",
        "decision": "human_reviewed",
        "reviewer_id": "reviewer:fixture:001",
        "notes": ["Synthetic human outcome; no publication is claimed."],
        "metrics": [valid_metric_payload()],
    }


def valid_proposal_payload() -> dict:
    return {
        "proposal_id": "proposal:fixture:001",
        "outcome_id": "outcome:fixture:001",
        "owner_subsystem": "retrieval",
        "evidence_observation_ids": ["observation:fixture:001"],
        "expected_benefit": "Make evidence gaps easier for reviewers to inspect.",
        "verification_steps": ["Evaluate the proposal in a new owning-module task."],
        "rollback_requirements": ["Revert the owning change if evaluation regresses."],
        "apply_allowed": False,
    }


def valid_run_payload(*, with_outcome: bool = False) -> dict:
    handoff = valid_handoff_payload()
    if with_outcome:
        handoff["state"] = "learning_proposal_ready"
    return {
        "schema_version": "feedback-loop-run/v1",
        "run_id": "feedback-run:fixture:001",
        "policy_version": "vfl-policy/1.0.0",
        "source_id": "media:fixture:001",
        "audit_id": "audit:fixture:001",
        "local_probes": [valid_local_probe_payload()],
        "observations": [valid_observation_payload()],
        "improvement_candidates": [valid_candidate_payload()],
        "video_production_request": valid_video_production_request_payload(),
        "manual_publication_handoff": handoff,
        "outcome": valid_outcome_payload() if with_outcome else None,
        "learning_update_proposal": valid_proposal_payload() if with_outcome else None,
        "metrics": [valid_metric_payload()],
    }
