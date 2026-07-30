from __future__ import annotations

import hashlib

import pytest

from src.video_pipeline.assisted_review import (
    AIAssistedVisualCheckV1,
    AIAssistedVisualReviewV1,
    RendererArtifactBindingV1,
    RendererHardGateReportV1,
    ReviewIssueV1,
    canonical_renderer_hard_gate_bytes,
    verify_ai_visual_review,
)


def hard_gate(*, status: str = "passed") -> RendererHardGateReportV1:
    issues = []
    if status == "rejected":
        issues = [
            ReviewIssueV1(
                code="media.contract_mismatch",
                artifact="preview.mp4",
                field="duration_ms",
                message="preview duration differs from the contract",
            )
        ]
    return RendererHardGateReportV1(
        review_input_sha256="a" * 64,
        checked_artifacts=[
            RendererArtifactBindingV1(
                path="preview.mp4",
                sha256="c" * 64,
            ),
            RendererArtifactBindingV1(
                path="screenshots/frame-01.png",
                sha256="d" * 64,
            ),
        ],
        status=status,
        issues=issues,
    )


def ai_report(
    *,
    gate: RendererHardGateReportV1 | None = None,
    **overrides: object,
) -> AIAssistedVisualReviewV1:
    bound_gate = gate or hard_gate()
    values: dict[str, object] = {
        "review_input_sha256": "a" * 64,
        "hard_gate_report_sha256": hashlib.sha256(
            canonical_renderer_hard_gate_bytes(bound_gate)
        ).hexdigest(),
        "preview_sha256": "c" * 64,
        "screenshot_sha256": ["d" * 64],
        "provider": "openai-compatible",
        "model": "vision-model-v1",
        "prompt_policy_version": "b9-ai-visual/v1",
        "decision": "passed",
        "confidence": 0.96,
        "checks": [
            AIAssistedVisualCheckV1(
                category="subtitle_readability",
                status="passed",
                evidence_frame_sha256=["d" * 64],
                summary="subtitles are readable",
            )
        ],
    }
    values.update(overrides)
    return AIAssistedVisualReviewV1(**values)


def test_ai_report_verifier_accepts_exact_passed_bindings() -> None:
    gate = hard_gate()
    report = ai_report(gate=gate)

    verified = verify_ai_visual_review(
        report=report,
        hard_gate=gate,
        preview_sha256="c" * 64,
        screenshot_sha256=["d" * 64],
    )

    assert verified == report


def test_ai_report_cannot_override_hard_rejection() -> None:
    gate = hard_gate(status="rejected")
    report = ai_report(gate=gate)

    with pytest.raises(ValueError, match="hard gate"):
        verify_ai_visual_review(
            report=report,
            hard_gate=gate,
            preview_sha256="c" * 64,
            screenshot_sha256=["d" * 64],
        )


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"review_input_sha256": "f" * 64}, "review input"),
        ({"hard_gate_report_sha256": "f" * 64}, "hard gate report"),
        ({"preview_sha256": "f" * 64}, "preview"),
        (
            {
                "screenshot_sha256": ["e" * 64],
                "checks": [
                    AIAssistedVisualCheckV1(
                        category="subtitle_readability",
                        status="passed",
                        evidence_frame_sha256=["e" * 64],
                        summary="subtitles are readable",
                    )
                ],
            },
            "screenshot",
        ),
    ],
)
def test_ai_report_verifier_rejects_hash_drift(
    override: dict[str, object],
    message: str,
) -> None:
    gate = hard_gate()
    report = ai_report(gate=gate, **override)

    with pytest.raises(ValueError, match=message):
        verify_ai_visual_review(
            report=report,
            hard_gate=gate,
            preview_sha256="c" * 64,
            screenshot_sha256=["d" * 64],
        )


def test_ai_report_verifier_rejects_missing_or_reordered_frames() -> None:
    gate = hard_gate()
    report = ai_report(
        gate=gate,
        screenshot_sha256=["d" * 64, "e" * 64],
        checks=[
            AIAssistedVisualCheckV1(
                category="subtitle_readability",
                status="passed",
                evidence_frame_sha256=["e" * 64],
                summary="subtitles are readable",
            )
        ],
    )

    with pytest.raises(ValueError, match="screenshot"):
        verify_ai_visual_review(
            report=report,
            hard_gate=gate,
            preview_sha256="c" * 64,
            screenshot_sha256=["e" * 64, "d" * 64],
        )
