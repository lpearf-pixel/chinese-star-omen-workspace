from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.rule_structuring.calibration import (
    CalibrationObservationV1,
    GoldenCaseV1,
    GoldenLabelV1,
    GoldenManifestEntryV1,
    GoldenManifestV1,
    ReviewerSlotV1,
    SealedGoldenLabelV1,
    ThresholdFreezeV1,
    build_calibration_report,
    build_threshold_freeze,
    canonical_calibration_bytes,
    load_golden_manifest,
    load_sealed_holdout_labels,
    issue_anonymous_reviewer_slots,
    publish_no_overwrite,
    validate_disjoint_splits,
    validate_reviewer_slots,
)


SHA = "a" * 64


def _label(*, formal: bool = True, citable: bool = True) -> GoldenLabelV1:
    return GoldenLabelV1(
        formal_candidate=formal,
        citation_eligible=citable,
        eligibility="eligible" if formal else "no_candidate",
    )


def _case(split: str = "development", label: GoldenLabelV1 | None = None) -> GoldenCaseV1:
    return GoldenCaseV1(
        schema_version="golden-case/v1",
        case_id=f"golden:{split}:001",
        passage_id="passage:kaiyuan:031:0001",
        source_fingerprint=SHA,
        split=split,
        volume="031",
        celestial_categories=["five_planets"],
        relation_terms=["守"],
        sentence_complexity="simple",
        computability="partially_computable",
        evidence_risk="medium",
        reviewer_ids=["reviewer:alice", "reviewer:bob"],
        annotation_guide_version="kaiyuan-rule-annotation/v1",
        expected_label=label,
    )


def test_cases_are_strict_and_holdout_labels_are_sealed() -> None:
    assert _case(label=_label()).expected_label is not None
    with pytest.raises(ValidationError, match="holdout"):
        _case("holdout", _label())
    with pytest.raises(ValidationError, match="expected_label"):
        _case("validation", None)
    with pytest.raises(ValidationError):
        GoldenCaseV1.model_validate(
            {**_case(label=_label()).model_dump(mode="json"), "unknown": True}
        )


def test_project_issues_stable_anonymous_reviewer_slots_without_external_ids() -> None:
    pilot_id = "pilot:kaiyuan-b10-pr-c-v1"
    first = issue_anonymous_reviewer_slots(pilot_id)
    second = issue_anonymous_reviewer_slots(pilot_id)

    assert first == second
    assert [slot.slot for slot in first] == ["reviewer_a", "reviewer_b"]
    assert len({slot.reviewer_id for slot in first}) == 2
    assert all(slot.reviewer_id.startswith("reviewer:anon:") for slot in first)
    assert all(slot.pilot_id == pilot_id for slot in first)
    assert all(slot.external_account_required is False for slot in first)
    assert all(slot.human_review_completed is False for slot in first)
    assert canonical_calibration_bytes(
        {"slots": [slot.model_dump(mode="json") for slot in first]}
    ) == canonical_calibration_bytes(
        {"slots": [slot.model_dump(mode="json") for slot in second]}
    )

    validate_reviewer_slots(
        pilot_id=pilot_id,
        reviewer_ids=[slot.reviewer_id for slot in first],
        slots=first,
    )
    with pytest.raises(ValueError, match="pilot"):
        validate_reviewer_slots(
            pilot_id="pilot:other",
            reviewer_ids=[slot.reviewer_id for slot in first],
            slots=first,
        )
    with pytest.raises(ValueError, match="exactly two distinct"):
        validate_reviewer_slots(
            pilot_id=pilot_id,
            reviewer_ids=[first[0].reviewer_id, first[0].reviewer_id],
            slots=first,
        )
    with pytest.raises(ValidationError):
        ReviewerSlotV1.model_validate(
            {
                **first[0].model_dump(mode="json"),
                "human_review_completed": True,
            }
        )


def test_pilot_reviewer_slot_manifest_is_canonical_and_unreviewed() -> None:
    path = (
        Path(__file__).resolve().parents[4]
        / "eval/rules/v2/manifests/reviewer-slots.json"
    )
    data = path.read_bytes()
    payload = json.loads(data)
    slots = [ReviewerSlotV1.model_validate(item) for item in payload["slots"]]

    assert payload["schema_version"] == "reviewer-slot-set/v1"
    assert slots == list(issue_anonymous_reviewer_slots(payload["pilot_id"]))
    assert data == canonical_calibration_bytes(payload)
    assert all(slot.human_review_completed is False for slot in slots)


def test_manifest_verifies_case_hash_and_split(tmp_path: Path) -> None:
    case = _case(label=_label())
    case_path = tmp_path / "case.json"
    case_path.write_bytes(canonical_calibration_bytes(case))
    digest = hashlib.sha256(case_path.read_bytes()).hexdigest()
    manifest = GoldenManifestV1(
        schema_version="golden-manifest/v1",
        split="development",
        annotation_guide_version="kaiyuan-rule-annotation/v1",
        cases=[GoldenManifestEntryV1(path="case.json", sha256=digest)],
        sealed_labels_sha256=None,
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(canonical_calibration_bytes(manifest))

    loaded, cases = load_golden_manifest(manifest_path)
    assert loaded == manifest and cases == [case]
    case_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        load_golden_manifest(manifest_path)


def test_manifest_rejects_symlinked_member_directory(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    case = _case(label=_label())
    case_path = outside / "case.json"
    case_path.write_bytes(canonical_calibration_bytes(case))
    (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    manifest = GoldenManifestV1(
        schema_version="golden-manifest/v1",
        split="development",
        annotation_guide_version="kaiyuan-rule-annotation/v1",
        cases=[
            GoldenManifestEntryV1(
                path="linked/case.json",
                sha256=hashlib.sha256(case_path.read_bytes()).hexdigest(),
            )
        ],
        sealed_labels_sha256=None,
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(canonical_calibration_bytes(manifest))
    with pytest.raises(ValueError, match="symlink"):
        load_golden_manifest(manifest_path)


def test_holdout_labels_require_explicit_release_gate(tmp_path: Path) -> None:
    labels = [
        SealedGoldenLabelV1(
            case_id="golden:holdout:001",
            expected_label=_label(),
            reviewer_ids=["reviewer:alice", "reviewer:bob"],
            annotation_guide_version="kaiyuan-rule-annotation/v1",
        )
    ]
    path = tmp_path / "sealed-labels.json"
    path.write_text(
        json.dumps([item.model_dump(mode="json") for item in labels]),
        encoding="utf-8",
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(PermissionError, match="release gate"):
        load_sealed_holdout_labels(
            path,
            expected_sha256=digest,
            expected_case_ids=["golden:holdout:001"],
            annotation_guide_version="kaiyuan-rule-annotation/v1",
        )
    assert load_sealed_holdout_labels(
        path,
        expected_sha256=digest,
        expected_case_ids=["golden:holdout:001"],
        annotation_guide_version="kaiyuan-rule-annotation/v1",
        release_gate=True,
    ) == labels
    with pytest.raises(ValueError, match="hash"):
        load_sealed_holdout_labels(
            path,
            expected_sha256="b" * 64,
            expected_case_ids=["golden:holdout:001"],
            annotation_guide_version="kaiyuan-rule-annotation/v1",
            release_gate=True,
        )


def test_split_case_ids_must_be_disjoint() -> None:
    development = [_case(label=_label())]
    validation = [
        _case("validation", _label()).model_copy(
            update={"case_id": development[0].case_id}
        )
    ]
    with pytest.raises(ValueError, match="split overlap"):
        validate_disjoint_splits(
            {
                "development": development,
                "validation": validation,
                "holdout": [],
            }
        )


def test_calibration_report_preserves_denominators_and_false_positives() -> None:
    observations = [
        CalibrationObservationV1(
            case_id=f"golden:validation:{index:03d}",
            expected_formal_candidate=expected,
            predicted_formal_candidate=predicted,
            expected_citation_eligible=citable,
            predicted_citation_eligible=predicted_citable,
            reviewers_agree=agree,
            category="five_planets",
        )
        for index, (expected, predicted, citable, predicted_citable, agree) in enumerate(
            [
                (True, True, True, True, True),
                (True, False, True, False, False),
                (False, True, False, True, True),
                (False, False, False, False, True),
            ],
            start=1,
        )
    ]
    report = build_calibration_report(
        observations=observations,
        split="validation",
        manifest_sha256=SHA,
        extractor_version="deterministic/v1",
        pattern_version="patterns/v1",
        review_policy_version="review/v1",
    )
    assert (report.true_positive, report.false_positive, report.false_negative) == (1, 1, 1)
    assert report.precision == 0.5
    assert report.recall == 0.5
    assert report.citable_false_positive_count == 1
    assert report.review_agreement == 0.75
    with pytest.raises(ValidationError, match="confusion matrix"):
        report.model_copy(update={"true_positive": 99}).model_validate(
            {**report.model_dump(mode="json"), "true_positive": 99}
        )


def test_freeze_cannot_approve_without_passing_metrics_and_human_record() -> None:
    passing = build_calibration_report(
        observations=[
            CalibrationObservationV1(
                case_id=f"golden:validation:{index:03d}",
                expected_formal_candidate=True,
                predicted_formal_candidate=True,
                expected_citation_eligible=True,
                predicted_citation_eligible=True,
                reviewers_agree=True,
                category="five_planets",
            )
            for index in range(1, 11)
        ],
        split="validation",
        manifest_sha256=SHA,
        extractor_version="deterministic/v1",
        pattern_version="patterns/v1",
        review_policy_version="review/v1",
    )
    pending = build_threshold_freeze(
        report=passing,
        source_release_head="1" * 40,
        annotation_guide_version="kaiyuan-rule-annotation/v1",
        development_manifest_sha256=SHA,
        validation_manifest_sha256=SHA,
        sealed_holdout_manifest_sha256=SHA,
        formal_candidate_precision_min=0.9,
        formal_candidate_recall_min=0.8,
        review_agreement_min=0.8,
        category_thresholds={"five_planets": 0.9},
        created_at=datetime(2026, 7, 30, tzinfo=timezone.utc),
        approved_by=None,
        decision_reference=None,
    )
    assert pending.status == "needs_human_approval"
    approved = build_threshold_freeze(
        report=passing,
        source_release_head="1" * 40,
        annotation_guide_version="kaiyuan-rule-annotation/v1",
        development_manifest_sha256=SHA,
        validation_manifest_sha256=SHA,
        sealed_holdout_manifest_sha256=SHA,
        formal_candidate_precision_min=0.9,
        formal_candidate_recall_min=0.8,
        review_agreement_min=0.8,
        category_thresholds={"five_planets": 0.9},
        created_at=datetime(2026, 7, 30, tzinfo=timezone.utc),
        approved_by="reviewer:principal",
        decision_reference="decision:b10-pr-c-pilot",
    )
    assert approved.status == "approved"
    assert approved.citable_false_positive_max == 0
    with pytest.raises(ValidationError):
        ThresholdFreezeV1.model_validate(
            {
                **approved.model_dump(mode="json"),
                "formal_candidate_precision_min": 0.89,
            }
        )
    failing = passing.model_copy(update={"false_positive": 1, "true_negative": -1})
    with pytest.raises((ValidationError, ValueError)):
        build_threshold_freeze(
            report=failing,
            source_release_head="1" * 40,
            annotation_guide_version="kaiyuan-rule-annotation/v1",
            development_manifest_sha256=SHA,
            validation_manifest_sha256=SHA,
            sealed_holdout_manifest_sha256=SHA,
            formal_candidate_precision_min=0.9,
            formal_candidate_recall_min=0.8,
            review_agreement_min=0.8,
            category_thresholds={"five_planets": 0.9},
            created_at=datetime(2026, 7, 30, tzinfo=timezone.utc),
            approved_by="reviewer:principal",
            decision_reference="decision:b10-pr-c-pilot",
        )


def test_publish_is_canonical_and_no_overwrite(tmp_path: Path) -> None:
    case = _case(label=_label())
    target = tmp_path / "case.json"
    publish_no_overwrite(target, canonical_calibration_bytes(case))
    assert target.read_bytes() == canonical_calibration_bytes(case)
    with pytest.raises(FileExistsError):
        publish_no_overwrite(target, canonical_calibration_bytes(case))
