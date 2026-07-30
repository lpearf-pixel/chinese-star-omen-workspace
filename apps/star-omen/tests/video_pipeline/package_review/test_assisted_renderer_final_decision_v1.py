from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from src.video_pipeline.assisted_review import (
    AIAssistedVisualCheckV1,
    AIAssistedVisualReviewV1,
    HumanExperienceConfirmationV1,
    RendererArtifactBindingV1,
    RendererHardGateReportV1,
    ReviewIssueV1,
    canonical_ai_visual_review_bytes,
    canonical_assisted_renderer_review_bytes,
    canonical_human_experience_confirmation_bytes,
    canonical_renderer_hard_gate_bytes,
    resolve_assisted_renderer_review,
)


def hard_gate(status: str = "passed") -> RendererHardGateReportV1:
    issues = []
    if status == "rejected":
        issues = [
            ReviewIssueV1(
                code="media.contract_mismatch",
                artifact="preview.mp4",
                field="sha256",
                message="preview hash differs from the contract",
            )
        ]
    return RendererHardGateReportV1(
        review_input_sha256="a" * 64,
        checked_artifacts=[
            RendererArtifactBindingV1(path="preview.mp4", sha256="c" * 64),
            RendererArtifactBindingV1(
                path="screenshots/frame-01.png",
                sha256="d" * 64,
            ),
        ],
        status=status,
        issues=issues,
    )


def ai_report(
    gate: RendererHardGateReportV1,
    decision: str = "passed",
) -> AIAssistedVisualReviewV1:
    return AIAssistedVisualReviewV1(
        review_input_sha256=gate.review_input_sha256,
        hard_gate_report_sha256=hashlib.sha256(
            canonical_renderer_hard_gate_bytes(gate)
        ).hexdigest(),
        preview_sha256="c" * 64,
        screenshot_sha256=["d" * 64],
        provider="openai-compatible",
        model="vision-model-v1",
        prompt_policy_version="b9-ai-visual/v1",
        decision=decision,
        confidence=0.96,
        checks=[
            AIAssistedVisualCheckV1(
                category="subtitle_readability",
                status=decision,
                evidence_frame_sha256=["d" * 64],
                summary="subtitle review result",
            )
        ],
    )


def human_report(
    gate: RendererHardGateReportV1,
    ai: AIAssistedVisualReviewV1,
    *,
    all_confirmed: bool,
    **overrides: object,
) -> HumanExperienceConfirmationV1:
    values: dict[str, object] = {
        "hard_gate_report_sha256": hashlib.sha256(
            canonical_renderer_hard_gate_bytes(gate)
        ).hexdigest(),
        "ai_visual_review_sha256": hashlib.sha256(
            canonical_ai_visual_review_bytes(ai)
        ).hexdigest(),
        "subtitles_readable": all_confirmed,
        "no_obvious_visual_problem": all_confirmed,
        "expression_matches_expectation": all_confirmed,
    }
    values.update(overrides)
    return HumanExperienceConfirmationV1(**values)


@pytest.mark.parametrize(
    ("hard_status", "ai_decision", "human_confirmed", "expected"),
    [
        ("rejected", "passed", True, "rejected"),
        ("passed", "rejected", True, "rejected"),
        ("passed", "needs_human_review", False, "rejected"),
        ("passed", "passed", True, "approved"),
        ("passed", "needs_human_review", True, "approved"),
    ],
)
def test_final_review_truth_table(
    hard_status: str,
    ai_decision: str,
    human_confirmed: bool,
    expected: str,
) -> None:
    gate = hard_gate(hard_status)
    ai = ai_report(gate, ai_decision)
    human = human_report(gate, ai, all_confirmed=human_confirmed)

    result = resolve_assisted_renderer_review(
        hard_gate=gate,
        ai_review=ai,
        human_confirmation=human,
    )

    assert result.status == expected
    assert canonical_assisted_renderer_review_bytes(result).endswith(b"\n")


def test_final_review_is_incomplete_when_required_report_is_missing() -> None:
    gate = hard_gate()
    ai = ai_report(gate)

    without_ai = resolve_assisted_renderer_review(
        hard_gate=gate,
        ai_review=None,
        human_confirmation=None,
    )
    without_human = resolve_assisted_renderer_review(
        hard_gate=gate,
        ai_review=ai,
        human_confirmation=None,
    )

    assert without_ai.status == "incomplete"
    assert without_ai.reason == "ai_report_missing"
    assert without_human.status == "incomplete"
    assert without_human.reason == "human_confirmation_missing"


def test_final_review_is_incomplete_when_report_hash_binding_drifts() -> None:
    gate = hard_gate()
    ai = ai_report(gate)
    human = human_report(
        gate,
        ai,
        all_confirmed=True,
        ai_visual_review_sha256="f" * 64,
    )

    result = resolve_assisted_renderer_review(
        hard_gate=gate,
        ai_review=ai,
        human_confirmation=human,
    )

    assert result.status == "incomplete"
    assert result.reason == "binding_mismatch"


def test_human_confirmation_has_exactly_three_layperson_checks() -> None:
    gate = hard_gate()
    ai = ai_report(gate)
    report = human_report(gate, ai, all_confirmed=True)

    assert report.all_confirmed is True
    assert canonical_human_experience_confirmation_bytes(report).endswith(b"\n")

    with pytest.raises(ValidationError, match="extra|approval|generic"):
        HumanExperienceConfirmationV1(
            **report.model_dump(mode="json"),
            generic_approval=True,
        )
