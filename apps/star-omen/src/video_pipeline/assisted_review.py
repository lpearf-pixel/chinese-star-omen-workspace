from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import PurePosixPath
from typing import Literal, Sequence

from pydantic import Field, field_validator, model_validator

from src.video_pipeline.contracts import AstronomyEventV1
from src.video_pipeline.contracts._common import (
    StableId,
    StrictContractModel,
    ensure_unique,
)

ReviewIssueCode = Literal[
    "astronomy.provenance_placeholder",
    "astronomy.provenance_mismatch",
    "astronomy.recomputation_mismatch",
    "astronomy.observer_mismatch",
    "astronomy.time_mismatch",
    "astronomy.target_mismatch",
    "astronomy.measurement_mismatch",
    "lineage.hash_mismatch",
    "media.contract_mismatch",
    "screenshot.inventory_mismatch",
    "ocr.subtitle_missing",
    "ocr.subtitle_order_mismatch",
    "ocr.subtitle_out_of_frame",
]
AIVisualCheckCategory = Literal[
    "celestial_object_shot_match",
    "subtitle_readability",
    "playback_integrity",
    "unexpected_window_or_cursor",
    "internal_field_leakage",
    "audience_coherence",
]
AIVisualCheckStatus = Literal["passed", "rejected", "needs_human_review"]
AIVisualDecision = Literal["passed", "rejected", "needs_human_review"]

_AI_VISUAL_CHECK_ORDER = (
    "celestial_object_shot_match",
    "subtitle_readability",
    "playback_integrity",
    "unexpected_window_or_cursor",
    "internal_field_leakage",
    "audience_coherence",
)

_MACHINE_PATH_MARKERS = (
    "/Users/",
    "/home/",
    "/root/",
    "/tmp/",
    "\\Users\\",
)


def _canonical_json_bytes(payload: object) -> bytes:
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


def _safe_relative_path(value: str) -> str:
    if not value or "\\" in value or "\x00" in value:
        raise ValueError("renderer review artifact path is unsafe")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("renderer review artifact path must be relative")
    if path.as_posix() != value:
        raise ValueError("renderer review artifact path must be canonical")
    return value


class RendererArtifactBindingV1(StrictContractModel):
    schema_version: Literal["renderer-artifact-binding/v1"] = (
        "renderer-artifact-binding/v1"
    )
    path: str = Field(min_length=1, max_length=256)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _safe_relative_path(value)


class RendererReviewInputV1(StrictContractModel):
    schema_version: Literal["renderer-review-input/v1"] = "renderer-review-input/v1"
    review_input_id: StableId
    created_at: datetime
    artifacts: list[RendererArtifactBindingV1] = Field(min_length=1, max_length=64)

    @field_validator("created_at")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("renderer review input timestamp must be explicit UTC")
        if value.utcoffset() != timedelta(0):
            raise ValueError("renderer review input timestamp must be expressed in UTC")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_artifacts(self) -> "RendererReviewInputV1":
        paths = [artifact.path for artifact in self.artifacts]
        ensure_unique(
            paths,
            "renderer review artifact paths",
        )
        if paths != sorted(paths):
            raise ValueError(
                "renderer review artifacts must use canonical path order"
            )
        return self


class ReviewIssueV1(StrictContractModel):
    schema_version: Literal["renderer-review-issue/v1"] = "renderer-review-issue/v1"
    code: ReviewIssueCode
    severity: Literal["hard"] = "hard"
    artifact: str = Field(min_length=1, max_length=256)
    field: str = Field(pattern=r"^[a-z][a-z0-9_.-]{0,95}$")
    message: str = Field(min_length=1, max_length=320)

    @field_validator("artifact")
    @classmethod
    def validate_artifact(cls, value: str) -> str:
        return _safe_relative_path(value)

    @field_validator("message")
    @classmethod
    def reject_machine_paths(cls, value: str) -> str:
        if any(marker in value for marker in _MACHINE_PATH_MARKERS):
            raise ValueError("renderer review issue message must not contain a machine path")
        return value


class OCRObservationV1(StrictContractModel):
    schema_version: Literal["ocr-observation/v1"] = "ocr-observation/v1"
    frame_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    text: str = Field(min_length=1, max_length=2000)
    order: int = Field(strict=True, ge=1, le=256)
    fully_in_frame: bool


class AIAssistedVisualCheckV1(StrictContractModel):
    schema_version: Literal["ai-assisted-visual-check/v1"] = (
        "ai-assisted-visual-check/v1"
    )
    category: AIVisualCheckCategory
    status: AIVisualCheckStatus
    evidence_frame_sha256: list[str] = Field(
        min_length=1,
        max_length=30,
    )
    summary: str = Field(min_length=1, max_length=320)

    @field_validator("evidence_frame_sha256")
    @classmethod
    def validate_frame_hashes(cls, value: list[str]) -> list[str]:
        for frame_sha256 in value:
            if (
                len(frame_sha256) != 64
                or any(character not in "0123456789abcdef" for character in frame_sha256)
            ):
                raise ValueError(
                    "AI visual evidence frame hashes must be lowercase SHA-256"
                )
        ensure_unique(value, "AI visual evidence frame hashes")
        return value

    @field_validator("summary")
    @classmethod
    def reject_machine_paths(cls, value: str) -> str:
        if any(marker in value for marker in _MACHINE_PATH_MARKERS):
            raise ValueError("AI visual check summary must not contain a machine path")
        return value


class AIAssistedVisualReviewV1(StrictContractModel):
    schema_version: Literal["ai-assisted-visual-review/v1"] = (
        "ai-assisted-visual-review/v1"
    )
    review_input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    hard_gate_report_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preview_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    screenshot_sha256: list[str] = Field(min_length=1, max_length=30)
    provider: StableId
    model: StableId
    prompt_policy_version: StableId
    decision: AIVisualDecision
    confidence: float = Field(strict=True, ge=0, le=1, allow_inf_nan=False)
    checks: list[AIAssistedVisualCheckV1] = Field(min_length=1, max_length=6)

    @field_validator("screenshot_sha256")
    @classmethod
    def validate_screenshot_hashes(cls, value: list[str]) -> list[str]:
        for screenshot_sha256 in value:
            if (
                len(screenshot_sha256) != 64
                or any(
                    character not in "0123456789abcdef"
                    for character in screenshot_sha256
                )
            ):
                raise ValueError("AI visual screenshot hashes must be lowercase SHA-256")
        ensure_unique(value, "AI visual screenshot hashes")
        return value

    @model_validator(mode="after")
    def validate_checks_and_decision(self) -> "AIAssistedVisualReviewV1":
        categories = [check.category for check in self.checks]
        ensure_unique(categories, "AI visual check categories")
        expected_order = sorted(
            categories,
            key=_AI_VISUAL_CHECK_ORDER.index,
        )
        if categories != expected_order:
            raise ValueError("AI visual checks must use canonical category order")

        screenshot_hashes = set(self.screenshot_sha256)
        referenced_frames = {
            frame_sha256
            for check in self.checks
            for frame_sha256 in check.evidence_frame_sha256
        }
        if not referenced_frames.issubset(screenshot_hashes):
            raise ValueError(
                "AI visual evidence frames must reference declared screenshots"
            )
        screenshot_order = {
            frame_sha256: index
            for index, frame_sha256 in enumerate(self.screenshot_sha256)
        }
        for check in self.checks:
            expected_frame_order = sorted(
                check.evidence_frame_sha256,
                key=screenshot_order.__getitem__,
            )
            if check.evidence_frame_sha256 != expected_frame_order:
                raise ValueError(
                    "AI visual evidence frames must use canonical screenshot order"
                )

        statuses = {check.status for check in self.checks}
        expected_decision: AIVisualDecision
        if "rejected" in statuses:
            expected_decision = "rejected"
        elif "needs_human_review" in statuses:
            expected_decision = "needs_human_review"
        else:
            expected_decision = "passed"
        if self.decision != expected_decision:
            raise ValueError("AI visual decision does not match its checks")
        return self


class RendererHardGateReportV1(StrictContractModel):
    schema_version: Literal["renderer-hard-gate-report/v1"] = (
        "renderer-hard-gate-report/v1"
    )
    review_input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    checked_artifacts: list[RendererArtifactBindingV1] = Field(
        min_length=1,
        max_length=64,
    )
    status: Literal["passed", "rejected"]
    issues: list[ReviewIssueV1] = Field(max_length=128)

    @model_validator(mode="after")
    def validate_status(self) -> "RendererHardGateReportV1":
        expected = "rejected" if self.issues else "passed"
        if self.status != expected:
            raise ValueError("renderer hard gate status does not match its issues")
        ensure_unique(
            [
                (issue.code, issue.artifact, issue.field)
                for issue in self.issues
            ],
            "renderer hard gate issues",
        )
        artifact_paths = [artifact.path for artifact in self.checked_artifacts]
        ensure_unique(artifact_paths, "renderer hard gate artifact paths")
        if artifact_paths != sorted(artifact_paths):
            raise ValueError(
                "renderer hard gate artifacts must use canonical path order"
            )
        return self


def canonical_renderer_review_input_bytes(
    review_input: RendererReviewInputV1,
) -> bytes:
    validated = RendererReviewInputV1.model_validate(
        review_input.model_dump(mode="json")
    )
    return _canonical_json_bytes(
        validated.model_dump(mode="json", exclude_none=False)
    )


def build_renderer_hard_gate_report(
    *,
    review_input: RendererReviewInputV1,
    issues: Sequence[ReviewIssueV1],
) -> RendererHardGateReportV1:
    validated_input = RendererReviewInputV1.model_validate(
        review_input.model_dump(mode="json")
    )
    validated_issues = [
        ReviewIssueV1.model_validate(issue.model_dump(mode="json"))
        for issue in issues
    ]
    ordered_issues = sorted(
        validated_issues,
        key=lambda issue: (issue.code, issue.artifact, issue.field),
    )
    return RendererHardGateReportV1(
        review_input_sha256=hashlib.sha256(
            canonical_renderer_review_input_bytes(validated_input)
        ).hexdigest(),
        checked_artifacts=validated_input.artifacts,
        status="rejected" if ordered_issues else "passed",
        issues=ordered_issues,
    )


def canonical_renderer_hard_gate_bytes(
    report: RendererHardGateReportV1,
) -> bytes:
    validated = RendererHardGateReportV1.model_validate(
        report.model_dump(mode="json")
    )
    return _canonical_json_bytes(
        validated.model_dump(mode="json", exclude_none=False)
    )


def canonical_ai_visual_review_bytes(
    report: AIAssistedVisualReviewV1,
) -> bytes:
    validated = AIAssistedVisualReviewV1.model_validate(
        report.model_dump(mode="json")
    )
    return _canonical_json_bytes(
        validated.model_dump(mode="json", exclude_none=False)
    )


def verify_ai_visual_review(
    *,
    report: AIAssistedVisualReviewV1,
    hard_gate: RendererHardGateReportV1,
    preview_sha256: str,
    screenshot_sha256: Sequence[str],
) -> AIAssistedVisualReviewV1:
    validated_report = AIAssistedVisualReviewV1.model_validate(
        report.model_dump(mode="json")
    )
    validated_hard_gate = RendererHardGateReportV1.model_validate(
        hard_gate.model_dump(mode="json")
    )
    if validated_hard_gate.status != "passed":
        raise ValueError("AI visual review requires a passed hard gate")

    if (
        validated_report.review_input_sha256
        != validated_hard_gate.review_input_sha256
    ):
        raise ValueError("AI visual review input hash differs from the hard gate")

    expected_hard_gate_sha256 = hashlib.sha256(
        canonical_renderer_hard_gate_bytes(validated_hard_gate)
    ).hexdigest()
    if validated_report.hard_gate_report_sha256 != expected_hard_gate_sha256:
        raise ValueError("AI visual hard gate report hash does not match")

    if validated_report.preview_sha256 != preview_sha256:
        raise ValueError("AI visual preview hash does not match")

    observed_screenshot_sha256 = list(screenshot_sha256)
    ensure_unique(
        observed_screenshot_sha256,
        "observed AI visual screenshot hashes",
    )
    if validated_report.screenshot_sha256 != observed_screenshot_sha256:
        raise ValueError("AI visual screenshot hashes do not match")

    hard_gate_preview = [
        artifact.sha256
        for artifact in validated_hard_gate.checked_artifacts
        if artifact.path == "preview.mp4"
    ]
    if hard_gate_preview != [preview_sha256]:
        raise ValueError("hard gate preview binding does not match")

    hard_gate_screenshots = [
        artifact.sha256
        for artifact in validated_hard_gate.checked_artifacts
        if artifact.path.startswith("screenshots/")
    ]
    if hard_gate_screenshots != observed_screenshot_sha256:
        raise ValueError("hard gate screenshot bindings do not match")

    return validated_report


def _astronomy_issue(
    *,
    code: ReviewIssueCode,
    field: str,
    message: str,
) -> ReviewIssueV1:
    return ReviewIssueV1(
        code=code,
        artifact="astronomy-event.json",
        field=field,
        message=message,
    )


def _angular_measurements(event: AstronomyEventV1):
    accepted = {"angular-distance-deg", "angular-separation-deg"}
    return [
        measurement
        for measurement in event.measurements
        if measurement.kind.replace("_", "-") in accepted
    ]


def verify_recomputed_astronomy(
    *,
    packaged: AstronomyEventV1,
    recomputed: AstronomyEventV1,
    angular_tolerance_deg: Decimal | float | str = Decimal("0.01"),
) -> list[ReviewIssueV1]:
    packaged = AstronomyEventV1.model_validate(packaged.model_dump(mode="json"))
    recomputed = AstronomyEventV1.model_validate(
        recomputed.model_dump(mode="json")
    )
    tolerance = Decimal(str(angular_tolerance_deg))
    if not tolerance.is_finite() or tolerance < 0:
        raise ValueError("astronomy angular tolerance must be finite and non-negative")

    issues: list[ReviewIssueV1] = []
    packaged_hash = packaged.calculation_provenance.ephemeris_sha256
    placeholder_hash = len(set(packaged_hash)) == 1
    if placeholder_hash:
        issues.append(
            _astronomy_issue(
                code="astronomy.provenance_placeholder",
                field="calculation_provenance.ephemeris_sha256",
                message="packaged astronomy uses a placeholder ephemeris hash",
            )
        )

    packaged_provenance = packaged.calculation_provenance.model_dump(mode="json")
    recomputed_provenance = recomputed.calculation_provenance.model_dump(mode="json")
    provenance_fields = (
        "provider",
        "provider_version",
        "ephemeris_id",
        "timescale_source",
    )
    provenance_mismatch = any(
        packaged_provenance[field] != recomputed_provenance[field]
        for field in provenance_fields
    )
    if not placeholder_hash:
        provenance_mismatch = provenance_mismatch or (
            packaged_hash
            != recomputed.calculation_provenance.ephemeris_sha256
        )
    if provenance_mismatch:
        issues.append(
            _astronomy_issue(
                code="astronomy.provenance_mismatch",
                field="calculation_provenance",
                message="packaged astronomy provenance differs from recomputation",
            )
        )

    if (
        packaged.start_utc,
        packaged.peak_utc,
        packaged.end_utc,
    ) != (
        recomputed.start_utc,
        recomputed.peak_utc,
        recomputed.end_utc,
    ):
        issues.append(
            _astronomy_issue(
                code="astronomy.time_mismatch",
                field="start_utc",
                message="packaged astronomy time window differs from recomputation",
            )
        )

    if packaged.observer != recomputed.observer:
        issues.append(
            _astronomy_issue(
                code="astronomy.observer_mismatch",
                field="observer",
                message="packaged observer differs from recomputation",
            )
        )

    if (
        packaged.calculation_id,
        packaged.event_id,
        packaged.event_type,
        packaged.primary_body,
        packaged.target_body_or_region,
    ) != (
        recomputed.calculation_id,
        recomputed.event_id,
        recomputed.event_type,
        recomputed.primary_body,
        recomputed.target_body_or_region,
    ):
        issues.append(
            _astronomy_issue(
                code="astronomy.target_mismatch",
                field="target_body_or_region",
                message="packaged event identity differs from recomputation",
            )
        )

    packaged_measurements = _angular_measurements(packaged)
    recomputed_measurements = _angular_measurements(recomputed)
    if len(packaged_measurements) != 1 or len(recomputed_measurements) != 1:
        issues.append(
            _astronomy_issue(
                code="astronomy.measurement_mismatch",
                field="measurements",
                message="astronomy review requires one angular measurement",
            )
        )
    else:
        packaged_measurement = packaged_measurements[0]
        recomputed_measurement = recomputed_measurements[0]
        if (
            packaged_measurement.kind.replace("_", "-")
            != recomputed_measurement.kind.replace("_", "-")
            or packaged_measurement.unit != recomputed_measurement.unit
            or packaged_measurement.reference_frame
            != recomputed_measurement.reference_frame
        ):
            issues.append(
                _astronomy_issue(
                    code="astronomy.measurement_mismatch",
                    field="measurements",
                    message="angular measurement semantics differ from recomputation",
                )
            )
        difference = abs(
            Decimal(str(packaged_measurement.value))
            - Decimal(str(recomputed_measurement.value))
        )
        if difference > tolerance:
            issues.append(
                _astronomy_issue(
                    code="astronomy.recomputation_mismatch",
                    field="measurements",
                    message="angular separation differs from provider recomputation",
                )
            )

    if packaged.quality_status != "verified" or recomputed.quality_status != "verified":
        issues.append(
            _astronomy_issue(
                code="astronomy.measurement_mismatch",
                field="quality_status",
                message="astronomy hard gate requires verified event quality",
            )
        )

    return sorted(
        issues,
        key=lambda issue: (issue.code, issue.artifact, issue.field),
    )


def verify_renderer_artifacts(
    *,
    declared_artifacts: Sequence[RendererArtifactBindingV1],
    observed_artifacts: Sequence[RendererArtifactBindingV1],
    declared_screenshot_sha256: Sequence[str],
    observed_screenshot_sha256: Sequence[str],
    ocr: Sequence[OCRObservationV1],
    expected_subtitles: Sequence[str],
) -> list[ReviewIssueV1]:
    declared = [
        RendererArtifactBindingV1.model_validate(item.model_dump(mode="json"))
        for item in declared_artifacts
    ]
    observed = [
        RendererArtifactBindingV1.model_validate(item.model_dump(mode="json"))
        for item in observed_artifacts
    ]
    ensure_unique([item.path for item in declared], "declared renderer artifact paths")
    ensure_unique([item.path for item in observed], "observed renderer artifact paths")
    declared_by_path = {item.path: item.sha256 for item in declared}
    observed_by_path = {item.path: item.sha256 for item in observed}
    issues: list[ReviewIssueV1] = []

    for path in sorted(set(declared_by_path) | set(observed_by_path)):
        if declared_by_path.get(path) == observed_by_path.get(path):
            continue
        if path == "preview.mp4":
            issues.append(
                ReviewIssueV1(
                    code="media.contract_mismatch",
                    artifact="preview.mp4",
                    field="sha256",
                    message="observed preview does not match its declared hash",
                )
            )
        else:
            issues.append(
                ReviewIssueV1(
                    code="lineage.hash_mismatch",
                    artifact=path,
                    field="sha256",
                    message="observed artifact does not match its declared hash",
                )
            )

    declared_screenshots = list(declared_screenshot_sha256)
    observed_screenshots = list(observed_screenshot_sha256)
    ensure_unique(declared_screenshots, "declared screenshot hashes")
    ensure_unique(observed_screenshots, "observed screenshot hashes")
    normalized_ocr = [
        OCRObservationV1.model_validate(item.model_dump(mode="json"))
        for item in ocr
    ]
    ocr_frames = {item.frame_sha256 for item in normalized_ocr}
    if (
        declared_screenshots != observed_screenshots
        or not ocr_frames.issubset(set(observed_screenshots))
    ):
        issues.append(
            ReviewIssueV1(
                code="screenshot.inventory_mismatch",
                artifact="screenshots/inventory.json",
                field="sha256",
                message="observed screenshots do not match the declared inventory",
            )
        )

    ensure_unique([item.order for item in normalized_ocr], "OCR subtitle order")
    ordered_ocr = sorted(normalized_ocr, key=lambda item: item.order)
    observed_text = [item.text for item in ordered_ocr]
    expected_text = list(expected_subtitles)
    if sorted(observed_text) != sorted(expected_text):
        issues.append(
            ReviewIssueV1(
                code="ocr.subtitle_missing",
                artifact="subtitles.srt",
                field="text",
                message="OCR observations do not cover the expected subtitles",
            )
        )
    elif observed_text != expected_text:
        issues.append(
            ReviewIssueV1(
                code="ocr.subtitle_order_mismatch",
                artifact="subtitles.srt",
                field="order",
                message="OCR subtitle order differs from the expected timeline",
            )
        )
    if any(not item.fully_in_frame for item in ordered_ocr):
        issues.append(
            ReviewIssueV1(
                code="ocr.subtitle_out_of_frame",
                artifact="subtitles.srt",
                field="bounds",
                message="one or more OCR subtitles extend outside the frame",
            )
        )

    return sorted(
        issues,
        key=lambda issue: (issue.code, issue.artifact, issue.field),
    )


__all__ = [
    "AIAssistedVisualCheckV1",
    "AIAssistedVisualReviewV1",
    "RendererArtifactBindingV1",
    "RendererHardGateReportV1",
    "RendererReviewInputV1",
    "OCRObservationV1",
    "ReviewIssueV1",
    "build_renderer_hard_gate_report",
    "canonical_ai_visual_review_bytes",
    "canonical_renderer_hard_gate_bytes",
    "canonical_renderer_review_input_bytes",
    "verify_ai_visual_review",
    "verify_renderer_artifacts",
    "verify_recomputed_astronomy",
]
