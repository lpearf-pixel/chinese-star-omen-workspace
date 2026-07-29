from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.video_pipeline.capability import (
    PreviewMediaEvidenceV1,
    ScreenshotEvidenceV1,
    build_local_capability_evidence,
    canonical_capability_evidence_bytes,
    inspect_preview_media_evidence,
)
from src.video_pipeline.preview import PreviewCapabilityV1, build_minimal_preview_command
from tests.video_pipeline.package_review.helpers import july_editorial_and_script


def valid_ffprobe_payload(**overrides: object) -> dict:
    payload = {
        "streams": [
            {
                "index": 0,
                "codec_name": "h264",
                "codec_type": "video",
                "width": 1080,
                "height": 1920,
            }
        ],
        "format": {
            "filename": "preview.mp4",
            "duration": "80.000000",
            "size": "19",
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        },
    }
    for key, value in overrides.items():
        if key.startswith("stream_"):
            payload["streams"][0][key.removeprefix("stream_")] = value
        else:
            payload["format"][key] = value
    return payload


def write_preview(path: Path, payload: bytes = b"synthetic-mp4-bytes") -> Path:
    path.write_bytes(payload)
    return path


def preview_capability() -> PreviewCapabilityV1:
    return PreviewCapabilityV1(
        ffmpeg_version="7.1.1",
        enabled_features=["lavfi-color", "subtitles", "libx264"],
        max_timeout_seconds=120,
    )


def screenshot() -> ScreenshotEvidenceV1:
    return ScreenshotEvidenceV1(
        path="screenshots/frame-01.png",
        byte_size=1024,
        sha256="a" * 64,
    )


def test_preview_media_evidence_binds_actual_bytes_and_ffprobe_properties(
    tmp_path: Path,
) -> None:
    path = write_preview(tmp_path / "preview.mp4")

    evidence = inspect_preview_media_evidence(
        path=path,
        ffprobe_payload=valid_ffprobe_payload(),
    )

    assert evidence.schema_version == "preview-media-evidence/v1"
    assert evidence.path == "preview.mp4"
    assert evidence.byte_size == len(b"synthetic-mp4-bytes")
    assert len(evidence.sha256) == 64
    assert evidence.width == 1080
    assert evidence.height == 1920
    assert evidence.duration_ms == 80_000
    assert evidence.duration_tolerance_ms == 500
    assert evidence.video_codec == "h264"
    assert evidence.video_stream_count == 1
    assert evidence.audio_stream_count == 0


def test_preview_media_hash_changes_when_actual_bytes_change(tmp_path: Path) -> None:
    path = write_preview(tmp_path / "preview.mp4", b"first-preview")
    first_payload = valid_ffprobe_payload(size=str(len(b"first-preview")))
    first = inspect_preview_media_evidence(path=path, ffprobe_payload=first_payload)

    path.write_bytes(b"second-preview")
    second_payload = valid_ffprobe_payload(size=str(len(b"second-preview")))
    second = inspect_preview_media_evidence(path=path, ffprobe_payload=second_payload)

    assert first.sha256 != second.sha256
    assert first.byte_size != second.byte_size


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (valid_ffprobe_payload(stream_width=720), "width|1080"),
        (valid_ffprobe_payload(stream_height=1080), "height|1920"),
        (valid_ffprobe_payload(stream_codec_name="hevc"), "codec|h264"),
        (valid_ffprobe_payload(duration="79.000000"), "duration|80"),
        (valid_ffprobe_payload(duration="nan"), "duration|finite"),
        (
            {
                "streams": [
                    valid_ffprobe_payload()["streams"][0],
                    {"index": 1, "codec_name": "aac", "codec_type": "audio"},
                ],
                "format": valid_ffprobe_payload()["format"],
            },
            "audio",
        ),
        (
            {
                "streams": [
                    valid_ffprobe_payload()["streams"][0],
                    {
                        "index": 1,
                        "codec_name": "h264",
                        "codec_type": "video",
                        "width": 1080,
                        "height": 1920,
                    },
                ],
                "format": valid_ffprobe_payload()["format"],
            },
            "video stream|exactly one",
        ),
    ],
)
def test_preview_media_evidence_rejects_unsupported_or_ambiguous_metadata(
    tmp_path: Path,
    payload: dict,
    message: str,
) -> None:
    path = write_preview(tmp_path / "preview.mp4")

    with pytest.raises((ValidationError, ValueError, TypeError), match=message):
        inspect_preview_media_evidence(path=path, ffprobe_payload=payload)


def test_preview_media_evidence_rejects_wrong_name_symlink_and_oversized_file(
    tmp_path: Path,
) -> None:
    wrong_name = write_preview(tmp_path / "final.mp4")
    with pytest.raises((ValidationError, ValueError), match="preview.mp4|path"):
        inspect_preview_media_evidence(
            path=wrong_name,
            ffprobe_payload=valid_ffprobe_payload(filename="final.mp4"),
        )

    target = write_preview(tmp_path / "target.mp4")
    linked = tmp_path / "preview.mp4"
    linked.symlink_to(target)
    with pytest.raises((ValidationError, ValueError), match="symlink"):
        inspect_preview_media_evidence(
            path=linked,
            ffprobe_payload=valid_ffprobe_payload(),
        )

    oversized = write_preview(tmp_path / "preview.mp4", b"x" * 17)
    with pytest.raises((ValidationError, ValueError), match="large|size"):
        inspect_preview_media_evidence(
            path=oversized,
            ffprobe_payload=valid_ffprobe_payload(size="17"),
            max_bytes=16,
        )


def test_local_capability_requires_media_for_observed_or_approved_preview(
    tmp_path: Path,
) -> None:
    _event, _result, editorial, script = july_editorial_and_script()
    capability = preview_capability()
    command = build_minimal_preview_command(
        subtitle_path="subtitles.srt",
        output_path="preview.mp4",
        duration_ms=editorial.total_duration_ms,
        capability=capability,
    )
    media = inspect_preview_media_evidence(
        path=write_preview(tmp_path / "preview.mp4"),
        ffprobe_payload=valid_ffprobe_payload(),
    )

    with pytest.raises((ValidationError, ValueError), match="media|preview"):
        build_local_capability_evidence(
            evidence_id="local-capability:missing-media-v1",
            captured_at=datetime(2026, 7, 30, 0, 0, tzinfo=timezone.utc),
            platform="macOS",
            architecture="arm64",
            stellarium_script=script,
            preview_command=command,
            preview_capability=capability,
            preview_media=None,
            preview_observed=True,
            visual_review_status="approved",
            screenshots=[screenshot()],
        )

    with pytest.raises((ValidationError, ValueError), match="unobserved|media"):
        build_local_capability_evidence(
            evidence_id="local-capability:unexpected-media-v1",
            captured_at=datetime(2026, 7, 30, 0, 0, tzinfo=timezone.utc),
            platform="macOS",
            architecture="arm64",
            stellarium_script=script,
            preview_command=command,
            preview_capability=capability,
            preview_media=media,
            preview_observed=False,
            visual_review_status="not_run",
            screenshots=[],
        )

    valid = build_local_capability_evidence(
        evidence_id="local-capability:media-bound-v1",
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
    raw = canonical_capability_evidence_bytes(valid)
    assert media.sha256.encode() in raw
    assert b'"preview_media"' in raw


def test_preview_media_model_rejects_non_finite_or_inconsistent_fields() -> None:
    with pytest.raises(ValidationError):
        PreviewMediaEvidenceV1(
            path="preview.mp4",
            byte_size=1,
            sha256="a" * 64,
            width=1080,
            height=1920,
            duration_ms=True,
            duration_tolerance_ms=500,
            video_codec="h264",
            video_stream_count=1,
            audio_stream_count=0,
        )
