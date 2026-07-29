from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Literal, Mapping

from pydantic import BaseModel

from src.video_pipeline.capability import (
    LocalCapabilityEvidenceV1,
    canonical_capability_evidence_bytes,
    canonical_preview_command_bytes,
)
from src.video_pipeline.contracts import (
    AstronomyEventV1,
    RuleAssessmentV1,
    canonical_contract_bytes,
)
from src.video_pipeline.editorial import EditorialPackageV1, canonical_editorial_bytes
from src.video_pipeline.evidence_bundle import (
    EvidenceBundleV1,
    canonical_evidence_bundle_bytes,
)
from src.video_pipeline.package import (
    PackageManifestV1,
    build_package_manifest,
    verify_package_members,
    write_package_atomic,
)
from src.video_pipeline.preview import (
    PreviewCapabilityV1,
    PreviewCommandV1,
    build_minimal_preview_command,
)
from src.video_pipeline.review import (
    ReviewBundleV1,
    ReviewGateResultV1,
    evaluate_review_gate,
)
from src.video_pipeline.stellarium import (
    StellariumScriptV1,
    canonical_stellarium_bytes,
)
from src.video_pipeline.subtitle import SrtDocumentV1, canonical_srt_bytes, generate_srt

LocalCapabilityStatus = Literal["not_supplied", "approved", "blocked"]


@dataclass(frozen=True, slots=True)
class VerticalPackageBuild:
    package_id: str
    manifest: PackageManifestV1
    members: Mapping[str, bytes]
    subtitle: SrtDocumentV1
    preview_command: PreviewCommandV1
    review_gate: ReviewGateResultV1
    local_capability_status: LocalCapabilityStatus
    local_capability_evidence: LocalCapabilityEvidenceV1 | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "members", MappingProxyType(dict(self.members)))


def _canonical_model_bytes(model: BaseModel) -> bytes:
    payload = model.model_dump(mode="json", exclude_none=False)
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


def _validate_input_identity(
    *,
    event: AstronomyEventV1,
    assessment: RuleAssessmentV1,
    evidence_bundle: EvidenceBundleV1,
    editorial: EditorialPackageV1,
    stellarium_script: StellariumScriptV1,
    reviews: ReviewBundleV1,
) -> None:
    package_id = editorial.video_package.package_id
    if assessment.event_id != event.event_id:
        raise ValueError("assessment event identity does not match astronomy event")
    if evidence_bundle.event_id != event.event_id:
        raise ValueError("evidence bundle event identity does not match astronomy event")
    if evidence_bundle.assessment_id != assessment.assessment_id:
        raise ValueError("evidence bundle assessment identity does not match assessment")
    if evidence_bundle.rule_set_version != assessment.rule_set_version:
        raise ValueError("evidence bundle rule set identity does not match assessment")
    if editorial.video_package.event_id != event.event_id:
        raise ValueError("editorial event identity does not match astronomy event")
    if editorial.video_package.assessment_id != assessment.assessment_id:
        raise ValueError("editorial assessment identity does not match assessment")
    if stellarium_script.event_id != event.event_id:
        raise ValueError("Stellarium script event identity does not match astronomy event")
    if stellarium_script.editorial_package_id != editorial.editorial_package_id:
        raise ValueError("Stellarium script identity does not match editorial package")
    if reviews.package_id != package_id:
        raise ValueError("review bundle package identity does not match video package")


def _validate_local_capability(
    *,
    evidence: LocalCapabilityEvidenceV1,
    stellarium_script: StellariumScriptV1,
    preview_command: PreviewCommandV1,
    preview_capability: PreviewCapabilityV1,
) -> LocalCapabilityStatus:
    evidence = LocalCapabilityEvidenceV1.model_validate(
        evidence.model_dump(mode="json")
    )
    if evidence.stellarium_version != stellarium_script.stellarium_version:
        raise ValueError("local capability Stellarium version does not match script")
    if evidence.ffmpeg_version != preview_capability.ffmpeg_version:
        raise ValueError("local capability FFmpeg version does not match preview capability")
    if evidence.stellarium_script_sha256 != stellarium_script.sha256:
        raise ValueError("local capability script hash does not match package script")
    expected_preview_hash = hashlib.sha256(
        canonical_preview_command_bytes(preview_command)
    ).hexdigest()
    if evidence.preview_command_sha256 != expected_preview_hash:
        raise ValueError("local capability preview command hash does not match package")
    if evidence.preview_observed and evidence.visual_review_status == "approved":
        return "approved"
    return "blocked"


def assemble_vertical_package(
    *,
    event: AstronomyEventV1,
    assessment: RuleAssessmentV1,
    evidence_bundle: EvidenceBundleV1,
    editorial: EditorialPackageV1,
    stellarium_script: StellariumScriptV1,
    reviews: ReviewBundleV1,
    preview_capability: PreviewCapabilityV1,
    local_capability_evidence: LocalCapabilityEvidenceV1 | None = None,
) -> VerticalPackageBuild:
    event = AstronomyEventV1.model_validate(event.model_dump(mode="json"))
    assessment = RuleAssessmentV1.model_validate(assessment.model_dump(mode="json"))
    evidence_bundle = EvidenceBundleV1.model_validate(
        evidence_bundle.model_dump(mode="json")
    )
    editorial = EditorialPackageV1.model_validate(editorial.model_dump(mode="json"))
    stellarium_script = StellariumScriptV1.model_validate(
        stellarium_script.model_dump(mode="json")
    )
    reviews = ReviewBundleV1.model_validate(reviews.model_dump(mode="json"))
    preview_capability = PreviewCapabilityV1.model_validate(
        preview_capability.model_dump(mode="json")
    )
    _validate_input_identity(
        event=event,
        assessment=assessment,
        evidence_bundle=evidence_bundle,
        editorial=editorial,
        stellarium_script=stellarium_script,
        reviews=reviews,
    )

    subtitle = generate_srt(editorial)
    preview_command = build_minimal_preview_command(
        subtitle_path="subtitles.srt",
        output_path="preview.mp4",
        duration_ms=editorial.total_duration_ms,
        capability=preview_capability,
    )
    review_gate = evaluate_review_gate(
        astronomy_event=event,
        editorial=editorial,
        evidence_bundle=evidence_bundle,
        stellarium_script=stellarium_script,
        reviews=reviews,
    )

    local_status: LocalCapabilityStatus = "not_supplied"
    if local_capability_evidence is not None:
        local_status = _validate_local_capability(
            evidence=local_capability_evidence,
            stellarium_script=stellarium_script,
            preview_command=preview_command,
            preview_capability=preview_capability,
        )

    members: dict[str, bytes] = {
        "astronomy-event.json": canonical_contract_bytes(event),
        "rule-assessment.json": canonical_contract_bytes(assessment),
        "evidence-bundle.json": canonical_evidence_bundle_bytes(evidence_bundle),
        "video-package.json": canonical_contract_bytes(editorial.video_package),
        "editorial-package.json": canonical_editorial_bytes(editorial),
        "scene.ssc": canonical_stellarium_bytes(stellarium_script),
        "subtitles.srt": canonical_srt_bytes(subtitle),
        "preview-command.json": canonical_preview_command_bytes(preview_command),
        "review-bundle.json": _canonical_model_bytes(reviews),
        "review-gate.json": _canonical_model_bytes(review_gate),
    }
    if local_capability_evidence is not None:
        members["local-capability-evidence.json"] = canonical_capability_evidence_bytes(
            local_capability_evidence
        )

    package_id = editorial.video_package.package_id
    manifest = build_package_manifest(package_id=package_id, members=members)
    verify_package_members(manifest, members)
    return VerticalPackageBuild(
        package_id=package_id,
        manifest=manifest,
        members=members,
        subtitle=subtitle,
        preview_command=preview_command,
        review_gate=review_gate,
        local_capability_status=local_status,
        local_capability_evidence=local_capability_evidence,
    )


def publish_vertical_package(
    *,
    output_dir: str | Path,
    build: VerticalPackageBuild,
) -> Path:
    verify_package_members(build.manifest, build.members)
    if build.manifest.package_id != build.package_id:
        raise ValueError("vertical package manifest identity does not match build")
    return write_package_atomic(
        output_dir=output_dir,
        manifest=build.manifest,
        members=build.members,
    )


__all__ = [
    "LocalCapabilityStatus",
    "VerticalPackageBuild",
    "assemble_vertical_package",
    "publish_vertical_package",
]
