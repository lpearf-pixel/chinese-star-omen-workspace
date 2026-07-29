from __future__ import annotations

import hashlib
from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.video_pipeline.asterisms import AsterismResolutionV1
from src.video_pipeline.contracts import RuleAssessmentV1
from src.video_pipeline.editorial import (
    ClassicalQuoteAssetV1,
    EditorialPackageV1,
    HistoricalContextAssetV1,
    ModernInterpretationAssetV1,
    compile_editorial_package,
    load_editorial_template,
)
from src.video_pipeline.stellarium import (
    StellariumCapabilityV1,
    StellariumScriptV1,
    generate_stellarium_script,
    validate_stellarium_script,
)
from tests.video_pipeline.editorial.helpers import (
    TEMPLATE_PATH,
    evidence_rich_inputs,
    historical_asset_payload,
    july_inputs,
    modern_asset_payload,
    stellarium_capability_payload,
)


def _compile_july(*, template=None, modern_text: str | None = None):
    event, result, mapping = july_inputs()
    package = compile_editorial_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        asterism_mapping=mapping,
        historical_assets=[
            HistoricalContextAssetV1.model_validate(historical_asset_payload())
        ],
        modern_assets=[
            ModernInterpretationAssetV1.model_validate(
                modern_asset_payload(modern_text)
            )
        ],
        classical_quotes=[],
        template=template or load_editorial_template(TEMPLATE_PATH),
    )
    return event, package


def _capability() -> StellariumCapabilityV1:
    return StellariumCapabilityV1.model_validate(stellarium_capability_payload())


def test_allowed_classical_lineage_requires_eligible_assessment() -> None:
    event, result = evidence_rich_inputs()
    blocked_payload = result.assessment.model_dump(mode="json")
    blocked_payload["recommended_rule_id"] = None
    blocked_payload["narration_eligibility"] = "blocked"
    blocked = RuleAssessmentV1.model_validate(blocked_payload)
    quote = ClassicalQuoteAssetV1(
        evidence_id=result.assessment.evidence_references[0].evidence_id,
        text="石氏曰熒惑守心，天下兵起。",
        review_status="approved",
    )

    with pytest.raises(ValueError, match="assessment|lineage|narration"):
        compile_editorial_package(
            event=event,
            assessment=blocked,
            evidence_bundle=result.evidence_bundle,
            asterism_mapping=None,
            historical_assets=[],
            modern_assets=[
                ModernInterpretationAssetV1.model_validate(modern_asset_payload())
            ],
            classical_quotes=[quote],
            template=load_editorial_template(TEMPLATE_PATH),
        )


def test_evidence_bundle_rule_set_must_match_assessment() -> None:
    event, result = evidence_rich_inputs()
    bundle_payload = result.evidence_bundle.model_dump(mode="json")
    bundle_payload["rule_set_version"] = "rules:other-v1"
    tampered_bundle = result.evidence_bundle.__class__.model_validate(bundle_payload)
    quote = ClassicalQuoteAssetV1(
        evidence_id=result.assessment.evidence_references[0].evidence_id,
        text="石氏曰熒惑守心，天下兵起。",
        review_status="approved",
    )

    with pytest.raises(ValueError, match="rule set"):
        compile_editorial_package(
            event=event,
            assessment=result.assessment,
            evidence_bundle=tampered_bundle,
            asterism_mapping=None,
            historical_assets=[],
            modern_assets=[
                ModernInterpretationAssetV1.model_validate(modern_asset_payload())
            ],
            classical_quotes=[quote],
            template=load_editorial_template(TEMPLATE_PATH),
        )


def test_verified_asterism_mapping_must_bind_to_event_target() -> None:
    event, result, mapping = july_inputs()
    template_snapshot = load_editorial_template(TEMPLATE_PATH)
    template_payload = template_snapshot.template.model_dump(mode="json")
    template_payload["object_names"]["hip:99999"] = "Sirius"
    template = load_editorial_template(template_payload)

    mapping_payload = mapping.model_dump(mode="json")
    mapping_payload.update(
        {
            "query": "hip:99999",
            "modern_object_id": "hip:99999",
            "traditional_star_id": "wrong-star",
            "asterism_id": "wrong-asterism",
            "canonical_chinese_name": "错误星",
        }
    )
    unrelated = AsterismResolutionV1.model_validate(mapping_payload)

    with pytest.raises(ValueError, match="event target|mapping target"):
        compile_editorial_package(
            event=event,
            assessment=result.assessment,
            evidence_bundle=result.evidence_bundle,
            asterism_mapping=unrelated,
            historical_assets=[],
            modern_assets=[
                ModernInterpretationAssetV1.model_validate(modern_asset_payload())
            ],
            classical_quotes=[],
            template=template,
        )


def test_editorial_package_rejects_duplicate_shot_for_one_claim() -> None:
    _event, package = _compile_july()
    payload = package.model_dump(mode="json")
    first = payload["shots"][0]
    midpoint = (first["start_ms"] + first["end_ms"]) // 2
    first_half = deepcopy(first)
    first_half["end_ms"] = midpoint
    second_half = deepcopy(first)
    second_half["shot_id"] = "shot:duplicate-segment"
    second_half["start_ms"] = midpoint
    payload["shots"] = [first_half, second_half, *payload["shots"][1:]]

    with pytest.raises(ValidationError, match="shot|claim"):
        EditorialPackageV1.model_validate(payload)


def test_editorial_package_rejects_shot_class_and_classical_status_drift() -> None:
    _event, package = _compile_july()

    wrong_class = package.model_dump(mode="json")
    wrong_class["shots"][0]["claim_class"] = "modern_interpretation"
    with pytest.raises(ValidationError, match="claim class|shot"):
        EditorialPackageV1.model_validate(wrong_class)

    wrong_status = package.model_dump(mode="json")
    wrong_status["classical_status"] = "included_citable"
    with pytest.raises(ValidationError, match="classical"):
        EditorialPackageV1.model_validate(wrong_status)


def test_open_mouth_phrase_is_rejected_in_production_instruction() -> None:
    snapshot = load_editorial_template(TEMPLATE_PATH)
    payload = snapshot.template.model_dump(mode="json")
    payload["production_instruction_text"] = "开口破局，画面仅用于文化展示。"

    with pytest.raises(ValueError, match="开口破局"):
        _compile_july(template=load_editorial_template(payload))


def test_prohibited_language_cannot_bypass_gate_with_spacing_and_punctuation() -> None:
    with pytest.raises(ValueError, match="prohibited"):
        _compile_july(modern_text="现代文化转译：命 运，已 经 注 定。")


def test_stellarium_script_binds_wait_metadata_to_content() -> None:
    event, editorial = _compile_july()
    script = generate_stellarium_script(
        event=event,
        editorial=editorial,
        capability=_capability(),
    )
    payload = script.model_dump(mode="json")
    payload["total_wait_ms"] += 1

    with pytest.raises(ValidationError, match="wait|duration"):
        StellariumScriptV1.model_validate(payload)


def test_stellarium_script_rejects_noncanonical_command_order() -> None:
    event, editorial = _compile_july()
    script = generate_stellarium_script(
        event=event,
        editorial=editorial,
        capability=_capability(),
    )
    lines = script.content.splitlines()
    lines[2], lines[3] = lines[3], lines[2]
    changed_content = "\n".join(lines) + "\n"
    payload = script.model_dump(mode="json")
    payload["content"] = changed_content
    payload["sha256"] = hashlib.sha256(changed_content.encode("utf-8")).hexdigest()
    payload["commands"] = validate_stellarium_script(changed_content)

    with pytest.raises(ValidationError, match="order|template|canonical"):
        StellariumScriptV1.model_validate(payload)


def test_generated_script_restores_tracking_time_and_gui_state() -> None:
    event, editorial = _compile_july()
    script = generate_stellarium_script(
        event=event,
        editorial=editorial,
        capability=_capability(),
    )

    assert script.content.splitlines()[-3:] == [
        "StelMovementMgr.setFlagTracking(false);",
        "core.setTimeRate(1.0);",
        "core.setGuiVisible(true);",
    ]
