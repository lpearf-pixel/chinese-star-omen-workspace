from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.video_pipeline.rule_assessment import (
    build_rule_assessment,
    build_rule_assessment_result,
    event_to_matcher_input,
    project_matcher_result,
)
from tests.video_pipeline.rule_assessment.helpers import (
    RAW_PASSAGE,
    matching_rule,
    valid_event,
    write_citable_source,
)


def test_event_projection_is_explicit_and_deterministic() -> None:
    event = valid_event()

    projected = event_to_matcher_input(event)

    assert projected == {
        "id": event.event_id,
        "datetime_utc": event.peak_utc.isoformat().replace("+00:00", "Z"),
        "body": "mars",
        "event_type": "guarding",
        "target_asterism": "xin_xiu",
        "related_asterisms": ["xin_xiu"],
        "angular_distance_deg": 0.8,
        "duration_days": 4.0,
        "visibility": {"is_visible": True},
    }


def test_citable_selected_rule_projects_to_eligible_assessment(tmp_path: Path) -> None:
    evidence = write_citable_source(tmp_path)
    rule = matching_rule(evidence)

    result = build_rule_assessment_result(
        event=valid_event(),
        rules=[rule],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
    )
    assessment = result.assessment

    assert assessment.schema_version == "rule-assessment/v1"
    assert assessment.event_id == "event:test:mars-guarding-xin"
    assert assessment.rule_set_version == "rules:test-v1"
    assert assessment.match_status == "matched"
    assert assessment.recommended_rule_id == rule["id"]
    assert assessment.provisional_rule_id is None
    assert assessment.narration_eligibility == "eligible"
    assert assessment.condition_states == {
        "angular_distance": "pass",
        "body": "pass",
        "duration": "pass",
        "event_type": "pass",
        "target": "pass",
        "visibility": "pass",
    }
    assert [(item.rule_id, item.status) for item in assessment.matched_rules] == [
        (rule["id"], "matched")
    ]
    assert len(assessment.evidence_references) == 1
    reference = assessment.evidence_references[0]
    assert reference.status == "citable"
    assert reference.source_locator == "KR3g0018_031"
    assert len(reference.content_hash or "") == 64

    bundle = result.evidence_bundle
    assert bundle.assessment_id == assessment.assessment_id
    assert len(bundle.entries) == 1
    lineage = bundle.entries[0]
    assert lineage.rule_id == rule["id"]
    assert lineage.evidence_id == reference.evidence_id
    assert lineage.claim_class == "classical_quote"
    assert lineage.narration_allowed is True
    assert lineage.blocking_reasons == []
    serialized = bundle.canonical_bytes()
    assert RAW_PASSAGE.encode("utf-8") not in serialized
    assert str(tmp_path.resolve()).encode("utf-8") not in serialized


def test_build_rule_assessment_returns_only_frozen_public_contract(tmp_path: Path) -> None:
    rule = matching_rule(write_citable_source(tmp_path))

    assessment = build_rule_assessment(
        event=valid_event(),
        rules=[rule],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
    )

    assert assessment.__class__.__name__ == "RuleAssessmentV1"
    payload = assessment.model_dump(mode="json")
    assert set(payload) == {
        "schema_version",
        "assessment_id",
        "event_id",
        "rule_set_version",
        "matched_rules",
        "condition_states",
        "match_status",
        "conflict_summary",
        "recommended_rule_id",
        "provisional_rule_id",
        "evidence_references",
        "narration_eligibility",
        "uncertainty_reasons",
    }
    assert "trigger_match_reason" not in payload
    assert "thresholds_used" not in payload
    assert "effect_domain" not in payload


def test_candidate_only_rule_is_blocked_and_only_provisional(tmp_path: Path) -> None:
    evidence = write_citable_source(tmp_path)
    evidence.pop("content_hash")
    evidence.pop("raw_content_hash")
    evidence.pop("normalized_content_hash")
    rule = matching_rule(evidence)

    assessment = build_rule_assessment(
        event=valid_event(),
        rules=[rule],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
    )

    assert assessment.match_status == "candidate_only"
    assert assessment.recommended_rule_id is None
    assert assessment.provisional_rule_id == rule["id"]
    assert assessment.narration_eligibility == "blocked"
    assert assessment.evidence_references[0].status == "candidate_only"
    assert "evidence:candidate_only" in assessment.uncertainty_reasons


def test_missing_rule_evidence_is_missing_and_blocked(tmp_path: Path) -> None:
    rule = matching_rule(None)

    result = build_rule_assessment_result(
        event=valid_event(),
        rules=[rule],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
    )

    assert result.assessment.match_status == "candidate_only"
    assert result.assessment.narration_eligibility == "blocked"
    assert result.assessment.evidence_references[0].status == "missing_evidence"
    assert result.evidence_bundle.entries[0].blocking_reasons == ["missing_evidence"]


def test_missing_measurements_project_insufficient_data(tmp_path: Path) -> None:
    event_payload = valid_event().model_dump(mode="json")
    event_payload["measurements"] = []
    event_payload["quality_status"] = "insufficient_data"
    event_payload["uncertainty_reasons"] = ["measurement-window-not-available"]
    event = valid_event().__class__.model_validate(event_payload)
    rule = matching_rule(write_citable_source(tmp_path))

    assessment = build_rule_assessment(
        event=event,
        rules=[rule],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
    )

    assert assessment.match_status == "insufficient_data"
    assert assessment.recommended_rule_id is None
    assert assessment.provisional_rule_id == rule["id"]
    assert assessment.narration_eligibility == "blocked"
    assert assessment.condition_states["angular_distance"] == "unknown"
    assert assessment.condition_states["duration"] == "unknown"
    assert "condition:angular_distance:unknown" in assessment.uncertainty_reasons


def test_manual_review_conflict_withholds_formal_recommendation(tmp_path: Path) -> None:
    evidence = write_citable_source(tmp_path)
    first = matching_rule(evidence)
    first["id"] = "rule:mars-guarding-xin:a"
    first["conflict_group"] = "group:mars-xin"
    first["resolution_policy"] = "manual_review"
    second = deepcopy(first)
    second["id"] = "rule:mars-guarding-xin:b"
    second["rule_priority"] = 20

    assessment = build_rule_assessment(
        event=valid_event(),
        rules=[first, second],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
    )

    assert assessment.match_status == "matched"
    assert assessment.recommended_rule_id is None
    assert assessment.provisional_rule_id == first["id"]
    assert assessment.narration_eligibility == "blocked"
    assert any("manual_review" in item for item in assessment.conflict_summary)
    assert "conflict:manual_review" in assessment.uncertainty_reasons


def test_internal_matcher_field_drift_does_not_change_public_projection(tmp_path: Path) -> None:
    rule = matching_rule(write_citable_source(tmp_path))
    base = build_rule_assessment_result(
        event=valid_event(),
        rules=[rule],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
    )
    internal = deepcopy(base.matcher_result)
    internal["new_internal_debug"] = {"anything": [1, 2, 3]}
    internal["matches"][0]["new_internal_rule_field"] = "ignored"

    projected = project_matcher_result(
        event=valid_event(),
        rule_set_version="rules:test-v1",
        matcher_result=internal,
        evidence_records=base.evidence_records,
        retrieval_reports=base.retrieval_reports,
    )

    assert projected.assessment == base.assessment
    assert projected.evidence_bundle == base.evidence_bundle


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.update(event_id="event:other"),
        lambda payload: payload.update(match_status="unknown-status"),
        lambda payload: payload["matches"].append(deepcopy(payload["matches"][0])),
    ],
)
def test_malformed_matcher_result_fails_closed(tmp_path: Path, mutation) -> None:
    rule = matching_rule(write_citable_source(tmp_path))
    base = build_rule_assessment_result(
        event=valid_event(),
        rules=[rule],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
    )
    malformed = deepcopy(base.matcher_result)
    mutation(malformed)

    with pytest.raises((ValueError, ValidationError)):
        project_matcher_result(
            event=valid_event(),
            rule_set_version="rules:test-v1",
            matcher_result=malformed,
            evidence_records=base.evidence_records,
            retrieval_reports=base.retrieval_reports,
        )
