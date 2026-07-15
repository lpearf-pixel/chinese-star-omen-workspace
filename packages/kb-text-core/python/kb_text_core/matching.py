from __future__ import annotations

from collections.abc import Iterable

from .anchors import build_anchor_context
from .models import MatchCluster, MatchSpan
from .normalization import (
    compact_with_index_map,
    normalize_search_text,
    normalized_query_variants,
    query_variants,
    split_loose_terms,
)

MATCH_PRIORITY = {
    "exact_raw": 0,
    "exact_normalized": 1,
    "loose_window": 2,
    "heading_only": 3,
}


def _find_all(haystack: str, needle: str) -> Iterable[int]:
    start = 0
    while needle:
        pos = haystack.find(needle, start)
        if pos < 0:
            break
        yield pos
        start = pos + 1


def find_exact_spans(text: str, query: str, *, variants: list[str] | None = None) -> list[MatchSpan]:
    raw_variants = variants or query_variants(query)
    spans: list[MatchSpan] = []

    for variant in raw_variants:
        if not variant:
            continue
        for start in _find_all(text, variant):
            spans.append(
                MatchSpan(
                    start=start,
                    end=start + len(variant),
                    match_type="exact_raw",
                    matched_variant=variant,
                    normalized_variant=normalize_search_text(variant),
                    score=1.0,
                )
            )

    normalized = compact_with_index_map(text)
    if normalized.compact and normalized.index_map:
        for variant in normalized_query_variants(query, raw_variants):
            for compact_start in _find_all(normalized.compact, variant):
                compact_end = compact_start + len(variant) - 1
                if compact_end >= len(normalized.index_map):
                    continue
                start = normalized.index_map[compact_start]
                end = normalized.index_map[compact_end] + 1
                spans.append(
                    MatchSpan(
                        start=start,
                        end=end,
                        match_type="exact_normalized",
                        matched_variant=text[start:end],
                        normalized_variant=variant,
                        score=0.95,
                    )
                )

    best_by_range: dict[tuple[int, int], MatchSpan] = {}
    for span in spans:
        key = (span.start, span.end)
        current = best_by_range.get(key)
        if current is None or MATCH_PRIORITY[span.match_type] < MATCH_PRIORITY[current.match_type]:
            best_by_range[key] = span

    return sorted(
        best_by_range.values(),
        key=lambda span: (span.start, MATCH_PRIORITY[span.match_type], span.end),
    )


def find_loose_window_spans(text: str, query: str, *, window: int = 400) -> list[MatchSpan]:
    terms = split_loose_terms(query)
    if len(terms) < 2:
        return []

    normalized = compact_with_index_map(text)
    positions: dict[str, list[int]] = {
        term: list(_find_all(normalized.compact, normalize_search_text(term)))
        for term in terms
    }
    if any(not values for values in positions.values()):
        return []

    spans: list[MatchSpan] = []
    first = terms[0]
    for first_pos in positions[first]:
        selected = [first_pos]
        cursor = first_pos
        valid = True
        for term in terms[1:]:
            candidates = [pos for pos in positions[term] if first_pos <= pos <= first_pos + window]
            if not candidates:
                valid = False
                break
            next_pos = min(candidates, key=lambda pos: (abs(pos - cursor), pos))
            selected.append(next_pos)
            cursor = next_pos
        if not valid:
            continue
        compact_start = min(selected)
        compact_end = max(pos + len(normalize_search_text(term)) for pos, term in zip(selected, terms)) - 1
        if compact_end >= len(normalized.index_map):
            continue
        start = normalized.index_map[compact_start]
        end = normalized.index_map[compact_end] + 1
        spans.append(
            MatchSpan(
                start=start,
                end=end,
                match_type="loose_window",
                matched_variant=text[start:end],
                normalized_variant="+".join(terms),
                score=0.55,
            )
        )
    return spans


def find_match_spans(
    text: str,
    query: str,
    *,
    variants: list[str] | None = None,
    allow_loose: bool = True,
    loose_window: int = 400,
) -> list[MatchSpan]:
    exact = find_exact_spans(text, query, variants=variants)
    if exact or not allow_loose:
        return exact
    return find_loose_window_spans(text, query, window=loose_window)


def cluster_match_spans(
    text: str,
    spans: list[MatchSpan],
    *,
    max_gap: int = 500,
    anchor_window: int = 160,
) -> list[MatchCluster]:
    clusters: list[MatchCluster] = []
    for span in sorted(spans, key=lambda item: (item.start, item.end)):
        context = build_anchor_context(text, span.start, span.end, window=anchor_window)
        if clusters:
            previous = clusters[-1]
            previous_context = previous.context
            same_page = previous_context is not None and previous_context.page_marker == context.page_marker
            same_heading = previous_context is not None and previous_context.heading_path == context.heading_path
            if same_page and same_heading and span.start - previous.end <= max_gap:
                previous.spans.append(span)
                previous.context = build_anchor_context(text, previous.start, previous.end, window=anchor_window)
                continue
        clusters.append(MatchCluster(spans=[span], context=context))
    return clusters
