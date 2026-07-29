from __future__ import annotations

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


def july_editorial_and_script():
    event, result, mapping = july_inputs()
    editorial = compile_editorial_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        asterism_mapping=mapping,
        historical_assets=[
            HistoricalContextAssetV1.model_validate(historical_asset_payload())
        ],
        modern_assets=[
            ModernInterpretationAssetV1.model_validate(modern_asset_payload())
        ],
        classical_quotes=[],
        template=load_editorial_template(TEMPLATE_PATH),
    )
    script = generate_stellarium_script(
        event=event,
        editorial=editorial,
        capability=StellariumCapabilityV1.model_validate(
            stellarium_capability_payload()
        ),
    )
    return event, result, editorial, script
