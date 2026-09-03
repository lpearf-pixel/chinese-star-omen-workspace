from __future__ import annotations

import functools
import hashlib
import json
import math
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from pydantic import TypeAdapter, ValidationError

import src.connectors.kb_retrieval.transport as transport_module
from src.config.settings import (
    SettingsError,
    load_kb_search_endpoint,
    load_settings,
    require_api_key,
    resolve_kb_search_config_path,
)
from src.connectors.evidence_resolver import EvidenceResolverContext
from src.connectors.kb_retrieval.client import KBSearchRetriever
from src.connectors.kb_retrieval.transport import (
    JSONRequestTransport,
    PinnedHTTPXJSONTransport,
    S1_REQUEST_TIMEOUT_SECONDS,
    VerifiedUpstreamProvenanceV1,
)
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    CorpusVersion,
    LocalKBSourceSnapshotV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
    SourceSnapshotBindingV1,
    canonical_contract_sha256,
)
from src.video_pipeline.feedback_loop.source_snapshot_v1 import LocalKBSourceAccessor


_CORPUS_VERSION_ADAPTER = TypeAdapter(CorpusVersion)
_SHA256 = "sha256:"
_META_BASE_FIELDS = {
    "schema_version",
    "corpus_version",
    "ingest_run_id",
    "source_manifest_hash",
    "collection",
    "created_at",
}
_META_PUBLIC_FIELDS = {"meta_status", *_META_BASE_FIELDS}
_SCRIPT_FIELDS = {"source_roots", "excluded_roots"}
_INGEST_FIELDS = {"managed_by", "collection_schema", "run_stats"}
_RUN_STAT_FIELDS = {
    "desired",
    "new",
    "changed",
    "unchanged",
    "stale",
    "upserted",
    "deleted",
    "errors",
    "elapsed_ms",
}
_RESPONSE_FIELDS = {
    "schema_version",
    "query_mode",
    "retrieval_stage",
    "card_types",
    "collection",
    "filters",
    "hits",
    "retrieved_count",
    "latency_ms",
}


def _fail(code: ReadOnlyErrorCode) -> None:
    raise ReadOnlyAdapterError(code)


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _strict_string(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip()


def _finite_json_graph(value: object) -> bool:
    nodes = 0
    stack: list[tuple[object, int]] = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > 100_000 or depth > 64:
            return False
        if item is None or isinstance(item, (str, bool)):
            continue
        if type(item) is int:
            if abs(item) > sys.float_info.max:
                return False
            continue
        if type(item) is float:
            if not math.isfinite(item):
                return False
            continue
        if isinstance(item, Mapping):
            if any(not isinstance(key, str) for key in item):
                return False
            stack.extend((child, depth + 1) for child in item.values())
            continue
        if isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
            continue
        return False
    return True


def _has_finite_float_conversion(
    value: object,
    *,
    maximum_absolute_value: float = sys.float_info.max,
) -> bool:
    if type(value) not in {int, float}:
        return False
    try:
        converted = float(value)
    except (OverflowError, ValueError):
        return False
    return math.isfinite(converted) and abs(converted) <= maximum_absolute_value


def validate_literal_loopback_endpoint(value: str) -> str:
    """Return one canonical literal-loopback HTTP origin or fail safely."""

    origin: str | None = None
    valid = False
    try:
        if not isinstance(value, str) or not value or any(
            character.isspace() or ord(character) < 0x20 or ord(character) == 0x7F
            for character in value
        ):
            raise ValueError
        parsed = urlsplit(value)
        if (
            parsed.scheme != "http"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError
        port = parsed.port
        if port is None or not (1 <= port <= 65535):
            raise ValueError
        if parsed.hostname == "127.0.0.1":
            origin = f"http://127.0.0.1:{port}"
        elif parsed.hostname == "::1":
            origin = f"http://[::1]:{port}"
        else:
            raise ValueError
        if value not in {origin, f"{origin}/"}:
            raise ValueError
        valid = True
    except (TypeError, ValueError):
        pass
    if not valid or origin is None:
        _fail(ReadOnlyErrorCode.ENDPOINT_REJECTED)
    return origin


def validate_upstream_meta(
    response: Mapping[str, object],
    *,
    collection: str,
    expected_corpus_version: str,
) -> VerifiedUpstreamProvenanceV1:
    """Validate one exact deployed corpus manifest and derive two digests."""

    verified: VerifiedUpstreamProvenanceV1 | None = None
    try:
        if not isinstance(response, Mapping) or not _finite_json_graph(response):
            raise ValueError
        payload = dict(response)
        keys = set(payload)
        extension_keys = keys - _META_PUBLIC_FIELDS
        if extension_keys == set():
            producer_variant = "base"
        elif extension_keys == _SCRIPT_FIELDS:
            producer_variant = "corpus_manifest_script"
            for field in sorted(_SCRIPT_FIELDS):
                values = payload[field]
                if not isinstance(values, list) or any(
                    not _strict_string(item) for item in values
                ):
                    raise ValueError
        elif extension_keys == _INGEST_FIELDS:
            producer_variant = "normal_ingest"
            if (
                payload["managed_by"] != "local-kb-unified/v2"
                or payload["collection_schema"] != "passage-v2"
            ):
                raise ValueError
            stats = payload["run_stats"]
            if not isinstance(stats, Mapping) or set(stats) != _RUN_STAT_FIELDS:
                raise ValueError
            if any(
                isinstance(item, bool) or not isinstance(item, int) or item < 0
                for item in stats.values()
            ):
                raise ValueError
        else:
            raise ValueError
        if keys - extension_keys != _META_PUBLIC_FIELDS:
            raise ValueError
        if (
            payload["meta_status"] != "ok"
            or payload["schema_version"] != "corpus-manifest/v1"
            or payload["collection"] != collection
            or not _strict_string(payload["ingest_run_id"])
            or not _strict_string(payload["created_at"])
            or not isinstance(payload["source_manifest_hash"], str)
            or len(payload["source_manifest_hash"]) != 71
            or not payload["source_manifest_hash"].startswith(_SHA256)
            or any(
                character not in "0123456789abcdef"
                for character in payload["source_manifest_hash"][7:]
            )
        ):
            raise ValueError
        _CORPUS_VERSION_ADAPTER.validate_python(payload["corpus_version"])
        _CORPUS_VERSION_ADAPTER.validate_python(expected_corpus_version)
        if payload["corpus_version"] != expected_corpus_version:
            raise ValueError
        semantic = {
            field: payload[field]
            for field in (
                "schema_version",
                "corpus_version",
                "ingest_run_id",
                "source_manifest_hash",
                "collection",
                "created_at",
            )
        }
        semantic["producer_variant"] = producer_variant
        verified = VerifiedUpstreamProvenanceV1(
            corpus_version=str(payload["corpus_version"]),
            collection=str(payload["collection"]),
            ingest_run_id=str(payload["ingest_run_id"]),
            source_manifest_hash=str(payload["source_manifest_hash"]),
            created_at=str(payload["created_at"]),
            session_meta_sha256=_sha256_json(payload),
            provenance_sha256=_sha256_json(semantic),
        )
    except (KeyError, TypeError, ValueError, ValidationError):
        pass
    if verified is None:
        _fail(ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED)
    return verified


def validate_raw_official_retrieve_response(
    response: Mapping[str, object],
    *,
    request_payload: Mapping[str, object],
    verified_provenance: VerifiedUpstreamProvenanceV1,
) -> None:
    """Validate response-owned deployed fields before any normalization/fallback."""

    try:
        if (
            not isinstance(response, Mapping)
            or not isinstance(request_payload, Mapping)
            or not _finite_json_graph(response)
        ):
            raise ValueError
        response_value = dict(response)
        request_value = dict(request_payload)
        response_keys = set(response_value)
        if response_keys != _RESPONSE_FIELDS and response_keys != (
            _RESPONSE_FIELDS | {"corpus_version"}
        ):
            raise ValueError
        if (
            response_value["schema_version"] != "kb-retrieve/v2"
            or response_value["schema_version"] != request_value.get("schema_version")
            or response_value["query_mode"] != request_value.get("query_mode")
            or response_value["retrieval_stage"] != request_value.get("retrieval_stage")
            or response_value["card_types"] != request_value.get("card_types")
            or response_value["collection"] != request_value.get("collection")
            or response_value["collection"] != verified_provenance.collection
            or response_value["filters"] != request_value.get("filters", {})
        ):
            raise ValueError
        if "corpus_version" in response_value and response_value[
            "corpus_version"
        ] != verified_provenance.corpus_version:
            raise ValueError
        hits = response_value["hits"]
        count = response_value["retrieved_count"]
        latency = response_value["latency_ms"]
        if (
            not isinstance(hits, list)
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
            or count != len(hits)
            or isinstance(latency, bool)
            or not isinstance(latency, int)
            or latency < 0
            or not _has_finite_float_conversion(latency)
        ):
            raise ValueError
        requested_pool = request_value.get("card_types")
        if not isinstance(requested_pool, list) or any(
            not _strict_string(item) for item in requested_pool
        ):
            raise ValueError
        primary = request_value.get("retrieval_stage") == "primary_evidence"
        for hit in hits:
            if not isinstance(hit, Mapping):
                raise ValueError
            score = hit.get("score")
            snippet = hit.get("snippet")
            if (
                not _has_finite_float_conversion(
                    score,
                    maximum_absolute_value=sys.float_info.max / 10,
                )
                or not isinstance(snippet, str)
            ):
                raise ValueError
            if primary and hit.get("card_type") not in requested_pool:
                raise ValueError
    except (KeyError, TypeError, ValueError):
        pass
    else:
        return
    _fail(ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED)


class PinnedReadOnlyKBSession:
    """Narrow retriever session bound to immutable source and upstream identity."""

    def __init__(
        self,
        *,
        retriever: object,
        request_transport: JSONRequestTransport,
        validated_origin: str,
        collection: str,
        expected_corpus_version: str,
        verified_provenance: VerifiedUpstreamProvenanceV1,
        source_binding: SourceSnapshotBindingV1,
        resolver_context: EvidenceResolverContext,
    ) -> None:
        self._retriever = retriever
        self._request_transport = request_transport
        self._validated_origin = validated_origin
        self._collection = collection
        self._expected_corpus_version = expected_corpus_version
        self._verified_provenance = verified_provenance
        self._source_binding = source_binding
        self._resolver_context = resolver_context

    @property
    def source_binding(self) -> SourceSnapshotBindingV1:
        return self._source_binding

    @property
    def resolver_context(self) -> EvidenceResolverContext:
        return self._resolver_context

    def _assert_meta(self) -> None:
        response = self._request_transport.request(
            "GET",
            f"{self._validated_origin}/v1/meta",
            json_payload=None,
            headers={},
            timeout=S1_REQUEST_TIMEOUT_SECONDS,
        )
        observed = validate_upstream_meta(
            response,
            collection=self._collection,
            expected_corpus_version=self._expected_corpus_version,
        )
        if observed != self._verified_provenance:
            _fail(ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED)

    def two_stage_retrieve(self, query: str, **kwargs: object) -> Mapping[str, object]:
        self._assert_meta()
        try:
            return self._retriever.two_stage_retrieve(query, **kwargs)  # type: ignore[attr-defined]
        finally:
            self._assert_meta()


def build_readonly_kb_retriever(
    *,
    kb_root: Path,
    collection: str,
    expected_corpus_version: str,
    source_accessor: LocalKBSourceAccessor,
    source_snapshot: LocalKBSourceSnapshotV1,
    source_snapshot_sha256: str,
    config_path: Path | None = None,
) -> PinnedReadOnlyKBSession:
    """Build the production-only S1 retriever in fail-closed dependency order."""

    if collection != "local_kb_kaiyuan_v2":
        _fail(ReadOnlyErrorCode.PLAN_MISMATCH)
    if (
        canonical_contract_sha256(source_snapshot) != source_snapshot_sha256
        or source_snapshot.collection != collection
        or source_snapshot.corpus_version != expected_corpus_version
    ):
        _fail(ReadOnlyErrorCode.SNAPSHOT_MISMATCH)
    source_accessor.assert_bound(
        kb_root=kb_root,
        snapshot=source_snapshot,
        snapshot_sha256=source_snapshot_sha256,
    )
    binding = source_accessor.binding
    resolved_config: Path | None = None
    endpoint: str | None = None
    try:
        resolved_config = resolve_kb_search_config_path(config_path)
        endpoint = load_kb_search_endpoint(resolved_config)
    except (OSError, RuntimeError, SettingsError, ValueError):
        pass
    if resolved_config is None or endpoint is None:
        _fail(ReadOnlyErrorCode.ENDPOINT_REJECTED)
    validated_origin = validate_literal_loopback_endpoint(endpoint)
    root: Path | None = None
    root_valid = False
    try:
        _CORPUS_VERSION_ADAPTER.validate_python(expected_corpus_version)
        root = Path(kb_root).expanduser().resolve(strict=True)
        if not root.is_dir() or transport_module.httpx is None:
            raise ValueError
        root_valid = True
    except (OSError, RuntimeError, ValidationError, ValueError):
        pass
    if not root_valid or root is None:
        _fail(ReadOnlyErrorCode.SNAPSHOT_MISMATCH)
    request_transport = PinnedHTTPXJSONTransport(validated_origin)
    preflight_meta = request_transport.request(
        "GET",
        f"{validated_origin}/v1/meta",
        json_payload=None,
        headers={},
        timeout=S1_REQUEST_TIMEOUT_SECONDS,
    )
    verified = validate_upstream_meta(
        preflight_meta,
        collection=collection,
        expected_corpus_version=expected_corpus_version,
    )
    loaded_settings = None
    api_key: str | None = None
    try:
        loaded_settings = load_settings(
            resolved_config,
            kb_search_timeout_override=S1_REQUEST_TIMEOUT_SECONDS,
        )
        api_key = require_api_key(loaded_settings)
    except (SettingsError, OSError, RuntimeError, ValueError):
        pass
    if loaded_settings is None or api_key is None:
        _fail(ReadOnlyErrorCode.CREDENTIAL_UNAVAILABLE)
    isolated_settings = replace(
        loaded_settings,
        kb_search_base_url=validated_origin,
        kb_search_api_port=urlsplit(validated_origin).port or 0,
        kb_search_api_key=api_key,
        kb_search_default_collection=collection,
        kb_search_timeout_seconds=S1_REQUEST_TIMEOUT_SECONDS,
        kb_search_query_normalize=True,
        kb_search_query_s2t=True,
        kb_search_query_t2s=True,
        kb_sources_root=str(root),
        kb_enable_obsidian_source=False,
        kb_enable_candidate_overlay=False,
    )

    def assert_same_upstream_meta() -> None:
        current_meta = request_transport.request(
            "GET",
            f"{validated_origin}/v1/meta",
            json_payload=None,
            headers={},
            timeout=S1_REQUEST_TIMEOUT_SECONDS,
        )
        current = validate_upstream_meta(
            current_meta,
            collection=collection,
            expected_corpus_version=expected_corpus_version,
        )
        if current != verified:
            _fail(ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED)

    raw_validator = functools.partial(
        validate_raw_official_retrieve_response,
        verified_provenance=verified,
    )
    retriever = KBSearchRetriever(
        validated_origin,
        api_key,
        S1_REQUEST_TIMEOUT_SECONDS,
        collection,
        isolated_settings,
        request_transport=request_transport,
        primary_source_byte_loader=source_accessor,
        raw_response_validator=raw_validator,
        strict_primary_passages=True,
        verified_upstream_provenance=verified,
        upstream_provenance_guard=assert_same_upstream_meta,
    )
    resolver_context = EvidenceResolverContext(
        source_root_label=isolated_settings.kb_obsidian_source_root_label,
        ingest_source_label=isolated_settings.kb_obsidian_ingest_source_label,
    )
    return PinnedReadOnlyKBSession(
        retriever=retriever,
        request_transport=request_transport,
        validated_origin=validated_origin,
        collection=collection,
        expected_corpus_version=expected_corpus_version,
        verified_provenance=verified,
        source_binding=binding,
        resolver_context=resolver_context,
    )


__all__ = [
    "PinnedReadOnlyKBSession",
    "S1_REQUEST_TIMEOUT_SECONDS",
    "build_readonly_kb_retriever",
    "validate_literal_loopback_endpoint",
    "validate_raw_official_retrieve_response",
    "validate_upstream_meta",
]
