from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys
import types
import uuid
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import src.video_pipeline.feedback_loop.readonly_kb_v1 as readonly_kb_module
from src.config.settings import SettingsError
from src.connectors.evidence_resolver import EvidenceResolverContext
from src.connectors.kb_retrieval.transport import VerifiedUpstreamProvenanceV1
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalKBSourceSnapshotV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
    SourceSnapshotBindingV1,
    canonical_contract_sha256,
)
from src.video_pipeline.feedback_loop.readonly_kb_v1 import (
    PinnedReadOnlyKBSession,
    build_readonly_kb_retriever,
    validate_raw_official_retrieve_response,
    validate_upstream_meta,
)
from src.video_pipeline.feedback_loop.source_snapshot_v1 import LocalKBSourceAccessor


COLLECTION = "local_kb_kaiyuan_v2"
CORPUS_VERSION = "20260903T010203Z"
BOOK_ID = "kaiyuan_zhanjing"
RELATIVE_PATH = "古籍/唐開元占經/分卷/KR3g0018_031.md"
MANIFEST_HASH = "sha256:" + "a" * 64


def _tree_hash(files: list[dict[str, object]]) -> str:
    canonical = json.dumps(
        files,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _source_snapshot(
    root: Path,
    *,
    body: str = "# 唐開元占經\n<pb:KR3g0018_WYG_031-17a>\n石氏曰畢宿主兵。\n",
) -> LocalKBSourceSnapshotV1:
    source = root / RELATIVE_PATH
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(body, encoding="utf-8")
    raw = source.read_bytes()
    files = [
        {
            "relative_path": RELATIVE_PATH,
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    ]
    return LocalKBSourceSnapshotV1.model_validate(
        {
            "schema_version": "local-kb-source-snapshot/v1",
            "snapshot_id": "snapshot:readonly-kb-test",
            "corpus_version": CORPUS_VERSION,
            "collection": COLLECTION,
            "kb_book_id": BOOK_ID,
            "files": files,
            "tree_sha256": _tree_hash(files),
        }
    )


def _base_meta(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "meta_status": "ok",
        "schema_version": "corpus-manifest/v1",
        "corpus_version": CORPUS_VERSION,
        "ingest_run_id": "ingest_20260903T010203Z",
        "source_manifest_hash": MANIFEST_HASH,
        "collection": COLLECTION,
        "created_at": "2026-09-03T01:02:03Z",
    }
    value.update(changes)
    return value


def _provenance() -> VerifiedUpstreamProvenanceV1:
    return validate_upstream_meta(
        _base_meta(),
        collection=COLLECTION,
        expected_corpus_version=CORPUS_VERSION,
    )


def _request_payload(stage: str = "primary_evidence") -> dict[str, object]:
    card_types = (
        ["fenjuan", "fulltext"]
        if stage == "primary_evidence"
        else ["zhusu_card", "term_card", "extract_card"]
    )
    return {
        "schema_version": "kb-retrieve/v2",
        "query": "畢宿 烈風",
        "top_k": 8,
        "collection": COLLECTION,
        "query_mode": "evidence",
        "retrieval_stage": stage,
        "literal_first": True,
        "card_types": card_types,
        "filters": {"kb_book_id": BOOK_ID},
    }


def _raw_response(
    *,
    stage: str = "primary_evidence",
    hits: list[object] | None = None,
) -> dict[str, object]:
    request = _request_payload(stage)
    rows = [] if hits is None else hits
    return {
        "schema_version": "kb-retrieve/v2",
        "query_mode": "evidence",
        "retrieval_stage": stage,
        "card_types": request["card_types"],
        "collection": COLLECTION,
        "filters": {"kb_book_id": BOOK_ID},
        "hits": rows,
        "retrieved_count": len(rows),
        "latency_ms": 1,
    }


def _write_config(path: Path, *, endpoint: str = "http://127.0.0.1:8008") -> None:
    path.write_text(
        f"""
app:
  env: test
  debug: false
  log_level: INFO
  timezone: UTC
  default_limit: 8
kb_search:
  base_url: "{endpoint}"
  api_port: 8008
  api_key: "${{KB_SEARCH_API_KEY:-}}"
  default_collection: hostile_collection
  timeout_seconds: nan
  query_normalize: false
  query_s2t: false
  query_t2s: false
knowledge_base:
  sources_root: ./hostile
  enable_obsidian_source: true
  obsidian_root: ./hostile-obsidian
  obsidian_ingest_source_label: obsidian
  obsidian_source_root_label: kaiyuan_zhanjing
  enable_candidate_overlay: true
  candidate_overlay_root: ./hostile-overlay
astro:
  default_epoch: J2000
  default_lon: 116.4
  default_lat: 39.9
  default_location_name: Beijing
  visibility_min_alt_deg: 5
""",
        encoding="utf-8",
    )


def _tree_files(root: Path) -> tuple[str, ...]:
    return tuple(
        sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    )


@contextmanager
def _isolated_producer_import(*, cwd: Path, prepend: Path | None = None):
    """Restore every interpreter/environment surface touched by producer imports."""

    modules_before = dict(sys.modules)
    path_before = list(sys.path)
    environment_before = dict(os.environ)
    cwd_before = Path.cwd()
    os.chdir(cwd)
    if prepend is not None:
        sys.path.insert(0, str(prepend))
    try:
        yield
    finally:
        os.chdir(cwd_before)
        os.environ.clear()
        os.environ.update(environment_before)
        sys.path[:] = path_before
        for name in list(sys.modules):
            if name not in modules_before:
                del sys.modules[name]
        for name, module in modules_before.items():
            sys.modules[name] = module


def _load_fresh_module(path: Path) -> types.ModuleType:
    name = f"_task3_producer_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "collection",
    ["local_kb_default", "test_vfl_ephemeral_task3", "local_kb_kaiyuan_v3"],
)
def test_factory_rejects_every_nonproduction_collection_before_all_other_work(
    monkeypatch: pytest.MonkeyPatch,
    collection: str,
) -> None:
    """Catches collection validation occurring after config, snapshot, or network."""

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("collection rejection must be the first operation")

    monkeypatch.setattr(readonly_kb_module, "resolve_kb_search_config_path", forbidden)
    monkeypatch.setattr(readonly_kb_module, "load_kb_search_endpoint", forbidden)
    monkeypatch.setattr(readonly_kb_module, "load_settings", forbidden)
    monkeypatch.setattr(readonly_kb_module, "PinnedHTTPXJSONTransport", forbidden)
    monkeypatch.setattr(readonly_kb_module, "KBSearchRetriever", forbidden)

    with pytest.raises(ReadOnlyAdapterError) as caught:
        build_readonly_kb_retriever(
            kb_root=Path("unused"),
            collection=collection,
            expected_corpus_version=CORPUS_VERSION,
            source_accessor=forbidden,  # type: ignore[arg-type]
            source_snapshot=forbidden,  # type: ignore[arg-type]
            source_snapshot_sha256="0" * 64,
        )
    assert caught.value.code == ReadOnlyErrorCode.PLAN_MISMATCH


def test_factory_rejects_remote_endpoint_before_credential_or_transport(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Catches a credential lookup or client construction before endpoint validation."""

    root = tmp_path / "kb"
    snapshot = _source_snapshot(root)
    config = tmp_path / "config.yaml"
    _write_config(config, endpoint="http://198.51.100.9:8008")
    monkeypatch.delenv("KB_SEARCH_API_KEY", raising=False)
    calls = {"settings": 0, "transport": 0, "retriever": 0}

    def forbidden(name: str):
        def call(*args: object, **kwargs: object) -> object:
            calls[name] += 1
            raise AssertionError(name)

        return call

    monkeypatch.setattr(readonly_kb_module, "load_settings", forbidden("settings"))
    monkeypatch.setattr(
        readonly_kb_module,
        "PinnedHTTPXJSONTransport",
        forbidden("transport"),
    )
    monkeypatch.setattr(readonly_kb_module, "KBSearchRetriever", forbidden("retriever"))

    with LocalKBSourceAccessor.open(kb_root=root, snapshot=snapshot) as accessor:
        with pytest.raises(ReadOnlyAdapterError) as caught:
            build_readonly_kb_retriever(
                kb_root=root,
                collection=COLLECTION,
                expected_corpus_version=CORPUS_VERSION,
                source_accessor=accessor,
                source_snapshot=snapshot,
                source_snapshot_sha256=canonical_contract_sha256(snapshot),
                config_path=config,
            )
    assert caught.value.code == ReadOnlyErrorCode.ENDPOINT_REJECTED
    assert calls == {"settings": 0, "transport": 0, "retriever": 0}
    assert "198.51.100.9" not in str(caught.value)


def test_factory_wraps_config_failure_without_sensitive_exception_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Catches a preflight SettingsError surviving on the public exception."""

    root = tmp_path / "kb"
    snapshot = _source_snapshot(root)

    def reject_config(_path: Path | None = None) -> Path:
        raise SettingsError("attacker-secret-config-path")

    monkeypatch.setattr(
        readonly_kb_module,
        "resolve_kb_search_config_path",
        reject_config,
    )

    with LocalKBSourceAccessor.open(kb_root=root, snapshot=snapshot) as accessor:
        with pytest.raises(ReadOnlyAdapterError) as caught:
            build_readonly_kb_retriever(
                kb_root=root,
                collection=COLLECTION,
                expected_corpus_version=CORPUS_VERSION,
                source_accessor=accessor,
                source_snapshot=snapshot,
                source_snapshot_sha256=canonical_contract_sha256(snapshot),
            )
    assert caught.value.code == ReadOnlyErrorCode.ENDPOINT_REJECTED
    assert str(caught.value) == "endpoint_rejected"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "attacker-secret-config-path" not in str(caught.value)


def test_factory_rejects_meta_before_credential_and_retriever_construction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Catches loading a key or retriever before deployed meta is fully valid."""

    root = tmp_path / "kb"
    snapshot = _source_snapshot(root)
    config = tmp_path / "config.yaml"
    _write_config(config)
    calls = {"settings": 0, "retriever": 0}

    class InvalidMetaTransport(_MetaTransport):
        def __init__(self, origin: str) -> None:
            super().__init__([_base_meta(collection="wrong")])

    def forbidden(name: str):
        def call(*args: object, **kwargs: object) -> object:
            calls[name] += 1
            raise AssertionError(name)

        return call

    monkeypatch.setattr(
        readonly_kb_module,
        "PinnedHTTPXJSONTransport",
        InvalidMetaTransport,
    )
    monkeypatch.setattr(readonly_kb_module, "load_settings", forbidden("settings"))
    monkeypatch.setattr(readonly_kb_module, "KBSearchRetriever", forbidden("retriever"))

    with LocalKBSourceAccessor.open(kb_root=root, snapshot=snapshot) as accessor:
        with pytest.raises(ReadOnlyAdapterError) as caught:
            build_readonly_kb_retriever(
                kb_root=root,
                collection=COLLECTION,
                expected_corpus_version=CORPUS_VERSION,
                source_accessor=accessor,
                source_snapshot=snapshot,
                source_snapshot_sha256=canonical_contract_sha256(snapshot),
                config_path=config,
            )
    assert caught.value.code == ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED
    assert calls == {"settings": 0, "retriever": 0}


def test_validate_upstream_meta_accepts_base_and_exact_producer_variants() -> None:
    """Catches rejecting a deployed meta shape or hashing operational telemetry."""

    base = validate_upstream_meta(
        _base_meta(),
        collection=COLLECTION,
        expected_corpus_version=CORPUS_VERSION,
    )
    script = validate_upstream_meta(
        _base_meta(
            source_roots=["data/sources", "data/generated"],
            excluded_roots=["incoming/downstream_candidates"],
        ),
        collection=COLLECTION,
        expected_corpus_version=CORPUS_VERSION,
    )
    ingest = validate_upstream_meta(
        _base_meta(
            managed_by="local-kb-unified/v2",
            collection_schema="passage-v2",
            run_stats={
                "desired": 1,
                "new": 0,
                "changed": 0,
                "unchanged": 1,
                "stale": 0,
                "upserted": 0,
                "deleted": 0,
                "errors": 0,
                "elapsed_ms": 1,
            },
        ),
        collection=COLLECTION,
        expected_corpus_version=CORPUS_VERSION,
    )
    ingest_telemetry_change = validate_upstream_meta(
        _base_meta(
            managed_by="local-kb-unified/v2",
            collection_schema="passage-v2",
            run_stats={
                "desired": 1,
                "new": 0,
                "changed": 0,
                "unchanged": 1,
                "stale": 0,
                "upserted": 0,
                "deleted": 0,
                "errors": 0,
                "elapsed_ms": 999,
            },
        ),
        collection=COLLECTION,
        expected_corpus_version=CORPUS_VERSION,
    )

    assert base.collection == script.collection == ingest.collection == COLLECTION
    assert base.corpus_version == CORPUS_VERSION
    assert len({base.provenance_sha256, script.provenance_sha256, ingest.provenance_sha256}) == 3
    assert ingest.session_meta_sha256 != ingest_telemetry_change.session_meta_sha256
    assert ingest.provenance_sha256 == ingest_telemetry_change.provenance_sha256


def test_real_corpus_manifest_script_shape_is_accepted_without_import_side_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catches validator drift from the real script producer's exact output."""

    upstream = Path(__file__).resolve().parents[4] / "local-kb-unified"
    producer_path = upstream / "scripts" / "corpus_manifest.py"
    output = tmp_path / "script-manifest.json"
    before = _tree_files(tmp_path)

    original_cwd = Path.cwd()
    monkeypatch.chdir(tmp_path)
    try:
        with _isolated_producer_import(cwd=tmp_path):
            producer = _load_fresh_module(producer_path)
            manifest = producer.write_manifest(COLLECTION, output)
    finally:
        os.chdir(original_cwd)

    assert _tree_files(tmp_path) == (*before, "script-manifest.json")
    validated = validate_upstream_meta(
        {"meta_status": "ok", **manifest},
        collection=COLLECTION,
        expected_corpus_version=manifest["corpus_version"],
    )
    assert validated.collection == COLLECTION
    assert validated.source_manifest_hash == manifest["source_manifest_hash"]


def test_real_ingest_writer_shape_is_accepted_with_all_import_state_restored(
    tmp_path: Path,
) -> None:
    """Catches normal-ingest compatibility tests importing optional live clients."""

    upstream = Path(__file__).resolve().parents[4] / "local-kb-unified"
    index_jobs = upstream / "index-jobs"
    producer_path = index_jobs / "ingest.py"
    output = tmp_path / "ingest-manifest.json"
    external_calls: list[str] = []
    dotenv_calls: list[object] = []

    def forbidden(name: str):
        def call(*args: object, **kwargs: object) -> object:
            external_calls.append(name)
            raise AssertionError(name)

        return call

    requests_stub = types.ModuleType("requests")
    requests_stub.post = forbidden("requests.post")  # type: ignore[attr-defined]
    dotenv_stub = types.ModuleType("dotenv")

    def load_dotenv(path: object) -> None:
        dotenv_calls.append(path)

    dotenv_stub.load_dotenv = load_dotenv  # type: ignore[attr-defined]
    qdrant_stub = types.ModuleType("qdrant_client")
    qdrant_stub.QdrantClient = forbidden("QdrantClient")  # type: ignore[attr-defined]
    qdrant_http_stub = types.ModuleType("qdrant_client.http")
    qdrant_models_stub = types.ModuleType("qdrant_client.http.models")
    qdrant_http_stub.models = qdrant_models_stub  # type: ignore[attr-defined]
    desired_stub = types.ModuleType("desired_items")
    desired_stub.collect_desired_items = forbidden("collect_desired_items")  # type: ignore[attr-defined]
    incremental_stub = types.ModuleType("incremental")
    incremental_stub.MANAGED_BY = "local-kb-unified/v2"  # type: ignore[attr-defined]
    incremental_stub.COLLECTION_SCHEMA = "passage-v2"  # type: ignore[attr-defined]
    incremental_stub.execute_reconciliation = forbidden("execute_reconciliation")  # type: ignore[attr-defined]
    incremental_stub.plan_reconciliation = forbidden("plan_reconciliation")  # type: ignore[attr-defined]
    incremental_stub.managed_content_hash = forbidden("managed_content_hash")  # type: ignore[attr-defined]

    before = _tree_files(tmp_path)
    with _isolated_producer_import(cwd=tmp_path, prepend=index_jobs):
        sys.modules.update(
            {
                "requests": requests_stub,
                "dotenv": dotenv_stub,
                "qdrant_client": qdrant_stub,
                "qdrant_client.http": qdrant_http_stub,
                "qdrant_client.http.models": qdrant_models_stub,
                "desired_items": desired_stub,
                "incremental": incremental_stub,
            }
        )
        producer = _load_fresh_module(producer_path)
        manifest = producer.write_corpus_manifest(
            output,
            collection=COLLECTION,
            desired_by_id={},
            plan_stats={
                "desired": 0,
                "new": 0,
                "changed": 0,
                "unchanged": 0,
                "stale": 0,
            },
            execution_stats={"upserted": 0, "deleted": 0, "errors": 0},
            elapsed_ms=7,
        )

    assert dotenv_calls == [upstream / ".env"]
    assert external_calls == []
    assert _tree_files(tmp_path) == (*before, "ingest-manifest.json")
    validated = validate_upstream_meta(
        {"meta_status": "ok", **manifest},
        collection=COLLECTION,
        expected_corpus_version=manifest["corpus_version"],
    )
    assert validated.collection == COLLECTION
    assert validated.source_manifest_hash == manifest["source_manifest_hash"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.pop("created_at"),
        lambda value: value.update(extra="unknown"),
        lambda value: value.update(meta_status="degraded"),
        lambda value: value.update(schema_version="corpus-manifest/v2"),
        lambda value: value.update(collection="other"),
        lambda value: value.update(corpus_version="20260230T010203Z"),
        lambda value: value.update(ingest_run_id=1),
        lambda value: value.update(source_manifest_hash="sha256:not-a-hash"),
        lambda value: value.update(source_roots=[]),
        lambda value: value.update(managed_by="local-kb-unified/v2"),
        lambda value: value.update(
            managed_by="local-kb-unified/v2",
            collection_schema="passage-v2",
            run_stats={"desired": 0},
        ),
        lambda value: value.update(
            managed_by="local-kb-unified/v2",
            collection_schema="passage-v2",
            run_stats={
                "desired": True,
                "new": 0,
                "changed": 0,
                "unchanged": 0,
                "stale": 0,
                "upserted": 0,
                "deleted": 0,
                "errors": 0,
                "elapsed_ms": 0,
            },
        ),
    ],
)
def test_validate_upstream_meta_rejects_missing_unknown_typed_or_mixed_shapes(
    mutate,
) -> None:
    """Catches permissive deployed-meta validation before a pinned session."""

    value = _base_meta()
    mutate(value)
    with pytest.raises(ReadOnlyAdapterError) as caught:
        validate_upstream_meta(
            value,
            collection=COLLECTION,
            expected_corpus_version=CORPUS_VERSION,
        )
    assert caught.value.code == ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_validate_upstream_meta_semantic_change_changes_persisted_digest() -> None:
    """Catches excluding a stable semantic field from persisted provenance."""

    first = _provenance()
    second = validate_upstream_meta(
        _base_meta(ingest_run_id="ingest_20260903T010204Z"),
        collection=COLLECTION,
        expected_corpus_version=CORPUS_VERSION,
    )
    assert first.provenance_sha256 != second.provenance_sha256


def test_raw_validator_accepts_exact_deployed_response_without_corpus_version() -> None:
    """Catches requiring an unavailable response-native corpus field."""

    request = _request_payload()
    response = _raw_response()
    validate_raw_official_retrieve_response(
        response,
        request_payload=request,
        verified_provenance=_provenance(),
    )
    assert "corpus_version" not in response


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.pop("schema_version"),
        lambda value: value.update(schema_version="kb-retrieve/v1"),
        lambda value: value.update(query_mode="support"),
        lambda value: value.update(retrieval_stage="structured_recall"),
        lambda value: value.update(card_types=["fulltext", "fenjuan"]),
        lambda value: value.update(collection="other"),
        lambda value: value.update(filters={"kb_book_id": "other"}),
        lambda value: value.update(retrieved_count=True),
        lambda value: value.update(retrieved_count=1),
        lambda value: value.update(latency_ms=math.inf),
        lambda value: value.update(hits={}),
        lambda value: value.update(corpus_version="20260903T010204Z"),
        lambda value: value.update(extra="unknown"),
    ],
)
def test_raw_validator_rejects_stage_schema_pool_count_and_provenance_drift(
    mutate,
) -> None:
    """Catches malformed official responses reaching normalization or fallback."""

    request = _request_payload()
    response = _raw_response()
    mutate(response)
    with pytest.raises(ReadOnlyAdapterError) as caught:
        validate_raw_official_retrieve_response(
            response,
            request_payload=request,
            verified_provenance=_provenance(),
        )
    assert caught.value.code == ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED


@pytest.mark.parametrize(
    "hit",
    [
        {"snippet": "x", "score": 1.0},
        {"snippet": "x", "score": 1.0, "card_type": None},
        {"snippet": "x", "score": 1.0, "card_type": "term_card"},
        {"snippet": "x", "score": math.inf, "card_type": "fenjuan"},
        "not-a-mapping",
    ],
)
def test_raw_primary_hits_require_explicit_pool_card_type_and_finite_shape(hit: object) -> None:
    """Catches malformed nonempty primary hits being filtered into healthy empty."""

    request = _request_payload()
    response = _raw_response(hits=[hit])
    with pytest.raises(ReadOnlyAdapterError) as caught:
        validate_raw_official_retrieve_response(
            response,
            request_payload=request,
            verified_provenance=_provenance(),
        )
    assert caught.value.code == ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED


@pytest.mark.parametrize("field", ["score", "latency_ms"])
def test_raw_validator_rejects_unbounded_integers_with_fixed_error(field: str) -> None:
    """Catches huge upstream numbers raising OverflowError in later consumers."""

    request = _request_payload()
    response = _raw_response(
        hits=[{"snippet": "x", "score": 1.0, "card_type": "fenjuan"}]
    )
    if field == "score":
        response["hits"][0]["score"] = 10**400  # type: ignore[index]
    else:
        response["latency_ms"] = 10**400

    with pytest.raises(ReadOnlyAdapterError) as caught:
        validate_raw_official_retrieve_response(
            response,
            request_payload=request,
            verified_provenance=_provenance(),
        )
    assert caught.value.code == ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED
    assert str(caught.value) == "response_contract_rejected"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


class _MetaTransport:
    def __init__(self, metas: list[dict[str, object]]) -> None:
        self.metas = list(metas)
        self.calls: list[dict[str, object]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        json_payload: dict[str, Any] | None,
        headers: dict[str, str],
        timeout: float,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "json_payload": json_payload,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return dict(self.metas.pop(0))


class _Delegate:
    def __init__(self, result: dict[str, object] | None = None) -> None:
        self.calls = 0
        self.result = result or {"stage1": {}, "stage2": {}, "observability": {}}

    def two_stage_retrieve(self, query: str, **kwargs: object) -> dict[str, object]:
        self.calls += 1
        return self.result


def _binding(tmp_path: Path) -> SourceSnapshotBindingV1:
    return SourceSnapshotBindingV1(
        canonical_kb_root=tmp_path,
        snapshot_sha256="b" * 64,
        collection=COLLECTION,
        kb_book_id=BOOK_ID,
        corpus_version=CORPUS_VERSION,
    )


def test_session_rechecks_exact_meta_before_and_after_without_auth(tmp_path: Path) -> None:
    """Catches returning a result after in-session meta drift."""

    stable = _base_meta()
    drifted = _base_meta(ingest_run_id="ingest_drifted")
    transport = _MetaTransport([stable, drifted])
    delegate = _Delegate()
    session = PinnedReadOnlyKBSession(
        retriever=delegate,
        request_transport=transport,
        validated_origin="http://127.0.0.1:8008",
        collection=COLLECTION,
        expected_corpus_version=CORPUS_VERSION,
        verified_provenance=_provenance(),
        source_binding=_binding(tmp_path),
        resolver_context=EvidenceResolverContext(
            source_root_label="kaiyuan_zhanjing",
            ingest_source_label="official",
        ),
    )

    with pytest.raises(ReadOnlyAdapterError) as caught:
        session.two_stage_retrieve("畢宿")
    assert caught.value.code == ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED
    assert delegate.calls == 1
    assert [call["headers"] for call in transport.calls] == [{}, {}]
    assert [call["timeout"] for call in transport.calls] == [10.0, 10.0]
    assert session.source_binding.snapshot_sha256 == "b" * 64
    assert session.resolver_context.source_root_label == "kaiyuan_zhanjing"
    assert not hasattr(session, "settings")
    assert not hasattr(session, "api_key")


def test_factory_reuses_one_resolved_path_and_hard_pins_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Catches double resolution or hostile config altering S1 wire policy."""

    root = tmp_path / "kb"
    snapshot = _source_snapshot(root)
    config = tmp_path / "config.yaml"
    _write_config(config)
    monkeypatch.setenv("KB_SEARCH_API_KEY", "unit-secret")
    resolved = config.resolve()
    captured: dict[str, object] = {}
    real_endpoint_loader = readonly_kb_module.load_kb_search_endpoint
    real_settings_loader = readonly_kb_module.load_settings

    def resolve_once(value: Path | None = None) -> Path:
        captured.setdefault("resolve_calls", 0)
        captured["resolve_calls"] = int(captured["resolve_calls"]) + 1
        return resolved

    def endpoint_loader(path: Path) -> str:
        captured["endpoint_path"] = path
        return real_endpoint_loader(path)

    def settings_loader(
        path: Path,
        *,
        kb_search_timeout_override: float | None = None,
    ):
        captured["settings_path"] = path
        captured["settings_timeout_override"] = kb_search_timeout_override
        return real_settings_loader(
            path,
            kb_search_timeout_override=kb_search_timeout_override,
        )

    class FakePinnedTransport(_MetaTransport):
        def __init__(self, origin: str) -> None:
            captured["origin"] = origin
            super().__init__([_base_meta()] * 20)

    class FakeRetriever:
        def __init__(self, *args: object, **kwargs: object) -> None:
            captured["retriever_args"] = args
            captured["retriever_kwargs"] = kwargs

        def two_stage_retrieve(self, query: str, **kwargs: object) -> dict[str, object]:
            return {"stage1": {}, "stage2": {}, "observability": {}}

    monkeypatch.setattr(readonly_kb_module, "resolve_kb_search_config_path", resolve_once)
    monkeypatch.setattr(readonly_kb_module, "load_kb_search_endpoint", endpoint_loader)
    monkeypatch.setattr(readonly_kb_module, "load_settings", settings_loader)
    monkeypatch.setattr(readonly_kb_module, "PinnedHTTPXJSONTransport", FakePinnedTransport)
    monkeypatch.setattr(readonly_kb_module, "KBSearchRetriever", FakeRetriever)

    with LocalKBSourceAccessor.open(kb_root=root, snapshot=snapshot) as accessor:
        session = build_readonly_kb_retriever(
            kb_root=root,
            collection=COLLECTION,
            expected_corpus_version=CORPUS_VERSION,
            source_accessor=accessor,
            source_snapshot=snapshot,
            source_snapshot_sha256=canonical_contract_sha256(snapshot),
            config_path=config,
        )
        kwargs = captured["retriever_kwargs"]
        args = captured["retriever_args"]
        assert isinstance(kwargs, dict)
        assert isinstance(args, tuple)
        isolated = args[4]
        assert isolated.kb_search_timeout_seconds == 10.0
        assert isolated.kb_search_query_normalize is True
        assert isolated.kb_search_query_s2t is True
        assert isolated.kb_search_query_t2s is True
        assert isolated.kb_enable_obsidian_source is False
        assert isolated.kb_enable_candidate_overlay is False
        assert isolated.kb_sources_root == str(root.resolve())
        assert args[2] == 10.0
        assert kwargs["request_transport"].calls[0]["timeout"] == 10.0
        assert kwargs["strict_primary_passages"] is True
        assert kwargs["primary_source_byte_loader"] is accessor
        assert isinstance(session.resolver_context, EvidenceResolverContext)
        assert session.source_binding == accessor.binding
        assert not hasattr(session, "verified_upstream_provenance")

    assert captured["resolve_calls"] == 1
    assert captured["endpoint_path"] is resolved
    assert captured["settings_path"] is resolved
    assert captured["settings_timeout_override"] == 10.0
    assert captured["origin"] == "http://127.0.0.1:8008"


@pytest.mark.parametrize(
    ("configured_timeout", "environment_timeout"),
    [
        ("nan", None),
        ("inf", None),
        ("0", "-1"),
        ("-1", "inf"),
        ("9" * 400, None),
        ("nan", "9" * 400),
    ],
)
def test_real_s1_retriever_hard_pins_variants_fallback_and_wire_timeouts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    configured_timeout: str,
    environment_timeout: str | None,
) -> None:
    """Catches hostile settings or legacy provenance keys escaping the real seam."""

    root = tmp_path / "kb"
    snapshot = _source_snapshot(
        root,
        body=(
            "# 唐開元占經\n"
            "<pb:KR3g0018_WYG_031-17a>\n"
            "甘氏曰熒惑守心，天下有兵。\n"
        ),
    )
    config = tmp_path / "config.yaml"
    _write_config(config)
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "  timeout_seconds: nan",
            f"  timeout_seconds: {configured_timeout}",
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KB_SEARCH_API_KEY", "unit-secret")
    monkeypatch.setenv("KB_SEARCH_API_PORT", "9" * 400)
    monkeypatch.setenv("KB_SEARCH_DEFAULT_COLLECTION", "hostile_collection")
    monkeypatch.setenv("KB_SEARCH_QUERY_NORMALIZE", "false")
    monkeypatch.setenv("KB_SEARCH_QUERY_S2T", "false")
    monkeypatch.setenv("KB_SEARCH_QUERY_T2S", "false")
    monkeypatch.setenv("KB_SOURCES_ROOT", str(tmp_path / "hostile-root"))
    monkeypatch.setenv("KB_ENABLE_OBSIDIAN_SOURCE", "true")
    monkeypatch.setenv("KB_ENABLE_CANDIDATE_OVERLAY", "true")
    if environment_timeout is None:
        monkeypatch.delenv("KB_SEARCH_TIMEOUT_SECONDS", raising=False)
    else:
        monkeypatch.setenv("KB_SEARCH_TIMEOUT_SECONDS", environment_timeout)

    class RecordingPinnedTransport:
        instances: list[RecordingPinnedTransport] = []

        def __init__(self, origin: str) -> None:
            self.origin = origin
            self.calls: list[dict[str, object]] = []
            self.instances.append(self)

        def request(
            self,
            method: str,
            url: str,
            *,
            json_payload: dict[str, Any] | None,
            headers: dict[str, str],
            timeout: float,
        ) -> dict[str, Any]:
            self.calls.append(
                {
                    "method": method,
                    "url": url,
                    "json_payload": json_payload,
                    "headers": headers,
                    "timeout": timeout,
                }
            )
            if url.endswith("/v1/meta"):
                return _base_meta()
            assert json_payload is not None
            return {
                "schema_version": "kb-retrieve/v2",
                "query_mode": json_payload["query_mode"],
                "retrieval_stage": json_payload["retrieval_stage"],
                "card_types": json_payload["card_types"],
                "collection": json_payload["collection"],
                "filters": json_payload.get("filters", {}),
                "hits": [],
                "retrieved_count": 0,
                "latency_ms": 1,
            }

    monkeypatch.setattr(
        readonly_kb_module,
        "PinnedHTTPXJSONTransport",
        RecordingPinnedTransport,
    )

    with LocalKBSourceAccessor.open(kb_root=root, snapshot=snapshot) as accessor:
        session = build_readonly_kb_retriever(
            kb_root=root,
            collection=COLLECTION,
            expected_corpus_version=CORPUS_VERSION,
            source_accessor=accessor,
            source_snapshot=snapshot,
            source_snapshot_sha256=canonical_contract_sha256(snapshot),
            config_path=config,
        )
        result = session.two_stage_retrieve(
            "荧惑守心",
            query_mode="evidence",
            filters={"kb_book_id": BOOK_ID},
        )
        accessor.assert_unchanged()

    transport = RecordingPinnedTransport.instances[0]
    retrieves = [
        call for call in transport.calls if str(call["url"]).endswith("/v1/retrieve")
    ]
    metas = [
        call for call in transport.calls if str(call["url"]).endswith("/v1/meta")
    ]
    assert [call["json_payload"]["query"] for call in retrieves] == [  # type: ignore[index]
        "荧惑守心",
        "荧惑守心",
    ]
    assert result["stage1"]["query_variants"] == [
        "荧惑守心",
        "熒惑守心",
        "荧惑 守心",
        "熒惑 守心",
    ]
    assert result["stage2"]["query_variants"] == [
        "荧惑守心",
        "熒惑守心",
        "荧惑 守心",
        "熒惑 守心",
    ]
    assert result["stage2"]["fallback_used"] is True
    assert result["stage2"]["fallback_reason"] == "official_primary_empty"
    assert result["stage2"]["primary_candidates"]
    for observability in (
        result["stage1"]["observability"],
        result["stage2"]["official_result"]["observability"],
        result["observability"],
    ):
        assert observability["upstream_provenance_sha256"] == (
            "f786107305e14b583ee3c8d12500ec7686d4c2475c9c211e287fbfe72a7597af"
        )
        assert "provenance_sha256" not in observability
    assert all(call["timeout"] == 10.0 for call in retrieves + metas)
    assert all(call["headers"] == {} for call in metas)
    assert all(
        call["headers"]
        == {
            "Authorization": "Bearer unit-secret",
            "X-API-Key": "unit-secret",
        }
        for call in retrieves
    )
