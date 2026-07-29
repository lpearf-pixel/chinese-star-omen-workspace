from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from src.video_pipeline.rule_assessment import build_rule_assessment_result
from tests.video_pipeline.rule_assessment.helpers import (
    RAW_PASSAGE,
    FakeRetriever,
    matching_rule,
    primary_hit,
    valid_event,
    write_citable_source,
)


def test_non_matching_rule_does_not_call_retriever_or_affect_uncertainty(
    tmp_path: Path,
) -> None:
    evidence = write_citable_source(tmp_path)
    matching = matching_rule(evidence)
    unrelated = matching_rule(None)
    unrelated["id"] = "rule:venus-conjunction-test-v1"
    unrelated["source_text"] = "太白合辰星"
    unrelated["trigger"] = {
        "body": "venus",
        "event_type": "conjunction",
        "target": "mercury",
    }
    retriever = FakeRetriever(error=AssertionError("unrelated rule must not retrieve"))

    result = build_rule_assessment_result(
        event=valid_event(),
        rules=[matching, unrelated],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
        retriever=retriever,
    )

    assert retriever.calls == []
    assert [item.rule_id for item in result.assessment.matched_rules] == [matching["id"]]
    assert [item.rule_id for item in result.retrieval_reports] == [matching["id"]]
    assert result.assessment.uncertainty_reasons == []


def test_only_core_candidate_rules_are_hydrated(tmp_path: Path) -> None:
    evidence = write_citable_source(tmp_path)
    primary = primary_hit(evidence)
    candidate = matching_rule(None)
    unrelated = matching_rule(None)
    unrelated["id"] = "rule:venus-conjunction-test-v1"
    unrelated["source_text"] = "太白合辰星"
    unrelated["trigger"] = {
        "body": "venus",
        "event_type": "conjunction",
        "target": "mercury",
    }
    retriever = FakeRetriever(
        {
            "stage1": {"hits": []},
            "stage2": {
                "primary_candidates": [primary],
                "exact_hits": [primary],
                "candidate_overlay_hits": [],
                "structured_fallbacks": [],
                "official_primary_used": True,
                "fallback_used": False,
            },
        }
    )

    result = build_rule_assessment_result(
        event=valid_event(),
        rules=[candidate, unrelated],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
        retriever=retriever,
    )

    assert [call["query"] for call in retriever.calls] == ["熒惑守心"]
    assert result.assessment.recommended_rule_id == candidate["id"]
    assert result.assessment.narration_eligibility == "eligible"


def test_build_result_serialization_excludes_matcher_internal_content(
    tmp_path: Path,
) -> None:
    evidence = write_citable_source(tmp_path)
    result = build_rule_assessment_result(
        event=valid_event(),
        rules=[matching_rule(evidence)],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
    )

    assert RAW_PASSAGE in str(result.matcher_result)
    public_dump = result.model_dump_json()
    assert RAW_PASSAGE not in public_dump
    assert "trigger_match_reason" not in public_dump
    assert str(tmp_path.resolve()) not in public_dump


def test_invalid_rule_id_is_rejected_even_when_rule_does_not_match(
    tmp_path: Path,
) -> None:
    rule = matching_rule(None)
    rule["id"] = "INVALID RULE ID"
    rule["trigger"] = {
        "body": "venus",
        "event_type": "conjunction",
        "target": "mercury",
    }

    with pytest.raises(ValueError, match="rule id"):
        build_rule_assessment_result(
            event=valid_event(),
            rules=[rule],
            rule_set_version="rules:test-v1",
            kb_root=tmp_path,
        )


def test_explicit_non_exact_hit_inside_exact_hits_is_not_hydrated(
    tmp_path: Path,
) -> None:
    hit = primary_hit(write_citable_source(tmp_path))
    hit["match_type"] = "heading_only"
    retriever = FakeRetriever(
        {
            "stage1": {"hits": []},
            "stage2": {
                "primary_candidates": [deepcopy(hit)],
                "exact_hits": [hit],
                "candidate_overlay_hits": [],
                "structured_fallbacks": [],
                "official_primary_used": True,
                "fallback_used": False,
            },
        }
    )

    result = build_rule_assessment_result(
        event=valid_event(),
        rules=[matching_rule(None)],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
        retriever=retriever,
    )

    assert result.assessment.narration_eligibility == "blocked"
    assert result.assessment.evidence_references[0].status == "candidate_only"
    assert result.retrieval_reports[0].status == "no_exact_primary"
