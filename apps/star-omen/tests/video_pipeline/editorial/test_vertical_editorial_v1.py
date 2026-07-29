from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.video_pipeline.editorial import (
    ClassicalQuoteAssetV1,
    HistoricalContextAssetV1,
    ModernInterpretationAssetV1,
    canonical_editorial_bytes,
    compile_editorial_package,
    load_editorial_template,
)
from tests.video_pipeline.editorial.helpers import (
    TEMPLATE_PATH,
    evidence_rich_inputs,
    historical_asset_payload,
    july_inputs,
    modern_asset_payload,
)


def compile_july(*, modern_text: str | None = None, historical_text: str | None = None):
    event, result, mapping = july_inputs()
    return compile_editorial_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        asterism_mapping=mapping,
        historical_assets=[HistoricalContextAssetV1.model_validate(historical_asset_payload(historical_text))],
        modern_assets=[ModernInterpretationAssetV1.model_validate(modern_asset_payload(modern_text))],
        classical_quotes=[],
        template=load_editorial_template(TEMPLATE_PATH),
    )


def test_july_package_is_honest_non_classical_vertical_slice() -> None:
    package = compile_july()

    assert package.schema_version == "editorial-package/v1"
    assert package.video_package.schema_version == "video-package/v1"
    assert package.video_package.event_id == "event:2026-07-21:moon-spica"
    classes = [claim.claim_class for claim in package.video_package.claims]
    assert "astronomy_fact" in classes
    assert "historical_context" in classes
    assert "modern_interpretation" in classes
    assert "production_instruction" in classes
    assert "classical_quote" not in classes
    assert any("现代文化转译" in claim.text for claim in package.video_package.claims)
    assert any("开口破局" in claim.text for claim in package.video_package.claims)
    assert package.classical_status == "omitted_no_allowed_lineage"


def test_every_claim_has_one_class_stable_id_and_valid_source_refs() -> None:
    package = compile_july()
    ids = [claim.claim_id for claim in package.video_package.claims]

    assert len(ids) == len(set(ids))
    assert all(claim.claim_class for claim in package.video_package.claims)
    assert all(claim.review_status == "pending" for claim in package.video_package.claims)
    # Revalidation proves all source refs are same-package, typed, non-dangling and unique.
    assert package.video_package.__class__.model_validate(
        package.video_package.model_dump(mode="json")
    ) == package.video_package


def test_shot_timeline_is_continuous_and_exactly_80_seconds() -> None:
    package = compile_july()

    assert package.total_duration_ms == 80_000
    assert package.shots[0].start_ms == 0
    assert package.shots[-1].end_ms == 80_000
    assert all(
        left.end_ms == right.start_ms
        for left, right in zip(package.shots, package.shots[1:], strict=False)
    )
    claim_ids = {claim.claim_id for claim in package.video_package.claims}
    assert all(shot.claim_id in claim_ids for shot in package.shots)
    assert all(shot.end_ms > shot.start_ms for shot in package.shots)


def test_repeated_editorial_generation_is_byte_identical() -> None:
    first = compile_july()
    second = compile_july()

    assert first == second
    assert canonical_editorial_bytes(first) == canonical_editorial_bytes(second)
    assert canonical_editorial_bytes(first).endswith(b"\n")


def test_evidence_rich_lineage_allows_exact_classical_quote() -> None:
    event, result = evidence_rich_inputs()
    quote = ClassicalQuoteAssetV1(
        evidence_id=result.assessment.evidence_references[0].evidence_id,
        text="石氏曰熒惑守心，天下兵起。",
        review_status="approved",
    )
    package = compile_editorial_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        asterism_mapping=None,
        historical_assets=[HistoricalContextAssetV1.model_validate(historical_asset_payload())],
        modern_assets=[ModernInterpretationAssetV1.model_validate(modern_asset_payload("现代文化转译：此处只作历史文化讨论。"))],
        classical_quotes=[quote],
        template=load_editorial_template(TEMPLATE_PATH),
    )

    classical = [
        claim for claim in package.video_package.claims if claim.claim_class == "classical_quote"
    ]
    assert len(classical) == 1
    assert classical[0].text == quote.text
    assert classical[0].source_refs[0].reference_id == quote.evidence_id
    assert package.classical_status == "included_citable"


def test_tampered_or_unapproved_quote_is_rejected() -> None:
    event, result = evidence_rich_inputs()
    evidence_id = result.assessment.evidence_references[0].evidence_id

    with pytest.raises(ValueError, match="hash"):
        compile_editorial_package(
            event=event,
            assessment=result.assessment,
            evidence_bundle=result.evidence_bundle,
            asterism_mapping=None,
            historical_assets=[],
            modern_assets=[ModernInterpretationAssetV1.model_validate(modern_asset_payload())],
            classical_quotes=[
                ClassicalQuoteAssetV1(
                    evidence_id=evidence_id,
                    text="被篡改的古籍文字",
                    review_status="approved",
                )
            ],
            template=load_editorial_template(TEMPLATE_PATH),
        )

    with pytest.raises(ValidationError):
        ClassicalQuoteAssetV1(
            evidence_id=evidence_id,
            text="石氏曰熒惑守心，天下兵起。",
            review_status="pending",
        )


def test_quote_is_rejected_when_lineage_is_blocked() -> None:
    event, result, mapping = july_inputs()

    with pytest.raises(ValueError, match="quote|lineage"):
        compile_editorial_package(
            event=event,
            assessment=result.assessment,
            evidence_bundle=result.evidence_bundle,
            asterism_mapping=mapping,
            historical_assets=[],
            modern_assets=[ModernInterpretationAssetV1.model_validate(modern_asset_payload())],
            classical_quotes=[
                ClassicalQuoteAssetV1(
                    evidence_id="evidence:not-authorized",
                    text="伪引文不得进入包",
                    review_status="approved",
                )
            ],
            template=load_editorial_template(TEMPLATE_PATH),
        )


def test_open_mouth_phrase_is_restricted_to_modern_interpretation() -> None:
    with pytest.raises(ValueError, match="开口破局"):
        compile_july(historical_text="古籍记载开口破局。")

    package = compile_july(modern_text="现代文化转译：开口破局只是主动沟通的比喻。")
    containing = [claim for claim in package.video_package.claims if "开口破局" in claim.text]
    assert containing
    assert all(claim.claim_class == "modern_interpretation" for claim in containing)


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "现代文化转译：这一天必定发财。",
        "现代文化转译：命运已经注定。",
        "现代文化转译：灾难将至，不照做就会遭殃。",
        "现代文化转译：天象决定你必须辞职。",
    ],
)
def test_deterministic_fate_promises_and_fear_language_fail_closed(
    unsafe_text: str,
) -> None:
    with pytest.raises(ValueError, match="prohibited"):
        compile_july(modern_text=unsafe_text)


def test_template_unknown_fields_and_wrong_duration_fail_closed(tmp_path) -> None:
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    unknown = tmp_path / "unknown.yaml"
    unknown.write_text(text + "\nunexpected: true\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_editorial_template(unknown)

    wrong_duration = tmp_path / "duration.yaml"
    wrong_duration.write_text(
        text.replace("total_duration_ms: 80000", "total_duration_ms: 59000"),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_editorial_template(wrong_duration)
