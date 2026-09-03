from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import src.connectors.kb_retrieval.core as core_module
import src.connectors.kb_retrieval.two_stage as two_stage_module
from kb_contracts import SyncErrorCode
from src.connectors.kb_search_retriever import KBSearchRetriever
from src.connectors.kb_search_retriever import KBSearchError
from src.connectors.kb_retrieval.transport import VerifiedUpstreamProvenanceV1
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
)
from src.video_pipeline.feedback_loop.readonly_kb_v1 import (
    validate_raw_official_retrieve_response,
)


def _settings(**overrides):
    values = {
        "kb_search_effective_base_url": "http://127.0.0.1:8008",
        "kb_search_timeout_seconds": 5.0,
        "kb_search_api_key": "unit-test-key",
        "kb_search_default_collection": "local_kb_kaiyuan_v2",
        "app_default_limit": 8,
        "kb_search_query_normalize": True,
        "kb_search_query_s2t": False,
        "kb_search_query_t2s": False,
        "kb_enable_candidate_overlay": False,
        "kb_candidate_overlay_root": "/tmp/candidates",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _retriever(**settings_overrides) -> KBSearchRetriever:
    return KBSearchRetriever(settings=_settings(**settings_overrides))


def _structured_response() -> dict:
    return {
        "schema_version": "kb-retrieve/v2",
        "query_mode": "evidence",
        "retrieval_stage": "structured_recall",
        "card_types": ["zhusu_card", "term_card", "extract_card"],
        "collection": "local_kb_kaiyuan_v2",
        "hits": [
            {
                "chunk_id": "term-1",
                "score": 0.7,
                "path": "/cards/熒惑.md",
                "title": "熒惑",
                "snippet": "熒惑，火星之名。",
                "card_type": "term_card",
                "kb_book_id": "kaiyuan_zhanjing",
                "evidence_level": "structured",
            }
        ],
        "retrieved_count": 1,
        "latency_ms": 1,
    }


def _primary_response() -> dict:
    return {
        "schema_version": "kb-retrieve/v2",
        "query_mode": "evidence",
        "retrieval_stage": "primary_evidence",
        "card_types": ["fenjuan", "fulltext"],
        "collection": "local_kb_kaiyuan_v2",
        "hits": [
            {
                "chunk_id": "passage-31",
                "score": 0.98,
                "path": "/corpus/KR3g0018_031.md",
                "title": "KR3g0018_031.md",
                "snippet": "石氏曰熒惑守心，天下兵起。",
                "card_type": "fenjuan",
                "kb_book_id": "kaiyuan_zhanjing",
                "book_title": "唐開元占經",
                "evidence_level": "primary",
                "final_citable": True,
                "source_locator": "KR3g0018_031",
                "source_volume": "卷31",
                "page_marker": "KR3g0018_WYG_031-17a",
                "heading_path": ["熒惑占二", "熒惑犯心五"],
                "paragraph_index": 3,
                "raw_start": 100,
                "raw_end": 115,
                "content_hash": "sha256:raw",
                "raw_content_hash": "sha256:raw",
                "normalized_content_hash": "sha256:normalized",
                "managed_by": "local-kb-unified/v2",
                "collection_schema": "passage-v2",
            }
        ],
        "retrieved_count": 1,
        "latency_ms": 1,
    }


def test_two_stage_calls_official_structured_then_primary_before_filesystem(monkeypatch):
    retriever = _retriever()
    calls: list[dict] = []

    def fake_request(method, path, **kwargs):
        assert method == "POST"
        assert path == "/v1/retrieve"
        payload = kwargs["json_payload"]
        calls.append(payload)
        if payload["retrieval_stage"] == "structured_recall":
            return _structured_response()
        if payload["retrieval_stage"] == "primary_evidence":
            return _primary_response()
        raise AssertionError(payload)

    monkeypatch.setattr(retriever, "_request", fake_request)
    monkeypatch.setattr(
        retriever,
        "_scan_primary_files",
        lambda *args, **kwargs: pytest.fail("filesystem fallback must not run"),
    )

    result = retriever.two_stage_retrieve(
        "荧惑守心",
        query_mode="evidence",
        filters={"book_id": "kaiyuan_zhanjing"},
        top_k=8,
    )

    assert [call["retrieval_stage"] for call in calls] == [
        "structured_recall",
        "primary_evidence",
    ]
    assert calls[0]["card_types"] == ["zhusu_card", "term_card", "extract_card"]
    assert calls[1]["card_types"] == ["fenjuan", "fulltext"]
    assert calls[0]["filters"] == {"kb_book_id": "kaiyuan_zhanjing"}
    assert calls[1]["filters"] == {"kb_book_id": "kaiyuan_zhanjing"}
    assert all("card_type" not in call["filters"] for call in calls)

    stage2 = result["stage2"]
    assert stage2["official_primary_used"] is True
    assert stage2["fallback_used"] is False
    assert stage2["hits"][0]["source_locator"] == "KR3g0018_031"
    assert stage2["hits"][0]["page_marker"] == "KR3g0018_WYG_031-17a"
    assert stage2["exact_hits"][0]["card_type"] == "fenjuan"


def test_filesystem_fallback_runs_only_when_official_primary_is_empty(monkeypatch):
    retriever = _retriever()
    calls: list[dict] = []

    def fake_request(method, path, **kwargs):
        payload = kwargs["json_payload"]
        calls.append(payload)
        if payload["retrieval_stage"] == "structured_recall":
            return _structured_response()
        return {
            "schema_version": "kb-retrieve/v2",
            "query_mode": "evidence",
            "retrieval_stage": "primary_evidence",
            "card_types": ["fenjuan", "fulltext"],
            "collection": "local_kb_kaiyuan_v2",
            "hits": [],
            "retrieved_count": 0,
            "latency_ms": 1,
        }

    fallback_hit = {
        "chunk_id": "fallback:31",
        "score": 1.0,
        "path": "/local/KR3g0018_031.md",
        "snippet": "石氏曰熒惑守心，天下兵起。",
        "card_type": "fenjuan",
        "kb_book_id": "kaiyuan_zhanjing",
        "source_locator": "KR3g0018_031",
        "page_marker": "KR3g0018_WYG_031-17a",
        "match_type": "exact_raw",
    }
    scan_calls: list[dict] = []

    def fake_scan(query, **kwargs):
        scan_calls.append({"query": query, **kwargs})
        return [fallback_hit], {
            "files_scanned": 2,
            "matched_files": [fallback_hit["path"]],
            "matched_headings": ["熒惑犯心五"],
            "matched_quotes": [fallback_hit["snippet"]],
        }

    monkeypatch.setattr(retriever, "_request", fake_request)
    monkeypatch.setattr(retriever, "_scan_primary_files", fake_scan)

    result = retriever.two_stage_retrieve(
        "荧惑守心",
        query_mode="evidence",
        filters={"kb_book_id": "kaiyuan_zhanjing"},
    )

    assert [call["retrieval_stage"] for call in calls] == [
        "structured_recall",
        "primary_evidence",
    ]
    assert len(scan_calls) == 1
    assert result["stage2"]["official_primary_used"] is False
    assert result["stage2"]["fallback_used"] is True
    assert result["stage2"]["fallback_reason"] == "official_primary_empty"
    assert result["stage2"]["exact_hits"] == [fallback_hit]


def test_rag_wire_call_uses_question_top_k_and_v2_stage_fields(monkeypatch):
    retriever = _retriever()
    captured: dict = {}

    def fake_request(method, path, **kwargs):
        captured.update(kwargs["json_payload"])
        assert path == "/v1/rag/query"
        return {
            "schema_version": "kb-rag/v2",
            "answer": "",
            "citations": [],
            "retrieved_count": 0,
            "latency_ms": 1,
        }

    monkeypatch.setattr(retriever, "_request", fake_request)
    retriever.rag_query(
        "《開元占經》如何記載熒惑守心？",
        book_id="kaiyuan_zhanjing",
        limit=6,
        query_mode="evidence",
        retrieval_stage="primary_evidence",
        card_types=["fenjuan", "fulltext"],
        generate=False,
    )

    assert captured["question"].startswith("《開元占經》")
    assert captured["top_k"] == 6
    assert captured["filters"] == {"kb_book_id": "kaiyuan_zhanjing"}
    assert captured["retrieval_stage"] == "primary_evidence"
    assert captured["card_types"] == ["fenjuan", "fulltext"]
    assert captured["generate"] is False
    assert "query" not in captured
    assert "limit" not in captured


def test_meta_client_preserves_explicit_missing_status(monkeypatch):
    retriever = _retriever()
    calls: list[str] = []

    def fake_request(method, path, **kwargs):
        calls.append(path)
        return {
            "meta_status": "missing",
            "error_code": "CORPUS_MANIFEST_MISSING",
        }

    monkeypatch.setattr(retriever, "_request", fake_request)
    result = retriever.get_upstream_meta()

    assert calls == ["/v1/meta"]
    assert result["meta_status"] == "missing"
    assert result["error_code"] == "CORPUS_MANIFEST_MISSING"
    assert "corpus_version" not in result


def test_two_stage_observability_records_ordered_official_stages(monkeypatch):
    retriever = _retriever()
    core_ticks = iter([0, 2_000_000, 2_000_000, 5_000_000])
    total_ticks = iter([0, 8_000_000])
    monkeypatch.setattr(core_module, "monotonic_ns", lambda: next(core_ticks))
    monkeypatch.setattr(two_stage_module, "monotonic_ns", lambda: next(total_ticks))

    def fake_request(method, path, **kwargs):
        stage = kwargs["json_payload"]["retrieval_stage"]
        response = _structured_response() if stage == "structured_recall" else _primary_response()
        return {
            **response,
            "collection": "effective-alias-v2",
            "corpus_version": "corpus-v2",
        }

    monkeypatch.setattr(retriever, "_request", fake_request)
    monkeypatch.setattr(
        retriever,
        "_scan_primary_files",
        lambda *args, **kwargs: pytest.fail("filesystem fallback must not run"),
    )

    result = retriever.two_stage_retrieve("荧惑守心", query_mode="evidence", top_k=8)

    trace = result["observability"]
    assert trace["schema_version"] == "kb-observability/v1"
    assert trace["operation"] == "two_stage_retrieve"
    assert trace["total_latency_ms"] == 8.0
    assert trace["collection"] == "effective-alias-v2"
    assert trace["corpus_version"] == "corpus-v2"
    assert [stage["stage"] for stage in trace["stages"]] == [
        "structured_recall",
        "primary_evidence",
    ]
    assert [stage["latency_ms"] for stage in trace["stages"]] == [2.0, 3.0]
    assert trace["stages"][0]["requested_top_k"] == 8
    assert trace["stages"][0]["raw_pool_size"] == 1
    assert trace["stages"][0]["returned_pool_size"] == 1
    assert trace["stages"][0]["upstream_latency_ms"] == 1.0


def test_two_stage_observability_does_not_guess_conflicting_provenance(monkeypatch):
    retriever = _retriever()

    def fake_request(method, path, **kwargs):
        stage = kwargs["json_payload"]["retrieval_stage"]
        if stage == "structured_recall":
            return {**_structured_response(), "collection": "collection-a", "corpus_version": "v1"}
        return {**_primary_response(), "collection": "collection-b", "corpus_version": "v2"}

    monkeypatch.setattr(retriever, "_request", fake_request)
    result = retriever.two_stage_retrieve("荧惑守心", query_mode="evidence")

    trace = result["observability"]
    assert trace["collection"] is None
    assert trace["corpus_version"] is None
    assert trace["provenance_conflicts"] == ["collection", "corpus_version"]


def test_filesystem_fallback_observability_records_reason_and_pool(monkeypatch):
    retriever = _retriever()
    core_ticks = iter([0, 1_000_000, 1_000_000, 3_000_000])
    total_ticks = iter([0, 4_000_000, 7_000_000, 10_000_000])
    monkeypatch.setattr(core_module, "monotonic_ns", lambda: next(core_ticks))
    monkeypatch.setattr(two_stage_module, "monotonic_ns", lambda: next(total_ticks))

    def fake_request(method, path, **kwargs):
        stage = kwargs["json_payload"]["retrieval_stage"]
        if stage == "structured_recall":
            return _structured_response()
        return {**_primary_response(), "hits": [], "retrieved_count": 0}

    fallback_hit = {
        "chunk_id": "fallback:31",
        "path": "/local/KR3g0018_031.md",
        "snippet": "熒惑守心",
        "card_type": "fenjuan",
        "match_type": "exact_raw",
    }
    monkeypatch.setattr(retriever, "_request", fake_request)
    monkeypatch.setattr(
        retriever,
        "_scan_primary_files",
        lambda *args, **kwargs: (
            [fallback_hit],
            {"files_scanned": 122, "matched_files": [], "matched_headings": [], "matched_quotes": []},
        ),
    )

    result = retriever.two_stage_retrieve("荧惑守心", query_mode="evidence", top_k=3)

    trace = result["observability"]
    fallback = trace["stages"][-1]
    assert fallback["operation"] == "filesystem_fallback"
    assert fallback["fallback_reason"] == "official_primary_empty"
    assert fallback["latency_ms"] == 3.0
    assert fallback["raw_pool_size"] == 122
    assert fallback["returned_pool_size"] == 1
    assert result["stage2"]["fallback_reason"] == "official_primary_empty"


def test_official_primary_error_carries_trace_and_never_falls_back(monkeypatch):
    retriever = _retriever()
    core_ticks = iter([0, 1_000_000, 1_000_000, 5_000_000])
    monkeypatch.setattr(core_module, "monotonic_ns", lambda: next(core_ticks))

    def fake_request(method, path, **kwargs):
        if kwargs["json_payload"]["retrieval_stage"] == "structured_recall":
            return _structured_response()
        raise KBSearchError("timed out", code=SyncErrorCode.TIMEOUT, retryable=True)

    monkeypatch.setattr(retriever, "_request", fake_request)
    monkeypatch.setattr(
        retriever,
        "_scan_primary_files",
        lambda *args, **kwargs: pytest.fail("error must not become filesystem fallback"),
    )

    with pytest.raises(KBSearchError) as caught:
        retriever.two_stage_retrieve("荧惑守心", query_mode="evidence", top_k=5)

    assert caught.value.code is SyncErrorCode.TIMEOUT
    trace = caught.value.details["observability"]
    assert trace["stage"] == "primary_evidence"
    assert trace["latency_ms"] == 4.0
    assert trace["requested_top_k"] == 5
    assert trace["collection"] == "local_kb_kaiyuan_v2"


def _verified_provenance() -> VerifiedUpstreamProvenanceV1:
    return VerifiedUpstreamProvenanceV1(
        corpus_version="20260903T010203Z",
        collection="local_kb_kaiyuan_v2",
        ingest_run_id="ingest_20260903T010203Z",
        source_manifest_hash="sha256:" + "a" * 64,
        created_at="2026-09-03T01:02:03Z",
        session_meta_sha256="b" * 64,
        provenance_sha256="c" * 64,
    )


def _strict_response(stage: str, hits: list[dict] | None = None) -> dict:
    rows = list(hits or [])
    return {
        "schema_version": "kb-retrieve/v2",
        "query_mode": "evidence",
        "retrieval_stage": stage,
        "card_types": (
            ["zhusu_card", "term_card", "extract_card"]
            if stage == "structured_recall"
            else ["fenjuan", "fulltext"]
        ),
        "collection": "local_kb_kaiyuan_v2",
        "filters": {"kb_book_id": "kaiyuan_zhanjing"},
        "hits": rows,
        "retrieved_count": len(rows),
        "latency_ms": 1,
    }


def _strict_retriever(**kwargs) -> KBSearchRetriever:
    provenance = _verified_provenance()

    def validator(response, *, request_payload):
        validate_raw_official_retrieve_response(
            response,
            request_payload=request_payload,
            verified_provenance=provenance,
        )

    return KBSearchRetriever(
        settings=_settings(
            kb_sources_root="/snapshot",
            kb_enable_obsidian_source=False,
        ),
        raw_response_validator=validator,
        strict_primary_passages=True,
        verified_upstream_provenance=provenance,
        **kwargs,
    )


@pytest.mark.parametrize("card_type", [None, "term_card", ""])
def test_malformed_nonempty_primary_response_fails_before_scanner(
    monkeypatch,
    card_type,
):
    """Catches filtering malformed official hits into fallback-eligible empty."""

    retriever = _strict_retriever()
    scanner_calls = 0

    def fake_request(method, path, **kwargs):
        stage = kwargs["json_payload"]["retrieval_stage"]
        if stage == "structured_recall":
            return _strict_response(stage)
        hit = {"snippet": "x", "score": 1.0}
        if card_type is not None:
            hit["card_type"] = card_type
        return _strict_response(stage, [hit])

    def scanner(*args, **kwargs):
        nonlocal scanner_calls
        scanner_calls += 1
        return [], {"files_scanned": 0}

    monkeypatch.setattr(retriever, "_request", fake_request)
    monkeypatch.setattr(retriever, "_scan_primary_files", scanner)

    with pytest.raises(ReadOnlyAdapterError) as caught:
        retriever.two_stage_retrieve(
            "荧惑守心",
            query_mode="evidence",
            filters={"kb_book_id": "kaiyuan_zhanjing"},
        )
    assert caught.value.code == ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED
    assert scanner_calls == 0


def test_malformed_empty_primary_response_fails_before_scanner(monkeypatch):
    """Catches fallback running before raw mandatory-field validation."""

    retriever = _strict_retriever()
    scanner_calls = 0

    def fake_request(method, path, **kwargs):
        stage = kwargs["json_payload"]["retrieval_stage"]
        response = _strict_response(stage)
        if stage == "primary_evidence":
            response.pop("filters")
        return response

    def scanner(*args, **kwargs):
        nonlocal scanner_calls
        scanner_calls += 1
        return [], {"files_scanned": 0}

    monkeypatch.setattr(retriever, "_request", fake_request)
    monkeypatch.setattr(retriever, "_scan_primary_files", scanner)

    with pytest.raises(ReadOnlyAdapterError):
        retriever.two_stage_retrieve(
            "荧惑守心",
            query_mode="evidence",
            filters={"kb_book_id": "kaiyuan_zhanjing"},
        )
    assert scanner_calls == 0


def test_validated_raw_empty_primary_response_may_use_snapshot_scanner(monkeypatch):
    """Catches preventing valid healthy-empty fallback after strict validation."""

    retriever = _strict_retriever()
    scanner_calls = 0

    def fake_request(method, path, **kwargs):
        return _strict_response(kwargs["json_payload"]["retrieval_stage"])

    def scanner(*args, **kwargs):
        nonlocal scanner_calls
        scanner_calls += 1
        return [], {
            "files_scanned": 1,
            "matched_files": [],
            "matched_headings": [],
            "matched_quotes": [],
        }

    monkeypatch.setattr(retriever, "_request", fake_request)
    monkeypatch.setattr(retriever, "_scan_primary_files", scanner)
    result = retriever.two_stage_retrieve(
        "荧惑守心",
        query_mode="evidence",
        filters={"kb_book_id": "kaiyuan_zhanjing"},
    )

    assert scanner_calls == 1
    assert result["stage2"]["official_primary_empty"] is True
    assert result["stage2"]["fallback_used"] is True


def test_verified_meta_provenance_is_added_only_to_observability(monkeypatch):
    """Catches mislabeling separately verified meta as a raw response field."""

    provenance = _verified_provenance()
    retriever = _strict_retriever()

    def fake_request(method, path, **kwargs):
        stage = kwargs["json_payload"]["retrieval_stage"]
        hits = []
        if stage == "primary_evidence":
            hits = [
                {
                    "snippet": "荧惑守心",
                    "score": 1.0,
                    "card_type": "fenjuan",
                }
            ]
        return _strict_response(stage, hits)

    monkeypatch.setattr(retriever, "_request", fake_request)
    monkeypatch.setattr(
        retriever,
        "_scan_primary_files",
        lambda *args, **kwargs: pytest.fail("official primary is nonempty"),
    )
    result = retriever.two_stage_retrieve(
        "荧惑守心",
        query_mode="evidence",
        filters={"kb_book_id": "kaiyuan_zhanjing"},
    )

    for stage in (result["stage1"], result["stage2"]["official_result"]):
        assert "corpus_version" not in stage
        assert stage["observability"]["corpus_version"] == provenance.corpus_version
        assert stage["observability"]["upstream_provenance_sha256"] == (
            provenance.provenance_sha256
        )
        assert "provenance_sha256" not in stage["observability"]
        assert stage["observability"]["corpus_provenance"] == "upstream_meta"
    outer = result["observability"]
    assert outer["corpus_version"] == provenance.corpus_version
    assert outer["upstream_provenance_sha256"] == provenance.provenance_sha256
    assert "provenance_sha256" not in outer
    assert outer["corpus_provenance"] == "upstream_meta"
    assert provenance.session_meta_sha256 not in json.dumps(result, ensure_ascii=False)


def test_provenance_guard_wraps_each_official_request_and_failure(monkeypatch):
    """Catches missing a pre/post meta guard around a failed stage-2 request."""

    events: list[str] = []
    retriever = _strict_retriever(
        upstream_provenance_guard=lambda: events.append("meta"),
    )

    def fake_request(method, path, **kwargs):
        stage = kwargs["json_payload"]["retrieval_stage"]
        events.append(stage)
        if stage == "primary_evidence":
            raise ReadOnlyAdapterError(ReadOnlyErrorCode.TRANSPORT_FAILED)
        return _strict_response(stage)

    monkeypatch.setattr(retriever, "_request", fake_request)
    monkeypatch.setattr(
        retriever,
        "_scan_primary_files",
        lambda *args, **kwargs: pytest.fail("failed official request must not scan"),
    )

    with pytest.raises(ReadOnlyAdapterError):
        retriever.two_stage_retrieve(
            "荧惑守心",
            query_mode="evidence",
            filters={"kb_book_id": "kaiyuan_zhanjing"},
        )
    assert events == [
        "meta",
        "structured_recall",
        "meta",
        "meta",
        "primary_evidence",
        "meta",
    ]
