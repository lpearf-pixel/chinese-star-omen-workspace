"""KB Search API backed by host Ollama and Qdrant."""

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
from .retrieval_pools import build_retrieval_filter
from .stellar_query_replacements import iter_embedding_query_strings, normalize_stellar_query

app = FastAPI(title="KB Search API", version="0.1.0")


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
    return bool(chunk_text) and any(len(value) >= 2 and value in chunk_text for value in variants)


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
            detail={"error": {"code": "UNAUTHORIZED", "message": "invalid or missing API key"}},
        )


QueryMode = Literal["evidence", "knowledge", "support"]


class RetrieveRequest(BaseModel):
    schema_version: Optional[str] = Field(default="v1")
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    collection: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    query_mode: Optional[QueryMode] = None
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
    evidence_level: Optional[str] = None
    final_citable: Optional[bool] = None
    source_locator: Optional[str] = None
    query_mode_hint: Optional[str] = None
    source_refs: Optional[List[str]] = None


class RetrieveResponse(BaseModel):
    schema_version: str = "v1"
    hits: List[Hit]
    retrieved_count: int
    latency_ms: int


class Citation(BaseModel):
    path: Optional[str] = None
    snippet: str
    score: float
    card_type: Optional[str] = None
    kb_book_id: Optional[str] = None
    evidence_level: Optional[str] = None
    source_locator: Optional[str] = None
    query_mode_hint: Optional[str] = None
    source_refs: Optional[List[str]] = None


class RAGRequest(BaseModel):
    schema_version: Optional[str] = Field(default="v1")
    question: str
    top_k: int = Field(default=5, ge=1, le=50)
    min_score: float = Field(default=0.0)
    collection: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    query_mode: Optional[QueryMode] = None
    generate: bool = True
    literal_first: bool = False
    literal_pool_factor: Optional[int] = Field(default=None, ge=2, le=40)


class RAGResponse(BaseModel):
    schema_version: str = "v1"
    answer: str
    citations: List[Citation]
    retrieved_count: int
    latency_ms: int


def _payload_to_hit(payload: Dict[str, Any], score: float) -> Hit:
    chunk_text = payload.get("chunk_text") or ""
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
        kb_book_id=payload.get("kb_book_id"),
        evidence_level=payload.get("evidence_level"),
        final_citable=payload.get("final_citable"),
        source_locator=payload.get("source_locator"),
        query_mode_hint=payload.get("query_mode_hint"),
        source_refs=payload.get("source_refs"),
    )


def _hit_merge_key(payload: Dict[str, Any]) -> str:
    chunk_id = payload.get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    text = payload.get("chunk_text") or ""
    return f"p:{payload.get('path', '')}\0{hash(text[:240])}"


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


def _vector_search_rows(
    embedding_text: str,
    collection: str,
    limit: int,
    min_score: Optional[float],
    filters: Optional[Dict[str, Any]],
    query_mode: Optional[str],
) -> List[Tuple[Dict[str, Any], float]]:
    vector = ollama_client.embed_text(embedding_text)
    client = _qdrant_client()
    q_filter = build_retrieval_filter(filters, query_mode)
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
        error = str(exc).lower()
        if any(token in error for token in ("404", "not found", "doesn't exist", "unknown collection")):
            return []
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "UPSTREAM_UNAVAILABLE",
                    "message": f"qdrant search failed: {exc}",
                }
            },
        ) from exc

    output: List[Tuple[Dict[str, Any], float]] = []
    for point in results:
        output.append((dict(point.payload or {}), float(point.score)))
    return output


def _search(
    query_text: str,
    collection: str,
    top_k: int,
    min_score: Optional[float],
    filters: Optional[Dict[str, Any]],
    query_mode: Optional[str] = None,
    literal_first: bool = False,
    literal_pool_factor: Optional[int] = None,
) -> List[Hit]:
    embedding_variants = iter_embedding_query_strings(query_text)
    factor = literal_pool_factor if literal_pool_factor is not None else config.KB_LITERAL_POOL_FACTOR
    if literal_first:
        fetch_limit = max(top_k, min(top_k * factor, config.KB_LITERAL_POOL_CAP))
    else:
        fetch_limit = top_k

    branches = [
        _vector_search_rows(
            value,
            collection,
            fetch_limit,
            min_score,
            filters,
            query_mode,
        )
        for value in embedding_variants
    ]
    merged = _merge_score_rows(branches) if len(branches) > 1 else branches[0]

    if literal_first:
        literal_variants = _literal_match_variants(query_text)
        merged.sort(
            key=lambda row: (
                0 if _chunk_matches_literals(row[0].get("chunk_text") or "", literal_variants) else 1,
                -row[1],
            )
        )
    else:
        merged.sort(key=lambda row: -row[1])

    return [_payload_to_hit(payload, score) for payload, score in merged[:top_k]]


@app.get("/v1/health")
def health() -> JSONResponse:
    ollama_ok = False
    qdrant_ok = False
    try:
        response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        ollama_ok = response.ok
    except Exception:
        pass
    try:
        _qdrant_client().get_collections()
        qdrant_ok = True
    except Exception:
        pass

    status = "ok" if ollama_ok and qdrant_ok else "degraded"
    return JSONResponse(
        content={"status": status, "ollama": ollama_ok, "qdrant": qdrant_ok},
        status_code=200 if status == "ok" else 503,
    )


@app.post("/v1/retrieve", dependencies=[Depends(require_api_key)])
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    started = time.perf_counter()
    collection = request.collection or config.KB_SEARCH_DEFAULT_COLLECTION
    hits = _search(
        request.query,
        collection,
        request.top_k,
        None,
        request.filters,
        request.query_mode,
        literal_first=request.literal_first,
        literal_pool_factor=request.literal_pool_factor,
    )
    return RetrieveResponse(
        hits=hits,
        retrieved_count=len(hits),
        latency_ms=int((time.perf_counter() - started) * 1000),
    )


@app.post("/v1/rag/query", dependencies=[Depends(require_api_key)])
def rag_query(request: RAGRequest) -> RAGResponse:
    started = time.perf_counter()
    collection = request.collection or config.KB_SEARCH_DEFAULT_COLLECTION
    hits = _search(
        request.question,
        collection,
        request.top_k,
        request.min_score,
        request.filters,
        request.query_mode,
        literal_first=request.literal_first,
        literal_pool_factor=request.literal_pool_factor,
    )
    citations = [
        Citation(
            path=hit.path,
            snippet=hit.snippet,
            score=hit.score,
            card_type=hit.card_type,
            kb_book_id=hit.kb_book_id,
            evidence_level=hit.evidence_level,
            source_locator=hit.source_locator,
            query_mode_hint=hit.query_mode_hint,
            source_refs=hit.source_refs,
        )
        for hit in hits
    ]

    answer = ""
    if request.generate:
        if not hits:
            answer = "未检索到相关片段，无法基于知识库生成答案。"
        else:
            context = "\n\n".join(
                f"[{index}] 来源: {hit.path or '(unknown)'}\n{hit.snippet or ''}"
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
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": {
                            "code": "UPSTREAM_UNAVAILABLE",
                            "message": f"ollama chat failed: {exc}",
                        }
                    },
                ) from exc

    return RAGResponse(
        answer=answer,
        citations=citations,
        retrieved_count=len(citations),
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
