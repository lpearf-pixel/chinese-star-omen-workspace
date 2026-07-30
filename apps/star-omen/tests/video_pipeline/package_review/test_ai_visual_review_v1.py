from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.video_pipeline.assisted_review import (
    AIAssistedVisualCheckV1,
    AIAssistedVisualReviewV1,
    canonical_ai_visual_review_bytes,
)


def visual_check(
    category: str,
    status: str,
    frame_sha256: list[str],
) -> AIAssistedVisualCheckV1:
    return AIAssistedVisualCheckV1(
        category=category,
        status=status,
        evidence_frame_sha256=frame_sha256,
        summary=f"{category} result",
    )


def ai_report(**overrides: object) -> AIAssistedVisualReviewV1:
    values: dict[str, object] = {
        "review_input_sha256": "a" * 64,
        "hard_gate_report_sha256": "b" * 64,
        "preview_sha256": "c" * 64,
        "screenshot_sha256": ["d" * 64, "e" * 64],
        "provider": "openai-compatible",
        "model": "vision-model-v1",
        "prompt_policy_version": "b9-ai-visual/v1",
        "decision": "passed",
        "confidence": 0.96,
        "checks": [
            visual_check("celestial_object_shot_match", "passed", ["d" * 64]),
            visual_check("subtitle_readability", "passed", ["e" * 64]),
        ],
    }
    values.update(overrides)
    return AIAssistedVisualReviewV1(**values)


def test_ai_report_is_hash_bound_and_canonical() -> None:
    report = ai_report()

    raw = canonical_ai_visual_review_bytes(report)

    assert raw.endswith(b"\n")
    assert raw == canonical_ai_visual_review_bytes(ai_report())
    assert b'"schema_version":"ai-assisted-visual-review/v1"' in raw
    assert b'"confidence":0.96' in raw
    assert b"/Users/" not in raw and b"/tmp/" not in raw


@pytest.mark.parametrize(
    ("decision", "statuses"),
    [
        ("rejected", ["passed", "rejected"]),
        ("needs_human_review", ["passed", "needs_human_review"]),
        ("passed", ["passed", "passed"]),
    ],
)
def test_ai_report_decision_is_derived_from_check_statuses(
    decision: str,
    statuses: list[str],
) -> None:
    report = ai_report(
        decision=decision,
        checks=[
            visual_check(
                "celestial_object_shot_match",
                statuses[0],
                ["d" * 64],
            ),
            visual_check("subtitle_readability", statuses[1], ["e" * 64]),
        ],
    )

    assert report.decision == decision

    with pytest.raises(ValidationError, match="decision|checks"):
        ai_report(
            decision="passed" if decision != "passed" else "rejected",
            checks=report.checks,
        )


def test_ai_report_rejects_unknown_duplicate_or_unbound_checks() -> None:
    with pytest.raises(ValidationError, match="category|literal"):
        visual_check("astronomy_accuracy", "passed", ["d" * 64])

    duplicate = visual_check("subtitle_readability", "passed", ["d" * 64])
    with pytest.raises(ValidationError, match="unique|duplicate"):
        ai_report(checks=[duplicate, duplicate])

    with pytest.raises(ValidationError, match="frame|screenshot"):
        ai_report(
            checks=[
                visual_check(
                    "subtitle_readability",
                    "passed",
                    ["f" * 64],
                )
            ]
        )


@pytest.mark.parametrize("confidence", [-0.01, 1.01, float("nan")])
def test_ai_report_rejects_invalid_confidence(confidence: float) -> None:
    with pytest.raises(ValidationError, match="confidence|finite|number"):
        ai_report(confidence=confidence)


def test_ai_report_requires_canonical_unique_hash_and_check_order() -> None:
    with pytest.raises(ValidationError, match="unique|duplicate"):
        ai_report(screenshot_sha256=["d" * 64, "d" * 64])

    with pytest.raises(ValidationError, match="canonical|order"):
        ai_report(
            checks=[
                visual_check("subtitle_readability", "passed", ["e" * 64]),
                visual_check(
                    "celestial_object_shot_match",
                    "passed",
                    ["d" * 64],
                ),
            ]
        )

    with pytest.raises(ValidationError, match="frame|canonical|order"):
        ai_report(
            checks=[
                visual_check(
                    "subtitle_readability",
                    "passed",
                    ["e" * 64, "d" * 64],
                )
            ]
        )
