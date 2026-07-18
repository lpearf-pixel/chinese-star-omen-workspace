from kb_contracts import (
    SYNC_ERROR_CODES,
    SyncErrorCode,
    SyncRunStatus,
    sync_error_payload,
)


def test_sync_error_codes_are_stable_and_complete():
    assert SYNC_ERROR_CODES == {
        "authentication_failed",
        "upstream_unavailable",
        "timeout",
        "contract_error",
        "collection_not_found",
        "invalid_response",
    }
    assert SyncRunStatus.OK.value == "ok"
    assert SyncRunStatus.ERROR.value == "error"


def test_sync_error_payload_derives_retryability_and_serializes_enum():
    retryable = sync_error_payload(
        SyncErrorCode.TIMEOUT,
        "upstream timed out",
        status_code=408,
        details={"operation": "retrieve"},
    )
    assert retryable == {
        "code": "timeout",
        "message": "upstream timed out",
        "status_code": 408,
        "retryable": True,
        "details": {"operation": "retrieve"},
    }

    terminal = sync_error_payload(
        "authentication_failed",
        "invalid API key",
        status_code=401,
    )
    assert terminal["retryable"] is False
    assert terminal["details"] == {}


def test_sync_error_payload_rejects_unknown_code():
    try:
        sync_error_payload("made_up", "bad")
    except ValueError as exc:
        assert "unknown sync error code" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("unknown code must be rejected")
