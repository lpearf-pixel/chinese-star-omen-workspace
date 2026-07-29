from __future__ import annotations

import pytest

from src.video_pipeline.asterisms import (
    AsterismNarrationPolicy,
    AsterismStatus,
)
from src.video_pipeline.editorial import (
    HistoricalContextAssetV1,
    ModernInterpretationAssetV1,
    compile_editorial_package,
    load_editorial_template,
)
from src.video_pipeline.stellarium import (
    StellariumCapabilityV1,
    generate_stellarium_script,
)
from tests.video_pipeline.editorial.helpers import (
    TEMPLATE_PATH,
    historical_asset_payload,
    july_inputs,
    modern_asset_payload,
    stellarium_capability_payload,
)


def _modern() -> ModernInterpretationAssetV1:
    return ModernInterpretationAssetV1.model_validate(modern_asset_payload())


def _history(*, asset_id: str = "history:traditional-asterism-context-v1") -> HistoricalContextAssetV1:
    payload = historical_asset_payload()
    payload["asset_id"] = asset_id
    return HistoricalContextAssetV1.model_validate(payload)


def test_historical_claim_discloses_source_type_and_title() -> None:
    event, result, mapping = july_inputs()
    historical = _history()
    package = compile_editorial_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        asterism_mapping=mapping,
        historical_assets=[historical],
        modern_assets=[_modern()],
        classical_quotes=[],
        template=load_editorial_template(TEMPLATE_PATH),
    )

    claim = next(
        item
        for item in package.video_package.claims
        if item.claim_class == "historical_context"
    )
    assert historical.source_type in claim.text
    assert historical.source_title in claim.text


def test_verified_membership_uses_membership_limited_wording() -> None:
    event, result, mapping = july_inputs()
    membership = mapping.model_copy(
        update={
            "status": AsterismStatus.VERIFIED_MEMBERSHIP,
            "narration_policy": AsterismNarrationPolicy.EXPLICIT_MEMBERSHIP,
        }
    )
    package = compile_editorial_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        asterism_mapping=membership,
        historical_assets=[],
        modern_assets=[_modern()],
        classical_quotes=[],
        template=load_editorial_template(TEMPLATE_PATH),
    )

    claim = next(
        item
        for item in package.video_package.claims
        if item.claim_class == "astronomy_fact"
    )
    assert "成员" in claim.text


def test_multiple_historical_assets_fail_instead_of_silent_truncation() -> None:
    event, result, mapping = july_inputs()

    with pytest.raises(ValueError, match="one historical"):
        compile_editorial_package(
            event=event,
            assessment=result.assessment,
            evidence_bundle=result.evidence_bundle,
            asterism_mapping=mapping,
            historical_assets=[
                _history(),
                _history(asset_id="history:second-context-v1"),
            ],
            modern_assets=[_modern()],
            classical_quotes=[],
            template=load_editorial_template(TEMPLATE_PATH),
        )


def test_template_observer_label_is_used_in_stellarium_script() -> None:
    event, result, mapping = july_inputs()
    snapshot = load_editorial_template(TEMPLATE_PATH)
    template_payload = snapshot.template.model_dump(mode="json")
    template_payload["observer_label"] = "Reviewed Observer"
    template = load_editorial_template(template_payload)
    package = compile_editorial_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        asterism_mapping=mapping,
        historical_assets=[],
        modern_assets=[_modern()],
        classical_quotes=[],
        template=template,
    )
    capability = StellariumCapabilityV1.model_validate(
        stellarium_capability_payload()
    )

    script = generate_stellarium_script(
        event=event,
        editorial=package,
        capability=capability,
    )
    assert '"Reviewed Observer", "Earth"' in script.content
