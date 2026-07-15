from __future__ import annotations

from pathlib import Path
from typing import Any

from src.connectors.candidate_overlay import overlay_hits


class TwoStageMixin:
    def two_stage_retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        collection: str | None = None,
        filters: dict[str, Any] | None = None,
        query_mode: str | None = None,
        literal_first: bool | None = None,
        literal_pool_factor: int | None = None,
    ) -> dict[str, Any]:
        effective_query_mode = query_mode or self._query_mode(query)
        effective_limit = top_k if top_k is not None else self.default_limit
        canonical_filters = self._canonicalize_filters(filters) or {}
        stage1_filters = {
            **canonical_filters,
            "card_type": list(
                self.RETRIEVAL_POOL_SPEC.get(
                    effective_query_mode,
                    self.RETRIEVAL_POOL_SPEC["knowledge"],
                )["stage1"]
            ),
        }
        stage1 = self.retrieve(
            query,
            top_k=effective_limit,
            collection=collection,
            filters=stage1_filters,
            query_mode=effective_query_mode,
            literal_first=literal_first,
            literal_pool_factor=literal_pool_factor,
        )

        mode = stage1.get("query_mode") or effective_query_mode
        variants = stage1.get("query_variants") or self._query_variants(query)
        book_id = canonical_filters.get("kb_book_id") or canonical_filters.get("book_id")
        primary_candidates: list[dict[str, Any]] = []
        scan_stats: dict[str, Any] = {
            "files_scanned": 0,
            "matched_files": [],
            "matched_headings": [],
            "matched_quotes": [],
        }
        fallback_used = False

        if mode != "support":
            primary_candidates, scan_stats = self._scan_primary_files(
                query,
                book_id=str(book_id) if book_id else None,
                mode=mode,
                limit=effective_limit,
                query_variants=variants,
            )
            fallback_used = bool(primary_candidates) or scan_stats.get("files_scanned", 0) > 0
            primary_candidates = [
                hit
                for hit in primary_candidates
                if hit.get("card_type") in self.PRIMARY_CARD_TYPES
            ][:effective_limit]

        exact_types = {"exact_raw", "exact_normalized"}
        stage2_exact = [
            hit
            for hit in primary_candidates
            if hit.get("card_type") in self.PRIMARY_CARD_TYPES
            and hit.get("match_type") in exact_types
        ][:effective_limit]
        stage2_related = [
            hit for hit in primary_candidates if hit not in stage2_exact
        ][:effective_limit]

        if self.settings.kb_enable_candidate_overlay and mode != "support":
            candidate_hits = overlay_hits(
                Path(self.settings.kb_candidate_overlay_root),
                query,
                book_id=str(book_id) if book_id else None,
                limit=effective_limit,
            )
            primary_candidates.extend(
                hit for hit in candidate_hits if hit not in primary_candidates
            )
            primary_candidates = primary_candidates[:effective_limit]
            stage2_related = [
                hit for hit in primary_candidates if hit not in stage2_exact
            ][:effective_limit]

        structured_fallbacks: list[dict[str, Any]] = []
        if mode == "evidence" and not primary_candidates:
            structured_fallbacks = [
                {**hit, "status": "candidate_only"}
                for hit in (
                    stage1.get("exact_hits", [])
                    + stage1.get("related_hits", [])
                )
                if hit.get("card_type") in self.STRUCTURED_CARD_TYPES
            ][:effective_limit]

        stage2 = {
            "raw_hits": [],
            "inferred_hits": primary_candidates,
            "query_mode": mode,
            "normalized_query": stage1.get(
                "normalized_query",
                self._normalize_query(query),
            ),
            "query_variants": variants,
            "exact_hits": stage2_exact,
            "related_hits": stage2_related,
            "hits": primary_candidates[:effective_limit],
            "primary_candidates": primary_candidates[:effective_limit],
            "structured_fallbacks": structured_fallbacks,
            "fallback_used": fallback_used,
            "files_scanned": scan_stats.get("files_scanned", 0),
            "matched_files": scan_stats.get("matched_files", []),
            "matched_headings": scan_stats.get("matched_headings", []),
            "matched_quotes": scan_stats.get("matched_quotes", []),
            "only_structured_no_primary": bool(stage1.get("hits")) and not bool(primary_candidates),
        }
        if "debug_scan" in scan_stats:
            stage2["debug_scan"] = scan_stats["debug_scan"]
        return {"stage1": stage1, "stage2": stage2}
