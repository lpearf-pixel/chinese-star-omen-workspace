from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.video_pipeline.feedback_loop.contracts_v1 import (
    FeedbackOutcomeV1,
    LocalEvidenceProbeV1,
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
        "synthetic-human-outcome.json",
    }
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
