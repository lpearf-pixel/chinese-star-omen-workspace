from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Callable, Sequence

MANAGED_BY = "local-kb-unified/v2"
COLLECTION_SCHEMA = "passage-v2"


@dataclass
class ReconciliationPlan:
    inserts: list[dict[str, Any]]
    updates: list[dict[str, Any]]
    unchanged: list[dict[str, Any]]
    stale_ids: list[str]
    desired_by_id: dict[str, dict[str, Any]]

    @property
    def upserts(self) -> list[dict[str, Any]]:
        return sorted(
            [*self.inserts, *self.updates],
            key=point_id_for_item,
        )

    @property
    def stats(self) -> dict[str, int]:
        return {
            "desired": len(self.desired_by_id),
            "new": len(self.inserts),
            "changed": len(self.updates),
            "unchanged": len(self.unchanged),
            "stale": len(self.stale_ids),
        }


def stable_point_key(item: dict[str, Any]) -> str:
    """Return the stable logical identity used as the UUIDv5 input."""

    normalized_hash = item.get("normalized_content_hash")
    if normalized_hash:
        required = (
            "kb_book_id",
            "source_locator",
            "paragraph_index",
            "normalized_content_hash",
        )
        missing = [
            key for key in required
            if item.get(key) is None or item.get(key) == ""
        ]
        if missing:
            raise ValueError(f"missing passage identity fields: {missing}")
        return "\0".join(
            (
                COLLECTION_SCHEMA,
                str(item["kb_book_id"]),
                str(item["source_locator"]),
                str(item.get("page_marker") or "no-page"),
                str(item["paragraph_index"]),
                str(normalized_hash),
            )
        )

    relative_path = item.get("relative_path")
    source_root_label = item.get("source_root_label") or "primary"
    path = relative_path or item.get("path") or item.get("source_path")
    chunk_index = item.get("chunk_index", item.get("paragraph_index", 0))
    content_hash = item.get("content_hash") or item.get("raw_content_hash")
    if not path or content_hash is None:
        raise ValueError("missing generic identity fields: path/content_hash")
    return "\0".join(
        (
            "generic-v2",
            str(source_root_label),
            str(path),
            str(chunk_index),
            str(content_hash),
        )
    )


def point_id_for_item(item: dict[str, Any]) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, stable_point_key(item)))


def managed_content_hash(item: dict[str, Any]) -> str:
    return str(
        item.get("content_hash")
        or item.get("raw_content_hash")
        or item.get("normalized_content_hash")
        or ""
    )


def plan_reconciliation(
    desired: list[dict[str, Any]],
    existing: dict[str, dict[str, Any]],
    *,
    mode: str,
) -> ReconciliationPlan:
    """Classify desired and existing managed points without side effects."""

    if mode not in {"incremental", "full"}:
        raise ValueError("mode must be incremental or full")
    if not desired:
        raise ValueError("refusing to reconcile an empty desired corpus")

    desired_by_id: dict[str, dict[str, Any]] = {}
    for item in desired:
        point_id = point_id_for_item(item)
        if point_id in desired_by_id:
            raise ValueError(f"duplicate desired point id: {point_id}")
        desired_by_id[point_id] = item

    managed_existing = {
        str(point_id): payload
        for point_id, payload in existing.items()
        if payload.get("managed_by") == MANAGED_BY
    }

    inserts: list[dict[str, Any]] = []
    updates: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []

    for point_id in sorted(desired_by_id):
        item = desired_by_id[point_id]
        current = managed_existing.get(point_id)
        if current is None:
            inserts.append(item)
        elif mode == "full" or managed_content_hash(current) != managed_content_hash(item):
            updates.append(item)
        else:
            unchanged.append(item)

    stale_ids = sorted(set(managed_existing) - set(desired_by_id))
    return ReconciliationPlan(
        inserts=inserts,
        updates=updates,
        unchanged=unchanged,
        stale_ids=stale_ids,
        desired_by_id=desired_by_id,
    )


def execute_reconciliation(
    plan: ReconciliationPlan,
    *,
    embed_item: Callable[[dict[str, Any]], Sequence[float]],
    upsert_batch: Callable[[list[dict[str, Any]]], None],
    delete_points: Callable[[Sequence[str]], None],
    batch_size: int = 32,
) -> dict[str, int]:
    """Embed/upsert planned items and delete stale IDs only after success.

    Callback-based execution keeps the ordering rule independently testable and
    prevents Qdrant-specific code from obscuring the stale-delete safety gate.
    Exceptions intentionally propagate; the caller may report them, but this
    function never invokes ``delete_points`` after an embedding/upsert failure.
    """

    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    batch: list[dict[str, Any]] = []
    upserted = 0

    def flush() -> None:
        nonlocal batch, upserted
        if not batch:
            return
        upsert_batch(batch)
        upserted += len(batch)
        batch = []

    for item in plan.upserts:
        vector = list(embed_item(item))
        if not vector:
            raise RuntimeError(
                f"embedding returned an empty vector for {point_id_for_item(item)}"
            )
        batch.append(
            {
                "point_id": point_id_for_item(item),
                "item": item,
                "vector": vector,
            }
        )
        if len(batch) >= batch_size:
            flush()

    flush()
    if plan.stale_ids:
        delete_points(plan.stale_ids)

    return {
        "upserted": upserted,
        "deleted": len(plan.stale_ids),
        "errors": 0,
    }
