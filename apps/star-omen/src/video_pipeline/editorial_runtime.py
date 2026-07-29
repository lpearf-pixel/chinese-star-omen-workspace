from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Mapping, Sequence

from pydantic import Field, TypeAdapter

from src.video_pipeline.asterisms import AsterismResolutionV1
from src.video_pipeline.contracts import AstronomyEventV1, RuleAssessmentV1
from src.video_pipeline.evidence_bundle import EvidenceBundleV1

from . import editorial_impl as _impl

ClassicalQuoteAssetV1 = _impl.ClassicalQuoteAssetV1
EditorialPackageV1 = _impl.EditorialPackageV1
EditorialShotV1 = _impl.EditorialShotV1
EditorialTemplateSnapshotV1 = _impl.EditorialTemplateSnapshotV1
EditorialTemplateV1 = _impl.EditorialTemplateV1
HistoricalContextAssetV1 = _impl.HistoricalContextAssetV1
ModernInterpretationAssetV1 = _impl.ModernInterpretationAssetV1
canonical_editorial_bytes = _impl.canonical_editorial_bytes

_SAFE_OBJECT_NAME = TypeAdapter(
    Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9 ._+\-]{0,79}$")]
)


def _validate_object_names(template: EditorialTemplateV1) -> None:
    for object_name in template.object_names.values():
        _SAFE_OBJECT_NAME.validate_python(object_name, strict=True)


def load_editorial_template(
    source: str | Path | Mapping[str, Any],
) -> EditorialTemplateSnapshotV1 | EditorialTemplateV1:
    loaded = _impl.load_editorial_template(source)
    template = loaded.template if isinstance(loaded, EditorialTemplateSnapshotV1) else loaded
    _validate_object_names(template)
    return loaded


def compile_editorial_package(
    *,
    event: AstronomyEventV1,
    assessment: RuleAssessmentV1,
    evidence_bundle: EvidenceBundleV1,
    asterism_mapping: AsterismResolutionV1 | None,
    historical_assets: Sequence[HistoricalContextAssetV1],
    modern_assets: Sequence[ModernInterpretationAssetV1],
    classical_quotes: Sequence[ClassicalQuoteAssetV1],
    template: EditorialTemplateSnapshotV1 | EditorialTemplateV1,
) -> EditorialPackageV1:
    template_model = template.template if isinstance(template, EditorialTemplateSnapshotV1) else template
    _validate_object_names(template_model)
    return _impl.compile_editorial_package(
        event=event,
        assessment=assessment,
        evidence_bundle=evidence_bundle,
        asterism_mapping=asterism_mapping,
        historical_assets=historical_assets,
        modern_assets=modern_assets,
        classical_quotes=classical_quotes,
        template=template,
    )


__all__ = [
    "ClassicalQuoteAssetV1",
    "EditorialPackageV1",
    "EditorialShotV1",
    "EditorialTemplateSnapshotV1",
    "EditorialTemplateV1",
    "HistoricalContextAssetV1",
    "ModernInterpretationAssetV1",
    "canonical_editorial_bytes",
    "compile_editorial_package",
    "load_editorial_template",
]
