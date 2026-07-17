from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module(monkeypatch, name: str):
    monkeypatch.setenv("KB_SEARCH_API_KEY", "unit-test-key")
    monkeypatch.setenv("KB_SEARCH_DEFAULT_COLLECTION", "local_kb_kaiyuan_v2")
    monkeypatch.syspath_prepend(str(ROOT / "kb-search"))
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name)
    return importlib.import_module(name)


def _json(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


def _manifest(collection: str = "local_kb_kaiyuan_v2") -> dict:
    return {
        "schema_version": "corpus-manifest/v1",
        "corpus_version": "20260717T120000Z",
        "ingest_run_id": "ingest_20260717T120000Z",
        "source_manifest_hash": "sha256:abc",
        "collection": collection,
        "created_at": "2026-07-17T12:00:00Z",
        "managed_by": "local-kb-unified/v2",
        "collection_schema": "passage-v2",
        "run_stats": {"desired": 12, "unchanged": 10},
    }


def test_load_corpus_meta_returns_valid_manifest_fields(monkeypatch, tmp_path: Path):
    meta = _load_module(monkeypatch, "app.meta")
    path = tmp_path / "corpus_manifest.json"
    path.write_text(json.dumps(_manifest()), encoding="utf-8")

    result = meta.load_corpus_meta(path)

    assert result == {"meta_status": "ok", **_manifest()}


def test_load_corpus_meta_distinguishes_missing_and_invalid(monkeypatch, tmp_path: Path):
    meta = _load_module(monkeypatch, "app.meta")

    missing = meta.load_corpus_meta(tmp_path / "missing.json")
    assert missing["meta_status"] == "missing"
    assert missing["error_code"] == "CORPUS_MANIFEST_MISSING"

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{not-json", encoding="utf-8")
    invalid = meta.load_corpus_meta(invalid_path)
    assert invalid["meta_status"] == "invalid"
    assert invalid["error_code"] == "CORPUS_MANIFEST_INVALID"


def test_meta_endpoint_returns_200_only_for_valid_manifest(monkeypatch):
    main = _load_module(monkeypatch, "app.main")
    valid = {"meta_status": "ok", **_manifest()}
    monkeypatch.setattr(main, "load_corpus_meta", lambda: valid)

    response = main.meta()
    assert response.status_code == 200
    assert _json(response)["collection"] == "local_kb_kaiyuan_v2"

    monkeypatch.setattr(
        main,
        "load_corpus_meta",
        lambda: {
            "meta_status": "missing",
            "error_code": "CORPUS_MANIFEST_MISSING",
        },
    )
    response = main.meta()
    assert response.status_code == 503
    assert _json(response)["meta_status"] == "missing"


def test_health_requires_model_qdrant_collection_manifest_and_match(monkeypatch):
    main = _load_module(monkeypatch, "app.main")
    manifest = {"meta_status": "ok", **_manifest()}
    monkeypatch.setattr(main, "load_corpus_meta", lambda: manifest)
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
            "qdrant": True,
            "default_collection": True,
            "collections": [collection],
        },
    )

    response = main.health()
    body = _json(response)
    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["ready"] is True
    assert all(body["checks"].values())
    assert body["corpus"]["corpus_version"] == "20260717T120000Z"


def test_health_degrades_on_manifest_collection_mismatch(monkeypatch):
    main = _load_module(monkeypatch, "app.main")
    monkeypatch.setattr(
        main,
        "load_corpus_meta",
        lambda: {"meta_status": "ok", **_manifest("other_collection")},
    )
    monkeypatch.setattr(
        main,
        "_ollama_readiness",
        lambda: {"ollama": True, "embedding_model": True, "models": []},
    )
    monkeypatch.setattr(
        main,
        "_qdrant_readiness",
        lambda collection: {
            "qdrant": True,
            "default_collection": True,
            "collections": [collection],
        },
    )

    response = main.health()
    body = _json(response)
    assert response.status_code == 503
    assert body["status"] == "degraded"
    assert body["checks"]["manifest_collection_match"] is False


def test_health_degrades_when_embedding_model_is_absent(monkeypatch):
    main = _load_module(monkeypatch, "app.main")
    monkeypatch.setattr(main, "load_corpus_meta", lambda: {"meta_status": "ok", **_manifest()})
    monkeypatch.setattr(
        main,
        "_ollama_readiness",
        lambda: {"ollama": True, "embedding_model": False, "models": ["other"]},
    )
    monkeypatch.setattr(
        main,
        "_qdrant_readiness",
        lambda collection: {
            "qdrant": True,
            "default_collection": True,
            "collections": [collection],
        },
    )

    response = main.health()
    assert response.status_code == 503
    assert _json(response)["checks"]["embedding_model"] is False
