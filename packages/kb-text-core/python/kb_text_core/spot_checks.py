from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .normalization import normalize_search_text
from .passages import canonical_source_locator

STATUSES = (
    "exact_raw",
    "exact_normalized",
    "mismatch",
    "missing_source",
    "missing_page",
    "invalid",
)


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _page_block(text: str, page_marker: str) -> str | None:
    token = f"<pb:{page_marker}>"
    start = text.find(token)
    if start < 0:
        return None
    body_start = start + len(token)
    next_marker = text.find("<pb:", body_start)
    return text[body_start : next_marker if next_marker >= 0 else len(text)]


def audit_ctext_spot_checks(
    config_path: Path,
    corpus_root: Path,
) -> dict[str, Any]:
    """Compare manually supplied CText excerpts with local files, without I/O to CText."""

    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("spot-check configuration must be a JSON object")
    checks = config.get("checks") or []
    if not isinstance(checks, list):
        raise ValueError("spot-check configuration field 'checks' must be a list")

    root = corpus_root.expanduser().resolve()
    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()

    for raw in checks:
        item = raw if isinstance(raw, dict) else {}
        row: dict[str, Any] = {
            "id": item.get("id"),
            "source_locator": item.get("source_locator"),
            "page_marker": item.get("page_marker"),
            "local_relative_path": item.get("local_relative_path"),
            "reference_text": item.get("reference_text"),
            "status": "invalid",
            "local_raw_preserved": True,
            "reason": None,
        }
        relative = str(item.get("local_relative_path") or "")
        page_marker = str(item.get("page_marker") or "")
        reference = str(item.get("reference_text") or "")
        expected_locator = str(item.get("source_locator") or "")
        if not relative or not page_marker or not reference:
            row["reason"] = "missing_required_field"
            counts[row["status"]] += 1
            rows.append(row)
            continue

        path = (root / relative).resolve()
        row["resolved_path"] = str(path)
        if not _within(path, root):
            row["reason"] = "source_path_escapes_corpus_root"
            counts[row["status"]] += 1
            rows.append(row)
            continue
        if not path.is_file():
            row["status"] = "missing_source"
            row["reason"] = "local_source_not_found"
            counts[row["status"]] += 1
            rows.append(row)
            continue

        actual_locator = canonical_source_locator(str(path), page_marker)
        row["actual_source_locator"] = actual_locator
        if expected_locator and actual_locator != expected_locator:
            row["reason"] = "source_locator_mismatch"
            counts[row["status"]] += 1
            rows.append(row)
            continue

        before = path.read_bytes()
        text = before.decode("utf-8")
        block = _page_block(text, page_marker)
        if block is None:
            row["status"] = "missing_page"
            row["reason"] = "page_marker_not_found"
        elif reference in block:
            row["status"] = "exact_raw"
        elif normalize_search_text(reference) in normalize_search_text(block):
            row["status"] = "exact_normalized"
        else:
            row["status"] = "mismatch"
            row["reason"] = "reference_excerpt_not_found"
        row["local_raw_preserved"] = path.read_bytes() == before
        counts[row["status"]] += 1
        rows.append(row)

    rendered_counts = {status: int(counts.get(status, 0)) for status in STATUSES}
    return {
        "schema_version": "kaiyuan-ctext-spot-check-report/v1",
        "config_path": str(config_path),
        "corpus_root": str(root),
        "source": config.get("source") or {},
        "network_accessed": False,
        "counts": rendered_counts,
        "all_matched": bool(rows)
        and all(row["status"] in {"exact_raw", "exact_normalized"} for row in rows),
        "checks": rows,
    }
