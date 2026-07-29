from __future__ import annotations

import pytest

from src.video_pipeline.editorial import (
    ClassicalQuoteAssetV1,
    HistoricalContextAssetV1,
    ModernInterpretationAssetV1,
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


def _modern() -> ModernInterpretationAssetV1:
    return ModernInterpretationAssetV1.model_validate(modern_asset_payload())


def test_video_package_id_changes_when_production_claim_text_changes() -> None:
    event, result, mapping = july_inputs()
    snapshot = load_editorial_template(TEMPLATE_PATH)
    changed_payload = snapshot.template.model_dump(mode="json")
    changed_payload["production_instruction_text"] = (
        "制作说明：画面仍只用于展示固定计算结果，但采用另一条审核说明。"
    )
    changed_template = load_editorial_template(changed_payload)

    original = compile_editorial_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        asterism_mapping=mapping,
        historical_assets=[
            HistoricalContextAssetV1.model_validate(historical_asset_payload())
        ],
        modern_assets=[_modern()],
        classical_quotes=[],
        template=snapshot,
    )
    changed = compile_editorial_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        asterism_mapping=mapping,
        historical_assets=[
            HistoricalContextAssetV1.model_validate(historical_asset_payload())
        ],
        modern_assets=[_modern()],
        classical_quotes=[],
        template=changed_template,
    )

    assert original.video_package.package_id != changed.video_package.package_id
    assert original.video_package.claims != changed.video_package.claims


def test_quote_assets_are_rejected_when_no_classical_lineage_is_allowed() -> None:
    event, result, mapping = july_inputs()
    unused = ClassicalQuoteAssetV1(
        evidence_id="evidence:unused-classical-quote",
        text="此句不应在无古籍 lineage 的样片中被静默接收。",
        review_status="approved",
    )

    with pytest.raises(ValueError, match="quote|lineage|unused"):
        compile_editorial_package(
            event=event,
            assessment=result.assessment,
            evidence_bundle=result.evidence_bundle,
            asterism_mapping=mapping,
            historical_assets=[],
            modern_assets=[_modern()],
            classical_quotes=[unused],
            template=load_editorial_template(TEMPLATE_PATH),
        )


def test_extra_quote_asset_is_rejected_beside_the_allowed_lineage() -> None:
    event, result = evidence_rich_inputs()
    allowed = ClassicalQuoteAssetV1(
        evidence_id=result.assessment.evidence_references[0].evidence_id,
        text="石氏曰熒惑守心，天下兵起。",
        review_status="approved",
    )
    extra = ClassicalQuoteAssetV1(
        evidence_id="evidence:unrelated-extra-quote",
        text="无关的额外引文不得被静默忽略。",
        review_status="approved",
    )

    with pytest.raises(ValueError, match="quote|lineage|unused|exact"):
        compile_editorial_package(
            event=event,
            assessment=result.assessment,
            evidence_bundle=result.evidence_bundle,
            asterism_mapping=None,
            historical_assets=[],
            modern_assets=[_modern()],
            classical_quotes=[allowed, extra],
            template=load_editorial_template(TEMPLATE_PATH),
        )
