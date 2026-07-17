from __future__ import annotations

import importlib
import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_QDRANT_RETRIEVAL_INTEGRATION") != "1",
    reason="requires ephemeral Qdrant service",
)


def _load_main(monkeypatch):
    monkeypatch.setenv("KB_SEARCH_API_KEY", "integration-key")
    monkeypatch.setenv("KB_SEARCH_DEFAULT_COLLECTION", "local_kb_kaiyuan_v2")
    monkeypatch.syspath_prepend(str(ROOT / "kb-search"))
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)
    return importlib.import_module("app.main")


def test_qdrant_structured_and_primary_pools_remain_separate(monkeypatch):
    main = _load_main(monkeypatch)
    client = QdrantClient(
        url=os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"),
        timeout=30,
    )
    collection = "test_retrieval_contract_" + uuid.uuid4().hex
    client.create_collection(
        collection_name=collection,
        vectors_config=qm.VectorParams(size=2, distance=qm.Distance.COSINE),
    )
    points = [
        qm.PointStruct(
            id=str(uuid.uuid4()),
            vector=[1.0, 0.0],
            payload={
                "chunk_id": "term-1",
                "chunk_text": "熒惑，火星之名。",
                "path": "/cards/熒惑.md",
                "title": "熒惑",
                "card_type": "term_card",
                "kb_book_id": "kaiyuan_zhanjing",
                "evidence_level": "structured",
            },
        ),
        qm.PointStruct(
            id=str(uuid.uuid4()),
            vector=[1.0, 0.0],
            payload={
                "chunk_id": "passage-31",
                "chunk_text": "石氏曰熒惑守心，天下兵起。",
                "path": "/corpus/KR3g0018_031.md",
                "title": "KR3g0018_031.md",
                "card_type": "fenjuan",
                "kb_book_id": "kaiyuan_zhanjing",
                "book_title": "唐開元占經",
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
                "managed_by": "local-kb-unified/v2",
                "collection_schema": "passage-v2",
            },
        ),
    ]
    client.upsert(collection_name=collection, points=points, wait=True)

    monkeypatch.setattr(main, "_qdrant_client", lambda: client)
    monkeypatch.setattr(main.ollama_client, "embed_text", lambda text: [1.0, 0.0])
    monkeypatch.setattr(main, "iter_embedding_query_strings", lambda text: [text])

    try:
        structured = main.retrieve(
            main.RetrieveRequest(
                query="荧惑守心",
                collection=collection,
                query_mode="evidence",
                retrieval_stage="structured_recall",
                card_types=["term_card", "extract_card"],
                filters={"kb_book_id": "kaiyuan_zhanjing"},
            )
        )
        assert structured.retrieved_count == 1
        assert {hit.card_type for hit in structured.hits} == {"term_card"}
        assert structured.retrieval_stage == "structured_recall"

        primary = main.retrieve(
            main.RetrieveRequest(
                query="荧惑守心",
                collection=collection,
                query_mode="evidence",
                retrieval_stage="primary_evidence",
                card_types=["fenjuan", "fulltext"],
                filters={"kb_book_id": "kaiyuan_zhanjing"},
            )
        )
        assert primary.retrieved_count == 1
        assert {hit.card_type for hit in primary.hits} == {"fenjuan"}
        assert primary.hits[0].source_locator == "KR3g0018_031"
        assert primary.hits[0].page_marker == "KR3g0018_WYG_031-17a"

        no_match = main.retrieve(
            main.RetrieveRequest(
                query="荧惑守心",
                collection=collection,
                retrieval_stage="primary_evidence",
                filters={"kb_book_id": "other_book"},
            )
        )
        assert no_match.retrieved_count == 0
        assert no_match.hits == []

        with pytest.raises(HTTPException) as exc:
            main.retrieve(
                main.RetrieveRequest(
                    query="荧惑守心",
                    collection=collection + "_missing",
                    retrieval_stage="primary_evidence",
                )
            )
        assert exc.value.status_code == 404
        assert exc.value.detail["error"]["code"] == "COLLECTION_NOT_FOUND"
    finally:
        client.delete_collection(collection)
