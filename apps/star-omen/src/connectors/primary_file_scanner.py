from __future__ import annotations

from collections.abc import Sequence
import os
import re
import sys
from pathlib import Path
from typing import Any

from src.connectors.kb_contract import infer_metadata_from_path
from src.connectors.primary_passage_cache import (
    PrimarySourceByteLoader,
    PrimarySourceReadError,
    primary_passage_cache,
)

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
VOLUME_PATH_RE = re.compile(r"(KR[0-9A-Za-z]+_\d{3})(?:\.md|$)")
PAGE_VOLUME_RE = re.compile(r"^(KR[0-9A-Za-z]+)(?:_[A-Za-z0-9]+)*_(\d{3})(?:-|$)")


def basename(path: str | None) -> str:
    return Path(str(path or "").replace("\\", "/")).stem


def source_locator(path: str, page_marker: str | None = None) -> str:
    """Return the canonical volume locator, including for fulltext page markers.

    A fulltext page marker such as ``KR3g0018_WYG_031-17a`` belongs to
    ``KR3g0018_031``.  The old generic regex returned
    ``KR3g0018_WYG_031``, which made fulltext and fenjuan provenance disagree.
    """

    normalized = path.replace("\\", "/")
    path_match = VOLUME_PATH_RE.search(normalized)
    if path_match:
        return path_match.group(1)

    marker = str(page_marker or "")
    marker_match = PAGE_VOLUME_RE.search(marker)
    if marker_match:
        return f"{marker_match.group(1)}_{marker_match.group(2)}"

    if "全文合併版" in normalized or "全文合并版" in normalized:
        return "fulltext"
    return Path(normalized).stem


def source_volume(locator: str, page_marker: str | None = None) -> str | None:
    marker = str(page_marker or "")
    marker_match = PAGE_VOLUME_RE.search(marker)
    if marker_match:
        return f"卷{int(marker_match.group(2))}"

    locator_match = re.search(r"_(\d{3})(?:-|$)", locator)
    return f"卷{int(locator_match.group(1))}" if locator_match else None


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


def _display_heading(hit: dict[str, Any]) -> str:
    heading_path = hit.get("heading_path")
    if isinstance(heading_path, list) and heading_path:
        return str(heading_path[-1])
    return str(hit.get("title") or "")


def scan_primary_files(
    settings: Any,
    query: str,
    *,
    book_id: str | None,
    mode: str,
    limit: int,
    query_variants: Sequence[str],
    passage_loader: PrimarySourceByteLoader | None = None,
    strict_exact_passages: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Scan all eligible primary files, then rank, deduplicate and truncate.

    The scan deliberately does not return early at ``limit``: a more relevant
    fenjuan match may appear after a fulltext file in filesystem order.
    """

    if strict_exact_passages and passage_loader is None:
        raise ValueError("strict_exact_passages requires passage_loader")
    roots = (
        [Path(settings.kb_sources_root)]
        if strict_exact_passages
        else _unique_roots(settings)
    )
    debug_enabled = os.getenv("KB_DEBUG_SCAN", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    hits: list[dict[str, Any]] = []
    files_scanned = 0
    debug_matches: list[dict[str, Any]] = []
    read_errors: list[dict[str, str]] = []

    for root in roots:
        if strict_exact_passages:
            assert passage_loader is not None
            source_paths: Sequence[str | Path] = passage_loader.relative_paths()
        else:
            if not root.exists():
                continue
            source_paths = sorted(root.rglob("*.md"))
        for source_path in source_paths:
            loader_path: str | Path = source_path
            path = Path(source_path)
            if strict_exact_passages:
                normalized_path = (root / path).as_posix()
                metadata_path = path.as_posix()
            else:
                normalized_path = str(path).replace("\\", "/")
                metadata_path = normalized_path
            if (
                "/分卷/" not in f"/{metadata_path}"
                and "全文合併版" not in metadata_path
                and "全文合并版" not in metadata_path
            ):
                continue

            meta = infer_metadata_from_path(metadata_path)
            if meta.get("card_type") not in PRIMARY_CARD_TYPES:
                if strict_exact_passages:
                    raise ValueError("loader inventory contains a non-primary path")
                continue
            kb_book_id = meta.get("kb_book_id") or meta.get("book_id")
            if strict_exact_passages:
                kb_book_id = book_id or kb_book_id
            elif book_id and kb_book_id != book_id:
                continue

            files_scanned += 1
            if passage_loader is not None:
                snapshot = passage_loader.load(
                    loader_path,
                    card_type=str(meta.get("card_type") or ""),
                    kb_book_id=str(kb_book_id or ""),
                    book_title=str(meta.get("book_title") or "唐開元占經"),
                )
            else:
                try:
                    snapshot = primary_passage_cache.load(
                        path,
                        card_type=str(meta.get("card_type") or ""),
                        kb_book_id=str(kb_book_id or ""),
                        book_title=str(meta.get("book_title") or "唐開元占經"),
                    )
                except PrimarySourceReadError as exc:
                    if debug_enabled:
                        read_errors.append({"path": normalized_path, "error": str(exc)})
                    continue
            text = snapshot.text

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

                best = min(
                    cluster.spans,
                    key=lambda span: (
                        {
                            "exact_raw": 0,
                            "exact_normalized": 1,
                            "loose_window": 2,
                            "heading_only": 3,
                        }.get(span.match_type, 99),
                        span.start,
                    ),
                )
                exact_passage = None
                if strict_exact_passages:
                    if best.match_type not in {"exact_raw", "exact_normalized"}:
                        continue
                    containing = [
                        passage
                        for passage in snapshot.passages
                        if passage.raw_start <= best.start
                        and best.end <= passage.raw_end
                    ]
                    if len(containing) != 1:
                        continue
                    exact_passage = containing[0]
                page_marker = (
                    exact_passage.page_marker
                    if exact_passage is not None
                    else context.page_marker
                )
                locator = (
                    exact_passage.source_locator
                    if exact_passage is not None
                    else source_locator(normalized_path, page_marker)
                )
                volume = (
                    exact_passage.source_volume
                    if exact_passage is not None
                    else source_volume(locator, page_marker)
                )
                heading_path = (
                    list(exact_passage.heading_path)
                    if exact_passage is not None
                    else context.heading_path
                )
                paragraph_index = (
                    exact_passage.paragraph_index
                    if exact_passage is not None
                    else context.paragraph_index
                )
                heading_text = normalize_search_text(" ".join(heading_path))
                heading_term_hits = sum(
                    1
                    for term in split_loose_terms(query)
                    if term and normalize_search_text(term) in heading_text
                )
                anchor = (
                    exact_passage.raw_text
                    if exact_passage is not None
                    else context.anchor_text
                )
                hit = {
                    "chunk_id": (
                        f"fallback:{path.name}:"
                        f"{page_marker or locator}:{cluster.start}"
                    ),
                    "score": fallback_score(
                        best.match_type,
                        str(meta.get("card_type") or ""),
                    ),
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
                    "page_marker": page_marker,
                    "heading_path": heading_path,
                    "paragraph_index": paragraph_index,
                    "anchor_text": anchor,
                    "match_type": best.match_type,
                    "matched_variant": best.matched_variant,
                    "matched_variants": list(
                        dict.fromkeys(span.matched_variant for span in cluster.spans)
                    ),
                    "match_offset": cluster.start,
                    "match_end": cluster.end,
                    "match_count": len(cluster.spans),
                    "heading_term_hits": heading_term_hits,
                }
                if exact_passage is not None:
                    hit.update(
                        {
                            "content_hash": exact_passage.raw_content_hash,
                            "raw_content_hash": exact_passage.raw_content_hash,
                            "normalized_content_hash": (
                                exact_passage.normalized_content_hash
                            ),
                            "raw_start": exact_passage.raw_start,
                            "raw_end": exact_passage.raw_end,
                        }
                    )
                hits.append(hit)
                if debug_enabled:
                    debug_matches.append(
                        {
                            "path": normalized_path,
                            "source_locator": locator,
                            "page_marker": page_marker,
                            "heading_path": heading_path,
                            "match_type": best.match_type,
                            "match_offset": cluster.start,
                            "match_count": len(cluster.spans),
                            "excerpt": anchor,
                        }
                    )

    final_hits = dedupe_primary_hits(hits)[: max(limit, 0)]
    stats: dict[str, Any] = {
        "files_scanned": files_scanned,
        "matched_files": [str(hit.get("path") or "") for hit in final_hits],
        "matched_headings": [_display_heading(hit) for hit in final_hits],
        "matched_quotes": [
            str(hit.get("excerpt") or hit.get("snippet") or "")
            for hit in final_hits
        ],
    }
    if debug_enabled:
        stats["debug_scan"] = {
            "roots": [str(root) for root in roots],
            "root_exists": {str(root): root.exists() for root in roots},
            "files_scanned": files_scanned,
            "raw_match_clusters": len(hits),
            "final_sorted_files": [
                str(hit.get("path") or "") for hit in final_hits
            ],
            "final_sorted_headings": [
                _display_heading(hit) for hit in final_hits
            ],
            "final_sorted_match_types": [
                str(hit.get("match_type") or "") for hit in final_hits
            ],
            "final_sorted_scores": [
                float(hit.get("score") or 0.0) for hit in final_hits
            ],
            "matched_files": debug_matches,
            "read_errors": read_errors,
        }
    return final_hits, stats
