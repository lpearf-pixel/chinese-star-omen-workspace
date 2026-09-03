from __future__ import annotations

import sys
from pathlib import Path
from time import monotonic_ns
from typing import Any

from src.connectors.kb_contract import infer_metadata_from_path
from src.connectors.kb_retrieval.transport import KBSearchError
from src.connectors.primary_file_scanner import scan_primary_files
from src.observability import base_observability, elapsed_ms, optional_ms

TEXT_CORE = Path(__file__).resolve().parents[5] / "packages" / "kb-text-core" / "python"
if str(TEXT_CORE) not in sys.path:
    sys.path.insert(0, str(TEXT_CORE))

from kb_text_core import normalize_search_text, query_variants as core_query_variants  # noqa: E402


class RetrievalCoreMixin:
    TRADITIONAL_MAP = str.maketrans({"荧": "熒", "并": "併"})
    SIMPLIFIED_MAP = str.maketrans({"熒": "荧", "併": "并"})
    EVIDENCE_EXCLUDED_CARD_TYPES = {"prompt_asset", "nav", "qa_example"}
    FACT_EXCLUDED_CARD_TYPES = {"qa_example"}
    PRIMARY_ONLY_PHRASES = {"荧惑守心", "熒惑守心", "月犯心宿", "五星聚", "土木合"}
    PRIMARY_CARD_TYPES = {"fenjuan", "fulltext"}
    STRUCTURED_CARD_TYPES = {"term_card", "zhusu_card", "extract_card"}
    RETRIEVAL_POOL_SPEC: dict[str, dict[str, list[str]]] = {
        "knowledge": {
            "stage1": [
                "xingguan_card",
                "zhusu_card",
                "term_card",
                "extract_card",
                "topic_index",
                "chapter_summary",
            ],
            "stage2": ["fenjuan", "fulltext"],
        },
        "evidence": {
            "stage1": ["zhusu_card", "term_card", "extract_card"],
            "stage2": ["fenjuan", "fulltext"],
        },
        "support": {
            "stage1": ["topic_index", "chapter_summary", "extract_card"],
            "stage2": ["fenjuan", "fulltext"],
        },
    }

    @staticmethod
    def _query_mode(query: str) -> str:
        value = query.strip()
        support_markers = {
            "如何",
            "怎么",
            "為何",
            "为何",
            "解释",
            "背景",
            "來源",
            "来源",
            "依据",
        }
        if any(marker in value for marker in support_markers):
            return "support"
        phrase_markers = {"守", "犯", "合", "聚", "逆", "留", "蚀", "蝕", "入"}
        if any(marker in value for marker in phrase_markers):
            return "evidence"
        return "knowledge"

    @classmethod
    def _normalize_query(cls, query: str) -> str:
        return normalize_search_text(query)

    @classmethod
    def _query_variants(cls, query: str) -> list[str]:
        return core_query_variants(query)

    @staticmethod
    def _normalize_hits(
        raw_hits: list[dict[str, Any]],
        *,
        strict_primary_passages: bool = False,
    ) -> list[dict[str, Any]]:
        if strict_primary_passages:
            return [dict(hit) for hit in raw_hits]
        inferred_hits: list[dict[str, Any]] = []
        for hit in raw_hits:
            upstream_meta = (
                hit.get("metadata")
                if isinstance(hit.get("metadata"), dict)
                else {}
            )
            inferred = infer_metadata_from_path(hit.get("path"))
            path = str(hit.get("path") or "")
            title = str(hit.get("title") or "")
            heading_path = (
                hit.get("heading_path")
                or upstream_meta.get("heading_path")
                or ([title] if title else [])
            )
            if not isinstance(heading_path, list):
                heading_path = [str(heading_path)]
            volume = (
                hit.get("source_volume")
                or hit.get("volume")
                or upstream_meta.get("source_volume")
                or upstream_meta.get("volume")
            )
            if not volume and "卷" in title:
                volume = title
            section = (
                hit.get("section")
                or upstream_meta.get("section")
                or (heading_path[-1] if heading_path else title or None)
            )
            source_locator = (
                hit.get("source_locator")
                or upstream_meta.get("source_locator")
            )
            if not source_locator:
                source_locator = (
                    f"{volume}/{section}"
                    if volume and section
                    else section or volume or None
                )
            anchor_text = hit.get("anchor_text") or upstream_meta.get("anchor_text")
            if not anchor_text:
                anchor_text = str(hit.get("snippet") or "")[:120]
            kb_book_id = (
                hit.get("kb_book_id")
                or hit.get("book_id")
                or upstream_meta.get("kb_book_id")
                or upstream_meta.get("book_id")
                or inferred.get("kb_book_id")
                or inferred.get("book_id")
            )
            inferred_hits.append(
                {
                    **hit,
                    "book_title": (
                        hit.get("book_title")
                        or upstream_meta.get("book_title")
                        or inferred.get("book_title")
                    ),
                    "kb_book_id": kb_book_id,
                    "book_id": kb_book_id,
                    "card_type": (
                        hit.get("card_type")
                        or upstream_meta.get("card_type")
                        or inferred.get("card_type")
                    ),
                    "evidence_level": (
                        hit.get("evidence_level")
                        or upstream_meta.get("evidence_level")
                        or inferred.get("evidence_level")
                    ),
                    "volume": volume,
                    "source_volume": volume,
                    "section": section,
                    "source_locator": source_locator,
                    "heading_path": heading_path,
                    "anchor_text": anchor_text,
                    "path": path,
                }
            )
        return inferred_hits

    @staticmethod
    def _basename(path: str | None) -> str:
        return Path(str(path or "").replace("\\", "/")).stem

    @classmethod
    def _rank_hit(cls, query: str, hit: dict[str, Any], mode: str) -> int:
        query_value = query.strip()
        query_lower = query_value.lower()
        title = str(hit.get("title") or "").strip()
        title_lower = title.lower()
        snippet = str(hit.get("snippet") or "")
        basename = cls._basename(hit.get("path")).lower()
        path = str(hit.get("path") or "").replace("\\", "/")
        score = int(float(hit.get("score") or 0) * 10)

        if mode == "knowledge":
            if title_lower == query_lower:
                score += 120
            if basename == query_lower:
                score += 110
            if f"# {query_value}" in snippet or f"## {query_value}" in snippet:
                score += 100
            if query_lower in title_lower:
                score += 30
            if query_lower in basename:
                score += 30
            if "/逐宿卡/" in path and basename != query_lower:
                score -= 20
        else:
            if query_value and query_value in snippet:
                score += 120
            if query_value and query_value in title:
                score += 90
            keywords = [
                keyword
                for keyword in ["荧惑", "熒惑", "守", "心", "月", "犯", "五星", "聚"]
                if keyword in query_value
            ]
            score += sum(
                1
                for keyword in keywords
                if keyword in snippet or keyword in title
            ) * 15
            if query_value and query_value not in snippet and query_value not in title:
                score -= 10
        return score

    @classmethod
    def _rerank_hits(
        cls,
        query: str,
        inferred_hits: list[dict[str, Any]],
        mode: str | None = None,
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        str,
    ]:
        mode = mode or cls._query_mode(query)
        ranked = [
            {**hit, "_rank": cls._rank_hit(query, hit, mode)}
            for hit in inferred_hits
        ]
        ranked.sort(key=lambda item: item.get("_rank", 0), reverse=True)
        if mode == "knowledge":
            exact_hits = [
                hit
                for hit in ranked
                if cls._basename(hit.get("path")) == query
                or str(hit.get("title") or "") == query
            ]
        else:
            normalized_query = normalize_search_text(query)
            exact_hits = [
                hit
                for hit in ranked
                if normalized_query
                and (
                    normalized_query
                    in normalize_search_text(str(hit.get("snippet") or ""))
                    or normalized_query
                    in normalize_search_text(str(hit.get("title") or ""))
                )
            ]
        related_hits = [hit for hit in ranked if hit not in exact_hits]
        ordered = exact_hits[:3] + related_hits[:3] if exact_hits else ranked[:6]
        return ordered, exact_hits[:3], related_hits[:3], mode

    @staticmethod
    def _apply_local_filters(
        inferred_hits: list[dict[str, Any]],
        *,
        book_id: str | None = None,
        card_types: list[str] | None = None,
        evidence_level: str | None = None,
    ) -> list[dict[str, Any]]:
        out = inferred_hits
        if book_id:
            out = [
                hit
                for hit in out
                if (hit.get("kb_book_id") or hit.get("book_id")) == book_id
            ]
        if card_types:
            allowed = set(card_types)
            out = [hit for hit in out if hit.get("card_type") in allowed]
        if evidence_level:
            out = [
                hit for hit in out if hit.get("evidence_level") == evidence_level
            ]
        return out

    @staticmethod
    def _canonicalize_filters(
        filters: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not filters:
            return None
        canonical = dict(filters)
        legacy = canonical.get("book_id")
        current = canonical.get("kb_book_id")
        if legacy is not None and current is not None and str(legacy) != str(current):
            raise ValueError("conflicting book identifiers: book_id and kb_book_id")
        if current is None and legacy is not None:
            canonical["kb_book_id"] = legacy
        canonical.pop("book_id", None)
        return canonical

    def _scan_primary_files(
        self,
        query: str,
        *,
        book_id: str | None,
        mode: str,
        limit: int = 3,
        query_variants: list[str] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        return scan_primary_files(
            self.settings,
            query,
            book_id=book_id,
            mode=mode,
            limit=limit,
            query_variants=query_variants or self._query_variants(query),
            passage_loader=getattr(self, "primary_source_byte_loader", None),
            strict_exact_passages=bool(
                getattr(self, "strict_primary_passages", False)
            ),
        )

    def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        collection: str | None = None,
        filters: dict[str, Any] | None = None,
        query_mode: str | None = None,
        retrieval_stage: str | None = None,
        card_types: list[str] | None = None,
        literal_first: bool | None = None,
        literal_pool_factor: int | None = None,
    ) -> dict[str, Any]:
        effective_query_mode = query_mode or self._query_mode(query)
        effective_stage = retrieval_stage or "auto"
        effective_literal_first = literal_first
        if effective_literal_first is None:
            effective_literal_first = effective_query_mode == "evidence"
        retrieval_pool = self.RETRIEVAL_POOL_SPEC.get(
            effective_query_mode,
            self.RETRIEVAL_POOL_SPEC["knowledge"],
        )
        effective_top_k = top_k if top_k is not None else self.default_limit
        canonical_filters = self._canonicalize_filters(filters) or {}
        payload: dict[str, Any] = {
            "schema_version": "kb-retrieve/v2",
            "query": query,
            "top_k": effective_top_k,
            "collection": collection or self.default_collection,
            "query_mode": effective_query_mode,
            "retrieval_stage": effective_stage,
            "literal_first": effective_literal_first,
        }
        if card_types:
            payload["card_types"] = list(card_types)
        if canonical_filters:
            payload["filters"] = canonical_filters
        if literal_pool_factor is not None:
            payload["literal_pool_factor"] = literal_pool_factor

        started_ns = monotonic_ns()
        try:
            provenance_guard = getattr(self, "upstream_provenance_guard", None)
            if provenance_guard is not None:
                provenance_guard()
            try:
                raw_result = self._request(
                    "POST",
                    "/v1/retrieve",
                    json_payload=payload,
                    use_auth=True,
                )
            finally:
                if provenance_guard is not None:
                    provenance_guard()
        except KBSearchError as exc:
            exc.details["observability"] = base_observability(
                "retrieve",
                stage=effective_stage,
                latency_ms=elapsed_ms(started_ns, monotonic_ns()),
                upstream_latency_ms=None,
                requested_top_k=effective_top_k,
                raw_pool_size=None,
                returned_pool_size=None,
                card_types=list(card_types or []),
                collection=collection or self.default_collection,
                corpus_version=None,
            )
            raise
        raw_validator = getattr(self, "raw_response_validator", None)
        if raw_validator is not None:
            raw_validator(raw_result, request_payload=payload)
        raw_hits = raw_result.get("hits", [])
        inferred_hits = self._normalize_hits(
            raw_hits,
            strict_primary_passages=bool(
                getattr(self, "strict_primary_passages", False)
            ),
        )
        reranked, _, _, mode = self._rerank_hits(
            query,
            inferred_hits,
            mode=effective_query_mode,
        )
        filtered_hits = reranked
        normalized_query = self._normalize_query(query)
        variants = self._query_variants(query)
        if mode in {"knowledge", "evidence"}:
            filtered_hits = [
                hit
                for hit in filtered_hits
                if hit.get("card_type") not in self.FACT_EXCLUDED_CARD_TYPES
            ]
        if mode == "evidence":
            filtered_hits = [
                hit
                for hit in filtered_hits
                if hit.get("card_type") not in self.EVIDENCE_EXCLUDED_CARD_TYPES
            ]

        if mode == "knowledge":
            exact_hits = [
                hit
                for hit in filtered_hits
                if self._basename(hit.get("path")) == query
                or str(hit.get("title") or "") == query
            ]
        else:
            normalized_variants = [
                normalize_search_text(value) for value in variants
            ]
            exact_hits = [
                hit
                for hit in filtered_hits
                if any(
                    value
                    and value
                    in normalize_search_text(str(hit.get("snippet") or ""))
                    for value in normalized_variants
                )
                or any(
                    value
                    and value
                    in normalize_search_text(str(hit.get("title") or ""))
                    for value in normalized_variants
                )
            ]
        related_hits = [hit for hit in filtered_hits if hit not in exact_hits]
        effective_card_types = list(
            raw_result.get("card_types") or card_types or []
        )
        result = {
            **raw_result,
            "schema_version": raw_result.get(
                "schema_version",
                "kb-retrieve/v2",
            ),
            "query_mode": raw_result.get("query_mode") or mode,
            "retrieval_stage": raw_result.get("retrieval_stage") or effective_stage,
            "card_types": effective_card_types,
            "collection": raw_result.get("collection")
            or collection
            or self.default_collection,
            "filters": raw_result.get("filters") or canonical_filters,
            "literal_first": effective_literal_first,
            "literal_pool_factor": literal_pool_factor,
            "payload_contract_version": "kb-retrieve/v2",
            "retrieval_pool_spec": retrieval_pool,
            "normalized_query": normalized_query,
            "query_variants": variants,
            "raw_hits": raw_hits,
            "inferred_hits": inferred_hits,
            "exact_hits": exact_hits[:effective_top_k],
            "related_hits": related_hits[:effective_top_k],
            "hits": filtered_hits[:effective_top_k],
        }
        verified_provenance = getattr(self, "verified_upstream_provenance", None)
        result["observability"] = base_observability(
            "retrieve",
            stage=result["retrieval_stage"],
            latency_ms=elapsed_ms(started_ns, monotonic_ns()),
            upstream_latency_ms=optional_ms(raw_result.get("latency_ms")),
            requested_top_k=effective_top_k,
            raw_pool_size=len(raw_hits),
            returned_pool_size=len(result["hits"]),
            card_types=list(effective_card_types),
            collection=result["collection"],
            corpus_version=(
                verified_provenance.corpus_version
                if verified_provenance is not None
                else raw_result.get("corpus_version")
            ),
            provenance_sha256=(
                verified_provenance.provenance_sha256
                if verified_provenance is not None
                else None
            ),
            corpus_provenance=(
                "upstream_meta" if verified_provenance is not None else None
            ),
        )
        return result

    def rag_query(
        self,
        query: str,
        *,
        book_id: str | None = None,
        limit: int | None = None,
        collection: str | None = None,
        filters: dict[str, Any] | None = None,
        query_mode: str | None = None,
        retrieval_stage: str | None = None,
        card_types: list[str] | None = None,
        generate: bool = True,
        literal_first: bool | None = None,
        literal_pool_factor: int | None = None,
    ) -> dict[str, Any]:
        canonical_filters = self._canonicalize_filters(filters) or {}
        if book_id:
            existing = canonical_filters.get("kb_book_id")
            if existing is not None and str(existing) != str(book_id):
                raise ValueError("conflicting book identifiers")
            canonical_filters["kb_book_id"] = book_id
        effective_mode = query_mode or self._query_mode(query)
        effective_literal_first = literal_first
        if effective_literal_first is None:
            effective_literal_first = effective_mode == "evidence"
        payload: dict[str, Any] = {
            "schema_version": "kb-rag/v2",
            "question": query,
            "top_k": limit if limit is not None else self.default_limit,
            "collection": collection or self.default_collection,
            "query_mode": effective_mode,
            "retrieval_stage": retrieval_stage or "auto",
            "generate": generate,
            "literal_first": effective_literal_first,
        }
        if canonical_filters:
            payload["filters"] = canonical_filters
        if card_types:
            payload["card_types"] = list(card_types)
        if literal_pool_factor is not None:
            payload["literal_pool_factor"] = literal_pool_factor
        return self._request(
            "POST",
            "/v1/rag/query",
            json_payload=payload,
            use_auth=True,
        )

    def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        collection: str | None = None,
        filters: dict[str, Any] | None = None,
        query_mode: str | None = None,
        retrieval_stage: str | None = None,
        card_types: list[str] | None = None,
        literal_first: bool | None = None,
        literal_pool_factor: int | None = None,
    ) -> dict[str, Any]:
        return self.retrieve(
            query,
            top_k=top_k,
            collection=collection,
            filters=filters,
            query_mode=query_mode,
            retrieval_stage=retrieval_stage,
            card_types=card_types,
            literal_first=literal_first,
            literal_pool_factor=literal_pool_factor,
        )
