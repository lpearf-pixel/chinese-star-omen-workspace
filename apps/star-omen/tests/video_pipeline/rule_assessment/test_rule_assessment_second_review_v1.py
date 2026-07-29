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


class SequencedRetriever:
    def __init__(self, results: list[dict]):
        self.results = [deepcopy(item) for item in results]
        self.calls: list[str] = []

    def two_stage_retrieve(self, query: str, **kwargs):
        self.calls.append(query)
        if not self.results:
            raise AssertionError("unexpected retrieval call")
        return self.results.pop(0)


def official_result(hit: dict) -> dict:
    return {
        "stage1": {"hits": []},
        "stage2": {
            "primary_candidates": [deepcopy(hit)],
            "exact_hits": [deepcopy(hit)],
            "candidate_overlay_hits": [],
            "structured_fallbacks": [],
            "official_primary_used": True,
            "fallback_used": False,
        },
    }


def test_hydration_may_change_candidate_order_without_changing_candidate_set(
    tmp_path: Path,
) -> None:
    evidence = write_citable_source(tmp_path)
    missing = matching_rule(None)
    missing["id"] = "rule:mars-guarding-xin:priority-a"
    missing["rule_priority"] = 1
    citable = matching_rule(evidence)
    citable["id"] = "rule:mars-guarding-xin:priority-b"
    citable["rule_priority"] = 100
    retriever = SequencedRetriever([official_result(primary_hit(evidence))])

    result = build_rule_assessment_result(
        event=valid_event(),
        rules=[missing, citable],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
        retriever=retriever,
    )

    assert retriever.calls == ["熒惑守心"]
    assert {item.rule_id for item in result.assessment.matched_rules} == {
        missing["id"],
        citable["id"],
    }
    assert result.assessment.recommended_rule_id == missing["id"]


def test_exact_hit_without_official_or_fallback_provenance_fails_closed(
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
                "official_primary_used": False,
                "fallback_used": False,
            },
        }
    )

    with pytest.raises(ValueError, match="provenance"):
        build_rule_assessment_result(
            event=valid_event(),
            rules=[matching_rule(None)],
            rule_set_version="rules:test-v1",
            kb_root=tmp_path,
            retriever=retriever,
        )


def test_explicit_candidate_only_exact_hit_is_never_hydrated(
    tmp_path: Path,
) -> None:
    hit = primary_hit(write_citable_source(tmp_path))
    hit["status"] = "candidate_only"
    retriever = FakeRetriever(official_result(hit))

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


def test_invalid_rule_set_version_fails_before_external_retrieval(
    tmp_path: Path,
) -> None:
    retriever = FakeRetriever(error=AssertionError("retrieval must not be called"))

    with pytest.raises(ValueError, match="rule set version"):
        build_rule_assessment_result(
            event=valid_event(),
            rules=[matching_rule(None)],
            rule_set_version="INVALID RULE SET",
            kb_root=tmp_path,
            retriever=retriever,
        )

    assert retriever.calls == []
