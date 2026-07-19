from __future__ import annotations

import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
import httpx

from release_observation import ReleaseObservationError, _config_hash, capture_phase_observation
from release_observation_live import KBSearchReadClient, QdrantCollectionReader
from release_drill import MANIFEST_IDENTITY_FIELDS, validate_release_drill


STRUCTURED = [
    "xingguan_card",
    "zhusu_card",
    "term_card",
    "extract_card",
    "topic_index",
    "chapter_summary",
]
PRIMARY = ["fenjuan", "fulltext"]
ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "capture_release_observation.py"


def test_capture_builds_content_free_phase_from_read_only_adapters():
    calls = []

    def fetch_health():
        return {
            "http_status": 200,
            "body": {
                "status": "ok",
                "ready": True,
                "checks": {
                    "ollama": True,
                    "embedding_model": True,
                    "qdrant": True,
                    "default_collection": True,
                    "corpus_manifest": True,
                    "manifest_collection_match": True,
                },
                "default_collection": "local_kb_kaiyuan_v2",
            },
        }

    def fetch_meta():
        return {
            "http_status": 200,
            "body": {
                "meta_status": "ok",
                "schema_version": "corpus-manifest/v1",
                "corpus_version": "release",
                "ingest_run_id": "ingest_release",
                "source_manifest_hash": "sha256:source",
                "collection": "local_kb_kaiyuan_v2",
                "created_at": "2026-07-18T12:00:00Z",
                "managed_by": "local-kb-unified/v2",
                "collection_schema": "passage-v2",
            },
        }

    def retrieve(**request):
        calls.append(request)
        stage = request["retrieval_stage"]
        return {
            "http_status": 200,
            "body": {
                "retrieval_stage": stage,
                "card_types": request["card_types"],
                "collection": request["collection"],
                "retrieved_count": 1,
                "hits": [{"snippet": "SECRET SOURCE CONTENT", "path": "/private/source.md"}],
            },
        }

    def inspect_collection(collection):
        return {
            "exists": True,
            "points_count": 41 if collection == "local_kb_default" else 57,
            "config": {"vectors": {"size": 768, "distance": "Cosine"}, "shard_number": 1},
        }

    result = capture_phase_observation(
        active_collection="local_kb_kaiyuan_v2",
        query="熒惑守心",
        fetch_health=fetch_health,
        fetch_meta=fetch_meta,
        retrieve=retrieve,
        inspect_collection=inspect_collection,
        captured_at="2026-07-18T12:30:00Z",
    )

    assert result["schema_version"] == "kaiyuan-release-observation/v1"
    assert result["phase"]["active_collection"] == "local_kb_kaiyuan_v2"
    assert result["phase"]["smoke"]["structured_recall"]["card_types"] == STRUCTURED
    assert result["phase"]["smoke"]["primary_evidence"]["card_types"] == PRIMARY
    assert result["phase"]["collections"]["local_kb_default"]["points_count"] == 41
    assert result["phase"]["collections"]["local_kb_default"]["config_hash"].startswith("sha256:")
    assert [call["retrieval_stage"] for call in calls] == ["structured_recall", "primary_evidence"]
    assert all(call["filters"] == {"kb_book_id": "kaiyuan_zhanjing"} for call in calls)
    encoded = json.dumps(result, ensure_ascii=False, allow_nan=False)
    assert "SECRET SOURCE CONTENT" not in encoded
    assert "/private/source.md" not in encoded

    drill = json.loads((ROOT / "tests" / "fixtures" / "release_drill_v1.json").read_text(encoding="utf-8"))
    drill["after_switch"] = result["phase"]
    drill["expected_release_manifest"] = {
        name: result["phase"]["meta"][name] for name in MANIFEST_IDENTITY_FIELDS
    }
    protected_hash = result["phase"]["collections"]["local_kb_default"]["config_hash"]
    for phase in ("before_switch", "after_rollback"):
        drill[phase]["collections"]["local_kb_default"]["config_hash"] = protected_hash
    assert validate_release_drill(drill)["status"] == "passed"


def test_config_fingerprint_ignores_non_allowlisted_metadata():
    public = {
        "vectors": {"size": 768, "distance": "Cosine"},
        "shard_number": 1,
        "optimizer_config": {"indexing_threshold": 20000},
    }

    first = _config_hash({**public, "payload_sample": "SECRET-A", "internal_status": "green"})
    second = _config_hash({**public, "payload_sample": "SECRET-B", "internal_status": "yellow"})

    assert first == second


def test_config_fingerprint_rejects_missing_vector_schema():
    with pytest.raises(ReleaseObservationError) as caught:
        _config_hash({"shard_number": 1})

    assert caught.value.code == "invalid_response"
    assert caught.value.operation == "inspect_collection"


@pytest.mark.parametrize(
    ("active_collection", "query"),
    [
        ("../local_kb_kaiyuan_v2", "熒惑守心"),
        ("local_kb_kaiyuan_v2", "   "),
    ],
)
def test_builder_rejects_invalid_operator_input_before_network(active_collection, query):
    def unexpected():
        raise AssertionError("network adapter must not run")

    with pytest.raises(ReleaseObservationError) as caught:
        capture_phase_observation(
            active_collection=active_collection,
            query=query,
            fetch_health=unexpected,
            fetch_meta=unexpected,
            retrieve=unexpected,
            inspect_collection=unexpected,
            captured_at="2026-07-18T12:30:00Z",
        )

    assert caught.value.code == "contract_error"
    assert caught.value.operation == "input"


class _Response:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class _Session:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.response


def test_http_adapter_sends_secret_only_in_header_and_exact_retrieve_body():
    session = _Session(
        _Response(
            200,
            {
                "retrieval_stage": "primary_evidence",
                "card_types": PRIMARY,
                "collection": "local_kb_kaiyuan_v2",
                "retrieved_count": 1,
                "hits": [{}],
            },
        )
    )
    client = KBSearchReadClient(
        base_url="http://kb.example/",
        api_key="super-secret-key",
        timeout_seconds=3,
        session=session,
    )

    response = client.retrieve(
        query="熒惑守心",
        collection="local_kb_kaiyuan_v2",
        retrieval_stage="primary_evidence",
        card_types=PRIMARY,
        filters={"kb_book_id": "kaiyuan_zhanjing"},
    )

    assert response["http_status"] == 200
    method, url, kwargs = session.calls[0]
    assert (method, url) == ("POST", "http://kb.example/v1/retrieve")
    assert kwargs["headers"] == {"Authorization": "Bearer super-secret-key"}
    assert kwargs["timeout"] == 3
    assert kwargs["allow_redirects"] is False
    assert kwargs["json"] == {
        "schema_version": "kb-retrieve/v2",
        "query": "熒惑守心",
        "top_k": 5,
        "collection": "local_kb_kaiyuan_v2",
        "filters": {"kb_book_id": "kaiyuan_zhanjing"},
        "retrieval_stage": "primary_evidence",
        "card_types": PRIMARY,
        "literal_first": True,
    }
    assert "super-secret-key" not in json.dumps(response)


@pytest.mark.parametrize(
    ("response", "code"),
    [
        (_Response(401, {"error": {"message": "secret body"}}), "authentication_failed"),
        (_Response(503, {"secret": "raw service body"}), "upstream_unavailable"),
        (_Response(200, ValueError("raw invalid json")), "invalid_response"),
    ],
)
def test_http_adapter_uses_safe_structured_errors(response, code):
    client = KBSearchReadClient(
        base_url="http://kb.example",
        api_key="super-secret-key",
        timeout_seconds=3,
        session=_Session(response),
    )

    with pytest.raises(ReleaseObservationError) as caught:
        client.meta()

    assert caught.value.code == code
    assert caught.value.operation == "meta"
    text = str(caught.value)
    assert "super-secret-key" not in text
    assert "secret body" not in text
    assert "raw service body" not in text


def test_generic_404_is_contract_error_not_missing_collection():
    client = KBSearchReadClient(
        base_url="http://kb.example",
        api_key="secret",
        timeout_seconds=3,
        session=_Session(_Response(404, {"detail": "route not found"})),
    )

    with pytest.raises(ReleaseObservationError) as caught:
        client.meta()

    assert caught.value.code == "contract_error"


def test_http_adapter_rejects_redirect_instead_of_treating_it_as_success():
    client = KBSearchReadClient(
        base_url="http://kb.example",
        api_key="secret",
        timeout_seconds=3,
        session=_Session(_Response(302, {"status": "ok"})),
    )

    with pytest.raises(ReleaseObservationError) as caught:
        client.health()

    assert caught.value.code == "invalid_response"


def test_http_adapter_maps_timeout_without_leaking_exception_text():
    class TimeoutSession:
        def request(self, *args, **kwargs):
            raise __import__("requests").Timeout("secret endpoint detail")

    client = KBSearchReadClient(
        base_url="http://kb.example",
        api_key="secret",
        timeout_seconds=3,
        session=TimeoutSession(),
    )

    with pytest.raises(ReleaseObservationError) as caught:
        client.meta()

    assert caught.value.code == "timeout"
    assert "secret endpoint detail" not in str(caught.value)


class _QdrantReaderFake:
    def __init__(self):
        self.calls = []

    def collection_exists(self, collection_name):
        self.calls.append(("collection_exists", collection_name))
        return True

    def get_collection(self, collection_name):
        self.calls.append(("get_collection", collection_name))
        return SimpleNamespace(
            config=SimpleNamespace(
                params=SimpleNamespace(
                    vectors=SimpleNamespace(size=768, distance=SimpleNamespace(value="Cosine"), on_disk=False),
                    shard_number=1,
                    replication_factor=1,
                    write_consistency_factor=1,
                    on_disk_payload=True,
                ),
                optimizer_config=SimpleNamespace(indexing_threshold=20000),
                hnsw_config=SimpleNamespace(m=16, ef_construct=100),
            )
        )

    def count(self, collection_name, exact):
        self.calls.append(("count", collection_name, exact))
        return SimpleNamespace(count=57)


def test_qdrant_reader_uses_only_exact_read_calls_and_allowlisted_config():
    client = _QdrantReaderFake()

    result = QdrantCollectionReader(client).inspect("ephemeral_release_test")

    assert result == {
        "exists": True,
        "points_count": 57,
        "config": {
            "vectors": {"size": 768, "distance": "Cosine", "on_disk": False},
            "shard_number": 1,
            "replication_factor": 1,
            "write_consistency_factor": 1,
            "on_disk_payload": True,
            "optimizer_config": {"indexing_threshold": 20000},
            "hnsw_config": {"m": 16, "ef_construct": 100},
        },
    }
    assert client.calls == [
        ("collection_exists", "ephemeral_release_test"),
        ("get_collection", "ephemeral_release_test"),
        ("count", "ephemeral_release_test", True),
    ]


def test_qdrant_reader_preserves_timeout_taxonomy():
    class TimedOutQdrant:
        def collection_exists(self, collection_name):
            raise httpx.ReadTimeout("secret qdrant endpoint")

    with pytest.raises(ReleaseObservationError) as caught:
        QdrantCollectionReader(TimedOutQdrant()).inspect("ephemeral_release_test")

    assert caught.value.code == "timeout"
    assert caught.value.operation == "inspect_collection"
    assert "secret qdrant endpoint" not in str(caught.value)


def test_cli_rejects_missing_secret_without_creating_output(tmp_path: Path):
    output = tmp_path / "phase.json"
    env = dict(os.environ)
    env.pop("B7_TEST_API_KEY", None)

    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--phase",
            "before_switch",
            "--active-collection",
            "ephemeral_release_test",
            "--query",
            "熒惑守心",
            "--base-url",
            "http://kb.example",
            "--qdrant-url",
            "http://qdrant.example",
            "--api-key-env",
            "B7_TEST_API_KEY",
            "--out",
            str(output),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "release observation input error: missing_api_key\n"
    assert not output.exists()


def test_atomic_writer_creates_strict_json_and_refuses_overwrite(tmp_path: Path):
    spec = importlib.util.spec_from_file_location("capture_release_observation_cli", CLI)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / "phase.json"

    module._write_new_atomic(output, {"value": 1})

    assert json.loads(output.read_text(encoding="utf-8")) == {"value": 1}
    with pytest.raises(FileExistsError):
        module._write_new_atomic(output, {"value": 2})
    assert json.loads(output.read_text(encoding="utf-8")) == {"value": 1}
    assert list(tmp_path.glob(".phase.json.*")) == []


def test_cli_reports_output_exists_when_atomic_create_loses_race(tmp_path: Path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("capture_release_observation_race_cli", CLI)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / "phase.json"
    monkeypatch.setenv("B7_TEST_API_KEY", "secret")
    monkeypatch.setattr(
        module,
        "KBSearchReadClient",
        lambda **kwargs: SimpleNamespace(health=lambda: None, meta=lambda: None, retrieve=lambda **request: None),
    )
    monkeypatch.setattr(module, "QdrantClient", lambda **kwargs: SimpleNamespace())
    monkeypatch.setattr(module, "QdrantCollectionReader", lambda client: SimpleNamespace(inspect=lambda name: None))
    monkeypatch.setattr(module, "capture_phase_observation", lambda **kwargs: {"phase": {}})
    monkeypatch.setattr(module, "_write_new_atomic", lambda path, payload: (_ for _ in ()).throw(FileExistsError()))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(CLI), "--phase", "before_switch", "--active-collection", "ephemeral_release_test",
            "--query", "熒惑守心", "--base-url", "http://kb.example", "--qdrant-url",
            "http://qdrant.example", "--api-key-env", "B7_TEST_API_KEY", "--out", str(output),
        ],
    )

    assert module.main() == 2
    assert capsys.readouterr().err == "release observation input error: output_exists\n"


def test_builder_rejects_retrieved_count_hit_length_mismatch():
    health = {
        "http_status": 200,
        "body": {
            "status": "ok",
            "ready": True,
            "default_collection": "local_kb_kaiyuan_v2",
            "checks": {name: True for name in (
                "ollama", "embedding_model", "qdrant", "default_collection",
                "corpus_manifest", "manifest_collection_match",
            )},
        },
    }
    meta = {
        "http_status": 200,
        "body": {
            "meta_status": "ok",
            "schema_version": "corpus-manifest/v1",
            "corpus_version": "release",
            "ingest_run_id": "ingest_release",
            "source_manifest_hash": "sha256:source",
            "collection": "local_kb_kaiyuan_v2",
            "created_at": "2026-07-18T12:00:00Z",
            "managed_by": "local-kb-unified/v2",
            "collection_schema": "passage-v2",
        },
    }

    def retrieve(**request):
        return {
            "http_status": 200,
            "body": {
                "retrieval_stage": request["retrieval_stage"],
                "card_types": request["card_types"],
                "collection": request["collection"],
                "retrieved_count": 2,
                "hits": [{}],
            },
        }

    with pytest.raises(ReleaseObservationError) as caught:
        capture_phase_observation(
            active_collection="local_kb_kaiyuan_v2",
            query="熒惑守心",
            fetch_health=lambda: health,
            fetch_meta=lambda: meta,
            retrieve=retrieve,
            inspect_collection=lambda name: {
                "exists": True,
                "points_count": 1,
                "config": {"vectors": {"size": 768, "distance": "Cosine"}},
            },
            captured_at="2026-07-18T12:30:00Z",
        )

    assert caught.value.code == "invalid_response"
    assert caught.value.operation == "structured_recall"


def test_live_modules_have_no_qdrant_or_ingest_mutation_calls():
    source = "\n".join(
        (ROOT / name).read_text(encoding="utf-8")
        for name in ("release_observation.py", "release_observation_live.py", "scripts/capture_release_observation.py")
    )
    for forbidden in (".upsert(", ".delete(", ".create_collection(", ".recreate_collection(", " ingest("):
        assert forbidden not in source


def test_runbook_names_the_verifier_input_schema():
    runbook = (ROOT.parent.parent / "docs" / "development" / "B6_RELEASE_ROLLBACK_RUNBOOK.md").read_text(
        encoding="utf-8"
    )

    assert "`kaiyuan-release-drill-input/v1` root" in runbook
