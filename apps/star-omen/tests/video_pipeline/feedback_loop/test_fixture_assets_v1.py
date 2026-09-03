from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.video_pipeline.feedback_loop.contracts_v1 import (
    FeedbackOutcomeV1,
    LocalEvidenceProbeV1,
)
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalEvidenceQueryPlanV1,
)


APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parents[1]
FIXTURE_ROOT = WORKSPACE_ROOT / "tests" / "fixtures" / "video-feedback-loop" / "v1"
EXPECTED_CLAIM_IDS = {
    "claim:douyin:zushan:episode-22:01",
    "claim:douyin:zushan:episode-22:02",
}
EXPECTED_SOURCE_ID = (
    "media:douyin:zushan:collection-7664842437629921326:episode-22"
)


def canonical_json_bytes(payload: object) -> bytes:
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


def test_fixture_manifest_is_canonical_and_hash_binds_every_asset() -> None:
    """Catches hand-edited, unhashed, or omitted feedback-loop fixture bytes."""
    manifest_path = FIXTURE_ROOT / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)

    assert manifest_bytes == canonical_json_bytes(manifest)
    assert manifest["schema_version"] == "video-feedback-loop-fixture-manifest/v1"
    assert manifest["fixture_policy"] == (
        "canonical-json-test-only-no-classical-or-publication-authority"
    )
    assert {entry["path"] for entry in manifest["fixtures"]} == {
        "episode-22-probes.json",
        "episode-22-query-plan.json",
        "synthetic-human-outcome.json",
    }
    assert all(set(entry) == {"path", "sha256"} for entry in manifest["fixtures"])
    for entry in manifest["fixtures"]:
        fixture_bytes = (FIXTURE_ROOT / entry["path"]).read_bytes()
        assert fixture_bytes == canonical_json_bytes(json.loads(fixture_bytes))
        assert hashlib.sha256(fixture_bytes).hexdigest() == entry["sha256"]


def test_episode_22_probe_fixture_binds_only_the_two_audited_claims() -> None:
    """Catches claim drift, partial coverage, or a fixture granting classical evidence."""
    payload = json.loads((FIXTURE_ROOT / "episode-22-probes.json").read_bytes())
    probes = [LocalEvidenceProbeV1.model_validate(item) for item in payload]

    assert len(probes) == 2
    assert {probe.claim_id for probe in probes} == EXPECTED_CLAIM_IDS
    assert {probe.source_id for probe in probes} == {EXPECTED_SOURCE_ID}
    assert {probe.result_state for probe in probes} == {"unresolved"}
    assert all(probe.evidence_references == [] for probe in probes)
    assert all(
        "no citable classical evidence" in " ".join(probe.notes).lower()
        for probe in probes
    )


def test_episode_22_query_plan_is_the_exact_hermetic_recording_fixture() -> None:
    """Catches plan identity/query drift or accidental live-release authority."""
    payload = json.loads(
        (FIXTURE_ROOT / "episode-22-query-plan.json").read_bytes()
    )
    plan = LocalEvidenceQueryPlanV1.model_validate(payload)

    assert plan.plan_id == "query-plan:vfl:zushan:episode-22:v1"
    assert plan.policy_version == "vfl-readonly-probe/1.0.0"
    assert plan.source_id == EXPECTED_SOURCE_ID
    assert plan.audit_id == "audit:douyin:zushan:episode-22"
    assert plan.execution_scope == "hermetic_test"
    assert plan.collection == "test_vfl_ephemeral_episode_22"
    assert plan.kb_book_id == "kaiyuan_zhanjing"
    assert plan.expected_corpus_version == "20260902T000000Z"
    assert [
        (
            request.request_id,
            request.claim_id,
            request.query,
            request.kb_book_id,
            request.query_mode,
            request.top_k,
        )
        for request in plan.requests
    ] == [
        (
            "query-request:vfl:zushan:episode-22:01",
            "claim:douyin:zushan:episode-22:01",
            "毕宿 烈风 古典原文 来源",
            "kaiyuan_zhanjing",
            "evidence",
            8,
        ),
        (
            "query-request:vfl:zushan:episode-22:02",
            "claim:douyin:zushan:episode-22:02",
            "烈风 海上风暴 古典对应关系",
            "kaiyuan_zhanjing",
            "evidence",
            8,
        ),
    ]
    assert {request.source_id for request in plan.requests} == {EXPECTED_SOURCE_ID}
    assert {request.audit_id for request in plan.requests} == {
        "audit:douyin:zushan:episode-22"
    }


def test_synthetic_outcome_is_a_test_only_human_decision_not_publication() -> None:
    """Catches a gold outcome being mistaken for a real platform publication fact."""
    payload = json.loads(
        (FIXTURE_ROOT / "synthetic-human-outcome.json").read_bytes()
    )
    outcome = FeedbackOutcomeV1.model_validate(payload)

    assert outcome.decision == "human_reviewed"
    assert outcome.decision != "publication_observed"
    assert outcome.reviewer_id == "reviewer:fixture:human"
    notes = " ".join(outcome.notes).lower()
    assert "test-only" in notes
    assert "human decision" in notes
    assert "no platform publication" in notes
    assert outcome.metrics == []
