from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

try:
    import httpx
except ModuleNotFoundError:  # pragma: no cover
    httpx = None

CONTRACTS = Path(__file__).resolve().parents[5] / "packages" / "kb-contracts" / "python"
if str(CONTRACTS) not in sys.path:
    sys.path.insert(0, str(CONTRACTS))

from kb_contracts import SyncErrorCode, sync_error_payload  # noqa: E402
from src.config.settings import (  # noqa: E402
    Settings,
    SettingsError,
    get_settings,
    mask_secret,
    require_api_key,
)

logger = logging.getLogger(__name__)


class KBSearchError(RuntimeError):
    """Structured downstream error used by retrieval and candidate sync."""

    def __init__(
        self,
        message: str,
        *,
        code: SyncErrorCode | str = SyncErrorCode.UPSTREAM_UNAVAILABLE,
        status_code: int | None = None,
        retryable: bool | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        payload = sync_error_payload(
            code,
            message,
            status_code=status_code,
            retryable=retryable,
            details=details,
        )
        super().__init__(payload["message"])
        self.code = SyncErrorCode(payload["code"])
        self.status_code = payload["status_code"]
        self.retryable = bool(payload["retryable"])
        self.details = dict(payload["details"])

    def to_dict(self) -> dict[str, Any]:
        return sync_error_payload(
            self.code,
            str(self),
            status_code=self.status_code,
            retryable=self.retryable,
            details=self.details,
        )


def _response_error_data(response: Any) -> tuple[str | None, str, dict[str, Any]]:
    body: Any = None
    try:
        body = response.json()
    except Exception:
        body = None

    details: dict[str, Any] = {}
    raw_code: str | None = None
    message = f"HTTP {getattr(response, 'status_code', 'error')}"
    if isinstance(body, dict):
        details = dict(body)
        detail = body.get("detail", body)
        if isinstance(detail, dict):
            error = detail.get("error", detail)
            if isinstance(error, dict):
                if error.get("code") is not None:
                    raw_code = str(error.get("code"))
                if error.get("message") is not None:
                    message = str(error.get("message"))
            elif detail.get("message") is not None:
                message = str(detail.get("message"))
        elif detail is not None:
            message = str(detail)
    return raw_code, message, details


def _code_from_status(status: int | None, raw_code: str | None) -> SyncErrorCode:
    normalized = str(raw_code or "").strip().upper()
    explicit = {
        "UNAUTHORIZED": SyncErrorCode.AUTHENTICATION_FAILED,
        "AUTHENTICATION_FAILED": SyncErrorCode.AUTHENTICATION_FAILED,
        "UPSTREAM_UNAVAILABLE": SyncErrorCode.UPSTREAM_UNAVAILABLE,
        "TIMEOUT": SyncErrorCode.TIMEOUT,
        "CONTRACT_ERROR": SyncErrorCode.CONTRACT_ERROR,
        "COLLECTION_NOT_FOUND": SyncErrorCode.COLLECTION_NOT_FOUND,
        "INVALID_RESPONSE": SyncErrorCode.INVALID_RESPONSE,
    }
    if normalized in explicit:
        return explicit[normalized]
    if status in {401, 403}:
        return SyncErrorCode.AUTHENTICATION_FAILED
    if status == 404:
        # Only an explicit upstream COLLECTION_NOT_FOUND code proves that the
        # Qdrant collection is absent. A generic 404 commonly means an old or
        # missing route and is therefore a non-retryable contract mismatch.
        return SyncErrorCode.CONTRACT_ERROR
    if status in {408, 504}:
        return SyncErrorCode.TIMEOUT
    if status == 422:
        return SyncErrorCode.CONTRACT_ERROR
    if status == 429 or (status is not None and status >= 500):
        return SyncErrorCode.UPSTREAM_UNAVAILABLE
    return SyncErrorCode.INVALID_RESPONSE


def classify_transport_exception(exc: Exception) -> KBSearchError:
    """Normalize HTTP/client failures into the shared sync taxonomy."""

    if isinstance(exc, KBSearchError):
        return exc

    if httpx is not None:
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            raw_code, message, details = _response_error_data(exc.response)
            return KBSearchError(
                message,
                code=_code_from_status(status, raw_code),
                status_code=status,
                details=details,
            )
        if isinstance(exc, httpx.TimeoutException):
            return KBSearchError(
                str(exc) or "upstream request timed out",
                code=SyncErrorCode.TIMEOUT,
                retryable=True,
            )
        if isinstance(exc, httpx.RequestError):
            return KBSearchError(
                str(exc) or "upstream request failed",
                code=SyncErrorCode.UPSTREAM_UNAVAILABLE,
                retryable=True,
            )

    try:
        from urllib.error import HTTPError, URLError

        if isinstance(exc, HTTPError):
            status = int(exc.code)
            raw_body = exc.read().decode("utf-8", errors="replace")
            parsed: Any = None
            try:
                parsed = json.loads(raw_body) if raw_body else None
            except json.JSONDecodeError:
                parsed = None
            raw_code: str | None = None
            message = str(exc.reason or f"HTTP {status}")
            details: dict[str, Any] = {}
            if isinstance(parsed, dict):
                details = parsed
                detail = parsed.get("detail", parsed)
                if isinstance(detail, dict):
                    error = detail.get("error", detail)
                    if isinstance(error, dict):
                        raw_code = str(error.get("code") or "") or None
                        message = str(error.get("message") or message)
                elif detail is not None:
                    message = str(detail)
            return KBSearchError(
                message,
                code=_code_from_status(status, raw_code),
                status_code=status,
                details=details,
            )
        if isinstance(exc, TimeoutError):
            return KBSearchError(
                str(exc) or "upstream request timed out",
                code=SyncErrorCode.TIMEOUT,
                retryable=True,
            )
        if isinstance(exc, URLError):
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, TimeoutError):
                return KBSearchError(
                    str(reason),
                    code=SyncErrorCode.TIMEOUT,
                    retryable=True,
                )
            return KBSearchError(
                str(reason),
                code=SyncErrorCode.UPSTREAM_UNAVAILABLE,
                retryable=True,
            )
    except ImportError:  # pragma: no cover
        pass

    if isinstance(exc, (json.JSONDecodeError, ValueError)):
        return KBSearchError(
            str(exc) or "invalid upstream response",
            code=SyncErrorCode.INVALID_RESPONSE,
        )
    return KBSearchError(
        str(exc) or exc.__class__.__name__,
        code=SyncErrorCode.UPSTREAM_UNAVAILABLE,
        retryable=True,
    )


def decode_json_object(response: Any) -> dict[str, Any]:
    """Decode and validate that an upstream success response is a JSON object."""

    try:
        payload = response.json()
    except Exception as exc:
        raise KBSearchError(
            f"invalid upstream JSON: {exc}",
            code=SyncErrorCode.INVALID_RESPONSE,
        ) from exc
    if not isinstance(payload, dict):
        raise KBSearchError(
            "upstream response must be a JSON object",
            code=SyncErrorCode.INVALID_RESPONSE,
            details={"response_type": type(payload).__name__},
        )
    return payload


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
                raise KBSearchError(
                    str(exc),
                    code=SyncErrorCode.AUTHENTICATION_FAILED,
                    status_code=401,
                ) from exc
        if key.lower() in self.INVALID_API_KEY_PLACEHOLDERS:
            raise KBSearchError(
                "Invalid KB_SEARCH_API_KEY: placeholder value detected, please set a real API key",
                code=SyncErrorCode.AUTHENTICATION_FAILED,
                status_code=401,
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
                    "conflicting book identifiers in filters: book_id and kb_book_id",
                    code=SyncErrorCode.CONTRACT_ERROR,
                    status_code=422,
                )
            if current is None and legacy is not None:
                canonical_filters["kb_book_id"] = legacy
            canonical_filters.pop("book_id", None)
            payload["filters"] = canonical_filters

        legacy_top = payload.get("book_id")
        current_top = payload.get("kb_book_id")
        if legacy_top is not None and current_top is not None and str(legacy_top) != str(current_top):
            raise KBSearchError(
                "conflicting top-level book identifiers: book_id and kb_book_id",
                code=SyncErrorCode.CONTRACT_ERROR,
                status_code=422,
            )
        if current_top is None and legacy_top is not None:
            payload["kb_book_id"] = legacy_top
        payload.pop("book_id", None)
        payload.pop("retrieval_pool", None)
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
                    response = client.request(
                        method,
                        url,
                        json=wire_payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    return decode_json_object(response)

            import urllib.request

            data = (
                json.dumps(wire_payload).encode("utf-8")
                if wire_payload is not None
                else None
            )
            request = urllib.request.Request(
                url,
                data=data,
                method=method,
                headers={**headers, "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                raw = response.read().decode("utf-8")
                if not raw:
                    return {}
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise KBSearchError(
                        f"invalid upstream JSON: {exc}",
                        code=SyncErrorCode.INVALID_RESPONSE,
                    ) from exc
                if not isinstance(payload, dict):
                    raise KBSearchError(
                        "upstream response must be a JSON object",
                        code=SyncErrorCode.INVALID_RESPONSE,
                    )
                return payload
        except KBSearchError:
            raise
        except Exception as exc:
            classified = classify_transport_exception(exc)
            logger.error(
                "kb-search request failed method=%s url=%s api_key=%s code=%s error=%s",
                method,
                url,
                mask_secret(self.api_key),
                classified.code.value,
                classified,
            )
            raise classified from exc

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/v1/health", use_auth=False)

    def get_upstream_meta(self) -> dict[str, Any]:
        """Return the explicit `/v1/meta` status without inventing unknown values."""

        return self._request("GET", "/v1/meta", use_auth=False)
