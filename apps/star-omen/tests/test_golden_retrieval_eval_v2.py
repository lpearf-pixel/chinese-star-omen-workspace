from __future__ import annotations

from pathlib import Path

import yaml

from src.eval.corpus_eval import run_corpus_eval


STRUCTURED_POOL = ["zhusu_card", "term_card", "extract_card"]
PRIMARY_POOL = ["fenjuan", "fulltext"]


def _stage(*, official: bool = True, fallback: bool = False, polluted: bool = False):
    primary_hit = {
        "chunk_id": "passage-31",
        "card_type": "fenjuan",
        "path": "/corpus/古籍/唐開元占經/分卷/KR3g0018_031.md",
        "source_locator": "KR3g0018_031",
        "source_volume": "卷31",
        "page_marker": "KR3g0018_WYG_031-17a",
        "heading_path": ["熒惑占二", "熒惑犯心五"],
        "paragraph_index": 3,
        "raw_start": 100,
        "raw_end": 115,
        "content_hash": "sha256:raw",
        "raw_content_hash": "sha256:raw",
        "normalized_content_hash": "sha256:normalized",
        "final_citable": True,
        "managed_by": "local-kb-unified/v2",
        "collection_schema": "passage-v2",
    }
    structured_hits = [
        {"chunk_id": "term", "card_type": "term_card", "path": "/cards/熒惑.md"}
    ]
    if polluted:
        structured_hits.append(
            {"chunk_id": "asset", "card_type": "prompt_asset", "path": "/assets/p.md"}
        )
    return {
        "stage1": {
            "query_mode": "evidence",
            "retrieval_stage": "structured_recall",
            "card_types": STRUCTURED_POOL,
            "hits": structured_hits,
        },
        "stage2": {
            "query_mode": "evidence",
            "retrieval_stage": "primary_evidence",
            "card_types": PRIMARY_POOL,
            "hits": [primary_hit],
            "primary_candidates": [primary_hit],
            "official_primary_used": official,
            "fallback_used": fallback,
            "structured_fallbacks": [],
        },
    }


class FakeRetriever:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def two_stage_retrieve(self, query, **kwargs):
        self.calls.append({"query": query, **kwargs})
        return self.responses.pop(0)


def _write_cases(path: Path, cases: list[dict]) -> None:
    path.write_text(
        yaml.safe_dump({"cases": cases}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _case(**overrides):
    base = {
        "query": "荧惑守心",
        "expected_query_mode": "evidence",
        "expected_stage1_card_types": STRUCTURED_POOL,
        "expected_stage2_card_types": PRIMARY_POOL,
        "must_use_official_primary": True,
        "allow_filesystem_fallback": False,
        "expected_primary_card_type": "fenjuan",
        "expected_source_locator": "KR3g0018_031",
        "expected_page_marker": "KR3g0018_WYG_031-17a",
        "expected_heading_contains": "熒惑犯心五",
        "require_final_citable": True,
        "forbidden_card_types": ["prompt_asset", "nav", "qa_example"],
    }
    base.update(overrides)
    return base


def test_golden_eval_validates_stage_pools_provenance_and_citable_fields(tmp_path: Path):
    eval_path = tmp_path / "cases.yaml"
    _write_cases(eval_path, [_case()])
    retriever = FakeRetriever([_stage()])

    report = run_corpus_eval(eval_path=eval_path, retriever=retriever)

    assert report["schema_version"] == "corpus-eval/v2"
    assert report["all_passed"] is True
    assert report["passed"] == 1
    row = report["rows"][0]
    assert row["stage1_pool_match"] is True
    assert row["stage2_pool_match"] is True
    assert row["official_primary_used"] is True
    assert row["fallback_used"] is False
    assert row["source_locator_match"] is True
    assert row["page_marker_match"] is True
    assert row["heading_match"] is True
    assert row["citable_fields_present"] is True
    assert row["pollution_detected"] is False
    assert row["failure_reasons"] == []
    assert row["pass"] is True


def test_golden_eval_fails_for_disallowed_fallback_and_pollution(tmp_path: Path):
    eval_path = tmp_path / "cases.yaml"
    _write_cases(eval_path, [_case()])
    retriever = FakeRetriever([_stage(official=False, fallback=True, polluted=True)])

    report = run_corpus_eval(eval_path=eval_path, retriever=retriever)

    assert report["all_passed"] is False
    row = report["rows"][0]
    assert row["official_primary_used"] is False
    assert row["fallback_used"] is True
    assert row["pollution_detected"] is True
    assert "official_primary_required" in row["failure_reasons"]
    assert "filesystem_fallback_disallowed" in row["failure_reasons"]
    assert "forbidden_card_type_pollution" in row["failure_reasons"]


def test_legacy_case_fields_remain_compatible(tmp_path: Path):
    eval_path = tmp_path / "legacy.yaml"
    _write_cases(
        eval_path,
        [
            {
                "query": "荧惑守心",
                "query_mode": "evidence",
                "expected_top1_path_contains": "分卷",
                "must_hit_primary": True,
            }
        ],
    )

    report = run_corpus_eval(
        eval_path=eval_path,
        retriever=FakeRetriever([_stage()]),
    )

    assert report["all_passed"] is True
    assert report["rows"][0]["legacy_case"] is True
