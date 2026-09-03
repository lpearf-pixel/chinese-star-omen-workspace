from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import pytest

import src.connectors.kb_retrieval.transport as transport_module
from src.connectors.kb_retrieval.transport import PinnedHTTPXJSONTransport
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
)
from src.video_pipeline.feedback_loop.readonly_kb_v1 import (
    S1_REQUEST_TIMEOUT_SECONDS,
    validate_literal_loopback_endpoint,
)


class _Response:
    def __init__(
        self,
        body: bytes,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        chunks: tuple[bytes, ...] | None = None,
    ) -> None:
        self.status_code = status_code
        self.headers = {
            "content-type": "application/json",
            **(headers or {}),
        }
        self._chunks = chunks if chunks is not None else (body,)
        self.iterated_chunks = 0
        self.json_calls = 0

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def iter_bytes(self) -> Iterator[bytes]:
        for chunk in self._chunks:
            self.iterated_chunks += 1
            yield chunk

    def json(self) -> object:  # pragma: no cover - a call is always a failure
        self.json_calls += 1
        raise AssertionError("strict transport must parse streamed raw bytes")


class _Client:
    def __init__(self, response: _Response, calls: list[tuple[object, ...]]) -> None:
        self._response = response
        self._calls = calls

    def __enter__(self) -> _Client:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def stream(self, method: str, url: str, **kwargs: object) -> _Response:
        self._calls.append((method, url, kwargs))
        return self._response


def _install_client(
    monkeypatch: pytest.MonkeyPatch,
    response: _Response,
) -> tuple[list[dict[str, object]], list[tuple[object, ...]]]:
    constructor_calls: list[dict[str, object]] = []
    stream_calls: list[tuple[object, ...]] = []

    def factory(**kwargs: object) -> _Client:
        constructor_calls.append(dict(kwargs))
        return _Client(response, stream_calls)

    assert transport_module.httpx is not None
    monkeypatch.setattr(transport_module.httpx, "Client", factory)
    return constructor_calls, stream_calls


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("http://127.0.0.1:1", "http://127.0.0.1:1"),
        ("http://127.0.0.1:65535/", "http://127.0.0.1:65535"),
        ("http://[::1]:8008", "http://[::1]:8008"),
        ("http://[::1]:8008/", "http://[::1]:8008"),
    ],
)
def test_literal_loopback_endpoint_accepts_only_canonical_origins(
    value: str,
    expected: str,
) -> None:
    """Catches rejecting either exact loopback literal or retaining a slash."""

    assert validate_literal_loopback_endpoint(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        " http://127.0.0.1:8008",
        "http://127.0.0.1:8008\n",
        "https://127.0.0.1:8008",
        "http://user@127.0.0.1:8008",
        "http://127.0.0.1:8008/path",
        "http://127.0.0.1:8008?x=1",
        "http://127.0.0.1:8008#fragment",
        "http://localhost:8008",
        "http://127.1:8008",
        "http://2130706433:8008",
        "http://0177.0.0.1:8008",
        "http://[0:0:0:0:0:0:0:1]:8008",
        "http://[::ffff:127.0.0.1]:8008",
        "http://[::1%25lo]:8008",
        "http://127.0.0.1",
        "http://127.0.0.1:0",
        "http://127.0.0.1:65536",
        "http://192.168.1.2:8008",
    ],
)
def test_literal_loopback_endpoint_rejects_every_noncanonical_form(value: str) -> None:
    """Catches a permissive URL parser widening the credential destination."""

    with pytest.raises(ReadOnlyAdapterError) as caught:
        validate_literal_loopback_endpoint(value)
    assert caught.value.code == ReadOnlyErrorCode.ENDPOINT_REJECTED
    assert str(caught.value) == "endpoint_rejected"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert value not in str(caught.value)


def test_pinned_transport_disables_environment_and_redirects_and_streams_raw_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catches proxy/redirect enablement or response.json() bypass."""

    response = _Response(b'{"meta_status":"ok"}')
    constructor_calls, stream_calls = _install_client(monkeypatch, response)
    transport = PinnedHTTPXJSONTransport("http://127.0.0.1:8008")

    result = transport.request(
        "GET",
        "http://127.0.0.1:8008/v1/meta",
        json_payload=None,
        headers={},
        timeout=S1_REQUEST_TIMEOUT_SECONDS,
    )

    assert result == {"meta_status": "ok"}
    assert constructor_calls == [{"trust_env": False, "follow_redirects": False}]
    assert stream_calls == [
        (
            "GET",
            "http://127.0.0.1:8008/v1/meta",
            {
                "json": None,
                "headers": {},
                "timeout": 10.0,
            },
        )
    ]
    assert response.json_calls == 0


@pytest.mark.parametrize(
    ("method", "url", "payload", "headers"),
    [
        ("POST", "http://127.0.0.1:8008/v1/meta", None, {}),
        ("GET", "http://127.0.0.1:8008/v1/meta", {}, {}),
        ("GET", "http://127.0.0.1:8008/v1/meta", None, {"X-API-Key": "secret"}),
        ("GET", "http://127.0.0.1:8009/v1/meta", None, {}),
        ("GET", "http://127.0.0.1:8008/v1/meta?x=1", None, {}),
        ("GET", "http://127.0.0.1:8008/v1/health", None, {}),
        ("GET", "http://127.0.0.1:8008/v1/retrieve", {}, {}),
        ("POST", "http://127.0.0.1:8008/v1/retrieve", None, {}),
        ("POST", "http://127.0.0.1:8008/v1/retrieve", {}, {}),
        (
            "POST",
            "http://127.0.0.1:8008/v1/retrieve",
            {},
            {"Authorization": "Bearer secret"},
        ),
        (
            "POST",
            "http://127.0.0.1:8008/v1/retrieve",
            {},
            {"Authorization": "secret", "X-API-Key": "secret"},
        ),
    ],
)
def test_pinned_transport_rejects_request_mismatch_before_client_construction(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    headers: dict[str, str],
) -> None:
    """Catches method/path/origin/auth mismatches opening a socket."""

    response = _Response(b"{}")
    constructor_calls, stream_calls = _install_client(monkeypatch, response)
    transport = PinnedHTTPXJSONTransport("http://127.0.0.1:8008")

    with pytest.raises(ReadOnlyAdapterError) as caught:
        transport.request(
            method,
            url,
            json_payload=payload,
            headers=headers,
            timeout=10.0,
        )
    assert caught.value.code == ReadOnlyErrorCode.TRANSPORT_FAILED
    assert str(caught.value) == "transport_failed"
    assert caught.value.__cause__ is None
    assert constructor_calls == []
    assert stream_calls == []


def test_pinned_transport_allows_only_exact_retrieve_auth_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catches dropping either credential header or adding ambient headers."""

    response = _Response(b'{"hits":[]}')
    _, stream_calls = _install_client(monkeypatch, response)
    transport = PinnedHTTPXJSONTransport("http://127.0.0.1:8008")
    headers = {"Authorization": "Bearer secret", "X-API-Key": "secret"}

    assert transport.request(
        "POST",
        "http://127.0.0.1:8008/v1/retrieve",
        json_payload={"query": "safe"},
        headers=headers,
        timeout=10.0,
    ) == {"hits": []}
    assert stream_calls[0][2] == {
        "json": {"query": "safe"},
        "headers": headers,
        "timeout": 10.0,
    }


def test_redirect_is_rejected_without_a_second_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catches following redirects to another origin."""

    response = _Response(b"redirect", status_code=302)
    _, stream_calls = _install_client(monkeypatch, response)
    transport = PinnedHTTPXJSONTransport("http://127.0.0.1:8008")

    with pytest.raises(ReadOnlyAdapterError) as caught:
        transport.request(
            "GET",
            "http://127.0.0.1:8008/v1/meta",
            json_payload=None,
            headers={},
            timeout=10.0,
        )
    assert caught.value.code == ReadOnlyErrorCode.TRANSPORT_FAILED
    assert len(stream_calls) == 1
    assert response.iterated_chunks == 0


def test_missing_httpx_fails_without_urllib_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches the strict path silently using the legacy urllib transport."""

    monkeypatch.setattr(transport_module, "httpx", None)
    transport = PinnedHTTPXJSONTransport("http://127.0.0.1:8008")
    with pytest.raises(ReadOnlyAdapterError) as caught:
        transport.request(
            "GET",
            "http://127.0.0.1:8008/v1/meta",
            json_payload=None,
            headers={},
            timeout=10.0,
        )
    assert caught.value.code == ReadOnlyErrorCode.TRANSPORT_FAILED
    assert caught.value.__cause__ is None


@pytest.mark.parametrize(
    ("body", "headers"),
    [
        (b"\xff", {}),
        (b'{"collection":"a","collection":"b"}', {}),
        (b'{"value":NaN}', {}),
        (b'{"value":Infinity}', {}),
        (b'{"value":1e999}', {}),
        (b'{"value":-1e999}', {}),
        (b"[]", {}),
        (b"{}", {"content-type": "text/plain"}),
        (b"{}", {"content-encoding": "gzip"}),
    ],
)
def test_strict_stream_decoder_rejects_unsafe_body_without_leaking_it(
    monkeypatch: pytest.MonkeyPatch,
    body: bytes,
    headers: dict[str, str],
) -> None:
    """Catches unsafe decoding, duplicate keys, non-finite numbers, or media."""

    response = _Response(body, headers=headers)
    _install_client(monkeypatch, response)
    transport = PinnedHTTPXJSONTransport("http://127.0.0.1:8008")

    with pytest.raises(ReadOnlyAdapterError) as caught:
        transport.request(
            "GET",
            "http://127.0.0.1:8008/v1/meta",
            json_payload=None,
            headers={},
            timeout=10.0,
        )
    assert caught.value.code == ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED
    assert str(caught.value) == "response_contract_rejected"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert response.json_calls == 0
    assert "secret" not in str(caught.value)
    decoded_body = body.decode("utf-8", errors="ignore")
    if decoded_body:
        assert decoded_body not in str(caught.value)


@pytest.mark.parametrize(
    ("path", "limit"),
    [("/v1/meta", 256 * 1024), ("/v1/retrieve", 4 * 1024 * 1024)],
)
def test_content_length_is_rejected_before_streaming(
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    limit: int,
) -> None:
    """Catches an excessive declared body being read before rejection."""

    response = _Response(
        b"{}",
        headers={"content-length": str(limit + 1)},
    )
    _install_client(monkeypatch, response)
    transport = PinnedHTTPXJSONTransport("http://127.0.0.1:8008")
    method = "GET" if path == "/v1/meta" else "POST"
    payload = None if path == "/v1/meta" else {}
    headers = {} if path == "/v1/meta" else {
        "Authorization": "Bearer secret",
        "X-API-Key": "secret",
    }

    with pytest.raises(ReadOnlyAdapterError) as caught:
        transport.request(
            method,
            f"http://127.0.0.1:8008{path}",
            json_payload=payload,
            headers=headers,
            timeout=10.0,
        )
    assert caught.value.code == ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert response.iterated_chunks == 0


def test_streaming_overflow_stops_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches buffering the complete body after the decoded limit is crossed."""

    response = _Response(
        b"",
        chunks=(b"x" * (256 * 1024), b"y", b"must-not-be-read"),
    )
    _install_client(monkeypatch, response)
    transport = PinnedHTTPXJSONTransport("http://127.0.0.1:8008")

    with pytest.raises(ReadOnlyAdapterError):
        transport.request(
            "GET",
            "http://127.0.0.1:8008/v1/meta",
            json_payload=None,
            headers={},
            timeout=10.0,
        )
    assert response.iterated_chunks == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"root": None},
        {"root": [0] * 100_000},
    ],
)
def test_stream_decoder_enforces_shared_graph_budget(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
) -> None:
    """Catches depth/node budget checks being omitted after JSON parsing."""

    if payload["root"] is None:
        value: object = "leaf"
        for _ in range(65):
            value = [value]
        payload = {"root": value}
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    response = _Response(body)
    _install_client(monkeypatch, response)
    transport = PinnedHTTPXJSONTransport("http://127.0.0.1:8008")

    with pytest.raises(ReadOnlyAdapterError) as caught:
        transport.request(
            "POST",
            "http://127.0.0.1:8008/v1/retrieve",
            json_payload={},
            headers={
                "Authorization": "Bearer secret",
                "X-API-Key": "secret",
            },
            timeout=10.0,
        )
    assert caught.value.code == ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED
    assert response.json_calls == 0


def test_stream_decoder_rejects_unbounded_json_integer_with_fixed_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catches arbitrary-size JSON integers escaping the adapter taxonomy."""

    attacker_value = "9" * 400
    response = _Response(f'{{"value":{attacker_value}}}'.encode("ascii"))
    _install_client(monkeypatch, response)
    transport = PinnedHTTPXJSONTransport("http://127.0.0.1:8008")

    with pytest.raises(ReadOnlyAdapterError) as caught:
        transport.request(
            "GET",
            "http://127.0.0.1:8008/v1/meta",
            json_payload=None,
            headers={},
            timeout=10.0,
        )
    assert caught.value.code == ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED
    assert str(caught.value) == "response_contract_rejected"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert attacker_value not in str(caught.value)


def test_pinned_transport_rejects_unbounded_timeout_before_client_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catches float conversion overflow bypassing the fixed transport error."""

    response = _Response(b"{}")
    constructor_calls, _ = _install_client(monkeypatch, response)
    transport = PinnedHTTPXJSONTransport("http://127.0.0.1:8008")

    with pytest.raises(ReadOnlyAdapterError) as caught:
        transport.request(
            "GET",
            "http://127.0.0.1:8008/v1/meta",
            json_payload=None,
            headers={},
            timeout=10**400,
        )
    assert caught.value.code == ReadOnlyErrorCode.TRANSPORT_FAILED
    assert str(caught.value) == "transport_failed"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert constructor_calls == []
