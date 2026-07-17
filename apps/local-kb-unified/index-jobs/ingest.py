#!/usr/bin/env python3
"""Reconcile the desired local knowledge corpus into a managed Qdrant collection.

Kaiyuan primary sources are parsed by ``kb-text-core`` into canonical page/
paragraph passages. Incremental mode skips unchanged point IDs, embeds only new
or changed items, and deletes stale points only after every required upsert
succeeds. Collection recreation remains explicit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from desired_items import collect_desired_items
from incremental import (
    COLLECTION_SCHEMA,
    MANAGED_BY,
    execute_reconciliation,
    managed_content_hash,
    plan_reconciliation,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def resolve_sources_root() -> Path:
    raw = os.environ.get("KB_SOURCES_ROOT", "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else (REPO_ROOT / path).resolve()
    return (REPO_ROOT / "data" / "sources").resolve()


def resolve_generated_root() -> Path:
    raw = os.environ.get("KB_GENERATED_ROOT", "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else (REPO_ROOT / path).resolve()
    return (REPO_ROOT / "data" / "generated").resolve()


def resolve_obsidian_root() -> Optional[Path]:
    if not _env_bool("KB_ENABLE_OBSIDIAN_SOURCE"):
        return None
    raw = os.environ.get("KB_OBSIDIAN_ROOT", "").strip()
    if not raw:
        return None
    path = Path(raw)
    path = path if path.is_absolute() else (REPO_ROOT / path).resolve()
    return path if path.is_dir() else None


def ollama_embed(host: str, port: int, model: str, text: str) -> list[float]:
    response = requests.post(
        f"http://{host}:{port}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    vector = data.get("embedding")
    if not vector:
        raise RuntimeError(f"No embedding in response: {data}")
    return list(vector)


_PAYLOAD_KEYS = (
    "doc_id",
    "chunk_id",
    "source_type",
    "path",
    "title",
    "chunk_text",
    "chunk_index",
    "mtime",
    "content_hash",
    "raw_content_hash",
    "normalized_content_hash",
    "normalized_text",
    "managed_by",
    "collection_schema",
    "ingest_source",
    "source_root_label",
    "relative_path",
    "source_content_hash",
    "wiki_links",
    "tags",
    "aliases",
    "section_heading",
    "frontmatter",
    "kb_book_id",
    "book_title",
    "card_type",
    "evidence_level",
    "final_citable",
    "query_mode_hint",
    "variant_terms",
    "normalized_terms",
    "source_locator",
    "source_volume",
    "volume",
    "section",
    "page_marker",
    "heading_path",
    "paragraph_index",
    "raw_start",
    "raw_end",
    "source_refs",
    "duplicate_sources",
    "anchor_text",
)


def build_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        key: item[key]
        for key in _PAYLOAD_KEYS
        if key in item and item[key] is not None
    }
    if item.get("source_type") == "code" and str(item.get("path") or "").endswith(".py"):
        payload["lang"] = "python"
    payload.pop("book_id", None)
    return payload


def _missing_collection_error(exc: Exception) -> bool:
    value = str(exc).lower()
    return any(
        token in value
        for token in ("404", "not found", "doesn't exist", "unknown collection")
    )


def collection_exists(client: QdrantClient, collection: str) -> bool:
    try:
        client.get_collection(collection)
        return True
    except Exception as exc:
        if _missing_collection_error(exc):
            return False
        raise


def scroll_existing_managed(
    client: QdrantClient,
    collection: str,
    *,
    page_size: int = 256,
) -> dict[str, dict[str, Any]]:
    """Read only points explicitly owned by the v2 ingest producer."""

    managed_filter = qm.Filter(
        must=[
            qm.FieldCondition(
                key="managed_by",
                match=qm.MatchValue(value=MANAGED_BY),
            )
        ]
    )
    existing: dict[str, dict[str, Any]] = {}
    offset = None
    while True:
        records, next_offset = client.scroll(
            collection_name=collection,
            scroll_filter=managed_filter,
            limit=page_size,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for record in records:
            payload = dict(record.payload or {})
            if payload.get("managed_by") == MANAGED_BY:
                existing[str(record.id)] = payload
        if next_offset is None or next_offset == offset:
            break
        offset = next_offset
    return existing


def _source_manifest_hash(desired_by_id: dict[str, dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for point_id in sorted(desired_by_id):
        digest.update(point_id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(managed_content_hash(desired_by_id[point_id]).encode("utf-8"))
        digest.update(b"\n")
    return "sha256:" + digest.hexdigest()


def write_corpus_manifest(
    path: Path,
    *,
    collection: str,
    desired_by_id: dict[str, dict[str, Any]],
    plan_stats: dict[str, int],
    execution_stats: dict[str, int],
    elapsed_ms: int,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    manifest = {
        "schema_version": "corpus-manifest/v1",
        "corpus_version": timestamp,
        "ingest_run_id": f"ingest_{timestamp}",
        "source_manifest_hash": _source_manifest_hash(desired_by_id),
        "collection": collection,
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "managed_by": MANAGED_BY,
        "collection_schema": COLLECTION_SCHEMA,
        "run_stats": {
            **plan_stats,
            **execution_stats,
            "elapsed_ms": elapsed_ms,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return manifest


def _create_collection(
    client: QdrantClient,
    collection: str,
    dimension: int,
) -> None:
    client.create_collection(
        collection_name=collection,
        vectors_config=qm.VectorParams(
            size=dimension,
            distance=qm.Distance.COSINE,
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reconcile configured knowledge sources into Qdrant"
    )
    parser.add_argument(
        "--mode",
        choices=("full", "incremental"),
        default="incremental",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Explicitly delete and recreate the target collection",
    )
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--chunk-overlap", type=int, default=120)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--collection",
        default=os.environ.get(
            "KB_SEARCH_DEFAULT_COLLECTION",
            "local_kb_kaiyuan_v2",
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ollama_host = os.environ.get("OLLAMA_HOST", "127.0.0.1")
    ollama_port = _env_int("OLLAMA_PORT", 11434)
    qdrant_host = os.environ.get("QDRANT_HOST", "127.0.0.1")
    qdrant_port = _env_int("QDRANT_HTTP_PORT", 6333)
    embed_model = os.environ.get("EMBED_MODEL", "nomic-embed-text")

    sources_root = resolve_sources_root()
    generated_root = resolve_generated_root()
    obsidian_root = resolve_obsidian_root()
    started = time.perf_counter()

    desired = collect_desired_items(
        sources_root,
        generated_root=generated_root,
        obsidian_root=obsidian_root,
        chunk_size=args.chunk_size,
        overlap=args.chunk_overlap,
    )
    if not desired:
        print("refusing to ingest an empty desired corpus", file=sys.stderr)
        return 2

    client = QdrantClient(
        url=f"http://{qdrant_host}:{qdrant_port}",
        timeout=120,
    )
    exists = False if args.recreate else collection_exists(client, args.collection)
    existing = (
        scroll_existing_managed(client, args.collection)
        if exists
        else {}
    )
    effective_mode = "full" if args.recreate else args.mode
    plan = plan_reconciliation(desired, existing, mode=effective_mode)

    print(f"sources_root={sources_root}")
    print(f"generated_root={generated_root}")
    print(f"obsidian_root={obsidian_root if obsidian_root else '(disabled)'}")
    print(f"collection={args.collection}")
    print(f"mode={effective_mode}")
    print(json.dumps(plan.stats, ensure_ascii=False, sort_keys=True))

    if args.dry_run:
        return 0

    collection_ready = exists
    recreate_pending = bool(args.recreate)

    def embed_item(item: dict[str, Any]) -> Sequence[float]:
        return ollama_embed(
            ollama_host,
            ollama_port,
            embed_model,
            str(item.get("chunk_text") or "")[:8000],
        )

    def upsert_batch(records: list[dict[str, Any]]) -> None:
        nonlocal collection_ready, recreate_pending
        if not records:
            return
        dimension = len(records[0]["vector"])
        if recreate_pending:
            try:
                client.delete_collection(args.collection)
            except Exception as exc:
                if not _missing_collection_error(exc):
                    raise
            _create_collection(client, args.collection, dimension)
            collection_ready = True
            recreate_pending = False
        elif not collection_ready:
            _create_collection(client, args.collection, dimension)
            collection_ready = True

        points = [
            qm.PointStruct(
                id=record["point_id"],
                vector=record["vector"],
                payload=build_payload(record["item"]),
            )
            for record in records
        ]
        client.upsert(
            collection_name=args.collection,
            points=points,
            wait=True,
        )

    def delete_points(point_ids: Sequence[str]) -> None:
        if not point_ids:
            return
        client.delete(
            collection_name=args.collection,
            points_selector=qm.PointIdsList(points=list(point_ids)),
            wait=True,
        )

    try:
        execution = execute_reconciliation(
            plan,
            embed_item=embed_item,
            upsert_batch=upsert_batch,
            delete_points=delete_points,
            batch_size=args.batch_size,
        )
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        print(
            f"ingest_failed error={exc} elapsed_ms={elapsed_ms}; stale points were not deleted",
            file=sys.stderr,
        )
        return 1

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    manifest = write_corpus_manifest(
        REPO_ROOT / "data" / "corpus_manifest.json",
        collection=args.collection,
        desired_by_id=plan.desired_by_id,
        plan_stats=plan.stats,
        execution_stats=execution,
        elapsed_ms=elapsed_ms,
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "collection": args.collection,
                "plan": plan.stats,
                "execution": execution,
                "corpus_version": manifest["corpus_version"],
                "source_manifest_hash": manifest["source_manifest_hash"],
                "elapsed_ms": elapsed_ms,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
