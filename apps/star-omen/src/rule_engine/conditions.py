from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ConditionState(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


def _json_safe(value: Any) -> Any:
    """Return a trace value accepted by strict JSON encoders.

    Event measurements may contain NaN or infinities. They remain auditable as
    explicit strings, but never leak non-standard JSON constants into CLI or
    report output.
    """

    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return "nan"
        return "infinity" if value > 0 else "-infinity"
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


@dataclass(frozen=True)
class ConditionEvaluation:
    name: str
    state: ConditionState
    required: bool
    expected: Any
    actual: Any
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "required": self.required,
            "expected": _json_safe(self.expected),
            "actual": _json_safe(self.actual),
            "reason": self.reason,
        }


def _finite_threshold(name: str, value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} requires a finite numeric threshold")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} requires a finite numeric threshold") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} requires a finite numeric threshold")
    return number


def _measurement(value: Any) -> tuple[float | None, str | None]:
    if value is None:
        return None, "missing_value"
    if isinstance(value, str) and not value.strip():
        return None, "empty_value"
    if isinstance(value, bool):
        return None, "invalid_numeric"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, "invalid_numeric"
    if not math.isfinite(number):
        return None, "non_finite_numeric"
    return number, None


def evaluate_exact(
    name: str,
    actual: Any,
    *,
    expected: Any,
    passed: bool | None = None,
    pass_reason: str = "exact_match",
    fail_reason: str = "mismatch",
) -> ConditionEvaluation:
    is_match = actual == expected if passed is None else bool(passed)
    return ConditionEvaluation(
        name=name,
        state=ConditionState.PASS if is_match else ConditionState.FAIL,
        required=True,
        expected=expected,
        actual=actual,
        reason=pass_reason if is_match else fail_reason,
    )


def evaluate_max_numeric(
    name: str,
    value: Any,
    *,
    threshold: Any,
    expected_key: str = "maximum",
) -> ConditionEvaluation:
    configured = _finite_threshold(name, threshold)
    actual, unknown_reason = _measurement(value)
    expected = {expected_key: configured}
    if unknown_reason is not None:
        return ConditionEvaluation(
            name=name,
            state=ConditionState.UNKNOWN,
            required=True,
            expected=expected,
            actual=value,
            reason=unknown_reason,
        )
    assert actual is not None
    passed = actual <= configured
    return ConditionEvaluation(
        name=name,
        state=ConditionState.PASS if passed else ConditionState.FAIL,
        required=True,
        expected=expected,
        actual=actual,
        reason="within_maximum" if passed else "above_maximum",
    )


def evaluate_min_numeric(
    name: str,
    value: Any,
    *,
    threshold: Any,
    expected_key: str = "minimum",
) -> ConditionEvaluation:
    configured = _finite_threshold(name, threshold)
    actual, unknown_reason = _measurement(value)
    expected = {expected_key: configured}
    if unknown_reason is not None:
        return ConditionEvaluation(
            name=name,
            state=ConditionState.UNKNOWN,
            required=True,
            expected=expected,
            actual=value,
            reason=unknown_reason,
        )
    assert actual is not None
    passed = actual >= configured
    return ConditionEvaluation(
        name=name,
        state=ConditionState.PASS if passed else ConditionState.FAIL,
        required=True,
        expected=expected,
        actual=actual,
        reason="meets_minimum" if passed else "below_minimum",
    )


def evaluate_required_visibility(visibility: Any) -> ConditionEvaluation:
    expected = {"is_visible": True}
    if visibility is None:
        return ConditionEvaluation(
            name="visibility",
            state=ConditionState.UNKNOWN,
            required=True,
            expected=expected,
            actual=None,
            reason="missing_value",
        )
    if not isinstance(visibility, dict):
        return ConditionEvaluation(
            name="visibility",
            state=ConditionState.UNKNOWN,
            required=True,
            expected=expected,
            actual=visibility,
            reason="invalid_visibility",
        )
    if "is_visible" not in visibility or visibility.get("is_visible") is None:
        return ConditionEvaluation(
            name="visibility",
            state=ConditionState.UNKNOWN,
            required=True,
            expected=expected,
            actual=visibility.get("is_visible"),
            reason="missing_value",
        )
    flag = visibility.get("is_visible")
    if not isinstance(flag, bool):
        return ConditionEvaluation(
            name="visibility",
            state=ConditionState.UNKNOWN,
            required=True,
            expected=expected,
            actual=flag,
            reason="invalid_visibility",
        )
    return ConditionEvaluation(
        name="visibility",
        state=ConditionState.PASS if flag else ConditionState.FAIL,
        required=True,
        expected=expected,
        actual=flag,
        reason="visible" if flag else "not_visible",
    )
