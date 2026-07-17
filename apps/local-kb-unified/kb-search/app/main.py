"""KB Search API backed by host Ollama and Qdrant.

The v2 contract separates user intent (``query_mode``), retrieval phase
(``retrieval_stage``), and the effective card pool (``card_types``).  It also
exposes the last successful corpus manifest and treats readiness as a compound
check rather than a process-liveness signal.
"""

from __future__ import annotations

import secrets
import time
from typing import Any, Dict, List, Literal, Optional, Tuple

import requests
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from . import config, ollama_client
from .meta import load_corpus_meta
from .retrieval_pools import build_retrieval_filter, resolve_card_types
from .stellar_query_replacements import iter_embedding_query_strings, normalize_stellar_query

app = FastAPI(title="KB Search API", version="0.2.0")

QueryMode = Literal["evidence", "knowledge", "support"]
RetrievalStage = Literal[
    "auto",
    "structured_recall",
    "primary_evidence",
    "support_context",
]


def _snippet(text: str, max_len: int = 500) -> str:
    value = (text or "").strip()
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


def _qdrant_client() -> QdrantClient:
    return QdrantClient(url=config.QDRANT_URL, timeout=60)


def _literal_match_variants(user_query: str) -> List[str]:
    output: List[str] = []
    for value in (user_query.strip(), normalize_stellar_query(user_query).strip()):
        if len(value) >= 2 and value not in output:
            output.append(value)
    return output


def _chunk_matches_literals(chunk_text: str, variants: List[str]) -> bool:
    return bool(chunk_text) and any(
        len(value) >= 2 and value in chunk_text for value in variants
    )


async def require_api_key(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> None:
    token: Optional[str] = None
    if isinstance(authorization, str) and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif isinstance(x_api_key, str):
        token = x_api_key.strip()
    if not token or not secrets.compare_digest(token, config.KB_SEARCH_API_KEY):
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "invalid or missing API key",
                }
            },
        )


class RetrieveRequest(BaseModel):
    schema_version: Optional[str] = Field(default="kb-retrieve/v2")
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    collection: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    query_mode: Optional[QueryMode] = None
    retrieval_stage: Optional[RetrievalStage] = None
    card_types: Optional[List[str]] = None
    literal_first: bool = False
    literal_pool_factor: Optional[int] = Field(default=None, ge=2, le=40)


class Hit(BaseModel):
    chunk_id: Optional[str] = None
    score: float
    path: Optional[str] = None
    snippet: str
    source_type: Optional[str] = None
    title: Optional[str] = None
    ingest_source: Optional[str] = None
    relative_path: Optional[str] = None
    section_heading: Optional[str] = None
    card_type: Optional[str] = None
    kb_book_id: Optional[str] = None
    book_title: Optional[str] = None
    evidence_level: Optional[str] = None
    final_citable: Optional[bool] = None
    source_locator: Optional[str] = None
    source_volume: Optional[str] = None
    page_marker: Optional[str] = None
    heading_path: Optional[List[str]] = None
    paragraph_index: Optional[int] = None
    raw_start: Optional[int] = None
    raw_end: Optional[int] = None
    content_hash: Optional[str] = None
    raw_content_hash: Optional[str] = None
    normalized_content_hash: Optional[str] = None
    query_mode_hint: Optional[str] = None
    source_refs: Optional[List[str]] = None
    managed_by: Optional[str] = None
    collection_schema: Optional[str] = None


class RetrieveResponse(BaseModel):
    schema_version: str = "kb-retrieve/v2"
    query_mode: Optional[QueryMode] = None
    retrieval_stage: RetrievalStage = "auto"
    card_types: List[str] = Field(default_factory=list)
    collection: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    hits: List[Hit]
    retrieved_count: int
    latency_ms: int


class Citation(BaseModel):
    path: Optional[str] = None
    snippet: str
    score: float
    card_type: Optional[str] = None
    kb_book_id: Optional[str] = None
    book_title: Optional[str] = None
    evidence_level: Optional[str] = None
    final_citable: Optional[bool] = None
    source_locator: Optional[str] = None
    source_volume: Optional[str] = None
    page_marker: Optional[str] = None
    heading_path: Optional[List[str]] = None
    paragraph_index: Optional[int] = None
    raw_start: Optional[int] = None
    raw_end: Optional[int] = None
    content_hash: Optional[str] = None
    raw_content_hash: Optional[str] = None
    normalized_content_hash: Optional[str] = None
    query_mode_hint: Optional[str] = None
    source_refs: Optional[List[str]] = None
    managed_by: Optional[str] = None
    collection_schema: Optional[str] = None


class RAGRequest(BaseModel):
    schema_version: Optional[str] = Field(default="kb-rag/v2")
    question: str
    top_k: int = Field(default=5, ge=1, le=50)
    min_score: float = Field(default=0.0)
    collection: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    query_mode: Optional[QueryMode] = None
    retrieval_stage: Optional[RetrievalStage] = None
    card_types: Optional[List[str]] = None
    generate: bool = True
    literal_first: bool = False
    literal_pool_factor: Optional[int] = Field(default=None, ge=2, le=40)


class RAGResponse(BaseModel):
    schema_version: str = "kb-rag/v2"
    query_mode: Optional[QueryMode] = None
    retrieval_stage: RetrievalStage = "auto"
    card_types: List[str] = Field(default_factory=list)
    collection: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    answer: str
    citations: List[Citation]
    retrieved_count: int
    latency_ms: int


def _payload_to_hit(payload: Dict[str, Any], score: float) -> Hit:
    chunk_text = payload.get("chunk_text") or payload.get("anchor_text") or ""
    refs = payload.get("source_refs")
    if refs is None:
        refs = payload.get("duplicate_sources")
    return Hit(
        chunk_id=payload.get("chunk_id"),
        score=float(score),
        path=payload.get("path"),
        snippet=_snippet(str(chunk_text)),
        source_type=payload.get("source_type"),
        title=payload.get("title"),
        ingest_source=payload.get("ingest_source"),
        relative_path=payload.get("relative_path"),
        section_heading=payload.get("section_heading"),
        card_type=payload.get("card_type"),
        kb_book_id=payload.get("kb_book_id") or payload.get("book_id"),
        book_title=payload.get("book_title"),
        evidence_level=payload.get("evidence_level"),
        final_citable=payload.get("final_citable"),
        source_locator=payload.get("source_locator"),
        source_volume=payload.get("source_volume") or payload.get("volume"),
        page_marker=payload.get("page_marker"),
        heading_path=payload.get("heading_path"),
        paragraph_index=payload.get("paragraph_index"),
        raw_start=payload.get("raw_start"),
        raw_end=payload.get("raw_end"),
        content_hash=payload.get("content_hash"),
        raw_content_hash=payload.get("raw_content_hash"),
        normalized_content_hash=payload.get("normalized_content_hash"),
        query_mode_hint=payload.get("query_mode_hint"),
        source_refs=refs,
        managed_by=payload.get("managed_by"),
        collection_schema=payload.get("collection_schema"),
    )


def _hit_merge_key(payload: Dict[str, Any]) -> str:
    chunk_id = payload.get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    text = payload.get("chunk_text") or payload.get("anchor_text") or ""
    return f"p:{payload.get('path', '')}\0{hash(str(text)[:240])}"


def _merge_score_rows(
    branches: List[List[Tuple[Dict[str, Any], float]]],
) -> List[Tuple[Dict[str, Any], float]]:
    best: Dict[str, Tuple[Dict[str, Any], float]] = {}
    for rows in branches:
        for payload, score in rows:
            key = _hit_merge_key(payload)
            previous = best.get(key)
            if previous is None or score > previous[1]:
                best[key] = (payload, score)
    return list(best.values())


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": message}},
    )


def _is_missing_collection_error(exc: Exception) -> bool:
    value = str(exc).lower()
    return any(
        token in value
        for token in ("404", "not found", "doesn't exist", "unknown collection")
    )


def _assert_collection_exists(client: Any, collection: str) -> None:
    checker = getattr(client, "collection_exists", None)
    getter = getattr(client, "get_collection", None)
    try:
        if callable(checker):
            try:
                exists = bool(checker(collection))
            except TypeError:
                exists = bool(checker(collection_name=collection))
            if not exists:
                raise _error(
                    404,
                    "COLLECTION_NOT_FOUND",
                    f"Qdrant collection not found: {collection}",
                )
            return
        if callable(getter):
            try:
                getter(collection)
            except TypeError:
                getter(collection_name=collection)
    except HTTPException:
        raise
    except Exception as exc:
        if _is_missing_collection_error(exc):
            raise _error(
                404,
                "COLLECTION_NOT_FOUND",
                f"Qdrant collection not found: {collection}",
            ) from exc
        raise _error(
            503,
            "UPSTREAM_UNAVAILABLE",
            f"qdrant collection check failed: {exc}",
        ) from exc


def _vector_search_rows(
    *,
    client: Any,
    embedding_text: str,
    collection: str,
    limit: int,
    min_score: Optional[float],
    filters: Optional[Dict[str, Any]],
    query_mode: Optional[str],
    retrieval_stage: Optional[str],
    card_types: Optional[List[str]],
) -> List[Tuple[Dict[str, Any], float]]:
    vector = ollama_client.embed_text(embedding_text)
    try:
        q_filter = build_retrieval_filter(
            filters=filters,
            query_mode=query_mode,
            retrieval_stage=retrieval_stage,
            card_types=card_types,
        )
    except ValueError as exc:
        raise _error(422, "CONTRACT_ERROR", str(exc)) from exc

    try:
        response = client.query_points(
            collection_name=collection,
            query=vector,
            limit=limit,
            score_threshold=min_score if min_score and min_score > 0 else None,
            query_filter=q_filter,
            with_payload=True,
        )
        results = response.points
    except Exception as exc:
        if _is_missing_collection_error(exc):
            raise _error(
                404,
                "COLLECTION_NOT_FOUND",
                f"Qdrant collection not found: {collection}",
            ) from exc
        raise _error(
            503,
            "UPSTREAM_UNAVAILABLE",
            f"qdrant search failed: {exc}",
        ) from exc

    return [
        (dict(point.payload or {}), float(point.score))
        for point in results
    ]


def _search(
    *,
    query_text: str,
    collection: str,
    top_k: int,
    min_score: Optional[float],
    filters: Optional[Dict[str, Any]],
    query_mode: Optional[str] = None,
    retrieval_stage: Optional[str] = None,
    card_types: Optional[List[str]] = None,
    literal_first: bool = False,
    literal_pool_factor: Optional[int] = None,
) -> List[Hit]:
    client = _qdrant_client()
    _assert_collection_exists(client, collection)

    embedding_variants = iter_embedding_query_strings(query_text)
    factor = (
        literal_pool_factor
        if literal_pool_factor is not None
        else config.KB_LITERAL_POOL_FACTOR
    )
    fetch_limit = (
        max(top_k, min(top_k * factor, config.KB_LITERAL_POOL_CAP))
        if literal_first
        else top_k
    )

    branches = [
        _vector_search_rows(
            client=client,
            embedding_text=value,
            collection=collection,
            limit=fetch_limit,
            min_score=min_score,
            filters=filters,
            query_mode=query_mode,
            retrieval_stage=retrieval_stage,
            card_types=card_types,
        )
        for value in embedding_variants
    ]
    merged = _merge_score_rows(branches) if len(branches) > 1 else branches[0]

    if literal_first:
        literal_variants = _literal_match_variants(query_text)
        merged.sort(
            key=lambda row: (
                0
                if _chunk_matches_literals(
                    str(row[0].get("chunk_text") or ""),
                    literal_variants,
                )
                else 1,
                -row[1],
            )
        )
    else:
        merged.sort(key=lambda row: -row[1])

    return [_payload_to_hit(payload, score) for payload, score in merged[:top_k]]


def _resolve_request_contract(
    *,
    query_mode: Optional[str],
    retrieval_stage: Optional[str],
    card_types: Optional[List[str]],
    filters: Optional[Dict[str, Any]],
) -> tuple[List[str], Dict[str, Any], str]:
    try:
        effective_card_types, canonical_filters = resolve_card_types(
            query_mode=query_mode,
            retrieval_stage=retrieval_stage,
            card_types=card_types,
            filters=filters,
        )
    except ValueError as exc:
        raise _error(422, "CONTRACT_ERROR", str(exc)) from exc
    effective_stage = (retrieval_stage or "auto").strip().lower()
    return list(effective_card_types or []), canonical_filters, effective_stage


def _ollama_readiness() -> Dict[str, Any]:
    try:
        response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if not response.ok:
            return {"ollama": False, "embedding_model": False, "models": []}
        payload = response.json() if hasattr(response, "json") else {}
        rows = payload.get("models", []) if isinstance(payload, dict) else []
        models = [
            str(row.get("name") or row.get("model") or "")
            for row in rows
            if isinstance(row, dict)
        ]
        target = config.EMBED_MODEL
        target_base = target.split(":", 1)[0]
        model_ready = any(
            name == target or name.split(":", 1)[0] == target_base
            for name in models
        )
        return {
            "ollama": True,
            "embedding_model": model_ready,
            "models": models,
        }
    except Exception:
        return {"ollama": False, "embedding_model": False, "models": []}


def _qdrant_readiness(collection: str) -> Dict[str, Any]:
    try:
        client = _qdrant_client()
        response = client.get_collections()
        rows = getattr(response, "collections", []) or []
        collections = [
            str(getattr(row, "name", row))
            for row in rows
        ]
        if collection not in collections:
            checker = getattr(client, "collection_exists", None)
            if callable(checker):
                try:
                    present = bool(checker(collection))
                except TypeError:
                    present = bool(checker(collection_name=collection))
                if present:
                    collections.append(collection)
        return {
            "qdrant": True,
            "default_collection": collection in collections,
            "collections": sorted(set(collections)),
        }
    except Exception:
        return {
            "qdrant": False,
            "default_collection": False,
            "collections": [],
        }


@app.get("/v1/meta")
def meta() -> JSONResponse:
    corpus = load_corpus_meta()
    return JSONResponse(
        content=corpus,
        status_code=200 if corpus.get("meta_status") == "ok" else 503,
    )


@app.get("/v1/health")
def health() -> JSONResponse:
    collection = config.KB_SEARCH_DEFAULT_COLLECTION
    corpus = load_corpus_meta()
    ollama = _ollama_readiness()
    qdrant = _qdrant_readiness(collection)

    manifest_ok = corpus.get("meta_status") == "ok"
    checks = {
        "ollama": bool(ollama.get("ollama")),
        "embedding_model": bool(ollama.get("embedding_model")),
        "qdrant": bool(qdrant.get("qdrant")),
        "default_collection": bool(qdrant.get("default_collection")),
        "corpus_manifest": manifest_ok,
        "manifest_collection_match": bool(
            manifest_ok and corpus.get("collection") == collection
        ),
    }
    ready = all(checks.values())
    body = {
        "status": "ok" if ready else "degraded",
        "ready": ready,
        "checks": checks,
        "dependencies": {
            "ollama": ollama,
            "qdrant": qdrant,
        },
        "corpus": corpus,
        "default_collection": collection,
    }
    return JSONResponse(content=body, status_code=200 if ready else 503)


@app.post("/v1/retrieve", dependencies=[Depends(require_api_key)])
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    started = time.perf_counter()
    collection = request.collection or config.KB_SEARCH_DEFAULT_COLLECTION
    effective_card_types, canonical_filters, effective_stage = _resolve_request_contract(
        query_mode=request.query_mode,
        retrieval_stage=request.retrieval_stage,
        card_types=request.card_types,
        filters=request.filters,
    )
    hits = _search(
        query_text=request.query,
        collection=collection,
        top_k=request.top_k,
        min_score=None,
        filters=canonical_filters,
        query_mode=request.query_mode,
        retrieval_stage=effective_stage,
        card_types=effective_card_types,
        literal_first=request.literal_first,
        literal_pool_factor=request.literal_pool_factor,
    )
    return RetrieveResponse(
        query_mode=request.query_mode,
        retrieval_stage=effective_stage,
        card_types=effective_card_types,
        collection=collection,
        filters=canonical_filters,
        hits=hits,
        retrieved_count=len(hits),
        latency_ms=int((time.perf_counter() - started) * 1000),
    )


def _citation_from_hit(hit: Hit) -> Citation:
    return Citation(
        path=hit.path,
        snippet=hit.snippet,
        score=hit.score,
        card_type=hit.card_type,
        kb_book_id=hit.kb_book_id,
        book_title=hit.book_title,
        evidence_level=hit.evidence_level,
        final_citable=hit.final_citable,
        source_locator=hit.source_locator,
        source_volume=hit.source_volume,
        page_marker=hit.page_marker,
        heading_path=hit.heading_path,
        paragraph_index=hit.paragraph_index,
        raw_start=hit.raw_start,
        raw_end=hit.raw_end,
        content_hash=hit.content_hash,
        raw_content_hash=hit.raw_content_hash,
        normalized_content_hash=hit.normalized_content_hash,
        query_mode_hint=hit.query_mode_hint,
        source_refs=hit.source_refs,
        managed_by=hit.managed_by,
        collection_schema=hit.collection_schema,
    )


@app.post("/v1/rag/query", dependencies=[Depends(require_api_key)])
def rag_query(request: RAGRequest) -> RAGResponse:
    started = time.perf_counter()
    collection = request.collection or config.KB_SEARCH_DEFAULT_COLLECTION
    effective_card_types, canonical_filters, effective_stage = _resolve_request_contract(
        query_mode=request.query_mode,
        retrieval_stage=request.retrieval_stage,
        card_types=request.card_types,
        filters=request.filters,
    )
    hits = _search(
        query_text=request.question,
        collection=collection,
        top_k=request.top_k,
        min_score=request.min_score,
        filters=canonical_filters,
        query_mode=request.query_mode,
        retrieval_stage=effective_stage,
        card_types=effective_card_types,
        literal_first=request.literal_first,
        literal_pool_factor=request.literal_pool_factor,
    )
    citations = [_citation_from_hit(hit) for hit in hits]

    answer = ""
    if request.generate:
        if not hits:
            answer = "未检索到相关片段，无法基于知识库生成答案。"
        else:
            context = "\n\n".join(
                (
                    f"[{index}] 来源: {hit.source_locator or hit.path or '(unknown)'}"
                    f" 页码: {hit.page_marker or '(unknown)'}\n{hit.snippet}"
                )
                for index, hit in enumerate(hits, 1)
            )
            system = (
                "你是本地知识库助手。请仅根据提供的上下文回答问题；"
                "若上下文不足，请明确说明。回答末尾可简要列出引用编号。"
            )
            try:
                answer = ollama_client.chat_completion(
                    system,
                    f"上下文：\n{context}\n\n问题：{request.question}",
                )
            except Exception as exc:
                raise _error(
                    503,
                    "UPSTREAM_UNAVAILABLE",
                    f"ollama chat failed: {exc}",
                ) from exc

    return RAGResponse(
        query_mode=request.query_mode,
        retrieval_stage=effective_stage,
        card_types=effective_card_types,
        collection=collection,
        filters=canonical_filters,
        answer=answer,
        citations=citations,
        retrieved_count=len(citations),
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
