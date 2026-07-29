from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.video_pipeline.capability import inspect_preview_media_evidence


def payload_with_sections(*, programs: list, stream_groups: list) -> dict:
    return {
        "programs": programs,
        "stream_groups": stream_groups,
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


def test_ffprobe_empty_program_and_stream_group_sections_are_accepted(
    tmp_path: Path,
) -> None:
    path = tmp_path / "preview.mp4"
    path.write_bytes(b"synthetic-mp4-bytes")

    evidence = inspect_preview_media_evidence(
        path=path,
        ffprobe_payload=payload_with_sections(programs=[], stream_groups=[]),
    )

    assert evidence.path == "preview.mp4"


@pytest.mark.parametrize(
    "field",
    ["programs", "stream_groups"],
)
def test_ffprobe_nonempty_program_or_stream_group_sections_fail_closed(
    tmp_path: Path,
    field: str,
) -> None:
    path = tmp_path / "preview.mp4"
    path.write_bytes(b"synthetic-mp4-bytes")
    payload = payload_with_sections(programs=[], stream_groups=[])
    payload[field] = [{"index": 0}]

    with pytest.raises((ValidationError, ValueError), match="program|stream group|empty"):
        inspect_preview_media_evidence(path=path, ffprobe_payload=payload)
