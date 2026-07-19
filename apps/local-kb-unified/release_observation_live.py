"""Live read-only adapters for Kaiyuan release observations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests

from release_observation import ReleaseObservationError


class KBSearchReadClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout_seconds: float,
        session: Any = requests,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._session = session

    def _request(self, method: str, path: str, *, operation: str, authenticated: bool, json_body=None):
        headers = {"Authorization": f"Bearer {self._api_key}"} if authenticated else {}
        try:
            response = self._session.request(
                method,
                f"{self._base_url}{path}",
                headers=headers,
                timeout=self._timeout,
                **({"json": json_body} if json_body is not None else {}),
            )
        except requests.Timeout as exc:
            raise ReleaseObservationError("timeout", operation) from exc
        except requests.RequestException as exc:
            raise ReleaseObservationError("upstream_unavailable", operation) from exc
        status = getattr(response, "status_code", None)
        if status in (401, 403):
            raise ReleaseObservationError("authentication_failed", operation)
        if status == 404:
            try:
                error_body = response.json()
            except (TypeError, ValueError):
                error_body = None
            error_code = _error_code(error_body)
            code = "collection_not_found" if error_code == "COLLECTION_NOT_FOUND" else "contract_error"
            raise ReleaseObservationError(code, operation)
        if status == 422:
            raise ReleaseObservationError("contract_error", operation)
        if not isinstance(status, int) or status >= 400:
            raise ReleaseObservationError("upstream_unavailable", operation)
        if status != 200:
            raise ReleaseObservationError("invalid_response", operation)
        try:
            body = response.json()
        except (TypeError, ValueError) as exc:
            raise ReleaseObservationError("invalid_response", operation) from exc
        if not isinstance(body, Mapping):
            raise ReleaseObservationError("invalid_response", operation)
        return {"http_status": status, "body": dict(body)}

    def health(self):
        return self._request("GET", "/v1/health", operation="health", authenticated=False)

    def meta(self):
        return self._request("GET", "/v1/meta", operation="meta", authenticated=False)

    def retrieve(self, *, query, collection, retrieval_stage, card_types, filters):
        body = {
            "schema_version": "kb-retrieve/v2",
            "query": query,
            "top_k": 5,
            "collection": collection,
            "filters": filters,
            "retrieval_stage": retrieval_stage,
            "card_types": list(card_types),
            "literal_first": True,
        }
        return self._request(
            "POST",
            "/v1/retrieve",
            operation=retrieval_stage,
            authenticated=True,
            json_body=body,
        )


class QdrantCollectionReader:
    def __init__(self, client: Any):
        self._client = client

    def inspect(self, collection: str):
        try:
            if not self._client.collection_exists(collection_name=collection):
                return {"exists": False}
            info = self._client.get_collection(collection_name=collection)
            counted = self._client.count(collection_name=collection, exact=True)
        except Exception as exc:
            raise ReleaseObservationError("upstream_unavailable", "inspect_collection") from exc

        config = getattr(info, "config", None)
        params = getattr(config, "params", None)
        vectors = getattr(params, "vectors", None)
        projected: dict[str, Any] = {}

        vector_fields = _object_fields(vectors, ("size", "distance", "on_disk", "datatype"))
        if vector_fields:
            projected["vectors"] = vector_fields
        for name in (
            "shard_number",
            "replication_factor",
            "write_consistency_factor",
            "on_disk_payload",
        ):
            value = getattr(params, name, None)
            if value is not None:
                projected[name] = _public_value(value)
        for section, fields in (
            (
                "optimizer_config",
                (
                    "deleted_threshold",
                    "vacuum_min_vector_number",
                    "default_segment_number",
                    "max_segment_size",
                    "memmap_threshold",
                    "indexing_threshold",
                    "flush_interval_sec",
                    "max_optimization_threads",
                ),
            ),
            (
                "hnsw_config",
                ("m", "ef_construct", "full_scan_threshold", "max_indexing_threads", "on_disk", "payload_m"),
            ),
        ):
            values = _object_fields(getattr(config, section, None), fields)
            if values:
                projected[section] = values

        points_count = getattr(counted, "count", None)
        if isinstance(points_count, bool) or not isinstance(points_count, int) or points_count < 0:
            raise ReleaseObservationError("invalid_response", "inspect_collection")
        return {"exists": True, "points_count": points_count, "config": projected}


def _public_value(value: Any) -> Any:
    public = getattr(value, "value", value)
    if isinstance(public, (str, int, float, bool)) or public is None:
        return public
    raise ReleaseObservationError("invalid_response", "inspect_collection")


def _error_code(body: Any) -> str | None:
    if not isinstance(body, Mapping):
        return None
    detail = body.get("detail")
    if isinstance(detail, Mapping):
        body = detail
    error = body.get("error") if isinstance(body, Mapping) else None
    if isinstance(error, Mapping) and isinstance(error.get("code"), str):
        return error["code"]
    if isinstance(body.get("code"), str):
        return body["code"]
    return None


def _object_fields(value: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    if value is None:
        return {}
    output = {}
    for name in fields:
        item = getattr(value, name, None)
        if item is not None:
            output[name] = _public_value(item)
    return output
