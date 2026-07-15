from .anchors import build_anchor_context, extract_anchor, heading_path_at, nearest_page_marker, paragraph_index_at
from .matching import cluster_match_spans, find_exact_spans, find_loose_window_spans, find_match_spans
from .models import AnchorContext, MatchCluster, MatchSpan, NormalizedText
from .normalization import (
    compact_with_index_map,
    normalize_search_text,
    normalized_query_variants,
    query_variants,
    split_loose_terms,
)
from .parser import (
    audit_kaiyuan_corpus,
    audit_page_markers,
    compare_volume_text,
    split_kaiyuan_fulltext,
    write_split_volumes,
)
from .ranking import dedupe_primary_hits, fallback_score, fallback_sort_key, normalized_anchor_hash

__all__ = [
    "AnchorContext",
    "MatchCluster",
    "MatchSpan",
    "NormalizedText",
    "audit_kaiyuan_corpus",
    "audit_page_markers",
    "build_anchor_context",
    "cluster_match_spans",
    "compact_with_index_map",
    "compare_volume_text",
    "dedupe_primary_hits",
    "extract_anchor",
    "fallback_score",
    "fallback_sort_key",
    "find_exact_spans",
    "find_loose_window_spans",
    "find_match_spans",
    "heading_path_at",
    "nearest_page_marker",
    "normalize_search_text",
    "normalized_anchor_hash",
    "normalized_query_variants",
    "paragraph_index_at",
    "query_variants",
    "split_kaiyuan_fulltext",
    "split_loose_terms",
    "write_split_volumes",
]
