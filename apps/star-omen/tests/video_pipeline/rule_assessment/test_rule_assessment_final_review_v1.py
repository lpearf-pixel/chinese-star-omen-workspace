from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from src.video_pipeline.rule_assessment import build_rule_assessment_result
from tests.video_pipeline.rule_assessment.helpers import (
    FakeRetriever,
    matching_rule,
    primary_hit,
    valid_event,
    write_citable_source,
)


def test_partial_match_does_not_call_external_retriever(tmp_path: Path) -> None:
    payload = valid_event().model_dump(mode="json")
    payload["measurements"][0]["value"] = 2.5
    event = valid_event().__class__.model_validate(payload)
    retriever = FakeRetriever(error=AssertionError("partial match must not retrieve"))

    result = build_rule_assessment_result(
        event=event,
        rules=[matching_rule(None)],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
        retriever=retriever,
    )

    assert retriever.calls == []
    assert result.assessment.match_status == "partial_match"
    assert result.assessment.narration_eligibility == "blocked"
    assert result.assessment.evidence_references[0].status == "missing_evidence"


def test_insufficient_data_does_not_call_external_retriever(tmp_path: Path) -> None:
    payload = valid_event().model_dump(mode="json")
    payload["measurements"] = []
    payload["quality_status"] = "insufficient_data"
    payload["uncertainty_reasons"] = ["measurement-window-not-available"]
    event = valid_event().__class__.model_validate(payload)
    retriever = FakeRetriever(error=AssertionError("insufficient data must not retrieve"))

    result = build_rule_assessment_result(
        event=event,
        rules=[matching_rule(None)],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
        retriever=retriever,
    )

    assert retriever.calls == []
    assert result.assessment.match_status == "insufficient_data"
    assert result.assessment.narration_eligibility == "blocked"


def test_conflicting_official_and_fallback_provenance_is_rejected(
    tmp_path: Path,
) -> None:
    hit = primary_hit(write_citable_source(tmp_path))
    retriever = FakeRetriever(
        {
            "stage1": {"hits": []},
            "stage2": {
                "primary_candidates": [deepcopy(hit)],
                "exact_hits": [hit],
                "candidate_overlay_hits": [],
                "structured_fallbacks": [],
                "official_primary_used": True,
                "fallback_used": True,
            },
        }
    )

    with pytest.raises(ValueError, match="conflicting.*provenance"):
        build_rule_assessment_result(
            event=valid_event(),
            rules=[matching_rule(None)],
            rule_set_version="rules:test-v1",
            kb_root=tmp_path,
            retriever=retriever,
        )


def test_exact_hit_must_belong_to_primary_candidate_set(tmp_path: Path) -> None:
    hit = primary_hit(write_citable_source(tmp_path))
    retriever = FakeRetriever(
        {
            "stage1": {"hits": []},
            "stage2": {
                "primary_candidates": [],
                "exact_hits": [hit],
                "candidate_overlay_hits": [],
                "structured_fallbacks": [],
                "official_primary_used": True,
                "fallback_used": False,
            },
        }
    )

    with pytest.raises(ValueError, match="primary candidate"):
        build_rule_assessment_result(
            event=valid_event(),
            rules=[matching_rule(None)],
            rule_set_version="rules:test-v1",
            kb_root=tmp_path,
            retriever=retriever,
        )
