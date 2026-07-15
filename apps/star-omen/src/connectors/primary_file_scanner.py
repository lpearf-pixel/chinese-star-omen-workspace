from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

from src.connectors.kb_contract import infer_metadata_from_path

TEXT_CORE = Path(__file__).resolve().parents[4] / "packages" / "kb-text-core" / "python"
if str(TEXT_CORE) not in sys.path:
    sys.path.insert(0, str(TEXT_CORE))

from kb_text_core import (  # noqa: E402
    cluster_match_spans,
    dedupe_primary_hits,
    fallback_score,
    find_match_spans,
    normalize_search_text,
    split_loose_terms,
)

PRIMARY_CARD_TYPES = {"fenjuan", "fulltext"}


def basename(path: str | None) -> str:
    return Path(str(path or "").replace("\\", "/")).stem


def source_locator(path: str, page_marker: str | None = None) -> str:
    normalized = path.replace("\\", "/")
    match = re.search(r"(KR\w+_\d+)", normalized)
    if match:
        return match.group(1)
    if page_marker:
        page_match = re.search(r"(KR\w+_\d+)", page_marker)
        if page_match:
            return page_match.group(1)
    if "全文合併版" in normalized or "全文合并版" in normalized:
        return "fulltext"
    return Path(normalized).stem


def source_volume(locator: str, page_marker: str | None = None) -> str | None:
    match = re.search(r"_(\d+)(?:-|$)", page_marker or locator)
    return f"卷{int(match.group(1))}" if match else None


def _unique_roots(settings: Any) -> list[Path]:
    roots = [Path(settings.kb_sources_root)]
    if settings.kb_enable_obsidian_source:
        roots.append(Path(settings.kb_obsidian_root))
    out: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        root = root.expanduser()
        key = str(root.resolve(strict=False))
        if key not in seen:
            seen.add(key)
            out.append(root)
    return out


def scan_primary_files(
    settings: Any,
    query: str,
    *,
    book_id: str | None,
    mode: str,
    limit: int,
    query_variants: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    roots = _unique_roots(settings)
    debug_enabled = os.getenv("KB_DEBUG_SCAN", "").strip().lower() in {"1", "true", "yes", "on"}
    hits: list[dict[str, Any]] = []
    files_scanned = 0
    debug_matches: list[dict[str, Any]] = []
    read_errors: list[dict[str, str]] = []

    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.md")):
            normalized_path = str(path).replace("\\", "/")
            if "/分卷/" not in normalized_path and "全文合併版" not in normalized_path and "全文合并版" not in normalized_path:
                continue
            meta = infer_metadata_from_path(normalized_path)
            if meta.get("card_type") not in PRIMARY_CARD_TYPES:
                continue
            kb_book_id = meta.get("kb_book_id") or meta.get("book_id")
            if book_id and kb_book_id != book_id:
                continue
            files_scanned += 1
            try:
                text = path.read_text(encoding="utf-8")
            except Exception as exc:
                if debug_enabled:
                    read_errors.append({"path": normalized_path, "error": str(exc)})
                continue

            spans = find_match_spans(
                text,
                query,
                variants=query_variants,
                allow_loose=mode == "evidence",
            )
            if not spans:
                continue

            for cluster in cluster_match_spans(text, spans):
                context = cluster.context
                if context is None:
                    continue
                best = min(cluster.spans, key=lambda span: (0 if span.match_type == "exact_raw" else 1, span.start))
                locator = source_locator(normalized_path, context.page_marker)
                volume = source_volume(locator, context.page_marker)
                heading_text = normalize_search_text(" ".join(context.heading_path))
                heading_term_hits = sum(
                    1
                    for term in split_loose_terms(query)
                    if term and normalize_search_text(term) in heading_text
                )
                anchor = context.anchor_text
                hit = {
                    "chunk_id": f"fallback:{path.name}:{context.page_marker or locator}:{cluster.start}",
                    "score": fallback_score(best.match_type, str(meta.get("card_type") or "")),
                    "path": normalized_path,
                    "snippet": anchor[:300],
                    "excerpt": anchor,
                    "source_type": "docs",
                    "title": basename(normalized_path),
                    "book_title": meta.get("book_title"),
                    "kb_book_id": kb_book_id,
                    "book_id": kb_book_id,
                    "card_type": meta.get("card_type"),
                    "evidence_level": meta.get("evidence_level"),
                    "source_locator": locator,
                    "source_volume": volume,
                    "volume": volume,
                    "page_marker": context.page_marker,
                    "heading_path": context.heading_path,
                    "paragraph_index": context.paragraph_index,
                    "anchor_text": anchor,
                    "match_type": best.match_type,
                    "matched_variant": best.matched_variant,
                    "matched_variants": list(dict.fromkeys(span.matched_variant for span in cluster.spans)),
                    "match_offset": cluster.start,
                    "match_end": cluster.end,
                    "match_count": len(cluster.spans),
                    "heading_term_hits": heading_term_hits,
                }
                hits.append(hit)
                if debug_enabled:
                    debug_matches.append({
                        "path": normalized_path,
                        "page_marker": context.page_marker,
                        "heading_path": context.heading_path,
                        "match_type": best.match_type,
                        "match_offset": cluster.start,
                        "match_count": len(cluster.spans),
                        "excerpt": anchor,
                    })

    final_hits = dedupe_primary_hits(hits)[: max(limit, 0)]
    stats: dict[str, Any] = {
        "files_scanned": files_scanned,
        "matched_files": [str(hit.get("path") or "") for hit in final_hits],
        "matched_headings": [str(hit.get("title") or "") for hit in final_hits],
        "matched_quotes": [str(hit.get("excerpt") or hit.get("snippet") or "") for hit in final_hits],
    }
    if debug_enabled:
        stats["debug_scan"] = {
            "roots": [str(root) for root in roots],
            "root_exists": {str(root): root.exists() for root in roots},
            "files_scanned": files_scanned,
            "raw_match_clusters": len(hits),
            "final_sorted_files": [str(hit.get("path") or "") for hit in final_hits],
            "final_sorted_match_types": [str(hit.get("match_type") or "") for hit in final_hits],
            "final_sorted_scores": [float(hit.get("score") or 0.0) for hit in final_hits],
            "matched_files": debug_matches,
            "read_errors": read_errors,
        }
    return final_hits, stats
