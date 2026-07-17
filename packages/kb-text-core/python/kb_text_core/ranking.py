from __future__ import annotations

import hashlib
from typing import Any

from .normalization import normalize_search_text


# Match quality and evidence granularity are ranked together. This prevents an
# exact_raw hit in a giant fulltext file from outranking an exact_normalized hit
# in the authoritative split volume.
COMBINED_PRIORITY = {
    ("exact_raw", "fenjuan"): 0,
    ("exact_normalized", "fenjuan"): 1,
    ("exact_raw", "fulltext"): 2,
    ("exact_normalized", "fulltext"): 3,
    ("loose_window", "fenjuan"): 4,
    ("loose_window", "fulltext"): 5,
    ("heading_only", "fenjuan"): 6,
    ("heading_only", "fulltext"): 7,
}


def fallback_score(match_type: str, card_type: str) -> float:
    table = {
        ("exact_raw", "fenjuan"): 1.0,
        ("exact_normalized", "fenjuan"): 0.95,
        ("exact_raw", "fulltext"): 0.85,
        ("exact_normalized", "fulltext"): 0.80,
        ("loose_window", "fenjuan"): 0.55,
        ("loose_window", "fulltext"): 0.40,
        ("heading_only", "fenjuan"): 0.25,
        ("heading_only", "fulltext"): 0.20,
    }
    return table.get((match_type, card_type), 0.10)


def fallback_sort_key(hit: dict[str, Any]) -> tuple[Any, ...]:
    match_type = str(hit.get("match_type") or "none")
    card_type = str(hit.get("card_type") or "")
    score = float(hit.get("score") or 0.0)
    offset = hit.get("match_offset")
    offset_value = int(offset) if isinstance(offset, int) else 10**15
    return (
        COMBINED_PRIORITY.get((match_type, card_type), 99),
        -int(hit.get("heading_term_hits") or 0),
        -score,
        offset_value,
        str(hit.get("path") or ""),
    )


def normalized_anchor_hash(value: str) -> str:
    normalized = normalize_search_text(value)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _dedupe_key(hit: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(hit.get("kb_book_id") or hit.get("book_id") or ""),
        str(hit.get("page_marker") or hit.get("source_locator") or ""),
        normalized_anchor_hash(str(hit.get("anchor_text") or hit.get("snippet") or hit.get("matched_variant") or "")),
    )


def dedupe_primary_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(hits, key=fallback_sort_key)
    output: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}

    for original in ordered:
        hit = dict(original)
        key = _dedupe_key(hit)
        candidates = by_key.setdefault(key, [])
        duplicate = next(
            (
                existing
                for existing in candidates
                if existing.get("card_type") != hit.get("card_type")
                or (
                    existing.get("path") == hit.get("path")
                    and existing.get("match_offset") == hit.get("match_offset")
                )
            ),
            None,
        )
        if duplicate is not None:
            duplicate_path = str(hit.get("path") or "")
            duplicate_sources = duplicate.setdefault("duplicate_sources", [])
            if duplicate_path and duplicate_path != duplicate.get("path") and duplicate_path not in duplicate_sources:
                duplicate_sources.append(duplicate_path)
            continue

        hit.setdefault("duplicate_sources", [])
        candidates.append(hit)
        output.append(hit)
    return output
