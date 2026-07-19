"""Build one content-free release observation from injected read adapters."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from typing import Any

from release_drill import (
    COLLECTION_NAME_RE,
    MANIFEST_IDENTITY_FIELDS,
    PROTECTED_COLLECTION,
    REQUIRED_HEALTH_CHECKS,
    STAGE_CARD_TYPES,
)

OBSERVATION_SCHEMA = "kaiyuan-release-observation/v1"
CONFIG_FIELDS = {
    "vectors": ("size", "distance", "on_disk", "datatype"),
    "optimizer_config": (
        "deleted_threshold",
        "vacuum_min_vector_number",
        "default_segment_number",
        "max_segment_size",
        "memmap_threshold",
        "indexing_threshold",
        "flush_interval_sec",
        "max_optimization_threads",
    ),
    "hnsw_config": ("m", "ef_construct", "full_scan_threshold", "max_indexing_threads", "on_disk", "payload_m"),
}
SCALAR_CONFIG_FIELDS = (
    "shard_number",
    "replication_factor",
    "write_consistency_factor",
    "on_disk_payload",
)


class ReleaseObservationError(RuntimeError):
    def __init__(self, code: str, operation: str):
        self.code = code
        self.operation = operation
        super().__init__(f"{code}: {operation}")


def _body(response: Any, operation: str) -> Mapping[str, Any]:
    if not isinstance(response, Mapping) or response.get("http_status") != 200:
        raise ReleaseObservationError("invalid_response", operation)
    body = response.get("body")
    if not isinstance(body, Mapping):
        raise ReleaseObservationError("invalid_response", operation)
    return body


def _config_hash(config: Any) -> str:
    if not isinstance(config, Mapping):
        raise ReleaseObservationError("invalid_response", "inspect_collection")
    vectors = config.get("vectors")
    if (
        not isinstance(vectors, Mapping)
        or isinstance(vectors.get("size"), bool)
        or not isinstance(vectors.get("size"), int)
        or vectors["size"] <= 0
        or not isinstance(vectors.get("distance"), str)
        or not vectors["distance"]
    ):
        raise ReleaseObservationError("invalid_response", "inspect_collection")
    projected = {name: config[name] for name in SCALAR_CONFIG_FIELDS if name in config}
    for section, fields in CONFIG_FIELDS.items():
        value = config.get(section)
        if isinstance(value, Mapping):
            projected[section] = {name: value[name] for name in fields if name in value}
    try:
        encoded = json.dumps(projected, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ReleaseObservationError("invalid_response", "inspect_collection") from exc
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def capture_phase_observation(
    *,
    active_collection: str,
    query: str,
    fetch_health: Callable[[], Any],
    fetch_meta: Callable[[], Any],
    retrieve: Callable[..., Any],
    inspect_collection: Callable[[str], Any],
    captured_at: str,
) -> dict[str, object]:
    if (
        not isinstance(active_collection, str)
        or COLLECTION_NAME_RE.fullmatch(active_collection) is None
        or not isinstance(query, str)
        or not query.strip()
    ):
        raise ReleaseObservationError("contract_error", "input")
    health = _body(fetch_health(), "health")
    checks = health.get("checks")
    if (
        health.get("status") != "ok"
        or health.get("ready") is not True
        or health.get("default_collection") != active_collection
        or not isinstance(checks, Mapping)
        or any(checks.get(name) is not True for name in REQUIRED_HEALTH_CHECKS)
    ):
        raise ReleaseObservationError("contract_error", "health")

    meta = _body(fetch_meta(), "meta")
    if (
        meta.get("meta_status") != "ok"
        or meta.get("schema_version") != "corpus-manifest/v1"
        or meta.get("managed_by") != "local-kb-unified/v2"
        or meta.get("collection_schema") != "passage-v2"
        or meta.get("collection") != active_collection
        or any(not isinstance(meta.get(name), str) or not meta[name] for name in MANIFEST_IDENTITY_FIELDS)
    ):
        raise ReleaseObservationError("contract_error", "meta")

    smoke = {}
    for stage in ("structured_recall", "primary_evidence"):
        pool = list(STAGE_CARD_TYPES[stage])
        body = _body(
            retrieve(
                query=query,
                collection=active_collection,
                retrieval_stage=stage,
                card_types=pool,
                filters={"kb_book_id": "kaiyuan_zhanjing"},
            ),
            stage,
        )
        count = body.get("retrieved_count")
        hits = body.get("hits")
        if (
            body.get("retrieval_stage") != stage
            or body.get("card_types") != pool
            or body.get("collection") != active_collection
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count <= 0
            or not isinstance(hits, list)
            or len(hits) != count
        ):
            raise ReleaseObservationError("invalid_response", stage)
        smoke[stage] = {
            "status": "ok",
            "http_status": 200,
            "retrieval_stage": stage,
            "card_types": pool,
            "collection": active_collection,
            "hits_count": count,
        }

    collections = {}
    for name in dict.fromkeys((PROTECTED_COLLECTION, active_collection)):
        observed = inspect_collection(name)
        if not isinstance(observed, Mapping) or observed.get("exists") is not True:
            raise ReleaseObservationError("collection_not_found", "inspect_collection")
        count = observed.get("points_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ReleaseObservationError("invalid_response", "inspect_collection")
        collections[name] = {
            "exists": True,
            "points_count": count,
            "config_hash": _config_hash(observed.get("config")),
        }

    return {
        "schema_version": OBSERVATION_SCHEMA,
        "captured_at": captured_at,
        "phase": {
            "active_collection": active_collection,
            "health": {
                "status": "ok",
                "ready": True,
                "checks": {name: True for name in REQUIRED_HEALTH_CHECKS},
            },
            "meta": {"meta_status": "ok", **{name: meta[name] for name in MANIFEST_IDENTITY_FIELDS}},
            "smoke": smoke,
            "collections": collections,
        },
    }
