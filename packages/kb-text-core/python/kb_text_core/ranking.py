from __future__ import annotations

import hashlib
from typing import Any

from .normalization import normalize_search_text


MATCH_PRIORITY = {
    "exact_raw": 0,
    "exact_normalized": 1,
    "loose_window": 2,
    "heading_only": 3,
}
CARD_PRIORITY = {"fenjuan": 0, "fulltext": 1}


def fallback_score(match_type: str, card_type: str) -> float:
    table = {
        ("exact_raw", "fenjuan"): 1.0,
        ("exact_normalized", "fenjuan"): 0.95,
        ("exact_raw", "fulltext"): 0.85,
        ("exact_normalized", "fulltext"): 0.80,
        ("loose_window", "fenjuan"): 0.55,
        ("loose_window", "fulltext"): 0.40,
        ("heading_only", "fenjuan"): 0.30,
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
        MATCH_PRIORITY.get(match_type, 99),
        CARD_PRIORITY.get(card_type, 99),
        -int(hit.get("heading_term_hits") or 0),
        -score,
        offset_value,
        str(hit.get("path") or ""),
    )


def normalized_anchor_hash(value: str) -> str:
    normalized = normalize_search_text(value)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def dedupe_primary_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(hits, key=fallback_sort_key)
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for hit in ordered:
        key = (
            str(hit.get("kb_book_id") or hit.get("book_id") or ""),
            str(hit.get("page_marker") or hit.get("source_locator") or ""),
            normalized_anchor_hash(str(hit.get("anchor_text") or hit.get("snippet") or "")),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(hit)
    return out
