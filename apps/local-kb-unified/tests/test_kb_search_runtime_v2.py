from __future__ import annotations

import asyncio
import importlib
import json
import sys
import types
from pathlib import Path

import pytest
from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[1]


def _install_fake_qdrant_modules() -> None:
    qdrant = types.ModuleType("qdrant_client")

    class QdrantClient:
        def __init__(self, *args, **kwargs):
            pass

    qdrant.QdrantClient = QdrantClient

    http = types.ModuleType("qdrant_client.http")
    models = types.ModuleType("qdrant_client.http.models")

    class _Value:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    for name in ("Filter", "FieldCondition", "MatchAny", "MatchValue"):
        setattr(models, name, type(name, (_Value,), {}))

    qdrant.http = http
    http.models = models
    sys.modules["qdrant_client"] = qdrant
    sys.modules["qdrant_client.http"] = http
    sys.modules["qdrant_client.http.models"] = models


def _load_main(monkeypatch):
    _install_fake_qdrant_modules()
    monkeypatch.setenv("KB_SEARCH_API_KEY", "unit-test-key")
    monkeypatch.setenv("KB_SEARCH_DEFAULT_COLLECTION", "local_kb_kaiyuan_v2")
    package_root = ROOT / "kb-search"
    sys.path.insert(0, str(package_root))
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)
    return importlib.import_module("app.main")


def _response_json(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


def test_api_key_accepts_x_api_key_and_rejects_missing(monkeypatch):
    main = _load_main(monkeypatch)
    asyncio.run(main.require_api_key(authorization=None, x_api_key="unit-test-key"))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(main.require_api_key(authorization=None, x_api_key=None))
    assert exc.value.status_code == 401


def test_health_degrades_instead_of_crashing_on_runtime_dependency_errors(monkeypatch):
    main = _load_main(monkeypatch)

    class Response:
        ok = True

    class BrokenQdrant:
        def get_collections(self):
            raise RuntimeError("qdrant unavailable")

    monkeypatch.setattr(main.requests, "get", lambda *args, **kwargs: Response())
    monkeypatch.setattr(main, "_qdrant_client", lambda: BrokenQdrant())

    response = main.health()
    assert response.status_code == 503
    assert _response_json(response) == {
        "status": "degraded",
        "ollama": True,
        "qdrant": False,
    }


def test_unknown_collection_returns_empty_retrieval_result(monkeypatch):
    main = _load_main(monkeypatch)
    monkeypatch.setattr(main.ollama_client, "embed_text", lambda text: [0.1, 0.2])

    class MissingCollectionClient:
        def query_points(self, **kwargs):
            raise RuntimeError("collection not found")

    monkeypatch.setattr(main, "_qdrant_client", lambda: MissingCollectionClient())
    request = main.RetrieveRequest(query="荧惑守心", top_k=3)
    response = main.retrieve(request)
    assert response.retrieved_count == 0
    assert response.hits == []
