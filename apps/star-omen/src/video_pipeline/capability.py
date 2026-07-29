from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
from typing import Literal, Sequence

from pydantic import Field, field_validator, model_validator

from src.video_pipeline.contracts._common import StableId, StrictContractModel, ensure_unique
from src.video_pipeline.preview import PreviewCapabilityV1, PreviewCommandV1
from src.video_pipeline.stellarium import StellariumScriptV1

_MAX_SCREENSHOTS = 30


class ScreenshotEvidenceV1(StrictContractModel):
    schema_version: Literal["screenshot-evidence/v1"] = "screenshot-evidence/v1"
    path: str = Field(min_length=1, max_length=256)
    byte_size: int = Field(strict=True, gt=0, le=50 * 1024 * 1024)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_path(self) -> "ScreenshotEvidenceV1":
        _safe_relative_path(self.path, required_prefix="screenshots/")
        return self


class LocalCapabilityEvidenceV1(StrictContractModel):
    schema_version: Literal["local-capability-evidence/v1"] = (
        "local-capability-evidence/v1"
    )
    evidence_id: StableId
    captured_at: datetime
    platform: Literal["macOS", "linux"]
    architecture: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
    stellarium_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    ffmpeg_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    stellarium_script_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preview_command_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    preview_observed: bool
    visual_review_status: Literal["approved", "rejected", "not_run"]
    screenshots: list[ScreenshotEvidenceV1]

    @field_validator("captured_at")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("capability capture timestamp must be explicit UTC")
        if value.utcoffset() != timedelta(0):
            raise ValueError("capability capture timestamp must be expressed in UTC")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_capture(self) -> "LocalCapabilityEvidenceV1":
        if len(self.screenshots) > _MAX_SCREENSHOTS:
            raise ValueError("capability evidence supports at most 30 screenshots")
        ensure_unique([item.path for item in self.screenshots], "screenshot paths")
        ensure_unique([item.sha256 for item in self.screenshots], "screenshot hashes")
        if self.visual_review_status == "approved":
            if not self.preview_observed:
                raise ValueError("approved visual review requires an observed preview")
            if not self.screenshots:
                raise ValueError("approved visual review requires screenshot evidence")
        if not self.preview_observed and self.visual_review_status != "not_run":
            raise ValueError("unobserved preview must use not_run visual status")
        return self


def _safe_relative_path(value: str, *, required_prefix: str | None = None) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("capability evidence path is unsafe")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("capability evidence path must be confined and relative")
    normalized = path.as_posix()
    if required_prefix is not None and not normalized.startswith(required_prefix):
        raise ValueError("capability evidence path uses an unexpected directory")
    return normalized


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


def canonical_preview_command_bytes(command: PreviewCommandV1) -> bytes:
    validated = PreviewCommandV1.model_validate(command.model_dump(mode="json"))
    return _canonical_json_bytes(validated.model_dump(mode="json", exclude_none=False))


def build_local_capability_evidence(
    *,
    evidence_id: str,
    captured_at: datetime,
    platform: Literal["macOS", "linux"],
    architecture: str,
    stellarium_script: StellariumScriptV1,
    preview_command: PreviewCommandV1,
    preview_capability: PreviewCapabilityV1,
    preview_observed: bool,
    visual_review_status: Literal["approved", "rejected", "not_run"],
    screenshots: Sequence[ScreenshotEvidenceV1],
) -> LocalCapabilityEvidenceV1:
    script = StellariumScriptV1.model_validate(
        stellarium_script.model_dump(mode="json")
    )
    command = PreviewCommandV1.model_validate(preview_command.model_dump(mode="json"))
    capability = PreviewCapabilityV1.model_validate(
        preview_capability.model_dump(mode="json")
    )
    return LocalCapabilityEvidenceV1(
        evidence_id=evidence_id,
        captured_at=captured_at,
        platform=platform,
        architecture=architecture,
        stellarium_version=script.stellarium_version,
        ffmpeg_version=capability.ffmpeg_version,
        stellarium_script_sha256=script.sha256,
        preview_command_sha256=hashlib.sha256(
            canonical_preview_command_bytes(command)
        ).hexdigest(),
        preview_observed=preview_observed,
        visual_review_status=visual_review_status,
        screenshots=list(screenshots),
    )


def canonical_capability_evidence_bytes(
    evidence: LocalCapabilityEvidenceV1,
) -> bytes:
    validated = LocalCapabilityEvidenceV1.model_validate(
        evidence.model_dump(mode="json")
    )
    return _canonical_json_bytes(validated.model_dump(mode="json", exclude_none=False))


__all__ = [
    "LocalCapabilityEvidenceV1",
    "ScreenshotEvidenceV1",
    "build_local_capability_evidence",
    "canonical_capability_evidence_bytes",
    "canonical_preview_command_bytes",
]
