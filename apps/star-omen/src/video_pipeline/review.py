from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Literal, Sequence

from pydantic import Field, field_validator, model_validator

from src.video_pipeline.contracts import (
    AstronomyEventV1,
    RuleAssessmentV1,
    canonical_contract_bytes,
)
from src.video_pipeline.contracts._common import StableId, StrictContractModel, ensure_unique
from src.video_pipeline.editorial import EditorialPackageV1, canonical_editorial_bytes
from src.video_pipeline.evidence_bundle import (
    EvidenceBundleV1,
    canonical_evidence_bundle_bytes,
)
from src.video_pipeline.stellarium import StellariumScriptV1

ReviewDimension = Literal["astronomy", "classical_evidence", "editorial", "render"]
ReviewDecision = Literal["approved", "rejected", "needs_revision"]
_REQUIRED_DIMENSIONS: tuple[ReviewDimension, ...] = (
    "astronomy",
    "classical_evidence",
    "editorial",
    "render",
)


class ReviewRecordV1(StrictContractModel):
    schema_version: Literal["review-record/v1"] = "review-record/v1"
    dimension: ReviewDimension
    reviewer_role: StableId
    decision: ReviewDecision
    reviewed_at: datetime
    reason: str = Field(min_length=1, max_length=1200)
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("reviewed_at")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("review timestamp must be explicit UTC")
        if value.utcoffset() != timedelta(0):
            raise ValueError("review timestamp must be expressed in UTC")
        return value.astimezone(timezone.utc)


class ReviewBundleV1(StrictContractModel):
    schema_version: Literal["review-bundle/v1"] = "review-bundle/v1"
    package_id: StableId
    records: list[ReviewRecordV1]

    @model_validator(mode="after")
    def validate_dimensions(self) -> "ReviewBundleV1":
        dimensions = [record.dimension for record in self.records]
        ensure_unique(dimensions, "review dimensions")
        if set(dimensions) != set(_REQUIRED_DIMENSIONS):
            raise ValueError("review bundle requires exactly one record per dimension")
        ordered = sorted(
            self.records,
            key=lambda record: _REQUIRED_DIMENSIONS.index(record.dimension),
        )
        if ordered != self.records:
            raise ValueError("review records must use canonical dimension order")
        return self


class ReviewGateResultV1(StrictContractModel):
    schema_version: Literal["review-gate-result/v1"] = "review-gate-result/v1"
    package_id: StableId
    status: Literal["previewable", "blocked"]
    classical_publishable: bool
    missing_dimensions: list[ReviewDimension]
    blocking_reasons: list[str]

    @model_validator(mode="after")
    def validate_gate(self) -> "ReviewGateResultV1":
        if self.status == "previewable" and (
            self.missing_dimensions or self.blocking_reasons
        ):
            raise ValueError("previewable gate cannot have blockers")
        if self.status == "blocked" and not (
            self.missing_dimensions or self.blocking_reasons
        ):
            raise ValueError("blocked gate requires a blocking reason")
        if self.classical_publishable and self.status != "previewable":
            raise ValueError("classical publishability requires a previewable package")
        return self


def build_review_bundle(
    *,
    package_id: str,
    records: Sequence[ReviewRecordV1],
) -> ReviewBundleV1:
    by_dimension = {record.dimension: record for record in records}
    if len(by_dimension) != len(records):
        raise ValueError("review dimensions must be unique")
    if set(by_dimension) != set(_REQUIRED_DIMENSIONS):
        raise ValueError("review bundle requires all four dimensions")
    return ReviewBundleV1(
        package_id=package_id,
        records=[by_dimension[dimension] for dimension in _REQUIRED_DIMENSIONS],
    )


def expected_review_artifact_hashes(
    *,
    astronomy_event: AstronomyEventV1,
    assessment: RuleAssessmentV1,
    evidence_bundle: EvidenceBundleV1,
    editorial: EditorialPackageV1,
    stellarium_script: StellariumScriptV1,
) -> dict[ReviewDimension, str]:
    event = AstronomyEventV1.model_validate(astronomy_event.model_dump(mode="json"))
    assessment_model = RuleAssessmentV1.model_validate(
        assessment.model_dump(mode="json")
    )
    evidence = EvidenceBundleV1.model_validate(
        evidence_bundle.model_dump(mode="json")
    )
    editorial_package = EditorialPackageV1.model_validate(
        editorial.model_dump(mode="json")
    )
    script = StellariumScriptV1.model_validate(
        stellarium_script.model_dump(mode="json")
    )
    classical_payload = {
        "assessment": assessment_model.model_dump(mode="json", exclude_none=False),
        "evidence_bundle": evidence.model_dump(mode="json", exclude_none=False),
    }
    return {
        "astronomy": hashlib.sha256(canonical_contract_bytes(event)).hexdigest(),
        "classical_evidence": hashlib.sha256(
            canonical_contract_bytes(classical_payload)
        ).hexdigest(),
        "editorial": hashlib.sha256(
            canonical_editorial_bytes(editorial_package)
        ).hexdigest(),
        "render": script.sha256,
    }


def evaluate_review_gate(
    *,
    astronomy_event: AstronomyEventV1,
    assessment: RuleAssessmentV1,
    editorial: EditorialPackageV1,
    evidence_bundle: EvidenceBundleV1,
    stellarium_script: StellariumScriptV1,
    reviews: ReviewBundleV1,
) -> ReviewGateResultV1:
    astronomy_event = AstronomyEventV1.model_validate(
        astronomy_event.model_dump(mode="json")
    )
    assessment = RuleAssessmentV1.model_validate(assessment.model_dump(mode="json"))
    editorial = EditorialPackageV1.model_validate(editorial.model_dump(mode="json"))
    evidence_bundle = EvidenceBundleV1.model_validate(
        evidence_bundle.model_dump(mode="json")
    )
    stellarium_script = StellariumScriptV1.model_validate(
        stellarium_script.model_dump(mode="json")
    )
    reviews = ReviewBundleV1.model_validate(reviews.model_dump(mode="json"))

    package_id = editorial.video_package.package_id
    if reviews.package_id != package_id:
        raise ValueError("review bundle package does not match editorial package")
    if assessment.event_id != astronomy_event.event_id:
        raise ValueError("reviewed assessment does not match astronomy event")
    if assessment.assessment_id != editorial.video_package.assessment_id:
        raise ValueError("reviewed assessment does not match editorial package")
    if astronomy_event.event_id != editorial.video_package.event_id:
        raise ValueError("reviewed astronomy event does not match editorial package")
    if stellarium_script.event_id != astronomy_event.event_id:
        raise ValueError("reviewed script event does not match astronomy event")
    if stellarium_script.editorial_package_id != editorial.editorial_package_id:
        raise ValueError("reviewed script does not match editorial package")
    if evidence_bundle.event_id != astronomy_event.event_id:
        raise ValueError("evidence bundle event does not match astronomy event")
    if evidence_bundle.assessment_id != assessment.assessment_id:
        raise ValueError("evidence bundle assessment does not match assessment")
    if evidence_bundle.rule_set_version != assessment.rule_set_version:
        raise ValueError("evidence bundle rule set does not match assessment")

    expected_hashes = expected_review_artifact_hashes(
        astronomy_event=astronomy_event,
        assessment=assessment,
        evidence_bundle=evidence_bundle,
        editorial=editorial,
        stellarium_script=stellarium_script,
    )
    for record in reviews.records:
        if record.artifact_sha256 != expected_hashes[record.dimension]:
            raise ValueError(
                f"review artifact hash does not match {record.dimension} artifact"
            )

    blockers = [
        f"{record.dimension}: {record.decision}: {record.reason}"
        for record in reviews.records
        if record.decision != "approved"
    ]
    status: Literal["previewable", "blocked"] = (
        "blocked" if blockers else "previewable"
    )
    allowed_lineage = [
        entry for entry in evidence_bundle.entries if entry.narration_allowed
    ]
    classical_publishable = (
        status == "previewable"
        and editorial.classical_status == "included_citable"
        and len(allowed_lineage) == 1
    )
    return ReviewGateResultV1(
        package_id=package_id,
        status=status,
        classical_publishable=classical_publishable,
        missing_dimensions=[],
        blocking_reasons=blockers,
    )


__all__ = [
    "ReviewBundleV1",
    "ReviewDecision",
    "ReviewDimension",
    "ReviewGateResultV1",
    "ReviewRecordV1",
    "build_review_bundle",
    "evaluate_review_gate",
    "expected_review_artifact_hashes",
]
