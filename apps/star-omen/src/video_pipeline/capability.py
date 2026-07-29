from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path, PurePosixPath
from typing import Literal, Mapping, Sequence

from pydantic import Field, field_validator, model_validator

from src.video_pipeline.contracts._common import StableId, StrictContractModel, ensure_unique
from src.video_pipeline.preview import PreviewCapabilityV1, PreviewCommandV1
from src.video_pipeline.stellarium import StellariumScriptV1

_MAX_SCREENSHOTS = 30
_MAX_PREVIEW_BYTES = 512 * 1024 * 1024
_PREVIEW_DURATION_MS = 80_000
_PREVIEW_DURATION_TOLERANCE_MS = 500


class ScreenshotEvidenceV1(StrictContractModel):
    schema_version: Literal["screenshot-evidence/v1"] = "screenshot-evidence/v1"
    path: str = Field(min_length=1, max_length=256)
    byte_size: int = Field(strict=True, gt=0, le=50 * 1024 * 1024)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_path(self) -> "ScreenshotEvidenceV1":
        _safe_relative_path(self.path, required_prefix="screenshots/")
        return self


class PreviewMediaEvidenceV1(StrictContractModel):
    schema_version: Literal["preview-media-evidence/v1"] = (
        "preview-media-evidence/v1"
    )
    path: Literal["preview.mp4"]
    byte_size: int = Field(strict=True, gt=0, le=_MAX_PREVIEW_BYTES)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    width: Literal[1080]
    height: Literal[1920]
    duration_ms: int = Field(
        strict=True,
        ge=_PREVIEW_DURATION_MS - _PREVIEW_DURATION_TOLERANCE_MS,
        le=_PREVIEW_DURATION_MS + _PREVIEW_DURATION_TOLERANCE_MS,
    )
    duration_tolerance_ms: Literal[500] = _PREVIEW_DURATION_TOLERANCE_MS
    video_codec: Literal["h264"]
    video_stream_count: Literal[1]
    audio_stream_count: Literal[0]


class _FFprobeStreamV1(StrictContractModel):
    index: int = Field(strict=True, ge=0)
    codec_name: str = Field(min_length=1, max_length=64)
    codec_type: Literal["video", "audio"]
    width: int | None = Field(default=None, strict=True, gt=0)
    height: int | None = Field(default=None, strict=True, gt=0)


class _FFprobeFormatV1(StrictContractModel):
    filename: Literal["preview.mp4"]
    duration: str = Field(min_length=1, max_length=64)
    size: str = Field(pattern=r"^[0-9]+$")
    format_name: str = Field(min_length=1, max_length=256)


class _FFprobePayloadV1(StrictContractModel):
    programs: list[object] = Field(default_factory=list)
    stream_groups: list[object] = Field(default_factory=list)
    streams: list[_FFprobeStreamV1]
    format: _FFprobeFormatV1

    @model_validator(mode="after")
    def validate_streams(self) -> "_FFprobePayloadV1":
        if self.programs or self.stream_groups:
            raise ValueError("ffprobe programs and stream groups must be empty")
        if not self.streams:
            raise ValueError("ffprobe payload requires streams")
        ensure_unique([stream.index for stream in self.streams], "ffprobe stream indexes")
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
    preview_media: PreviewMediaEvidenceV1 | None = None
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
        if self.preview_observed and self.preview_media is None:
            raise ValueError("observed preview requires preview media evidence")
        if not self.preview_observed and self.preview_media is not None:
            raise ValueError("unobserved preview cannot include media evidence")
        if self.preview_observed and self.visual_review_status == "not_run":
            raise ValueError("observed preview requires an explicit visual review decision")
        if self.visual_review_status == "approved":
            if not self.preview_observed or self.preview_media is None:
                raise ValueError("approved visual review requires observed preview media")
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
    if normalized != value:
        raise ValueError("capability evidence path must use canonical spelling")
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


def _hash_stable_file(path: Path, *, max_bytes: int) -> tuple[int, str]:
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        raise ValueError("preview maximum size must be a positive integer")
    if max_bytes > _MAX_PREVIEW_BYTES:
        raise ValueError("preview maximum size exceeds the evidence contract")
    if path.is_symlink():
        raise ValueError("preview media must not be a symlink")
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_file():
        raise ValueError("preview media path must be a regular file")
    if path.name != "preview.mp4":
        raise ValueError("preview media path must end with preview.mp4")
    before = path.stat()
    if before.st_size <= 0:
        raise ValueError("preview media is empty")
    if before.st_size > max_bytes:
        raise ValueError("preview media is too large")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if before_identity != after_identity:
        raise ValueError("preview media changed while hashing")
    return after.st_size, digest.hexdigest()


def _duration_ms(value: str) -> int:
    try:
        duration = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("preview duration is invalid") from exc
    if not duration.is_finite():
        raise ValueError("preview duration must be finite")
    milliseconds = int(
        (duration * Decimal(1000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    if abs(milliseconds - _PREVIEW_DURATION_MS) > _PREVIEW_DURATION_TOLERANCE_MS:
        raise ValueError("preview duration is outside the 80 second tolerance")
    return milliseconds


def inspect_preview_media_evidence(
    *,
    path: str | Path,
    ffprobe_payload: Mapping[str, object],
    max_bytes: int = _MAX_PREVIEW_BYTES,
) -> PreviewMediaEvidenceV1:
    media_path = Path(path)
    byte_size, sha256 = _hash_stable_file(media_path, max_bytes=max_bytes)
    probe = _FFprobePayloadV1.model_validate(dict(ffprobe_payload))
    format_size = int(probe.format.size)
    if format_size != byte_size:
        raise ValueError("ffprobe media size does not match preview bytes")
    format_names = {item.strip() for item in probe.format.format_name.split(",")}
    if "mp4" not in format_names:
        raise ValueError("ffprobe format does not identify MP4 media")
    video_streams = [stream for stream in probe.streams if stream.codec_type == "video"]
    audio_streams = [stream for stream in probe.streams if stream.codec_type == "audio"]
    if len(video_streams) != 1:
        raise ValueError("preview media requires exactly one video stream")
    if audio_streams:
        raise ValueError("preview media must contain zero audio streams")
    video = video_streams[0]
    if video.codec_name != "h264":
        raise ValueError("preview video codec must be h264")
    if video.width != 1080:
        raise ValueError("preview width must be 1080")
    if video.height != 1920:
        raise ValueError("preview height must be 1920")
    return PreviewMediaEvidenceV1(
        path="preview.mp4",
        byte_size=byte_size,
        sha256=sha256,
        width=video.width,
        height=video.height,
        duration_ms=_duration_ms(probe.format.duration),
        video_codec=video.codec_name,
        video_stream_count=len(video_streams),
        audio_stream_count=len(audio_streams),
    )


def build_local_capability_evidence(
    *,
    evidence_id: str,
    captured_at: datetime,
    platform: Literal["macOS", "linux"],
    architecture: str,
    stellarium_script: StellariumScriptV1,
    preview_command: PreviewCommandV1,
    preview_capability: PreviewCapabilityV1,
    preview_media: PreviewMediaEvidenceV1 | None,
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
    if preview_media is not None:
        preview_media = PreviewMediaEvidenceV1.model_validate(
            preview_media.model_dump(mode="json")
        )
        if preview_media.path != command.output_path:
            raise ValueError("preview media path does not match preview command output")
        if abs(preview_media.duration_ms - command.duration_ms) > preview_media.duration_tolerance_ms:
            raise ValueError("preview media duration does not match preview command")
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
        preview_media=preview_media,
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
    "PreviewMediaEvidenceV1",
    "ScreenshotEvidenceV1",
    "build_local_capability_evidence",
    "canonical_capability_evidence_bytes",
    "canonical_preview_command_bytes",
    "inspect_preview_media_evidence",
]
