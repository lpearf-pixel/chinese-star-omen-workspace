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


def retrieval_result(hit: dict | None = None, *, overlay: list[dict] | None = None) -> dict:
    primary = [deepcopy(hit)] if hit is not None else []
    return {
        "stage1": {"hits": [{"card_type": "omen_rule"}]},
        "stage2": {
            "source": "official_qdrant" if primary else "none",
            "primary_candidates": primary,
            "exact_hits": primary,
            "candidate_overlay_hits": list(overlay or []),
            "structured_fallbacks": [],
            "official_primary_used": bool(primary),
            "fallback_used": False,
        },
        "observability": {"schema_version": "kb-observability/v1"},
    }


def test_unique_exact_primary_hit_can_hydrate_missing_rule_evidence(tmp_path: Path) -> None:
    evidence = write_citable_source(tmp_path)
    retriever = FakeRetriever(retrieval_result(primary_hit(evidence)))
    rule = matching_rule(None)

    result = build_rule_assessment_result(
        event=valid_event(),
        rules=[rule],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
        retriever=retriever,
    )

    assert len(retriever.calls) == 1
    call = retriever.calls[0]
    assert call["query"] == "熒惑守心"
    assert call["query_mode"] == "evidence"
    assert call["filters"] == {"kb_book_id": "kaiyuan_zhanjing"}
    assert result.assessment.match_status == "matched"
    assert result.assessment.narration_eligibility == "eligible"
    assert result.assessment.evidence_references[0].status == "citable"
    assert result.retrieval_reports[0].status == "hydrated_citable"
    assert result.retrieval_reports[0].exact_primary_count == 1


def test_embedded_citable_evidence_does_not_call_retriever(tmp_path: Path) -> None:
    evidence = write_citable_source(tmp_path)
    retriever = FakeRetriever(error=AssertionError("retriever must not be called"))

    result = build_rule_assessment_result(
        event=valid_event(),
        rules=[matching_rule(evidence)],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
        retriever=retriever,
    )

    assert retriever.calls == []
    assert result.assessment.narration_eligibility == "eligible"
    assert result.retrieval_reports[0].status == "embedded_citable"


def test_candidate_overlay_is_never_used_as_citable_evidence(tmp_path: Path) -> None:
    evidence = write_citable_source(tmp_path)
    overlay = [{**primary_hit(evidence), "status": "candidate_only"}]
    retriever = FakeRetriever(retrieval_result(None, overlay=overlay))

    result = build_rule_assessment_result(
        event=valid_event(),
        rules=[matching_rule(None)],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
        retriever=retriever,
    )

    assert result.assessment.narration_eligibility == "blocked"
    assert result.assessment.evidence_references[0].status == "candidate_only"
    assert result.retrieval_reports[0].candidate_overlay_count == 1
    assert result.retrieval_reports[0].status == "candidate_overlay_only"
    assert result.evidence_bundle.entries[0].narration_allowed is False


def test_multiple_exact_primary_hits_are_ambiguous_and_blocked(tmp_path: Path) -> None:
    evidence = write_citable_source(tmp_path)
    first = primary_hit(evidence)
    second = deepcopy(first)
    second["paragraph_index"] = first["paragraph_index"] + 1
    retriever = FakeRetriever(
        {
            "stage1": {"hits": []},
            "stage2": {
                "primary_candidates": [first, second],
                "exact_hits": [first, second],
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
    assert result.assessment.evidence_references[0].status == "ambiguous"
    assert result.retrieval_reports[0].status == "ambiguous_exact_primary"
    assert result.retrieval_reports[0].exact_primary_count == 2
    assert "evidence:ambiguous" in result.assessment.uncertainty_reasons


def test_non_exact_primary_hit_is_not_hydrated(tmp_path: Path) -> None:
    evidence = primary_hit(write_citable_source(tmp_path))
    evidence["match_type"] = "heading_only"
    retriever = FakeRetriever(
        {
            "stage1": {"hits": []},
            "stage2": {
                "primary_candidates": [evidence],
                "exact_hits": [],
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

    assert result.assessment.evidence_references[0].status == "candidate_only"
    assert result.retrieval_reports[0].status == "no_exact_primary"
    assert result.assessment.narration_eligibility == "blocked"


def test_resolver_mismatch_after_retrieval_is_ambiguous(tmp_path: Path) -> None:
    evidence = primary_hit(write_citable_source(tmp_path))
    evidence["content_hash"] = "sha256:" + "0" * 64
    evidence["raw_content_hash"] = "sha256:" + "0" * 64
    retriever = FakeRetriever(retrieval_result(evidence))

    result = build_rule_assessment_result(
        event=valid_event(),
        rules=[matching_rule(None)],
        rule_set_version="rules:test-v1",
        kb_root=tmp_path,
        retriever=retriever,
    )

    assert result.assessment.evidence_references[0].status == "ambiguous"
    assert result.retrieval_reports[0].status == "resolver_rejected"
    assert result.retrieval_reports[0].resolver_status == "hash_mismatch"
    assert result.assessment.narration_eligibility == "blocked"


def test_transport_error_propagates_and_is_not_converted_to_empty_result(tmp_path: Path) -> None:
    sentinel = RuntimeError("transport unavailable")
    retriever = FakeRetriever(error=sentinel)

    with pytest.raises(RuntimeError, match="transport unavailable"):
        build_rule_assessment_result(
            event=valid_event(),
            rules=[matching_rule(None)],
            rule_set_version="rules:test-v1",
            kb_root=tmp_path,
            retriever=retriever,
        )


def test_malformed_two_stage_response_fails_closed(tmp_path: Path) -> None:
    retriever = FakeRetriever({"stage1": {}, "stage2": "not-a-mapping"})

    with pytest.raises(ValueError, match="stage2"):
        build_rule_assessment_result(
            event=valid_event(),
            rules=[matching_rule(None)],
            rule_set_version="rules:test-v1",
            kb_root=tmp_path,
            retriever=retriever,
        )
