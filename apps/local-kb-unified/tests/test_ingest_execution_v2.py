from __future__ import annotations

import sys
from pathlib import Path

import pytest

INDEX_JOBS = Path(__file__).resolve().parents[1] / "index-jobs"
sys.path.insert(0, str(INDEX_JOBS))

from incremental import (  # noqa: E402
    ReconciliationPlan,
    execute_reconciliation,
    point_id_for_item,
)


def _item(index: int) -> dict:
    return {
        "kb_book_id": "kaiyuan_zhanjing",
        "source_locator": "KR3g0018_031",
        "page_marker": "KR3g0018_WYG_031-17a",
        "paragraph_index": index,
        "normalized_content_hash": f"sha256:n{index}",
        "raw_content_hash": f"sha256:r{index}",
        "content_hash": f"sha256:r{index}",
        "chunk_text": f"passage-{index}",
        "managed_by": "local-kb-unified/v2",
        "collection_schema": "passage-v2",
    }


def _plan(*, inserts=None, updates=None, unchanged=None, stale_ids=None):
    inserts = inserts or []
    updates = updates or []
    unchanged = unchanged or []
    desired = {point_id_for_item(item): item for item in [*inserts, *updates, *unchanged]}
    return ReconciliationPlan(
        inserts=inserts,
        updates=updates,
        unchanged=unchanged,
        stale_ids=stale_ids or [],
        desired_by_id=desired,
    )


def test_unchanged_items_never_call_embedding():
    unchanged = _item(0)
    calls: list[str] = []

    result = execute_reconciliation(
        _plan(unchanged=[unchanged]),
        embed_item=lambda item: calls.append(item["chunk_text"]),
        upsert_batch=lambda batch: calls.append("upsert"),
        delete_points=lambda point_ids: calls.append("delete"),
        batch_size=2,
    )

    assert calls == []
    assert result == {"upserted": 0, "deleted": 0, "errors": 0}


def test_stale_points_are_deleted_only_after_all_upserts_succeed():
    first = _item(0)
    second = _item(1)
    events: list[object] = []

    result = execute_reconciliation(
        _plan(inserts=[first, second], stale_ids=["stale-a", "stale-b"]),
        embed_item=lambda item: events.append(("embed", item["chunk_text"])) or [0.1, 0.2],
        upsert_batch=lambda batch: events.append(
            ("upsert", [record["point_id"] for record in batch])
        ),
        delete_points=lambda point_ids: events.append(("delete", list(point_ids))),
        batch_size=1,
    )

    assert events[-1] == ("delete", ["stale-a", "stale-b"])
    assert result == {"upserted": 2, "deleted": 2, "errors": 0}


def test_upsert_failure_prevents_stale_deletion():
    inserted = _item(0)
    deleted: list[str] = []

    with pytest.raises(RuntimeError, match="upsert failed"):
        execute_reconciliation(
            _plan(inserts=[inserted], stale_ids=["stale-a"]),
            embed_item=lambda item: [0.1, 0.2],
            upsert_batch=lambda batch: (_ for _ in ()).throw(
                RuntimeError("upsert failed")
            ),
            delete_points=lambda point_ids: deleted.extend(point_ids),
            batch_size=10,
        )

    assert deleted == []


def test_embedding_failure_prevents_stale_deletion():
    inserted = _item(0)
    deleted: list[str] = []

    with pytest.raises(RuntimeError, match="embed failed"):
        execute_reconciliation(
            _plan(inserts=[inserted], stale_ids=["stale-a"]),
            embed_item=lambda item: (_ for _ in ()).throw(
                RuntimeError("embed failed")
            ),
            upsert_batch=lambda batch: None,
            delete_points=lambda point_ids: deleted.extend(point_ids),
        )

    assert deleted == []
