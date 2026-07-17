from __future__ import annotations

import sys
from pathlib import Path

import pytest

INDEX_JOBS = Path(__file__).resolve().parents[1] / "index-jobs"
sys.path.insert(0, str(INDEX_JOBS))

from incremental import point_id_for_item, plan_reconciliation, stable_point_key  # noqa: E402


MANAGED_BY = "local-kb-unified/v2"


def _item(
    paragraph_index: int,
    *,
    normalized_hash: str,
    raw_hash: str,
) -> dict:
    return {
        "kb_book_id": "kaiyuan_zhanjing",
        "source_locator": "KR3g0018_031",
        "page_marker": "KR3g0018_WYG_031-17a",
        "paragraph_index": paragraph_index,
        "normalized_content_hash": normalized_hash,
        "raw_content_hash": raw_hash,
        "content_hash": raw_hash,
        "chunk_text": "熒惑守心",
        "managed_by": MANAGED_BY,
        "collection_schema": "passage-v2",
    }


def test_point_id_is_deterministic_and_uses_normalized_passage_identity():
    compact = _item(
        0,
        normalized_hash="sha256:normalized",
        raw_hash="sha256:raw-a",
    )
    whitespace_changed = _item(
        0,
        normalized_hash="sha256:normalized",
        raw_hash="sha256:raw-b",
    )
    substantive_changed = _item(
        0,
        normalized_hash="sha256:different",
        raw_hash="sha256:raw-c",
    )

    assert stable_point_key(compact) == stable_point_key(whitespace_changed)
    assert point_id_for_item(compact) == point_id_for_item(compact)
    assert point_id_for_item(compact) == point_id_for_item(whitespace_changed)
    assert point_id_for_item(compact) != point_id_for_item(substantive_changed)


def test_incremental_plan_classifies_insert_update_unchanged_and_stale():
    unchanged = _item(0, normalized_hash="sha256:n0", raw_hash="sha256:r0")
    changed = _item(1, normalized_hash="sha256:n1", raw_hash="sha256:new-r1")
    inserted = _item(2, normalized_hash="sha256:n2", raw_hash="sha256:r2")

    unchanged_id = point_id_for_item(unchanged)
    changed_id = point_id_for_item(changed)
    stale = _item(3, normalized_hash="sha256:n3", raw_hash="sha256:r3")
    stale_id = point_id_for_item(stale)

    existing = {
        unchanged_id: {"managed_by": MANAGED_BY, "content_hash": "sha256:r0"},
        changed_id: {"managed_by": MANAGED_BY, "content_hash": "sha256:old-r1"},
        stale_id: {"managed_by": MANAGED_BY, "content_hash": "sha256:r3"},
    }

    plan = plan_reconciliation(
        [inserted, changed, unchanged],
        existing,
        mode="incremental",
    )

    assert [point_id_for_item(item) for item in plan.inserts] == [point_id_for_item(inserted)]
    assert [point_id_for_item(item) for item in plan.updates] == [changed_id]
    assert [point_id_for_item(item) for item in plan.unchanged] == [unchanged_id]
    assert plan.stale_ids == [stale_id]
    assert plan.stats == {
        "desired": 3,
        "new": 1,
        "changed": 1,
        "unchanged": 1,
        "stale": 1,
    }


def test_full_mode_schedules_every_desired_item_for_upsert():
    first = _item(0, normalized_hash="sha256:n0", raw_hash="sha256:r0")
    second = _item(1, normalized_hash="sha256:n1", raw_hash="sha256:r1")
    existing = {
        point_id_for_item(first): {
            "managed_by": MANAGED_BY,
            "content_hash": first["content_hash"],
        }
    }

    plan = plan_reconciliation([first, second], existing, mode="full")

    assert plan.unchanged == []
    assert [point_id_for_item(item) for item in plan.upserts] == sorted(
        [point_id_for_item(first), point_id_for_item(second)]
    )


def test_unmanaged_existing_points_are_neither_matched_nor_deleted():
    desired = _item(0, normalized_hash="sha256:n0", raw_hash="sha256:r0")
    point_id = point_id_for_item(desired)
    existing = {
        point_id: {"managed_by": "legacy-producer", "content_hash": "sha256:r0"},
        "legacy-only": {"managed_by": "legacy-producer", "content_hash": "sha256:x"},
    }

    plan = plan_reconciliation([desired], existing, mode="incremental")

    assert [point_id_for_item(item) for item in plan.inserts] == [point_id]
    assert plan.stale_ids == []


def test_empty_desired_corpus_aborts_instead_of_planning_mass_delete():
    existing = {
        "managed": {"managed_by": MANAGED_BY, "content_hash": "sha256:r0"}
    }
    with pytest.raises(ValueError, match="empty desired corpus"):
        plan_reconciliation([], existing, mode="incremental")


def test_invalid_mode_is_rejected():
    with pytest.raises(ValueError, match="mode"):
        plan_reconciliation(
            [_item(0, normalized_hash="sha256:n0", raw_hash="sha256:r0")],
            {},
            mode="recreate",
        )
