from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.video_pipeline.assisted_review import (
    RendererArtifactBindingV1,
    RendererReviewInputV1,
    ReviewIssueV1,
    build_renderer_hard_gate_report,
    canonical_renderer_hard_gate_bytes,
)


def review_input() -> RendererReviewInputV1:
    return RendererReviewInputV1(
        review_input_id="renderer-review-input:july-21-v1",
        created_at=datetime(2026, 7, 30, 4, 8, 56, tzinfo=timezone.utc),
        artifacts=[
            RendererArtifactBindingV1(
                path="astronomy-event.json",
                sha256="a" * 64,
            ),
            RendererArtifactBindingV1(
                path="preview.mp4",
                sha256="b" * 64,
            ),
        ],
    )


def test_hard_gate_derives_rejection_and_canonical_issue_order() -> None:
    report = build_renderer_hard_gate_report(
        review_input=review_input(),
        issues=[
            ReviewIssueV1(
                code="media.contract_mismatch",
                artifact="preview.mp4",
                field="width",
                message="preview width differs from the contract",
            ),
            ReviewIssueV1(
                code="astronomy.recomputation_mismatch",
                artifact="astronomy-event.json",
                field="measurements",
                message="angular separation differs from provider recomputation",
            ),
        ],
    )

    assert report.status == "rejected"
    assert [item.code for item in report.issues] == [
        "astronomy.recomputation_mismatch",
        "media.contract_mismatch",
    ]
    assert report.review_input_sha256 != "a" * 64
    assert report.checked_artifacts == review_input().artifacts
    raw = canonical_renderer_hard_gate_bytes(report)
    assert raw.endswith(b"\n")
    assert b"/Users/" not in raw and b"/tmp/" not in raw


def test_hard_gate_passes_only_without_issues_and_is_deterministic() -> None:
    first = build_renderer_hard_gate_report(
        review_input=review_input(),
        issues=[],
    )
    second = build_renderer_hard_gate_report(
        review_input=review_input(),
        issues=[],
    )

    assert first.status == "passed"
    assert first == second
    assert canonical_renderer_hard_gate_bytes(first) == (
        canonical_renderer_hard_gate_bytes(second)
    )


def test_review_input_rejects_duplicate_or_unsafe_artifacts() -> None:
    artifact = RendererArtifactBindingV1(
        path="preview.mp4",
        sha256="b" * 64,
    )
    with pytest.raises(ValidationError, match="unique|duplicate"):
        RendererReviewInputV1(
            review_input_id="renderer-review-input:duplicate-v1",
            created_at=datetime(2026, 7, 30, 4, 8, 56, tzinfo=timezone.utc),
            artifacts=[artifact, artifact],
        )

    with pytest.raises(ValidationError, match="path|relative|unsafe"):
        RendererArtifactBindingV1(
            path="/Users/example/preview.mp4",
            sha256="b" * 64,
        )

    with pytest.raises(ValidationError, match="canonical|order|sorted"):
        RendererReviewInputV1(
            review_input_id="renderer-review-input:unordered-v1",
            created_at=datetime(2026, 7, 30, 4, 8, 56, tzinfo=timezone.utc),
            artifacts=list(reversed(review_input().artifacts)),
        )


def test_review_issue_rejects_unknown_code_or_path_like_message() -> None:
    with pytest.raises(ValidationError, match="code|pattern"):
        ReviewIssueV1(
            code="unknown",
            artifact="preview.mp4",
            field="width",
            message="unsupported issue",
        )

    with pytest.raises(ValidationError, match="path|message"):
        ReviewIssueV1(
            code="media.contract_mismatch",
            artifact="preview.mp4",
            field="width",
            message="failure in /Users/example/private",
        )
