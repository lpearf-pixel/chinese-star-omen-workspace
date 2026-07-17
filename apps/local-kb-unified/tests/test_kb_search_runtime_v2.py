from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[1]


def _load_main(monkeypatch):
    monkeypatch.setenv("KB_SEARCH_API_KEY", "unit-test-key")
    monkeypatch.setenv("KB_SEARCH_DEFAULT_COLLECTION", "local_kb_kaiyuan_v2")
    package_root = ROOT / "kb-search"
    monkeypatch.syspath_prepend(str(package_root))
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)
    return importlib.import_module("app.main")


def _response_json(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


def _manifest() -> dict:
    return {
        "meta_status": "ok",
        "schema_version": "corpus-manifest/v1",
        "corpus_version": "20260717T120000Z",
        "ingest_run_id": "ingest_20260717T120000Z",
        "source_manifest_hash": "sha256:abc",
        "collection": "local_kb_kaiyuan_v2",
        "created_at": "2026-07-17T12:00:00Z",
    }


def test_api_key_accepts_x_api_key_and_rejects_missing(monkeypatch):
    main = _load_main(monkeypatch)
    asyncio.run(main.require_api_key(authorization=None, x_api_key="unit-test-key"))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(main.require_api_key(authorization=None, x_api_key=None))
    assert exc.value.status_code == 401


def test_health_degrades_instead_of_crashing_on_runtime_dependency_errors(monkeypatch):
    main = _load_main(monkeypatch)
    monkeypatch.setattr(main, "load_corpus_meta", _manifest)
    monkeypatch.setattr(
        main,
        "_ollama_readiness",
        lambda: {
            "ollama": True,
            "embedding_model": True,
            "models": ["nomic-embed-text:latest"],
        },
    )
    monkeypatch.setattr(
        main,
        "_qdrant_readiness",
        lambda collection: {
            "qdrant": False,
            "default_collection": False,
            "collections": [],
        },
    )

    response = main.health()
    body = _response_json(response)
    assert response.status_code == 503
    assert body["status"] == "degraded"
    assert body["ready"] is False
    assert body["checks"]["ollama"] is True
    assert body["checks"]["qdrant"] is False


def test_unknown_collection_returns_structured_not_found(monkeypatch):
    main = _load_main(monkeypatch)

    class MissingCollectionClient:
        def collection_exists(self, collection):
            return False

    monkeypatch.setattr(main, "_qdrant_client", lambda: MissingCollectionClient())
    request = main.RetrieveRequest(query="荧惑守心", top_k=3)

    with pytest.raises(HTTPException) as exc:
        main.retrieve(request)

    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "COLLECTION_NOT_FOUND"
