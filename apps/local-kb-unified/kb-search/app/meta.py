"""Read the last successful ingest manifest for metadata and readiness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import config

REQUIRED_FIELDS = (
    "schema_version",
    "corpus_version",
    "ingest_run_id",
    "source_manifest_hash",
    "collection",
    "created_at",
)


def load_corpus_meta(path: Path | None = None) -> dict[str, Any]:
    manifest_path = Path(path or config.KB_CORPUS_MANIFEST_PATH)
    if not manifest_path.is_file():
        return {
            "meta_status": "missing",
            "error_code": "CORPUS_MANIFEST_MISSING",
        }

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "meta_status": "invalid",
            "error_code": "CORPUS_MANIFEST_INVALID",
            "error": str(exc),
        }

    if not isinstance(raw, dict):
        return {
            "meta_status": "invalid",
            "error_code": "CORPUS_MANIFEST_INVALID",
            "error": "manifest root must be an object",
        }
    missing = [field for field in REQUIRED_FIELDS if raw.get(field) in (None, "")]
    if missing:
        return {
            "meta_status": "invalid",
            "error_code": "CORPUS_MANIFEST_INVALID",
            "error": f"missing required fields: {missing}",
        }

    return {"meta_status": "ok", **raw}
