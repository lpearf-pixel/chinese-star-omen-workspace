from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Annotated, Any, Mapping, Sequence

from pydantic import Field, TypeAdapter, model_validator

from src.video_pipeline.asterisms import (
    AsterismResolutionV1,
    AsterismStatus,
)
from src.video_pipeline.contracts import AstronomyEventV1, RuleAssessmentV1
from src.video_pipeline.evidence_bundle import EvidenceBundleV1

from . import editorial_impl as _impl

ClassicalQuoteAssetV1 = _impl.ClassicalQuoteAssetV1
EditorialShotV1 = _impl.EditorialShotV1
EditorialTemplateSnapshotV1 = _impl.EditorialTemplateSnapshotV1
EditorialTemplateV1 = _impl.EditorialTemplateV1
HistoricalContextAssetV1 = _impl.HistoricalContextAssetV1
ModernInterpretationAssetV1 = _impl.ModernInterpretationAssetV1

_SAFE_OBJECT_NAME = TypeAdapter(
    Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9 ._+\-]{0,79}$")]
)
_VERIFIED_MAPPING_STATUSES = {
    AsterismStatus.VERIFIED_IDENTITY,
    AsterismStatus.VERIFIED_MEMBERSHIP,
}
_PROHIBITED_COMPACT = {
    "必定发财",
    "必定發財",
    "命运已经注定",
    "命運已經注定",
    "灾难将至",
    "災難將至",
    "不照做就会",
    "不照做就會",
    "不照做就",
    "遭殃",
    "天象决定你必须",
    "天象決定你必須",
    "天象强迫",
    "天象強迫",
}
_OPEN_MOUTH_PHRASES = {"开口破局", "開口破局"}


class EditorialPackageV1(_impl.EditorialPackageV1):
    """Reviewed B9 editorial package with strict shot and status invariants."""

    @model_validator(mode="after")
    def validate_review_invariants(self) -> "EditorialPackageV1":
        claims = self.video_package.claims
        claims_by_id = {claim.claim_id: claim for claim in claims}
        shot_ids = [shot.shot_id for shot in self.shots]
        shot_claim_ids = [shot.claim_id for shot in self.shots]
        if len(shot_ids) != len(set(shot_ids)):
            raise ValueError("editorial shot IDs must be unique")
        if len(shot_claim_ids) != len(set(shot_claim_ids)):
            raise ValueError("each claim must have exactly one editorial shot")
        if len(self.shots) != len(claims):
            raise ValueError("editorial shots must cover claims one-to-one")
        if shot_claim_ids != [claim.claim_id for claim in claims]:
            raise ValueError("editorial shot order must match claim order")
        for shot in self.shots:
            claim = claims_by_id.get(shot.claim_id)
            if claim is None:
                raise ValueError("editorial shot references an unknown claim")
            if shot.claim_class != claim.claim_class:
                raise ValueError("editorial shot claim class does not match its claim")

        classical_count = sum(
            claim.claim_class == "classical_quote" for claim in claims
        )
        if self.classical_status == "included_citable" and classical_count != 1:
            raise ValueError("included classical status requires one classical claim")
        if self.classical_status == "omitted_no_allowed_lineage" and classical_count != 0:
            raise ValueError("omitted classical status cannot contain a classical claim")
        if len(self.disclosures) != len(set(self.disclosures)):
            raise ValueError("editorial disclosures must be unique")
        if any(claim.claim_class == "modern_interpretation" for claim in claims):
            if "现代文化转译" not in self.disclosures:
                raise ValueError("modern interpretation requires its disclosure")
        return self


def canonical_editorial_bytes(package: EditorialPackageV1) -> bytes:
    return _impl.canonical_editorial_bytes(package)


def _validate_object_names(template: EditorialTemplateV1) -> None:
    for object_name in template.object_names.values():
        _SAFE_OBJECT_NAME.validate_python(object_name, strict=True)


def _compact_policy_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(
        character
        for character in normalized
        if unicodedata.category(character)[0] in {"L", "N"}
    )


def _validate_editorial_language(
    *,
    historical_assets: Sequence[HistoricalContextAssetV1],
    modern_assets: Sequence[ModernInterpretationAssetV1],
    classical_quotes: Sequence[ClassicalQuoteAssetV1],
    template: EditorialTemplateV1,
) -> None:
    all_texts = [
        *(asset.text for asset in historical_assets),
        *(asset.text for asset in modern_assets),
        *(asset.text for asset in classical_quotes),
        template.production_instruction_text,
    ]
    for text in all_texts:
        compact = _compact_policy_text(text)
        if any(pattern in compact for pattern in _PROHIBITED_COMPACT):
            raise ValueError("prohibited deterministic or fear-based editorial language")

    non_modern_texts = [
        *(asset.text for asset in historical_assets),
        *(asset.text for asset in classical_quotes),
        template.production_instruction_text,
    ]
    for text in non_modern_texts:
        compact = _compact_policy_text(text)
        if any(_compact_policy_text(phrase) in compact for phrase in _OPEN_MOUTH_PHRASES):
            raise ValueError("开口破局 is restricted to modern_interpretation")


def _validate_assessment_bundle(
    assessment: RuleAssessmentV1,
    evidence_bundle: EvidenceBundleV1,
) -> None:
    if evidence_bundle.rule_set_version != assessment.rule_set_version:
        raise ValueError("evidence bundle rule set does not match assessment")

    allowed = [entry for entry in evidence_bundle.entries if entry.narration_allowed]
    should_allow = assessment.narration_eligibility == "eligible"
    if should_allow != bool(allowed):
        raise ValueError("assessment narration eligibility and lineage disagree")
    if not allowed:
        return
    if len(allowed) != 1:
        raise ValueError("B9 editorial package supports one allowed classical lineage")

    lineage = allowed[0]
    if assessment.recommended_rule_id != lineage.rule_id:
        raise ValueError("allowed lineage is not the assessment recommendation")
    evidence_by_id = {
        reference.evidence_id: reference for reference in assessment.evidence_references
    }
    reference = evidence_by_id.get(lineage.evidence_id)
    if reference is None or reference.status != "citable":
        raise ValueError("allowed lineage is missing citable assessment evidence")
    if reference.source_locator != lineage.source_locator:
        raise ValueError("assessment and lineage source locator disagree")
    if reference.content_hash != lineage.content_hash:
        raise ValueError("assessment and lineage content hash disagree")


def _validate_mapping_target(
    event: AstronomyEventV1,
    mapping: AsterismResolutionV1 | None,
    template: EditorialTemplateV1,
) -> None:
    if mapping is None or mapping.status not in _VERIFIED_MAPPING_STATUSES:
        return
    modern_id = mapping.modern_object_id
    if modern_id is None:
        raise ValueError("verified mapping target lacks a modern object ID")
    accepted = {modern_id.casefold()}
    render_name = template.object_names.get(modern_id)
    if render_name is not None:
        accepted.add(render_name.casefold())
    display_name = template.display_names.get(modern_id)
    if display_name is not None:
        accepted.add(display_name.casefold())
    if event.target_body_or_region.casefold() not in accepted:
        raise ValueError("asterism mapping target does not match event target")


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
    _validate_editorial_language(
        historical_assets=historical_assets,
        modern_assets=modern_assets,
        classical_quotes=classical_quotes,
        template=template_model,
    )
    _validate_assessment_bundle(assessment, evidence_bundle)
    _validate_mapping_target(event, asterism_mapping, template_model)
    compiled = _impl.compile_editorial_package(
        event=event,
        assessment=assessment,
        evidence_bundle=evidence_bundle,
        asterism_mapping=asterism_mapping,
        historical_assets=historical_assets,
        modern_assets=modern_assets,
        classical_quotes=classical_quotes,
        template=template,
    )
    return EditorialPackageV1.model_validate(compiled.model_dump(mode="json"))


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
