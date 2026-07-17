from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

INDEX_JOBS = Path(__file__).resolve().parents[1] / "index-jobs"
sys.path.insert(0, str(INDEX_JOBS))

from incremental import execute_reconciliation, plan_reconciliation  # noqa: E402
from ingest import build_payload, scroll_existing_managed  # noqa: E402

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_QDRANT_INTEGRATION") != "1",
    reason="requires ephemeral Qdrant service",
)


def _item(index: int, *, raw_hash: str, normalized_hash: str) -> dict:
    return {
        "doc_id": "doc-31",
        "chunk_id": f"chunk-{index}",
        "source_type": "docs",
        "path": f"/tmp/KR3g0018_031-{index}.md",
        "title": "KR3g0018_031.md",
        "chunk_text": f"passage-{index}",
        "chunk_index": index,
        "mtime": 1,
        "content_hash": raw_hash,
        "raw_content_hash": raw_hash,
        "normalized_content_hash": normalized_hash,
        "normalized_text": f"passage-{index}",
        "managed_by": "local-kb-unified/v2",
        "collection_schema": "passage-v2",
        "ingest_source": "default",
        "source_root_label": "primary",
        "relative_path": "古籍/唐開元占經/分卷/KR3g0018_031.md",
        "kb_book_id": "kaiyuan_zhanjing",
        "book_title": "唐開元占經",
        "card_type": "fenjuan",
        "evidence_level": "primary",
        "final_citable": True,
        "query_mode_hint": "evidence",
        "source_locator": "KR3g0018_031",
        "source_volume": "卷31",
        "page_marker": "KR3g0018_WYG_031-17a",
        "heading_path": ["熒惑占二", "熒惑犯心五"],
        "paragraph_index": index,
        "raw_start": index * 10,
        "raw_end": index * 10 + 9,
    }


def test_incremental_insert_skip_update_and_delete_against_qdrant():
    client = QdrantClient(url=os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"))
    collection = "test_kaiyuan_incremental_" + uuid.uuid4().hex
    client.create_collection(
        collection_name=collection,
        vectors_config=qm.VectorParams(size=2, distance=qm.Distance.COSINE),
    )

    embed_calls: list[str] = []

    def embed_item(item):
        embed_calls.append(item["content_hash"])
        return [float(item["paragraph_index"] + 1), 0.5]

    def upsert_batch(records):
        client.upsert(
            collection_name=collection,
            wait=True,
            points=[
                qm.PointStruct(
                    id=record["point_id"],
                    vector=record["vector"],
                    payload=build_payload(record["item"]),
                )
                for record in records
            ],
        )

    def delete_points(point_ids):
        client.delete(
            collection_name=collection,
            wait=True,
            points_selector=qm.PointIdsList(points=list(point_ids)),
        )

    try:
        first = _item(0, raw_hash="sha256:r0", normalized_hash="sha256:n0")
        second = _item(1, raw_hash="sha256:r1", normalized_hash="sha256:n1")

        initial = plan_reconciliation([first, second], {}, mode="incremental")
        initial_result = execute_reconciliation(
            initial,
            embed_item=embed_item,
            upsert_batch=upsert_batch,
            delete_points=delete_points,
            batch_size=2,
        )
        assert initial_result["upserted"] == 2
        assert client.count(collection_name=collection, exact=True).count == 2

        existing = scroll_existing_managed(client, collection)
        second_plan = plan_reconciliation(
            [first, second],
            existing,
            mode="incremental",
        )
        calls_before_unchanged = len(embed_calls)
        unchanged_result = execute_reconciliation(
            second_plan,
            embed_item=embed_item,
            upsert_batch=upsert_batch,
            delete_points=delete_points,
        )
        assert second_plan.stats["unchanged"] == 2
        assert unchanged_result["upserted"] == 0
        assert len(embed_calls) == calls_before_unchanged

        whitespace_changed = _item(
            0,
            raw_hash="sha256:r0-whitespace",
            normalized_hash="sha256:n0",
        )
        changed_plan = plan_reconciliation(
            [whitespace_changed, second],
            scroll_existing_managed(client, collection),
            mode="incremental",
        )
        assert changed_plan.stats["changed"] == 1
        execute_reconciliation(
            changed_plan,
            embed_item=embed_item,
            upsert_batch=upsert_batch,
            delete_points=delete_points,
        )

        removed_plan = plan_reconciliation(
            [whitespace_changed],
            scroll_existing_managed(client, collection),
            mode="incremental",
        )
        assert removed_plan.stats["stale"] == 1
        removed_result = execute_reconciliation(
            removed_plan,
            embed_item=embed_item,
            upsert_batch=upsert_batch,
            delete_points=delete_points,
        )
        assert removed_result["deleted"] == 1
        assert client.count(collection_name=collection, exact=True).count == 1
    finally:
        client.delete_collection(collection)
