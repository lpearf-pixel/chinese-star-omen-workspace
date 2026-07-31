from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal, Mapping, Sequence

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    model_validator,
)


Sha256Hex = Annotated[str, Field(strict=True, pattern=r"^[0-9a-f]{64}$")]
StableId = Annotated[
    str,
    Field(strict=True, min_length=1, max_length=160, pattern=r"^[a-z0-9][a-z0-9._:/-]{0,159}$"),
]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("datetime must be expressed in UTC")
    return value


UtcDateTime = Annotated[datetime, AfterValidator(_utc)]
Split = Literal["development", "validation", "holdout"]


class StrictCalibrationModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


def _unique(values: Sequence[str], field: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field} must contain unique values")


def _safe_relative(value: str) -> None:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError("manifest path must be safe and relative")


class GoldenLabelV1(StrictCalibrationModel):
    formal_candidate: bool
    citation_eligible: bool
    eligibility: Literal[
        "eligible",
        "no_candidate",
        "needs_review",
        "ambiguous",
        "duplicate",
        "conflict",
    ]

    @model_validator(mode="after")
    def validate_label(self) -> "GoldenLabelV1":
        if self.citation_eligible and not self.formal_candidate:
            raise ValueError("citation eligibility requires a formal candidate")
        return self


class GoldenCaseV1(StrictCalibrationModel):
    schema_version: Literal["golden-case/v1"]
    case_id: StableId
    passage_id: StableId
    source_fingerprint: Sha256Hex
    split: Split
    volume: str = Field(min_length=1, max_length=80)
    celestial_categories: list[StableId] = Field(min_length=1)
    relation_terms: list[str] = Field(min_length=1)
    sentence_complexity: Literal["simple", "compound", "cross_passage"]
    computability: Literal[
        "computable", "partially_computable", "not_computable", "unknown"
    ]
    evidence_risk: Literal["low", "medium", "high"]
    reviewer_ids: list[StableId] = Field(min_length=2)
    annotation_guide_version: StableId
    expected_label: GoldenLabelV1 | None = None

    @model_validator(mode="after")
    def validate_split(self) -> "GoldenCaseV1":
        _unique(self.celestial_categories, "celestial_categories")
        _unique(self.relation_terms, "relation_terms")
        _unique(self.reviewer_ids, "reviewer_ids")
        if self.split == "holdout" and self.expected_label is not None:
            raise ValueError("holdout expected_label must live in the sealed label asset")
        if self.split != "holdout" and self.expected_label is None:
            raise ValueError("development/validation expected_label is required")
        return self


class SealedGoldenLabelV1(StrictCalibrationModel):
    case_id: StableId
    expected_label: GoldenLabelV1
    reviewer_ids: list[StableId] = Field(min_length=2)
    annotation_guide_version: StableId

    @model_validator(mode="after")
    def validate_reviewers(self) -> "SealedGoldenLabelV1":
        _unique(self.reviewer_ids, "reviewer_ids")
        return self


class GoldenManifestEntryV1(StrictCalibrationModel):
    path: str = Field(min_length=1, max_length=512)
    sha256: Sha256Hex

    @model_validator(mode="after")
    def validate_path(self) -> "GoldenManifestEntryV1":
        _safe_relative(self.path)
        return self


class GoldenManifestV1(StrictCalibrationModel):
    schema_version: Literal["golden-manifest/v1"]
    split: Split
    annotation_guide_version: StableId
    cases: list[GoldenManifestEntryV1] = Field(min_length=1)
    sealed_labels_sha256: Sha256Hex | None = None

    @model_validator(mode="after")
    def validate_manifest(self) -> "GoldenManifestV1":
        paths = [entry.path for entry in self.cases]
        _unique(paths, "cases")
        if paths != sorted(paths):
            raise ValueError("manifest cases must be sorted by path")
        if self.split == "holdout" and self.sealed_labels_sha256 is None:
            raise ValueError("holdout manifest requires sealed_labels_sha256")
        if self.split != "holdout" and self.sealed_labels_sha256 is not None:
            raise ValueError("only holdout may bind sealed labels")
        return self


class CalibrationObservationV1(StrictCalibrationModel):
    case_id: StableId
    expected_formal_candidate: bool
    predicted_formal_candidate: bool
    expected_citation_eligible: bool
    predicted_citation_eligible: bool
    reviewers_agree: bool
    category: StableId


class CalibrationReportV1(StrictCalibrationModel):
    schema_version: Literal["calibration-report/v1"]
    split: Split
    manifest_sha256: Sha256Hex
    extractor_version: StableId
    pattern_version: StableId
    review_policy_version: StableId
    case_count: int = Field(strict=True, gt=0)
    true_positive: int = Field(strict=True, ge=0)
    false_positive: int = Field(strict=True, ge=0)
    false_negative: int = Field(strict=True, ge=0)
    true_negative: int = Field(strict=True, ge=0)
    precision: float = Field(ge=0, le=1, allow_inf_nan=False)
    recall: float = Field(ge=0, le=1, allow_inf_nan=False)
    review_agreement: float = Field(ge=0, le=1, allow_inf_nan=False)
    citable_false_positive_count: int = Field(strict=True, ge=0)
    category_case_counts: dict[StableId, int]

    @model_validator(mode="after")
    def validate_denominators(self) -> "CalibrationReportV1":
        if (
            self.true_positive
            + self.false_positive
            + self.false_negative
            + self.true_negative
            != self.case_count
        ):
            raise ValueError("confusion matrix must equal case_count")
        expected_precision = (
            self.true_positive / (self.true_positive + self.false_positive)
            if self.true_positive + self.false_positive
            else 0.0
        )
        expected_recall = (
            self.true_positive / (self.true_positive + self.false_negative)
            if self.true_positive + self.false_negative
            else 0.0
        )
        if abs(self.precision - expected_precision) > 1e-12:
            raise ValueError("precision must match confusion matrix")
        if abs(self.recall - expected_recall) > 1e-12:
            raise ValueError("recall must match confusion matrix")
        if sum(self.category_case_counts.values()) != self.case_count:
            raise ValueError("category denominators must equal case_count")
        return self


class ThresholdFreezeV1(StrictCalibrationModel):
    schema_version: Literal["threshold-freeze/v1"]
    freeze_id: StableId
    status: Literal["needs_human_approval", "approved"]
    created_at: UtcDateTime
    source_release_head: str = Field(pattern=r"^[0-9a-f]{40}$")
    annotation_guide_version: StableId
    development_manifest_sha256: Sha256Hex
    validation_manifest_sha256: Sha256Hex
    sealed_holdout_manifest_sha256: Sha256Hex
    extractor_version: StableId
    pattern_version: StableId
    review_policy_version: StableId
    formal_candidate_precision_min: float = Field(ge=0.9, le=1, allow_inf_nan=False)
    formal_candidate_recall_min: float = Field(ge=0, le=1, allow_inf_nan=False)
    category_thresholds: dict[StableId, float]
    review_agreement_min: float = Field(ge=0, le=1, allow_inf_nan=False)
    citable_false_positive_max: Literal[0]
    calibration_report_sha256: Sha256Hex
    approved_by: StableId | None
    decision_reference: StableId | None

    @model_validator(mode="after")
    def validate_approval(self) -> "ThresholdFreezeV1":
        if not self.category_thresholds:
            raise ValueError("category_thresholds cannot be empty")
        if any(
            isinstance(value, bool) or not 0 <= value <= 1
            for value in self.category_thresholds.values()
        ):
            raise ValueError("category thresholds must be finite values in [0, 1]")
        if self.status == "approved":
            if self.approved_by is None or self.decision_reference is None:
                raise ValueError("approved freeze requires approval and decision records")
            identity = self.approved_by.lower()
            terminal = identity.rsplit(":", 1)[-1]
            if terminal in {"pending", "unassigned", "codex", "model", "ai"}:
                raise ValueError("approved_by cannot be an automated or pending identity")
        elif self.approved_by is not None or self.decision_reference is not None:
            raise ValueError("pending freeze cannot claim approval records")
        return self


def canonical_calibration_bytes(value: BaseModel | Mapping[str, Any]) -> bytes:
    payload = (
        value.model_dump(mode="json", exclude_none=False)
        if isinstance(value, BaseModel)
        else dict(value)
    )
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required regular file missing: {path.name}")
    return path.read_bytes()


def _manifest_member(root: Path, relative: str) -> Path:
    candidate = root / relative
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"manifest member cannot traverse symlinks: {relative}")
    try:
        candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError(f"manifest member escapes its root: {relative}") from exc
    return candidate


def load_golden_manifest(
    manifest_path: Path,
) -> tuple[GoldenManifestV1, list[GoldenCaseV1]]:
    manifest = GoldenManifestV1.model_validate_json(_regular_file(manifest_path))
    cases: list[GoldenCaseV1] = []
    for entry in manifest.cases:
        path = _manifest_member(manifest_path.parent, entry.path)
        data = _regular_file(path)
        if _sha256(data) != entry.sha256:
            raise ValueError(f"case hash mismatch: {entry.path}")
        case = GoldenCaseV1.model_validate_json(data)
        if case.split != manifest.split:
            raise ValueError(f"case split mismatch: {entry.path}")
        if case.annotation_guide_version != manifest.annotation_guide_version:
            raise ValueError(f"annotation guide mismatch: {entry.path}")
        cases.append(case)
    case_ids = [case.case_id for case in cases]
    _unique(case_ids, "case IDs")
    return manifest, cases


def load_sealed_holdout_labels(
    path: Path,
    *,
    expected_sha256: str,
    expected_case_ids: Sequence[str],
    annotation_guide_version: str,
    release_gate: bool = False,
) -> list[SealedGoldenLabelV1]:
    if not release_gate:
        raise PermissionError("sealed holdout labels require an explicit release gate")
    data = _regular_file(path)
    if _sha256(data) != expected_sha256:
        raise ValueError("sealed holdout label hash mismatch")
    labels = TypeAdapter(list[SealedGoldenLabelV1]).validate_json(data)
    case_ids = [label.case_id for label in labels]
    _unique(case_ids, "sealed case IDs")
    if sorted(case_ids) != sorted(expected_case_ids):
        raise ValueError("sealed label case IDs do not match holdout manifest")
    if any(
        label.annotation_guide_version != annotation_guide_version
        for label in labels
    ):
        raise ValueError("sealed label annotation guide mismatch")
    return labels


def validate_disjoint_splits(
    cases_by_split: Mapping[Split, Sequence[GoldenCaseV1]],
) -> None:
    owners: dict[str, str] = {}
    for split in ("development", "validation", "holdout"):
        for case in cases_by_split.get(split, ()):
            if case.split != split:
                raise ValueError(f"case split mismatch in {split}")
            previous = owners.setdefault(case.case_id, split)
            if previous != split:
                raise ValueError(
                    f"golden split overlap: {case.case_id} is in {previous} and {split}"
                )


def build_calibration_report(
    *,
    observations: Sequence[CalibrationObservationV1],
    split: Split,
    manifest_sha256: str,
    extractor_version: str,
    pattern_version: str,
    review_policy_version: str,
) -> CalibrationReportV1:
    if not observations:
        raise ValueError("calibration observations cannot be empty")
    case_ids = [item.case_id for item in observations]
    _unique(case_ids, "observation case IDs")
    tp = sum(o.expected_formal_candidate and o.predicted_formal_candidate for o in observations)
    fp = sum(not o.expected_formal_candidate and o.predicted_formal_candidate for o in observations)
    fn = sum(o.expected_formal_candidate and not o.predicted_formal_candidate for o in observations)
    tn = len(observations) - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    agreement = sum(o.reviewers_agree for o in observations) / len(observations)
    citable_fp = sum(
        not o.expected_citation_eligible and o.predicted_citation_eligible
        for o in observations
    )
    category_counts: dict[str, int] = {}
    for observation in observations:
        category_counts[observation.category] = category_counts.get(observation.category, 0) + 1
    return CalibrationReportV1(
        schema_version="calibration-report/v1",
        split=split,
        manifest_sha256=manifest_sha256,
        extractor_version=extractor_version,
        pattern_version=pattern_version,
        review_policy_version=review_policy_version,
        case_count=len(observations),
        true_positive=tp,
        false_positive=fp,
        false_negative=fn,
        true_negative=tn,
        precision=precision,
        recall=recall,
        review_agreement=agreement,
        citable_false_positive_count=citable_fp,
        category_case_counts=dict(sorted(category_counts.items())),
    )


def build_threshold_freeze(
    *,
    report: CalibrationReportV1,
    source_release_head: str,
    annotation_guide_version: str,
    development_manifest_sha256: str,
    validation_manifest_sha256: str,
    sealed_holdout_manifest_sha256: str,
    formal_candidate_precision_min: float,
    formal_candidate_recall_min: float,
    review_agreement_min: float,
    category_thresholds: Mapping[str, float],
    created_at: datetime,
    approved_by: str | None,
    decision_reference: str | None,
) -> ThresholdFreezeV1:
    report = CalibrationReportV1.model_validate(report.model_dump(mode="json"))
    if (approved_by is None) != (decision_reference is None):
        raise ValueError("approval identity and decision reference must be supplied together")
    passes = (
        report.split == "validation"
        and report.precision >= formal_candidate_precision_min
        and report.recall >= formal_candidate_recall_min
        and report.review_agreement >= review_agreement_min
        and report.citable_false_positive_count == 0
    )
    if approved_by is not None and not passes:
        raise ValueError("cannot approve a threshold freeze whose metrics do not pass")
    approved = passes and approved_by is not None and decision_reference is not None
    seed = {
        "report_sha256": _sha256(canonical_calibration_bytes(report)),
        "source_release_head": source_release_head,
        "thresholds": dict(sorted(category_thresholds.items())),
        "precision_min": formal_candidate_precision_min,
        "recall_min": formal_candidate_recall_min,
        "agreement_min": review_agreement_min,
    }
    freeze_id = f"threshold-freeze:{_sha256(canonical_calibration_bytes(seed))[:32]}"
    return ThresholdFreezeV1(
        schema_version="threshold-freeze/v1",
        freeze_id=freeze_id,
        status="approved" if approved else "needs_human_approval",
        created_at=created_at,
        source_release_head=source_release_head,
        annotation_guide_version=annotation_guide_version,
        development_manifest_sha256=development_manifest_sha256,
        validation_manifest_sha256=validation_manifest_sha256,
        sealed_holdout_manifest_sha256=sealed_holdout_manifest_sha256,
        extractor_version=report.extractor_version,
        pattern_version=report.pattern_version,
        review_policy_version=report.review_policy_version,
        formal_candidate_precision_min=formal_candidate_precision_min,
        formal_candidate_recall_min=formal_candidate_recall_min,
        category_thresholds=dict(sorted(category_thresholds.items())),
        review_agreement_min=review_agreement_min,
        citable_false_positive_max=0,
        calibration_report_sha256=_sha256(canonical_calibration_bytes(report)),
        approved_by=approved_by if approved else None,
        decision_reference=decision_reference if approved else None,
    )


def publish_no_overwrite(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


__all__ = [
    "CalibrationObservationV1",
    "CalibrationReportV1",
    "GoldenCaseV1",
    "GoldenLabelV1",
    "GoldenManifestEntryV1",
    "GoldenManifestV1",
    "SealedGoldenLabelV1",
    "ThresholdFreezeV1",
    "build_calibration_report",
    "build_threshold_freeze",
    "canonical_calibration_bytes",
    "load_golden_manifest",
    "load_sealed_holdout_labels",
    "publish_no_overwrite",
    "validate_disjoint_splits",
]
