from __future__ import annotations

from pathlib import Path
from time import monotonic_ns
from typing import Any

from src.connectors.candidate_overlay import overlay_hits
from src.observability import base_observability, elapsed_ms


def _consensus_provenance(
    stages: list[dict[str, Any]],
    field: str,
    *,
    fallback: Any = None,
) -> tuple[Any, bool]:
    values = {stage.get(field) for stage in stages if stage.get(field) is not None}
    if len(values) > 1:
        return None, True
    if values:
        return next(iter(values)), False
    return fallback, False


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
        total_started_ns = monotonic_ns()
        effective_query_mode = query_mode or self._query_mode(query)
        effective_limit = top_k if top_k is not None else self.default_limit
        canonical_filters = self._canonicalize_filters(filters) or {}
        pool_spec = self.RETRIEVAL_POOL_SPEC.get(
            effective_query_mode,
            self.RETRIEVAL_POOL_SPEC["knowledge"],
        )

        stage1_types = list(pool_spec["stage1"])
        stage1 = self.retrieve(
            query,
            top_k=effective_limit,
            collection=collection,
            filters=canonical_filters,
            query_mode=effective_query_mode,
            retrieval_stage="structured_recall",
            card_types=stage1_types,
            literal_first=literal_first,
            literal_pool_factor=literal_pool_factor,
        )

        mode = stage1.get("query_mode") or effective_query_mode
        variants = stage1.get("query_variants") or self._query_variants(query)
        book_id = canonical_filters.get("kb_book_id")
        official_result: dict[str, Any] = {
            "schema_version": "kb-retrieve/v2",
            "query_mode": mode,
            "retrieval_stage": "primary_evidence",
            "card_types": list(pool_spec["stage2"]),
            "collection": collection or self.default_collection,
            "hits": [],
            "exact_hits": [],
            "related_hits": [],
            "raw_hits": [],
            "inferred_hits": [],
        }
        official_candidates: list[dict[str, Any]] = []

        if mode != "support":
            official_result = self.retrieve(
                query,
                top_k=effective_limit,
                collection=collection,
                filters=canonical_filters,
                query_mode=mode,
                retrieval_stage="primary_evidence",
                card_types=list(pool_spec["stage2"]),
                literal_first=True if literal_first is None else literal_first,
                literal_pool_factor=literal_pool_factor,
            )
            official_candidates = [
                hit
                for hit in official_result.get("hits", [])
                if hit.get("card_type") in self.PRIMARY_CARD_TYPES
            ][:effective_limit]

        primary_candidates = list(official_candidates)
        scan_stats: dict[str, Any] = {
            "files_scanned": 0,
            "matched_files": [],
            "matched_headings": [],
            "matched_quotes": [],
        }
        fallback_used = False
        fallback_reason: str | None = None
        fallback_observability: dict[str, Any] | None = None

        if mode != "support" and not primary_candidates:
            fallback_started_ns = monotonic_ns()
            primary_candidates, scan_stats = self._scan_primary_files(
                query,
                book_id=str(book_id) if book_id else None,
                mode=mode,
                limit=effective_limit,
                query_variants=variants,
            )
            fallback_used = True
            fallback_reason = "official_primary_empty"
            primary_candidates = [
                hit
                for hit in primary_candidates
                if hit.get("card_type") in self.PRIMARY_CARD_TYPES
            ][:effective_limit]
            fallback_observability = base_observability(
                "filesystem_fallback",
                stage="primary_evidence",
                source="filesystem",
                latency_ms=elapsed_ms(fallback_started_ns, monotonic_ns()),
                upstream_latency_ms=None,
                requested_top_k=effective_limit,
                raw_pool_size=int(scan_stats.get("files_scanned") or 0),
                returned_pool_size=len(primary_candidates),
                card_types=list(pool_spec["stage2"]),
                collection=collection or self.default_collection,
                corpus_version=None,
                fallback_reason=fallback_reason,
            )
        elif mode == "support":
            fallback_reason = "support_mode"

        if official_candidates:
            official_exact = [
                hit
                for hit in official_result.get("exact_hits", [])
                if hit.get("card_type") in self.PRIMARY_CARD_TYPES
            ]
            stage2_exact = [
                hit for hit in primary_candidates if hit in official_exact
            ][:effective_limit]
            stage2_related = [
                hit for hit in primary_candidates if hit not in stage2_exact
            ][:effective_limit]
        else:
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

        candidate_overlay_hits: list[dict[str, Any]] = []
        if self.settings.kb_enable_candidate_overlay and mode != "support":
            candidate_overlay_hits = [
                {**hit, "status": "candidate_only"}
                for hit in overlay_hits(
                    Path(self.settings.kb_candidate_overlay_root),
                    query,
                    book_id=str(book_id) if book_id else None,
                    limit=effective_limit,
                )
            ][:effective_limit]
            stage2_related.extend(
                hit
                for hit in candidate_overlay_hits
                if hit not in stage2_related
            )
            stage2_related = stage2_related[:effective_limit]

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
            "schema_version": "kb-two-stage/v2",
            "source": (
                "official_qdrant"
                if official_candidates
                else "filesystem"
                if primary_candidates and fallback_used
                else "none"
            ),
            "official_result": official_result,
            "raw_hits": official_result.get("raw_hits", []),
            "inferred_hits": primary_candidates,
            "query_mode": mode,
            "retrieval_stage": "primary_evidence",
            "card_types": list(pool_spec["stage2"]),
            "normalized_query": stage1.get(
                "normalized_query",
                self._normalize_query(query),
            ),
            "query_variants": variants,
            "exact_hits": stage2_exact,
            "related_hits": stage2_related,
            "hits": primary_candidates[:effective_limit],
            "primary_candidates": primary_candidates[:effective_limit],
            "candidate_overlay_hits": candidate_overlay_hits,
            "structured_fallbacks": structured_fallbacks,
            "official_primary_used": bool(official_candidates),
            "official_primary_empty": mode != "support" and not bool(official_candidates),
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "files_scanned": scan_stats.get("files_scanned", 0),
            "matched_files": scan_stats.get("matched_files", []),
            "matched_headings": scan_stats.get("matched_headings", []),
            "matched_quotes": scan_stats.get("matched_quotes", []),
            "only_structured_no_primary": bool(stage1.get("hits"))
            and not bool(primary_candidates),
        }
        if "debug_scan" in scan_stats:
            stage2["debug_scan"] = scan_stats["debug_scan"]
        stages: list[dict[str, Any]] = []
        if isinstance(stage1.get("observability"), dict):
            stages.append({**stage1["observability"], "source": "official_qdrant"})
        if mode != "support" and isinstance(official_result.get("observability"), dict):
            stages.append(
                {**official_result["observability"], "source": "official_qdrant"}
            )
        elif mode == "support":
            stages.append(
                base_observability(
                    "retrieve",
                    stage="primary_evidence",
                    source="skipped",
                    latency_ms=0.0,
                    upstream_latency_ms=None,
                    requested_top_k=effective_limit,
                    raw_pool_size=0,
                    returned_pool_size=0,
                    card_types=list(pool_spec["stage2"]),
                    collection=collection or self.default_collection,
                    corpus_version=None,
                    fallback_reason="support_mode",
                )
            )
        if fallback_observability is not None:
            stages.append(fallback_observability)

        official_stages = [
            stage for stage in stages if stage.get("source") == "official_qdrant"
        ]
        effective_collection, collection_conflict = _consensus_provenance(
            official_stages,
            "collection",
            fallback=collection or self.default_collection,
        )
        corpus_version, corpus_conflict = _consensus_provenance(
            official_stages,
            "corpus_version",
        )
        upstream_provenance_sha256, provenance_sha_conflict = _consensus_provenance(
            official_stages,
            "upstream_provenance_sha256",
        )
        corpus_provenance, corpus_provenance_conflict = _consensus_provenance(
            official_stages,
            "corpus_provenance",
        )
        provenance_conflicts = []
        if collection_conflict:
            provenance_conflicts.append("collection")
        if corpus_conflict:
            provenance_conflicts.append("corpus_version")
        if provenance_sha_conflict:
            provenance_conflicts.append("upstream_provenance_sha256")
        if corpus_provenance_conflict:
            provenance_conflicts.append("corpus_provenance")
        observability = base_observability(
            "two_stage_retrieve",
            total_latency_ms=elapsed_ms(total_started_ns, monotonic_ns()),
            collection=effective_collection,
            corpus_version=corpus_version,
            upstream_provenance_sha256=upstream_provenance_sha256,
            corpus_provenance=corpus_provenance,
            provenance_conflicts=provenance_conflicts,
            fallback_reason=fallback_reason,
            stages=stages,
        )
        return {"stage1": stage1, "stage2": stage2, "observability": observability}
