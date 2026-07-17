from __future__ import annotations

import httpx

from kb_contracts import SyncErrorCode
from src.connectors.kb_retrieval.transport import (
    KBSearchError,
    classify_transport_exception,
    decode_json_object,
)


def _status_error(status: int, body: dict) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "http://kb/v1/retrieve")
    response = httpx.Response(status, request=request, json=body)
    return httpx.HTTPStatusError(
        f"status={status}",
        request=request,
        response=response,
    )


def test_http_status_errors_preserve_upstream_code_and_retryability():
    auth = classify_transport_exception(
        _status_error(
            401,
            {"detail": {"error": {"code": "UNAUTHORIZED", "message": "bad key"}}},
        )
    )
    assert isinstance(auth, KBSearchError)
    assert auth.code == SyncErrorCode.AUTHENTICATION_FAILED
    assert auth.status_code == 401
    assert auth.retryable is False
    assert auth.to_dict()["message"] == "bad key"

    missing = classify_transport_exception(
        _status_error(
            404,
            {"detail": {"error": {"code": "COLLECTION_NOT_FOUND", "message": "missing"}}},
        )
    )
    assert missing.code == SyncErrorCode.COLLECTION_NOT_FOUND
    assert missing.retryable is False

    contract = classify_transport_exception(
        _status_error(
            422,
            {"detail": {"error": {"code": "CONTRACT_ERROR", "message": "bad filter"}}},
        )
    )
    assert contract.code == SyncErrorCode.CONTRACT_ERROR
    assert contract.retryable is False

    unavailable = classify_transport_exception(
        _status_error(
            503,
            {"detail": {"error": {"code": "UPSTREAM_UNAVAILABLE", "message": "qdrant down"}}},
        )
    )
    assert unavailable.code == SyncErrorCode.UPSTREAM_UNAVAILABLE
    assert unavailable.retryable is True


def test_timeout_connectivity_and_rate_limit_are_retryable():
    request = httpx.Request("GET", "http://kb/v1/meta")
    timeout = classify_transport_exception(httpx.ReadTimeout("slow", request=request))
    assert timeout.code == SyncErrorCode.TIMEOUT
    assert timeout.retryable is True

    connect = classify_transport_exception(httpx.ConnectError("offline", request=request))
    assert connect.code == SyncErrorCode.UPSTREAM_UNAVAILABLE
    assert connect.retryable is True

    rate_limited = classify_transport_exception(_status_error(429, {"detail": "later"}))
    assert rate_limited.code == SyncErrorCode.UPSTREAM_UNAVAILABLE
    assert rate_limited.retryable is True


def test_decode_json_object_rejects_invalid_json_and_non_object_shapes():
    request = httpx.Request("GET", "http://kb/v1/meta")
    invalid_json = httpx.Response(
        200,
        request=request,
        content=b"not json",
        headers={"content-type": "application/json"},
    )
    try:
        decode_json_object(invalid_json)
    except KBSearchError as exc:
        assert exc.code == SyncErrorCode.INVALID_RESPONSE
        assert exc.retryable is False
    else:  # pragma: no cover
        raise AssertionError("invalid JSON must fail")

    array_response = httpx.Response(200, request=request, json=[1, 2, 3])
    try:
        decode_json_object(array_response)
    except KBSearchError as exc:
        assert exc.code == SyncErrorCode.INVALID_RESPONSE
        assert "JSON object" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("non-object JSON must fail")
