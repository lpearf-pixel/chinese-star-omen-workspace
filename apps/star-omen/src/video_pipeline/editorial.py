from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

import yaml
from pydantic import Field, model_validator

from src.video_pipeline.asterisms import (
    AsterismNarrationPolicy,
    AsterismResolutionV1,
    AsterismStatus,
)
from src.video_pipeline.contracts import (
    AstronomyEventV1,
    ClaimV1,
    RuleAssessmentV1,
    SourceInventoryV1,
    SourceReferenceV1,
    VideoPackageV1,
)
from src.video_pipeline.contracts._common import StableId, StrictContractModel, ensure_unique
from src.video_pipeline.evidence_bundle import EvidenceBundleV1, stable_lineage_id

ClaimClass = Literal[
    "astronomy_fact",
    "classical_quote",
    "historical_context",
    "modern_interpretation",
    "production_instruction",
]

_PROHIBITED_PATTERNS = (
    "必定发财",
    "命运已经注定",
    "灾难将至",
    "不照做就会",
    "不照做就",
    "遭殃",
    "天象决定你必须",
    "天象强迫",
)
_OBJECT_NAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9 ._+\-]{0,79}$"
_MAX_TEMPLATE_BYTES = 256 * 1024


class HistoricalContextAssetV1(StrictContractModel):
    schema_version: Literal["historical-context-asset/v1"] = (
        "historical-context-asset/v1"
    )
    asset_id: StableId
    text: str = Field(min_length=1, max_length=1600)
    source_title: str = Field(min_length=1, max_length=256)
    source_type: str = Field(min_length=1, max_length=96)
    review_status: Literal["approved"]


class ModernInterpretationAssetV1(StrictContractModel):
    schema_version: Literal["modern-interpretation-asset/v1"] = (
        "modern-interpretation-asset/v1"
    )
    asset_id: StableId
    text: str = Field(min_length=1, max_length=1600)
    disclosure: Literal["现代文化转译"]
    review_status: Literal["approved"]

    @model_validator(mode="after")
    def validate_disclosure(self) -> "ModernInterpretationAssetV1":
        if self.disclosure not in self.text:
            raise ValueError("modern interpretation text must include its disclosure")
        return self


class ClassicalQuoteAssetV1(StrictContractModel):
    schema_version: Literal["classical-quote-asset/v1"] = (
        "classical-quote-asset/v1"
    )
    evidence_id: StableId
    text: str = Field(min_length=1, max_length=4000)
    review_status: Literal["approved"]


class EditorialTemplateV1(StrictContractModel):
    schema_version: Literal["editorial-template/v1"]
    template_id: StableId
    language: Literal["zh-CN"]
    orientation: Literal["vertical-9:16"]
    total_duration_ms: int = Field(strict=True, ge=60_000, le=90_000)
    claim_weights: dict[ClaimClass, int]
    fov_degrees: dict[ClaimClass, float]
    object_names: dict[StableId, str]
    display_names: dict[StableId, str]
    production_instruction_text: str = Field(min_length=1, max_length=800)
    observer_label: str = Field(min_length=1, max_length=80, pattern=_OBJECT_NAME_PATTERN)

    @model_validator(mode="after")
    def validate_template(self) -> "EditorialTemplateV1":
        if self.total_duration_ms != 80_000:
            raise ValueError("B9 vertical template duration must be exactly 80000 ms")
        classes = {
            "astronomy_fact",
            "classical_quote",
            "historical_context",
            "modern_interpretation",
            "production_instruction",
        }
        if set(self.claim_weights) != classes or set(self.fov_degrees) != classes:
            raise ValueError("template must define all claim classes exactly")
        if any(isinstance(value, bool) or value <= 0 for value in self.claim_weights.values()):
            raise ValueError("claim weights must be positive integers")
        if any(not 1.0 <= value <= 120.0 for value in self.fov_degrees.values()):
            raise ValueError("FOV values must be in [1,120]")
        if not self.object_names:
            raise ValueError("template requires object names")
        ensure_unique(list(self.object_names.values()), "Stellarium object names")
        return self


class EditorialTemplateSnapshotV1(StrictContractModel):
    schema_version: Literal["editorial-template-snapshot/v1"] = (
        "editorial-template-snapshot/v1"
    )
    logical_name: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(strict=True, gt=0, le=_MAX_TEMPLATE_BYTES)
    template: EditorialTemplateV1


class EditorialShotV1(StrictContractModel):
    schema_version: Literal["editorial-shot/v1"] = "editorial-shot/v1"
    shot_id: StableId
    claim_id: StableId
    claim_class: ClaimClass
    start_ms: int = Field(strict=True, ge=0)
    end_ms: int = Field(strict=True, gt=0)
    target_object_id: StableId
    fov_deg: float = Field(strict=True, ge=1.0, le=120.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_duration(self) -> "EditorialShotV1":
        if self.end_ms <= self.start_ms:
            raise ValueError("shot end must be after start")
        return self


class EditorialPackageV1(StrictContractModel):
    schema_version: Literal["editorial-package/v1"] = "editorial-package/v1"
    editorial_package_id: StableId
    template_id: StableId
    template_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    video_package: VideoPackageV1
    shots: list[EditorialShotV1]
    total_duration_ms: int = Field(strict=True, ge=60_000, le=90_000)
    classical_status: Literal["included_citable", "omitted_no_allowed_lineage"]
    disclosures: list[str]
    render_object_names: dict[StableId, str]

    @model_validator(mode="after")
    def validate_package(self) -> "EditorialPackageV1":
        if self.total_duration_ms != 80_000:
            raise ValueError("editorial package duration must be exactly 80000 ms")
        if not self.shots:
            raise ValueError("editorial package requires shots")
        if self.shots[0].start_ms != 0 or self.shots[-1].end_ms != self.total_duration_ms:
            raise ValueError("shot timeline must cover the full package")
        for left, right in zip(self.shots, self.shots[1:], strict=False):
            if left.end_ms != right.start_ms:
                raise ValueError("shot timeline must be continuous")
        claim_ids = {claim.claim_id for claim in self.video_package.claims}
        if {shot.claim_id for shot in self.shots} != claim_ids:
            raise ValueError("shots must cover package claims exactly")
        for shot in self.shots:
            if shot.target_object_id not in self.render_object_names:
                raise ValueError("shot target lacks a render object name")
        return self


def _canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def canonical_editorial_bytes(package: EditorialPackageV1) -> bytes:
    return _canonical_json_bytes(package.model_dump(mode="json", exclude_none=False))


def load_editorial_template(
    source: str | Path | Mapping[str, Any],
) -> EditorialTemplateSnapshotV1 | EditorialTemplateV1:
    if isinstance(source, Mapping):
        return EditorialTemplateV1.model_validate(dict(source))
    path = Path(source)
    if path.is_symlink():
        raise ValueError("editorial template must not be a symlink")
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("editorial template must be a YAML file")
    raw = path.read_bytes()
    if not raw or len(raw) > _MAX_TEMPLATE_BYTES:
        raise ValueError("editorial template size is invalid")
    try:
        payload = yaml.safe_load(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError("editorial template is invalid UTF-8 YAML") from exc
    if not isinstance(payload, dict):
        raise ValueError("editorial template root must be a mapping")
    return EditorialTemplateSnapshotV1(
        logical_name=path.name,
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_size=len(raw),
        template=EditorialTemplateV1.model_validate(payload),
    )


def _unwrap_template(
    template: EditorialTemplateSnapshotV1 | EditorialTemplateV1,
) -> tuple[EditorialTemplateV1, str]:
    if isinstance(template, EditorialTemplateSnapshotV1):
        return template.template, template.sha256
    raw = _canonical_json_bytes(template.model_dump(mode="json"))
    return template, hashlib.sha256(raw).hexdigest()


def _reject_prohibited(text: str) -> None:
    if any(pattern in text for pattern in _PROHIBITED_PATTERNS):
        raise ValueError("prohibited deterministic or fear-based editorial language")


def _quote_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _display(template: EditorialTemplateV1, object_id: str) -> str:
    return template.display_names.get(object_id, object_id)


def _mapping_id(mapping: AsterismResolutionV1) -> str:
    if not mapping.modern_object_id or not mapping.traditional_star_id:
        raise ValueError("verified asterism mapping lacks stable identities")
    return f"asterism-mapping:{mapping.modern_object_id}:{mapping.traditional_star_id}"


def _astronomy_text(
    event: AstronomyEventV1,
    mapping: AsterismResolutionV1 | None,
    template: EditorialTemplateV1,
) -> tuple[str, list[tuple[str, str]], str]:
    angular = [
        measurement
        for measurement in event.measurements
        if measurement.kind
        in {"angular-distance-deg", "angular-separation-deg", "angular_distance_deg"}
    ]
    if len(angular) != 1:
        raise ValueError("editorial astronomy claim requires one angular measurement")
    measurement = angular[0]
    refs: list[tuple[str, str]] = [
        ("astronomy_measurement", measurement.measurement_id)
    ]
    target_id = event.primary_body
    target_name = _display(template, event.target_body_or_region)
    if mapping is not None and mapping.status in {
        AsterismStatus.VERIFIED_IDENTITY,
        AsterismStatus.VERIFIED_MEMBERSHIP,
    }:
        if mapping.narration_policy not in {
            AsterismNarrationPolicy.EXPLICIT_STAR_NAME,
            AsterismNarrationPolicy.EXPLICIT_MEMBERSHIP,
        }:
            raise ValueError("asterism mapping narration policy is inconsistent")
        refs.append(("asterism_mapping", _mapping_id(mapping)))
        target_id = mapping.modern_object_id or event.primary_body
        target_name = mapping.canonical_chinese_name or target_name
    body_name = _display(template, event.primary_body)
    text = (
        f"在固定计算输入中，{body_name}与{target_name}的角距约为"
        f"{measurement.value:.2f}度。"
    )
    return text, refs, target_id


def _package_id(
    *,
    event: AstronomyEventV1,
    assessment: RuleAssessmentV1,
    template: EditorialTemplateV1,
    assets: Sequence[str],
) -> str:
    return stable_lineage_id(
        "package",
        event.event_id,
        assessment.assessment_id,
        template.template_id,
        *assets,
    )


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
    template_model, template_sha256 = _unwrap_template(template)
    if assessment.event_id != event.event_id:
        raise ValueError("assessment event does not match astronomy event")
    if evidence_bundle.event_id != event.event_id:
        raise ValueError("evidence bundle event does not match astronomy event")
    if evidence_bundle.assessment_id != assessment.assessment_id:
        raise ValueError("evidence bundle assessment does not match assessment")
    ensure_unique([asset.asset_id for asset in historical_assets], "historical assets")
    ensure_unique([asset.asset_id for asset in modern_assets], "modern assets")
    ensure_unique([asset.evidence_id for asset in classical_quotes], "classical quote assets")

    for asset in historical_assets:
        _reject_prohibited(asset.text)
        if "开口破局" in asset.text:
            raise ValueError("开口破局 is restricted to modern_interpretation")
    for asset in modern_assets:
        _reject_prohibited(asset.text)
    for asset in classical_quotes:
        _reject_prohibited(asset.text)

    asset_identity = [
        *(f"history:{asset.asset_id}:{asset.text}" for asset in historical_assets),
        *(f"modern:{asset.asset_id}:{asset.text}" for asset in modern_assets),
        *(f"quote:{asset.evidence_id}:{asset.text}" for asset in classical_quotes),
    ]
    package_id = _package_id(
        event=event,
        assessment=assessment,
        template=template_model,
        assets=asset_identity,
    )

    claim_specs: list[tuple[ClaimClass, str, list[tuple[str, str]], str]] = []
    astronomy_text, astronomy_refs, astronomy_target = _astronomy_text(
        event, asterism_mapping, template_model
    )
    claim_specs.append(("astronomy_fact", astronomy_text, astronomy_refs, astronomy_target))

    if historical_assets:
        asset = historical_assets[0]
        claim_specs.append(
            (
                "historical_context",
                asset.text,
                [("historical_source", asset.asset_id)],
                astronomy_target,
            )
        )

    allowed_lineage = [
        entry
        for entry in evidence_bundle.entries
        if entry.claim_class == "classical_quote" and entry.narration_allowed
    ]
    quotes_by_id = {asset.evidence_id: asset for asset in classical_quotes}
    classical_status: Literal["included_citable", "omitted_no_allowed_lineage"]
    if allowed_lineage:
        if len(allowed_lineage) != 1:
            raise ValueError("B9 vertical slice supports one allowed classical lineage")
        lineage = allowed_lineage[0]
        quote = quotes_by_id.get(lineage.evidence_id)
        if quote is None:
            raise ValueError("allowed classical lineage requires an approved quote asset")
        if lineage.content_hash is None or _quote_hash(quote.text) != lineage.content_hash:
            raise ValueError("classical quote text hash does not match lineage")
        claim_specs.append(
            (
                "classical_quote",
                quote.text,
                [("citable_passage", quote.evidence_id)],
                event.primary_body,
            )
        )
        classical_status = "included_citable"
    else:
        classical_status = "omitted_no_allowed_lineage"

    if not modern_assets:
        raise ValueError("B9 vertical slice requires one approved modern interpretation")
    if len(modern_assets) != 1:
        raise ValueError("B9 vertical slice supports one modern interpretation asset")
    modern = modern_assets[0]
    claim_specs.append(
        (
            "modern_interpretation",
            modern.text,
            [("modern_interpretation", modern.asset_id)],
            event.primary_body,
        )
    )
    _reject_prohibited(template_model.production_instruction_text)
    claim_specs.append(
        (
            "production_instruction",
            template_model.production_instruction_text,
            [],
            event.primary_body,
        )
    )

    measurement_ids = sorted(
        {
            ref_id
            for claim_class, _, refs, _ in claim_specs
            for ref_type, ref_id in refs
            if ref_type == "astronomy_measurement"
        }
    )
    mapping_ids = sorted(
        {
            ref_id
            for _, _, refs, _ in claim_specs
            for ref_type, ref_id in refs
            if ref_type == "asterism_mapping"
        }
    )
    passage_ids = sorted(
        {
            ref_id
            for _, _, refs, _ in claim_specs
            for ref_type, ref_id in refs
            if ref_type == "citable_passage"
        }
    )
    historical_ids = sorted(asset.asset_id for asset in historical_assets[:1])
    modern_ids = [modern.asset_id]
    inventory = SourceInventoryV1(
        astronomy_measurement_ids=measurement_ids,
        asterism_mapping_ids=mapping_ids,
        citable_passage_ids=passage_ids,
        historical_source_ids=historical_ids,
        modern_interpretation_ids=modern_ids,
    )

    claims: list[ClaimV1] = []
    targets: dict[str, str] = {}
    for index, (claim_class, text, refs, target_id) in enumerate(claim_specs, start=1):
        claim_id = stable_lineage_id(
            "claim",
            package_id,
            str(index),
            claim_class,
            text,
            *(f"{kind}:{identifier}" for kind, identifier in refs),
        )
        claims.append(
            ClaimV1(
                claim_id=claim_id,
                claim_class=claim_class,
                text=text,
                source_refs=[
                    SourceReferenceV1(
                        source_package_id=package_id,
                        reference_type=kind,
                        reference_id=identifier,
                    )
                    for kind, identifier in refs
                ],
                review_status="pending",
            )
        )
        targets[claim_id] = target_id

    video_package = VideoPackageV1(
        schema_version="video-package/v1",
        package_id=package_id,
        event_id=event.event_id,
        assessment_id=assessment.assessment_id,
        source_inventory=inventory,
        claims=claims,
    )

    total_weight = sum(template_model.claim_weights[claim.claim_class] for claim in claims)
    shots: list[EditorialShotV1] = []
    cursor = 0
    for index, claim in enumerate(claims):
        if index == len(claims) - 1:
            end = template_model.total_duration_ms
        else:
            duration = (
                template_model.total_duration_ms
                * template_model.claim_weights[claim.claim_class]
                // total_weight
            )
            end = cursor + duration
        shots.append(
            EditorialShotV1(
                shot_id=stable_lineage_id("shot", package_id, claim.claim_id),
                claim_id=claim.claim_id,
                claim_class=claim.claim_class,
                start_ms=cursor,
                end_ms=end,
                target_object_id=targets[claim.claim_id],
                fov_deg=template_model.fov_degrees[claim.claim_class],
            )
        )
        cursor = end

    used_targets = {shot.target_object_id for shot in shots}
    object_names = {
        object_id: template_model.object_names[object_id]
        for object_id in sorted(used_targets)
        if object_id in template_model.object_names
    }
    if set(object_names) != used_targets:
        missing = sorted(used_targets - set(object_names))
        raise ValueError(f"template lacks Stellarium object mapping for {missing!r}")

    editorial_id = stable_lineage_id(
        "editorial",
        package_id,
        template_sha256,
        classical_status,
    )
    return EditorialPackageV1(
        editorial_package_id=editorial_id,
        template_id=template_model.template_id,
        template_sha256=template_sha256,
        video_package=video_package,
        shots=shots,
        total_duration_ms=template_model.total_duration_ms,
        classical_status=classical_status,
        disclosures=[modern.disclosure],
        render_object_names=object_names,
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
