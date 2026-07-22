from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone

from hypothesis import given, strategies as st

from src.video_pipeline.contracts import AstronomyEventV1, canonical_contract_bytes
from tests.video_pipeline.contracts.test_contract_models_v1 import valid_astronomy_payload


@st.composite
def finite_measurements(draw: st.DrawFn) -> float:
    return draw(
        st.floats(
            min_value=-360.0,
            max_value=360.0,
            allow_nan=False,
            allow_infinity=False,
            width=64,
        )
    )


@given(value=finite_measurements())
def test_finite_measurements_roundtrip_to_strict_json(value: float) -> None:
    payload = valid_astronomy_payload()
    payload["measurements"][0]["value"] = value

    model = AstronomyEventV1.model_validate(payload)
    encoded = canonical_contract_bytes(model)

    assert b"NaN" not in encoded
    assert b"Infinity" not in encoded


@given(offset_seconds=st.integers(min_value=0, max_value=86_400))
def test_valid_time_windows_preserve_order(offset_seconds: int) -> None:
    payload = valid_astronomy_payload()
    start = datetime(2026, 7, 21, tzinfo=timezone.utc)
    peak = start + timedelta(seconds=offset_seconds)
    end = peak + timedelta(seconds=offset_seconds)
    payload["start_utc"] = start.isoformat().replace("+00:00", "Z")
    payload["peak_utc"] = peak.isoformat().replace("+00:00", "Z")
    payload["end_utc"] = end.isoformat().replace("+00:00", "Z")

    event = AstronomyEventV1.model_validate(payload)

    assert event.start_utc <= event.peak_utc <= event.end_utc


@given(st.permutations(list(valid_astronomy_payload().keys())))
def test_input_key_order_never_changes_canonical_bytes(key_order: list[str]) -> None:
    original = valid_astronomy_payload()
    reordered = {key: deepcopy(original[key]) for key in key_order}

    assert canonical_contract_bytes(
        AstronomyEventV1.model_validate(original)
    ) == canonical_contract_bytes(AstronomyEventV1.model_validate(reordered))
