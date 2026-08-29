from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from src.video_pipeline.feedback_loop.contracts_v1 import (
    FeedbackOutcomeV1,
    ManualPublicationHandoffV1,
)
from src.video_pipeline.feedback_loop.orchestrator import (
    FeedbackLoopBuild,
    build_feedback_loop_run,
    publish_feedback_loop_run,
)
from src.video_pipeline.package import build_package_manifest, verify_package_members
from tests.video_pipeline.feedback_loop.test_comparison_v1 import (
    episode_22_probes,
    load_episode_22_audit,
)


POLICY_VERSION = "vfl-policy/1.0.0"
EXPECTED_RUN_ID = (
    "feedback-run:vfl:"
    "2ed55b29d6bc21962a1c8a64f22b7f1639ba3e33455da2f7ee5080ea53a9d20d"
)
EXPECTED_OUTCOME_RUN_ID = (
    "feedback-run:vfl:"
    "d9ef04054a761736fe1a286728fba9bd5e68b9a678f27b8f3d5a12559ae30a03"
)
BASE_MEMBER_PATHS = {
    "external-audit-bundle.json",
    "local-evidence-probes.json",
    "feedback-observations.json",
    "improvement-candidates.json",
    "video-production-request.json",
    "manual-publication-handoff.json",
    "feedback-loop-run.json",
}


def synthetic_outcome() -> FeedbackOutcomeV1:
    return FeedbackOutcomeV1.model_validate(
        {
            "outcome_id": "outcome:vfl:episode-22:human-review",
            "handoff_id": (
                "handoff:vfl:video-request:vfl:audit:douyin:zushan:episode-22:"
                "source-audit-explainer"
            ),
            "decision": "human_reviewed",
            "reviewer_id": "reviewer:fixture:human",
            "notes": ["Synthetic human outcome; no publication is claimed."],
            "metrics": [],
        }
    )


def episode_22_build(*, outcome: FeedbackOutcomeV1 | None = None):
    return build_feedback_loop_run(
        audit_bundle=load_episode_22_audit(),
        local_probes=episode_22_probes(),
        outcome=outcome,
        policy_version=POLICY_VERSION,
    )


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def assert_no_staging(parent: Path, output_name: str) -> None:
    assert not list(parent.glob(f".{output_name}.*"))


def test_run_id_is_bound_to_canonical_inputs_and_exact_policy() -> None:
    """Catches omitting the audit, probes, outcome, or fixed policy from identity."""
    build = episode_22_build()

    assert build.run.run_id == EXPECTED_RUN_ID
    assert build.run.policy_version == POLICY_VERSION

    changed_probe = episode_22_probes()[0].model_copy(
        update={"query": "a distinct caller-supplied query"}
    )
    changed = build_feedback_loop_run(
        audit_bundle=load_episode_22_audit(),
        local_probes=(changed_probe, episode_22_probes()[1]),
        policy_version=POLICY_VERSION,
    )
    assert changed.run.run_id != build.run.run_id

    with pytest.raises(ValueError, match="policy_version"):
        build_feedback_loop_run(
            audit_bundle=load_episode_22_audit(),
            local_probes=episode_22_probes(),
            policy_version="vfl-policy/1.0.1",
        )


def test_reordered_probes_produce_byte_identical_builds() -> None:
    """Catches caller-order-dependent identities, run records, or manifests."""
    first = episode_22_build()
    reordered = build_feedback_loop_run(
        audit_bundle=load_episode_22_audit(),
        local_probes=tuple(reversed(episode_22_probes())),
        policy_version=POLICY_VERSION,
    )

    assert reordered.run == first.run
    assert reordered.manifest == first.manifest
    assert dict(reordered.members) == dict(first.members)


def test_build_contains_canonical_hash_verified_lifecycle_members() -> None:
    """Catches missing, noncanonical, unhashed, or stale lifecycle snapshots."""
    build = episode_22_build()

    assert set(build.members) == BASE_MEMBER_PATHS
    assert [entry.path for entry in build.manifest.members] == sorted(BASE_MEMBER_PATHS)
    assert build.manifest.package_id == build.run.run_id
    assert verify_package_members(build.manifest, build.members) is True
    for member_bytes in build.members.values():
        payload = json.loads(member_bytes)
        assert member_bytes == canonical_json_bytes(payload)

    assert json.loads(build.members["external-audit-bundle.json"])[
        "audit"
    ]["audit_id"] == build.run.audit_id
    assert json.loads(build.members["local-evidence-probes.json"]) == [
        probe.model_dump(mode="json", exclude_none=False)
        for probe in build.run.local_probes
    ]
    assert json.loads(build.members["feedback-observations.json"]) == [
        item.model_dump(mode="json", exclude_none=False)
        for item in build.run.observations
    ]
    assert json.loads(build.members["improvement-candidates.json"]) == [
        item.model_dump(mode="json", exclude_none=False)
        for item in build.run.improvement_candidates
    ]
    assert json.loads(build.members["video-production-request.json"]) == (
        build.run.video_production_request.model_dump(mode="json", exclude_none=False)
    )
    assert json.loads(build.members["manual-publication-handoff.json"]) == (
        build.run.manual_publication_handoff.model_dump(mode="json", exclude_none=False)
    )
    assert json.loads(build.members["feedback-loop-run.json"]) == (
        build.run.model_dump(mode="json", exclude_none=False)
    )


def test_optional_outcome_adds_one_linked_non_applying_proposal() -> None:
    """Catches an outcome being ignored, applied, unlinked, or emitted repeatedly."""
    build = episode_22_build(outcome=synthetic_outcome())

    assert build.run.run_id == EXPECTED_OUTCOME_RUN_ID
    assert build.run.run_id != EXPECTED_RUN_ID
    assert set(build.members) == BASE_MEMBER_PATHS | {
        "feedback-outcome.json",
        "learning-update-proposal.json",
    }
    assert build.run.outcome == synthetic_outcome()
    proposal = build.run.learning_update_proposal
    assert proposal is not None
    assert proposal.outcome_id == synthetic_outcome().outcome_id
    assert proposal.apply_allowed is False
    assert proposal.evidence_observation_ids == [
        observation.observation_id for observation in build.run.observations
    ]
    assert json.loads(build.members["learning-update-proposal.json"])[
        "proposal_id"
    ] == proposal.proposal_id


def test_no_outcome_omits_outcome_and_proposal_members() -> None:
    """Catches inventing lifecycle facts before a caller supplies an outcome."""
    build = episode_22_build()

    assert build.run.outcome is None
    assert build.run.learning_update_proposal is None
    assert "feedback-outcome.json" not in build.members
    assert "learning-update-proposal.json" not in build.members


def test_run_records_only_provable_deterministic_counts() -> None:
    """Catches missing counts or metrics that claim unobserved media/publication facts."""
    build = episode_22_build()

    assert {
        metric.metric_name: (metric.value, metric.unit)
        for metric in build.run.metrics
    } == {
        "candidate_count": (4.0, "count"),
        "claim_count": (2.0, "count"),
        "contradiction_count": (0.0, "count"),
        "observation_count": (2.0, "count"),
        "probe_count": (2.0, "count"),
        "unresolved_count": (2.0, "count"),
    }


def test_build_defensively_revalidates_inputs() -> None:
    """Catches trusting caller-mutated frozen audit, probe, or outcome objects."""
    audit = load_episode_22_audit()
    object.__setattr__(audit.audit, "source_id", "media:douyin:zushan:other")
    with pytest.raises(ValueError, match="source_id"):
        build_feedback_loop_run(
            audit_bundle=audit,
            local_probes=episode_22_probes(),
            policy_version=POLICY_VERSION,
        )

    probes = list(episode_22_probes())
    object.__setattr__(probes[0], "source_id", "media:douyin:zushan:other")
    with pytest.raises(ValueError, match="source_id"):
        build_feedback_loop_run(
            audit_bundle=load_episode_22_audit(),
            local_probes=probes,
            policy_version=POLICY_VERSION,
        )

    outcome = synthetic_outcome()
    object.__setattr__(outcome, "handoff_id", "handoff:vfl:other")
    with pytest.raises(ValueError, match="handoff_id"):
        episode_22_build(outcome=outcome)


def test_build_members_are_read_only_and_preserve_original_bytes() -> None:
    """Catches callers replacing hash-bound member bytes after a valid build."""
    build = episode_22_build()
    original = build.members["feedback-loop-run.json"]

    with pytest.raises(TypeError):
        build.members["feedback-loop-run.json"] = b"{}"  # type: ignore[index]

    assert build.members["feedback-loop-run.json"] == original


def test_publish_writes_complete_package_and_refuses_occupied_targets(
    tmp_path: Path,
) -> None:
    """Catches replacement of a directory or symlink and leftover staging output."""
    build = episode_22_build()
    output = tmp_path / "feedback-run"

    assert publish_feedback_loop_run(output_dir=output, build=build) == output
    assert (output / "manifest.json").is_file()
    assert (output / "feedback-loop-run.json").read_bytes() == build.members[
        "feedback-loop-run.json"
    ]
    assert_no_staging(tmp_path, output.name)

    before = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    with pytest.raises(FileExistsError):
        publish_feedback_loop_run(output_dir=output, build=build)
    assert before == {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    assert_no_staging(tmp_path, output.name)

    link = tmp_path / "feedback-link"
    link.symlink_to(tmp_path / "missing-target", target_is_directory=True)
    with pytest.raises(FileExistsError):
        publish_feedback_loop_run(output_dir=link, build=build)
    assert link.is_symlink()
    assert_no_staging(tmp_path, link.name)


def test_publish_rejects_invalid_build_without_partial_or_staging_output(
    tmp_path: Path,
) -> None:
    """Catches validation after staging or publication of tampered run members."""
    build = episode_22_build()
    tampered_members = dict(build.members)
    tampered_members["feedback-loop-run.json"] += b"tampered"
    invalid = replace(build, members=tampered_members)
    output = tmp_path / "invalid-feedback-run"

    with pytest.raises(ValueError, match="hash|size|member"):
        publish_feedback_loop_run(output_dir=output, build=invalid)

    assert not output.exists()
    assert_no_staging(tmp_path, output.name)


def test_publish_rejects_hash_valid_canonical_semantic_tamper(
    tmp_path: Path,
) -> None:
    """Catches publishing canonical members that disagree with deterministic rebuild."""
    build = episode_22_build()
    tampered_members = dict(build.members)
    handoff_payload = json.loads(tampered_members["manual-publication-handoff.json"])
    handoff_payload["blocked_reasons"] = [
        "Canonical contract-valid drift that was not derived by the planner."
    ]
    tampered_handoff = ManualPublicationHandoffV1.model_validate(handoff_payload)
    tampered_members["manual-publication-handoff.json"] = canonical_json_bytes(
        tampered_handoff.model_dump(mode="json", exclude_none=False)
    )

    self_consistent_manifest = build_package_manifest(
        package_id=build.run.run_id,
        members=tampered_members,
    )
    invalid = FeedbackLoopBuild(
        run=build.run,
        manifest=self_consistent_manifest,
        members=tampered_members,
    )
    output = tmp_path / "semantic-tamper"

    assert verify_package_members(invalid.manifest, invalid.members) is True
    assert json.loads(invalid.members["manual-publication-handoff.json"])
    with pytest.raises(
        ValueError,
        match="canonical feedback-loop member identity does not match build",
    ):
        publish_feedback_loop_run(output_dir=output, build=invalid)

    assert not output.exists()
    assert_no_staging(tmp_path, output.name)
