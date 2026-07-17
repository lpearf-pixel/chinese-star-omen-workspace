from .anchors import build_anchor_context, extract_anchor, heading_path_at, nearest_page_marker, paragraph_index_at
from .matching import cluster_match_spans, find_exact_spans, find_heading_only_spans, find_loose_window_spans, find_match_spans
from .models import AnchorContext, KaiyuanPassage, MatchCluster, MatchSpan, NormalizedText
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
from .passages import (
    canonical_source_locator,
    dedupe_kaiyuan_passages,
    parse_kaiyuan_passages,
    source_volume_for_locator,
)
from .ranking import dedupe_primary_hits, fallback_score, fallback_sort_key, normalized_anchor_hash
from .spot_checks import audit_ctext_spot_checks

__all__ = [
    "AnchorContext",
    "KaiyuanPassage",
    "MatchCluster",
    "MatchSpan",
    "NormalizedText",
    "audit_ctext_spot_checks",
    "audit_kaiyuan_corpus",
    "audit_page_markers",
    "build_anchor_context",
    "canonical_source_locator",
    "cluster_match_spans",
    "compact_with_index_map",
    "compare_volume_text",
    "dedupe_kaiyuan_passages",
    "dedupe_primary_hits",
    "extract_anchor",
    "fallback_score",
    "fallback_sort_key",
    "find_exact_spans",
    "find_heading_only_spans",
    "find_loose_window_spans",
    "find_match_spans",
    "heading_path_at",
    "nearest_page_marker",
    "normalize_search_text",
    "normalized_anchor_hash",
    "normalized_query_variants",
    "paragraph_index_at",
    "parse_kaiyuan_passages",
    "query_variants",
    "source_volume_for_locator",
    "split_kaiyuan_fulltext",
    "split_loose_terms",
    "write_split_volumes",
]
