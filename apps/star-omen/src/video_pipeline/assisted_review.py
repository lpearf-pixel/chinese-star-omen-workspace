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
        ensure_unique(
            [artifact.path for artifact in self.artifacts],
            "renderer review artifact paths",
        )
        ensure_unique(
            [artifact.sha256 for artifact in self.artifacts],
            "renderer review artifact hashes",
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
        packaged.event_type,
        packaged.primary_body,
        packaged.target_body_or_region,
    ) != (
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


__all__ = [
    "RendererArtifactBindingV1",
    "RendererHardGateReportV1",
    "RendererReviewInputV1",
    "ReviewIssueV1",
    "build_renderer_hard_gate_report",
    "canonical_renderer_hard_gate_bytes",
    "canonical_renderer_review_input_bytes",
    "verify_recomputed_astronomy",
]
