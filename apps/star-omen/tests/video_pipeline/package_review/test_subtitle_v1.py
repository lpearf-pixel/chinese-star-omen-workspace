from __future__ import annotations

import re

import pytest

from src.video_pipeline.subtitle import canonical_srt_bytes, generate_srt
from tests.video_pipeline.package_review.helpers import july_editorial_and_script


def test_srt_is_deterministic_monotonic_and_matches_editorial_timeline() -> None:
    _event, _result, editorial, _script = july_editorial_and_script()

    first = generate_srt(editorial)
    second = generate_srt(editorial)

    assert first == second
    assert first.total_duration_ms == editorial.total_duration_ms == 80_000
    assert len(first.cues) == len(editorial.video_package.claims)
    assert first.cues[0].start_ms == 0
    assert first.cues[-1].end_ms == 80_000
    assert all(
        left.end_ms == right.start_ms
        for left, right in zip(first.cues, first.cues[1:], strict=False)
    )
    assert [cue.claim_id for cue in first.cues] == [
        claim.claim_id for claim in editorial.video_package.claims
    ]
    raw = canonical_srt_bytes(first)
    assert raw.endswith(b"\n")
    assert raw == canonical_srt_bytes(second)
    text = raw.decode("utf-8")
    assert "00:00:00,000 -->" in text
    assert "00:01:20,000" in text


def test_srt_rejects_multiline_or_control_character_claim_text() -> None:
    _event, _result, editorial, _script = july_editorial_and_script()
    payload = editorial.model_dump(mode="json")
    payload["video_package"]["claims"][0]["text"] = "unsafe\nsecond line"

    with pytest.raises(ValueError, match="subtitle|line|control"):
        generate_srt(payload)
