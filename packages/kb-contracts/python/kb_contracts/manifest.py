from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def new_candidate_manifest(book_id: str, *, base_corpus_version: str = "unknown", base_ingest_run_id: str = "unknown") -> dict[str, Any]:
    return {
        "schema_version": "candidate-manifest/v1",
        "source_project": "Codex-ready-chinese-star-omen-project",
        "target_upstream": "Local-KB-Unified",
        "book_id": book_id,
        "base_corpus_version": base_corpus_version,
        "base_ingest_run_id": base_ingest_run_id,
        "current_upstream_corpus_version": None,
        "last_synced_at": None,
        "items": [],
    }


def load_candidate_manifest(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"candidate manifest not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("schema_version") != "candidate-manifest/v1":
        raise ValueError(f"unsupported candidate manifest schema_version: {data.get('schema_version')}")
    if not isinstance(data.get("items"), list):
        raise ValueError("candidate manifest field 'items' must be a list")
    return data


def save_candidate_manifest(path: str | Path, manifest: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    manifest.setdefault("schema_version", "candidate-manifest/v1")
    manifest.setdefault("items", [])
    p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def merge_candidate_item(manifest: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    if not item.get("id"):
        raise ValueError("candidate manifest item must include stable id")
    manifest.setdefault("items", [])
    for idx, existing in enumerate(manifest["items"]):
        if existing.get("id") == item["id"]:
            manifest["items"][idx] = {**existing, **item}
            return manifest
    manifest["items"].append(item)
    return manifest
