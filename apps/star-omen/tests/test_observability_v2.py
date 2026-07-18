from __future__ import annotations

import json
import math

import pytest

from src.observability import base_observability, elapsed_ms, optional_ms


def test_elapsed_ms_is_non_negative_and_rounded():
    assert elapsed_ms(1_000_000, 2_234_567) == 1.235
    assert elapsed_ms(2_000_000, 1_000_000) == 0.0


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1, 1.0),
        (1.23456, 1.235),
        (0, 0.0),
        (-1, None),
        (True, None),
        ("1", None),
        (None, None),
        (math.nan, None),
        (math.inf, None),
        (-math.inf, None),
    ],
)
def test_optional_ms_accepts_only_finite_non_negative_numbers(value, expected):
    assert optional_ms(value) == expected


def test_base_envelope_is_additive_json_safe_and_does_not_mutate_inputs():
    card_types = ["fenjuan", "fulltext"]
    fields = {
        "stage": "primary_evidence",
        "latency_ms": 1.25,
        "upstream_latency_ms": None,
        "card_types": card_types,
        "collection": "local_kb_kaiyuan_v2",
    }

    envelope = base_observability("retrieve", **fields)

    assert envelope == {
        "schema_version": "kb-observability/v1",
        "operation": "retrieve",
        **fields,
    }
    assert fields["card_types"] is card_types
    envelope["card_types"].append("poison")
    assert card_types == ["fenjuan", "fulltext"]
    json.dumps(envelope, allow_nan=False)


def test_base_envelope_sanitizes_nested_non_finite_values():
    details = {
        "latencies": [1.0, math.nan, math.inf, -math.inf],
        "nested": {"value": math.nan},
    }

    envelope = base_observability("candidate_sync", run_error={"details": details})

    assert envelope["run_error"]["details"] == {
        "latencies": [1.0, None, None, None],
        "nested": {"value": None},
    }
    assert math.isnan(details["latencies"][1])
    json.dumps(envelope, allow_nan=False)


@pytest.mark.parametrize("operation", ["", "  ", None, 1])
def test_base_envelope_rejects_invalid_operation(operation):
    with pytest.raises(ValueError, match="operation"):
        base_observability(operation)
