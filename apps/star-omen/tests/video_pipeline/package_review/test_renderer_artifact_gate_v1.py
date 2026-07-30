from __future__ import annotations

from src.video_pipeline.assisted_review import (
    OCRObservationV1,
    RendererArtifactBindingV1,
    verify_renderer_artifacts,
)


def binding(path: str, character: str) -> RendererArtifactBindingV1:
    return RendererArtifactBindingV1(path=path, sha256=character * 64)


def codes(**kwargs: object) -> list[str]:
    return [
        issue.code
        for issue in verify_renderer_artifacts(
            declared_artifacts=[
                binding("astronomy-event.json", "a"),
                binding("preview.mp4", "b"),
            ],
            observed_artifacts=[
                binding("astronomy-event.json", "a"),
                binding("preview.mp4", "b"),
            ],
            declared_screenshot_sha256=["c" * 64, "d" * 64],
            observed_screenshot_sha256=["c" * 64, "d" * 64],
            ocr=[
                OCRObservationV1(
                    frame_sha256="c" * 64,
                    text="第一段",
                    order=1,
                    fully_in_frame=True,
                ),
                OCRObservationV1(
                    frame_sha256="d" * 64,
                    text="第二段",
                    order=2,
                    fully_in_frame=True,
                ),
            ],
            expected_subtitles=["第一段", "第二段"],
            **kwargs,
        )
    ]


def test_renderer_artifact_gate_accepts_exact_bindings_and_ordered_ocr() -> None:
    assert codes() == []


def test_renderer_artifact_gate_rejects_lineage_media_and_screenshot_drift() -> None:
    issues = verify_renderer_artifacts(
        declared_artifacts=[
            binding("astronomy-event.json", "a"),
            binding("preview.mp4", "b"),
        ],
        observed_artifacts=[
            binding("astronomy-event.json", "e"),
            binding("preview.mp4", "f"),
        ],
        declared_screenshot_sha256=["c" * 64],
        observed_screenshot_sha256=["d" * 64],
        ocr=[],
        expected_subtitles=[],
    )

    assert [issue.code for issue in issues] == [
        "lineage.hash_mismatch",
        "media.contract_mismatch",
        "screenshot.inventory_mismatch",
    ]


def test_renderer_artifact_gate_rejects_missing_reordered_or_clipped_subtitles() -> None:
    common = {
        "declared_artifacts": [binding("preview.mp4", "b")],
        "observed_artifacts": [binding("preview.mp4", "b")],
        "declared_screenshot_sha256": ["c" * 64, "d" * 64],
        "observed_screenshot_sha256": ["c" * 64, "d" * 64],
        "expected_subtitles": ["第一段", "第二段"],
    }

    missing = verify_renderer_artifacts(
        **common,
        ocr=[
            OCRObservationV1(
                frame_sha256="c" * 64,
                text="第一段",
                order=1,
                fully_in_frame=True,
            )
        ],
    )
    reordered = verify_renderer_artifacts(
        **common,
        ocr=[
            OCRObservationV1(
                frame_sha256="d" * 64,
                text="第二段",
                order=1,
                fully_in_frame=True,
            ),
            OCRObservationV1(
                frame_sha256="c" * 64,
                text="第一段",
                order=2,
                fully_in_frame=False,
            ),
        ],
    )

    assert [issue.code for issue in missing] == ["ocr.subtitle_missing"]
    assert [issue.code for issue in reordered] == [
        "ocr.subtitle_order_mismatch",
        "ocr.subtitle_out_of_frame",
    ]
