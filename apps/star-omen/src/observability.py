from __future__ import annotations

import copy
import math
from typing import Any

OBSERVABILITY_SCHEMA_VERSION = "kb-observability/v1"


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return copy.deepcopy(value)


def elapsed_ms(start_ns: int, end_ns: int) -> float:
    """Return a finite non-negative monotonic duration in milliseconds."""

    delta = max(int(end_ns) - int(start_ns), 0)
    return round(delta / 1_000_000, 3)


def optional_ms(value: Any) -> float | None:
    """Normalize optional upstream timing without inventing missing values."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0:
        return None
    return round(normalized, 3)


def base_observability(operation: str, **fields: Any) -> dict[str, Any]:
    """Build an additive envelope isolated from caller-owned containers."""

    if not isinstance(operation, str) or not operation.strip():
        raise ValueError("operation must be a non-empty string")
    return {
        "schema_version": OBSERVABILITY_SCHEMA_VERSION,
        "operation": operation,
        **_json_safe(fields),
    }
