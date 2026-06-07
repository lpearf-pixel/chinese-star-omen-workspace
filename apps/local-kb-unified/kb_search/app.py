from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # pragma: no cover
    FastAPI = None


def _load_meta() -> dict[str, Any]:
    path = Path("data/corpus_manifest.json")
    if not path.exists():
        return {
            "corpus_version": "unknown",
            "ingest_run_id": "unknown",
            "source_manifest_hash": "unknown",
            "collection": "star_omen_kb",
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "corpus_version": data.get("corpus_version", "unknown"),
        "ingest_run_id": data.get("ingest_run_id", "unknown"),
        "source_manifest_hash": data.get("source_manifest_hash", "unknown"),
        "collection": data.get("collection", "star_omen_kb"),
    }

if FastAPI is not None:
    app = FastAPI(title="Local KB Search API")

    @app.get("/v1/meta")
    def meta() -> dict[str, Any]:
        return _load_meta()

    @app.get("/v1/health")
    def health() -> dict[str, Any]:
        return {"ok": True, **_load_meta()}
else:  # pragma: no cover
    app = None
