from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.video_pipeline.editorial import (
    ClassicalQuoteAssetV1,
    HistoricalContextAssetV1,
    ModernInterpretationAssetV1,
    compile_editorial_package,
    load_editorial_template,
)
from src.video_pipeline.preview import PreviewCapabilityV1
from src.video_pipeline.review import (
    ReviewRecordV1,
    build_review_bundle,
    expected_review_artifact_hashes,
)
from src.video_pipeline.stellarium import (
    StellariumCapabilityV1,
    generate_stellarium_script,
)
from src.video_pipeline.vertical_package import (
    assemble_vertical_package,
    publish_vertical_package,
)
from tests.video_pipeline.editorial.helpers import (
    TEMPLATE_PATH,
    evidence_rich_inputs,
    historical_asset_payload,
    modern_asset_payload,
    stellarium_capability_payload,
)
from tests.video_pipeline.package_review.helpers import july_editorial_and_script


EXPECTED_MEMBERS = {
    "astronomy-event.json",
    "rule-assessment.json",
    "evidence-bundle.json",
    "video-package.json",
    "editorial-package.json",
    "scene.ssc",
    "subtitles.srt",
    "preview-command.json",
    "review-bundle.json",
    "review-gate.json",
}


def preview_capability() -> PreviewCapabilityV1:
    return PreviewCapabilityV1(
        ffmpeg_version="7.1.1",
        enabled_features=["lavfi-color", "subtitles", "libx264"],
        max_timeout_seconds=120,
    )


def approved_reviews(event, evidence_bundle, editorial, script):
    hashes = expected_review_artifact_hashes(
        astronomy_event=event,
        evidence_bundle=evidence_bundle,
        editorial=editorial,
        stellarium_script=script,
    )
    return build_review_bundle(
        package_id=editorial.video_package.package_id,
        records=[
            ReviewRecordV1(
                dimension=dimension,
                reviewer_role=f"reviewer:{dimension}",
                decision="approved",
                reviewed_at=datetime(2026, 7, 30, 0, 0, tzinfo=timezone.utc),
                reason="reviewed against frozen B9 inputs",
                artifact_sha256=hashes[dimension],
            )
            for dimension in (
                "astronomy",
                "classical_evidence",
                "editorial",
                "render",
            )
        ],
    )


def july_build():
    event, result, editorial, script = july_editorial_and_script()
    reviews = approved_reviews(event, result.evidence_bundle, editorial, script)
    build = assemble_vertical_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        editorial=editorial,
        stellarium_script=script,
        reviews=reviews,
        preview_capability=preview_capability(),
    )
    return event, result, editorial, script, build


def evidence_rich_build():
    event, result = evidence_rich_inputs()
    quote = ClassicalQuoteAssetV1(
        evidence_id=result.assessment.evidence_references[0].evidence_id,
        text="石氏曰熒惑守心，天下兵起。",
        review_status="approved",
    )
    editorial = compile_editorial_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        asterism_mapping=None,
        historical_assets=[
            HistoricalContextAssetV1.model_validate(historical_asset_payload())
        ],
        modern_assets=[
            ModernInterpretationAssetV1.model_validate(
                modern_asset_payload("现代文化转译：此处只作历史文化讨论。")
            )
        ],
        classical_quotes=[quote],
        template=load_editorial_template(TEMPLATE_PATH),
    )
    script = generate_stellarium_script(
        event=event,
        editorial=editorial,
        capability=StellariumCapabilityV1.model_validate(
            stellarium_capability_payload()
        ),
    )
    reviews = approved_reviews(event, result.evidence_bundle, editorial, script)
    build = assemble_vertical_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        editorial=editorial,
        stellarium_script=script,
        reviews=reviews,
        preview_capability=preview_capability(),
    )
    return event, result, editorial, script, build


def test_july_blocked_classical_package_is_deterministic_and_previewable() -> None:
    _event, _result, editorial, _script, first = july_build()
    _event2, _result2, _editorial2, _script2, second = july_build()

    assert first == second
    assert first.package_id == editorial.video_package.package_id
    assert set(first.members) == EXPECTED_MEMBERS
    assert [entry.path for entry in first.manifest.members] == sorted(EXPECTED_MEMBERS)
    assert first.review_gate.status == "previewable"
    assert first.review_gate.classical_publishable is False
    assert first.local_capability_status == "not_supplied"
    assert "preview.mp4" not in first.members
    assert b"classical_quote" not in first.members["video-package.json"]
    assert first.preview_command.argv[-1] == "preview.mp4"


def test_evidence_rich_package_is_classical_publishable_and_contains_exact_quote() -> None:
    _event, _result, _editorial, _script, build = evidence_rich_build()

    assert build.review_gate.status == "previewable"
    assert build.review_gate.classical_publishable is True
    assert "石氏曰熒惑守心，天下兵起。" in build.members["subtitles.srt"].decode(
        "utf-8"
    )
    assert b'"classical_status":"included_citable"' in build.members[
        "editorial-package.json"
    ]


def test_vertical_package_publishes_atomically_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    _event, _result, _editorial, _script, build = july_build()
    output = tmp_path / "july-21-vertical-package"

    published = publish_vertical_package(output_dir=output, build=build)

    assert published == output
    assert (output / "manifest.json").is_file()
    assert (output / "subtitles.srt").read_bytes() == build.members["subtitles.srt"]
    assert not list(tmp_path.glob(".july-21-vertical-package.*"))

    with pytest.raises(FileExistsError):
        publish_vertical_package(output_dir=output, build=build)


def test_vertical_package_rejects_cross_input_identity_drift() -> None:
    event, result, editorial, script, _build = july_build()
    wrong_assessment = result.assessment.model_copy(
        update={"event_id": "event:other"}
    )
    reviews = approved_reviews(event, result.evidence_bundle, editorial, script)

    with pytest.raises((ValueError, TypeError), match="event|assessment|identity"):
        assemble_vertical_package(
            event=event,
            assessment=wrong_assessment,
            evidence_bundle=result.evidence_bundle,
            editorial=editorial,
            stellarium_script=script,
            reviews=reviews,
            preview_capability=preview_capability(),
        )
