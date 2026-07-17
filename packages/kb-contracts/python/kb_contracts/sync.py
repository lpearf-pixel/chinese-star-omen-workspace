from __future__ import annotations

from enum import Enum
from typing import Any


class SyncErrorCode(str, Enum):
    AUTHENTICATION_FAILED = "authentication_failed"
    UPSTREAM_UNAVAILABLE = "upstream_unavailable"
    TIMEOUT = "timeout"
    CONTRACT_ERROR = "contract_error"
    COLLECTION_NOT_FOUND = "collection_not_found"
    INVALID_RESPONSE = "invalid_response"


class SyncRunStatus(str, Enum):
    OK = "ok"
    ERROR = "error"


SYNC_ERROR_CODES = {code.value for code in SyncErrorCode}
RETRYABLE_SYNC_ERRORS = {
    SyncErrorCode.UPSTREAM_UNAVAILABLE,
    SyncErrorCode.TIMEOUT,
}


def _coerce_error_code(code: SyncErrorCode | str) -> SyncErrorCode:
    if isinstance(code, SyncErrorCode):
        return code
    try:
        return SyncErrorCode(str(code))
    except ValueError as exc:
        raise ValueError(f"unknown sync error code: {code!r}") from exc


def sync_error_payload(
    code: SyncErrorCode | str,
    message: str,
    *,
    status_code: int | None = None,
    details: dict[str, Any] | None = None,
    retryable: bool | None = None,
) -> dict[str, Any]:
    """Return the stable JSON representation used by sync and transport layers."""

    resolved = _coerce_error_code(code)
    return {
        "code": resolved.value,
        "message": str(message),
        "status_code": status_code,
        "retryable": (
            resolved in RETRYABLE_SYNC_ERRORS
            if retryable is None
            else bool(retryable)
        ),
        "details": dict(details or {}),
    }
