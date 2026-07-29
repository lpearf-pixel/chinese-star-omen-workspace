from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.video_pipeline.capability import (
    LocalCapabilityEvidenceV1,
    PreviewMediaEvidenceV1,
    ScreenshotEvidenceV1,
    build_local_capability_evidence,
    canonical_capability_evidence_bytes,
)
from src.video_pipeline.preview import PreviewCapabilityV1, build_minimal_preview_command
from tests.video_pipeline.package_review.helpers import july_editorial_and_script


def preview_capability() -> PreviewCapabilityV1:
    return PreviewCapabilityV1(
        ffmpeg_version="7.1.1",
        enabled_features=["lavfi-color", "subtitles", "libx264"],
        max_timeout_seconds=120,
    )


def preview_media() -> PreviewMediaEvidenceV1:
    return PreviewMediaEvidenceV1(
        path="preview.mp4",
        byte_size=2048,
        sha256="f" * 64,
        width=1080,
        height=1920,
        duration_ms=80_000,
        duration_tolerance_ms=500,
        video_codec="h264",
        video_stream_count=1,
        audio_stream_count=0,
    )


def screenshot(index: int = 1) -> ScreenshotEvidenceV1:
    return ScreenshotEvidenceV1(
        path=f"screenshots/frame-{index:02d}.png",
        byte_size=1024 + index,
        sha256=f"{index:064x}",
    )


def test_local_capability_evidence_is_path_free_hash_bound_and_canonical() -> None:
    _event, _result, editorial, script = july_editorial_and_script()
    capability = preview_capability()
    command = build_minimal_preview_command(
        subtitle_path="subtitles.srt",
        output_path="preview.mp4",
        duration_ms=editorial.total_duration_ms,
        capability=capability,
    )
    media = preview_media()

    first = build_local_capability_evidence(
        evidence_id="local-capability:macos-arm64-v1",
        captured_at=datetime(2026, 7, 30, 0, 0, tzinfo=timezone.utc),
        platform="macOS",
        architecture="arm64",
        stellarium_script=script,
        preview_command=command,
        preview_capability=capability,
        preview_media=media,
        preview_observed=True,
        visual_review_status="approved",
        screenshots=[screenshot()],
    )
    second = build_local_capability_evidence(
        evidence_id="local-capability:macos-arm64-v1",
        captured_at=datetime(2026, 7, 30, 0, 0, tzinfo=timezone.utc),
        platform="macOS",
        architecture="arm64",
        stellarium_script=script,
        preview_command=command,
        preview_capability=capability,
        preview_media=media,
        preview_observed=True,
        visual_review_status="approved",
        screenshots=[screenshot()],
    )

    assert first == second
    raw = canonical_capability_evidence_bytes(first)
    assert raw == canonical_capability_evidence_bytes(second)
    assert raw.endswith(b"\n")
    assert script.sha256.encode() in raw
    assert media.sha256.encode() in raw
    assert b"/Users/" not in raw and b"/tmp/" not in raw


def test_local_capability_evidence_rejects_non_utc_unsafe_or_excess_screenshots() -> None:
    _event, _result, editorial, script = july_editorial_and_script()
    capability = preview_capability()
    command = build_minimal_preview_command(
        subtitle_path="subtitles.srt",
        output_path="preview.mp4",
        duration_ms=editorial.total_duration_ms,
        capability=capability,
    )
    media = preview_media()

    with pytest.raises((ValidationError, ValueError), match="UTC|timezone"):
        build_local_capability_evidence(
            evidence_id="local-capability:bad-time-v1",
            captured_at=datetime(2026, 7, 30, 8, 0, tzinfo=timezone(timedelta(hours=8))),
            platform="macOS",
            architecture="arm64",
            stellarium_script=script,
            preview_command=command,
            preview_capability=capability,
            preview_media=media,
            preview_observed=True,
            visual_review_status="approved",
            screenshots=[screenshot()],
        )

    with pytest.raises((ValidationError, ValueError), match="path|relative|unsafe"):
        ScreenshotEvidenceV1(
            path="../frame.png",
            byte_size=1,
            sha256="a" * 64,
        )

    with pytest.raises((ValidationError, ValueError), match="30|screenshot"):
        build_local_capability_evidence(
            evidence_id="local-capability:too-many-v1",
            captured_at=datetime(2026, 7, 30, 0, 0, tzinfo=timezone.utc),
            platform="macOS",
            architecture="arm64",
            stellarium_script=script,
            preview_command=command,
            preview_capability=capability,
            preview_media=media,
            preview_observed=True,
            visual_review_status="approved",
            screenshots=[screenshot(index) for index in range(1, 32)],
        )


def test_capability_model_rejects_unobserved_approved_preview() -> None:
    payload = {
        "schema_version": "local-capability-evidence/v1",
        "evidence_id": "local-capability:invalid-v1",
        "captured_at": "2026-07-30T00:00:00Z",
        "platform": "macOS",
        "architecture": "arm64",
        "stellarium_version": "26.2.0",
        "ffmpeg_version": "7.1.1",
        "stellarium_script_sha256": "a" * 64,
        "preview_command_sha256": "b" * 64,
        "preview_media": None,
        "preview_observed": False,
        "visual_review_status": "approved",
        "screenshots": [],
    }
    with pytest.raises(ValidationError, match="observed|approved"):
        LocalCapabilityEvidenceV1.model_validate(payload)
