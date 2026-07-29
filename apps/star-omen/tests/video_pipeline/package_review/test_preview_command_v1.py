from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.video_pipeline.preview import (
    PreviewCapabilityV1,
    build_minimal_preview_command,
)


def capability() -> PreviewCapabilityV1:
    return PreviewCapabilityV1(
        ffmpeg_version="7.1.1",
        enabled_features=["lavfi-color", "subtitles", "libx264"],
        max_timeout_seconds=120,
    )


def test_preview_command_is_bounded_shell_free_and_vertical() -> None:
    command = build_minimal_preview_command(
        subtitle_path="subtitles.srt",
        output_path="preview.mp4",
        duration_ms=80_000,
        capability=capability(),
    )

    assert command.argv[0] == "ffmpeg"
    assert command.timeout_seconds == 120
    assert command.output_path == "preview.mp4"
    assert command.width == 1080
    assert command.height == 1920
    assert command.duration_ms == 80_000
    assert command.shell is False
    assert "1080x1920" in " ".join(command.argv)
    assert "subtitles.srt" in " ".join(command.argv)
    assert command.argv[-1] == "preview.mp4"
    assert all(";" not in argument and "&&" not in argument for argument in command.argv)


@pytest.mark.parametrize(
    "subtitle_path,output_path",
    [
        ("../subtitles.srt", "preview.mp4"),
        ("/tmp/subtitles.srt", "preview.mp4"),
        ("subtitles.srt", "../preview.mp4"),
        ("subtitles.srt", "/tmp/preview.mp4"),
        ("subtitles;touch-pwned.srt", "preview.mp4"),
    ],
)
def test_preview_command_rejects_unsafe_paths(
    subtitle_path: str,
    output_path: str,
) -> None:
    with pytest.raises((ValidationError, ValueError), match="path|relative|unsafe"):
        build_minimal_preview_command(
            subtitle_path=subtitle_path,
            output_path=output_path,
            duration_ms=80_000,
            capability=capability(),
        )


def test_preview_command_rejects_missing_capability_and_invalid_duration() -> None:
    missing = capability().model_copy(
        update={"enabled_features": ["lavfi-color", "libx264"]}
    )
    with pytest.raises((ValidationError, ValueError), match="capability|subtitles"):
        build_minimal_preview_command(
            subtitle_path="subtitles.srt",
            output_path="preview.mp4",
            duration_ms=80_000,
            capability=missing,
        )

    with pytest.raises((ValidationError, ValueError), match="duration|80000"):
        build_minimal_preview_command(
            subtitle_path="subtitles.srt",
            output_path="preview.mp4",
            duration_ms=80_001,
            capability=capability(),
        )
