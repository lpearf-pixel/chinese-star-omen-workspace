from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]


def _load_main(monkeypatch):
    monkeypatch.setenv("KB_SEARCH_API_KEY", "unit-test-key")
    monkeypatch.setenv("KB_SEARCH_DEFAULT_COLLECTION", "local_kb_kaiyuan_v2")
    monkeypatch.syspath_prepend(str(ROOT / "kb-search"))
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)
    return importlib.import_module("app.main")


def test_retrieve_v2_echoes_effective_stage_pool_and_collection(monkeypatch):
    main = _load_main(monkeypatch)
    captured = {}

    def fake_search(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(main, "_search", fake_search)
    request = main.RetrieveRequest(
        schema_version="kb-retrieve/v2",
        query="荧惑守心",
        top_k=8,
        collection="local_kb_kaiyuan_v2",
        query_mode="evidence",
        retrieval_stage="structured_recall",
        card_types=["zhusu_card", "term_card", "extract_card"],
        filters={"book_id": "kaiyuan_zhanjing"},
        literal_first=True,
    )

    response = main.retrieve(request)

    assert response.schema_version == "kb-retrieve/v2"
    assert response.query_mode == "evidence"
    assert response.retrieval_stage == "structured_recall"
    assert response.card_types == ["zhusu_card", "term_card", "extract_card"]
    assert response.collection == "local_kb_kaiyuan_v2"
    assert response.hits == []
    assert response.retrieved_count == 0
    assert captured["filters"] == {"kb_book_id": "kaiyuan_zhanjing"}
    assert captured["retrieval_stage"] == "structured_recall"
    assert captured["card_types"] == response.card_types


def test_payload_to_hit_exposes_primary_passage_provenance(monkeypatch):
    main = _load_main(monkeypatch)
    payload = {
        "chunk_id": "passage-id",
        "chunk_text": "石氏曰熒惑守心。",
        "path": "/corpus/KR3g0018_031.md",
        "title": "KR3g0018_031.md",
        "kb_book_id": "kaiyuan_zhanjing",
        "book_title": "唐開元占經",
        "card_type": "fenjuan",
        "evidence_level": "primary",
        "final_citable": True,
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
        "source_refs": ["fulltext.md"],
        "managed_by": "local-kb-unified/v2",
        "collection_schema": "passage-v2",
    }

    hit = main._payload_to_hit(payload, 0.98)

    assert hit.snippet == payload["chunk_text"]
    assert hit.kb_book_id == "kaiyuan_zhanjing"
    assert hit.book_title == "唐開元占經"
    assert hit.source_volume == "卷31"
    assert hit.page_marker == "KR3g0018_WYG_031-17a"
    assert hit.heading_path == ["熒惑占二", "熒惑犯心五"]
    assert hit.paragraph_index == 3
    assert hit.raw_start == 100
    assert hit.raw_end == 115
    assert hit.normalized_content_hash == "sha256:normalized"
    assert hit.managed_by == "local-kb-unified/v2"


def test_missing_collection_is_not_treated_as_successful_empty_result(monkeypatch):
    main = _load_main(monkeypatch)

    class Client:
        def collection_exists(self, collection):
            return False

    monkeypatch.setattr(main, "_qdrant_client", lambda: Client())

    with pytest.raises(HTTPException) as exc:
        main._search(
            query_text="荧惑守心",
            collection="missing",
            top_k=5,
            min_score=None,
            filters=None,
            query_mode="evidence",
            retrieval_stage="primary_evidence",
            card_types=["fenjuan", "fulltext"],
        )

    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "COLLECTION_NOT_FOUND"


def test_successful_no_match_is_a_v2_empty_response(monkeypatch):
    main = _load_main(monkeypatch)
    monkeypatch.setattr(main, "_search", lambda **kwargs: [])

    response = main.retrieve(
        main.RetrieveRequest(
            query="不存在的占辞",
            query_mode="evidence",
            retrieval_stage="primary_evidence",
        )
    )

    assert response.retrieved_count == 0
    assert response.hits == []
    assert response.schema_version == "kb-retrieve/v2"


def test_contract_conflicts_return_structured_422(monkeypatch):
    main = _load_main(monkeypatch)

    with pytest.raises(HTTPException) as exc:
        main.retrieve(
            main.RetrieveRequest(
                query="荧惑守心",
                query_mode="evidence",
                retrieval_stage="structured_recall",
                filters={
                    "book_id": "kaiyuan_zhanjing",
                    "kb_book_id": "other_book",
                },
            )
        )

    assert exc.value.status_code == 422
    assert exc.value.detail["error"]["code"] == "CONTRACT_ERROR"


def test_rag_v2_uses_question_top_k_and_same_retrieval_contract(monkeypatch):
    main = _load_main(monkeypatch)
    captured = {}

    def fake_search(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(main, "_search", fake_search)
    response = main.rag_query(
        main.RAGRequest(
            question="《開元占經》如何記載熒惑守心？",
            top_k=6,
            query_mode="evidence",
            retrieval_stage="primary_evidence",
            card_types=["fenjuan", "fulltext"],
            filters={"kb_book_id": "kaiyuan_zhanjing"},
            generate=False,
        )
    )

    assert response.schema_version == "kb-rag/v2"
    assert response.retrieval_stage == "primary_evidence"
    assert response.card_types == ["fenjuan", "fulltext"]
    assert response.answer == ""
    assert captured["query_text"].startswith("《開元占經》")
    assert captured["top_k"] == 6
