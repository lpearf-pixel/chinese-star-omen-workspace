from __future__ import annotations

import json
import logging
from typing import Any

try:
    import httpx
except ModuleNotFoundError:  # pragma: no cover
    httpx = None

from src.config.settings import Settings, SettingsError, get_settings, mask_secret, require_api_key

logger = logging.getLogger(__name__)


class KBSearchError(RuntimeError):
    pass


class TransportMixin:
    INVALID_API_KEY_PLACEHOLDERS = {"change_me", "please_change_me", "replace_me"}

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
        default_collection: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        cfg = settings or get_settings()
        self.settings = cfg
        self.base_url = (base_url or cfg.kb_search_effective_base_url).rstrip("/")
        self.timeout = timeout if timeout is not None else cfg.kb_search_timeout_seconds
        self.api_key = api_key if api_key is not None else cfg.kb_search_api_key
        self.default_collection = default_collection or cfg.kb_search_default_collection
        self.default_limit = cfg.app_default_limit

    def _auth_headers(self) -> dict[str, str]:
        key = (self.api_key or "").strip()
        if not key:
            try:
                key = require_api_key()
            except SettingsError as exc:
                raise KBSearchError(str(exc)) from exc
        if key.lower() in self.INVALID_API_KEY_PLACEHOLDERS:
            raise KBSearchError(
                "Invalid KB_SEARCH_API_KEY: placeholder value detected, please set a real API key"
            )
        return {"Authorization": f"Bearer {key}", "X-API-Key": key}

    @staticmethod
    def _wire_payload(json_payload: dict[str, Any] | None) -> dict[str, Any] | None:
        """Return the canonical HTTP representation without mutating callers."""

        if json_payload is None:
            return None
        payload = dict(json_payload)
        filters = payload.get("filters")
        if isinstance(filters, dict):
            canonical_filters = dict(filters)
            legacy = canonical_filters.get("book_id")
            current = canonical_filters.get("kb_book_id")
            if legacy is not None and current is not None and str(legacy) != str(current):
                raise KBSearchError(
                    "conflicting book identifiers in filters: book_id and kb_book_id"
                )
            if current is None and legacy is not None:
                canonical_filters["kb_book_id"] = legacy
            canonical_filters.pop("book_id", None)
            payload["filters"] = canonical_filters

        legacy_top = payload.get("book_id")
        current_top = payload.get("kb_book_id")
        if legacy_top is not None and current_top is not None and str(legacy_top) != str(current_top):
            raise KBSearchError(
                "conflicting top-level book identifiers: book_id and kb_book_id"
            )
        if current_top is None and legacy_top is not None:
            payload["kb_book_id"] = legacy_top
        payload.pop("book_id", None)
        return payload

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_payload: dict[str, Any] | None = None,
        use_auth: bool = False,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = self._auth_headers() if use_auth else {}
        wire_payload = self._wire_payload(json_payload)
        try:
            if httpx is not None:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(method, url, json=wire_payload, headers=headers)
                    response.raise_for_status()
                    return response.json()

            import urllib.request

            data = json.dumps(wire_payload).encode("utf-8") if wire_payload is not None else None
            request = urllib.request.Request(
                url,
                data=data,
                method=method,
                headers={**headers, "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except KBSearchError:
            raise
        except Exception as exc:  # pragma: no cover
            logger.error(
                "kb-search request failed method=%s url=%s api_key=%s error=%s",
                method,
                url,
                mask_secret(self.api_key),
                exc,
            )
            raise KBSearchError(
                f"kb-search request failed: method={method} url={url} error={exc}"
            ) from exc

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/v1/health", use_auth=False)

    def get_upstream_meta(self) -> dict[str, Any]:
        """Return the explicit `/v1/meta` status without inventing unknown values."""

        return self._request("GET", "/v1/meta", use_auth=False)
