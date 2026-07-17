# KB Search API — Kaiyuan Retrieval Contract v2

Base URL:

```text
http://127.0.0.1:8008
```

Authenticated endpoints accept either:

```http
Authorization: Bearer <key>
X-API-Key: <key>
```

## Contract concepts

The v2 contract keeps three concerns separate:

- `query_mode`: user intent — `evidence`, `knowledge`, or `support`;
- `retrieval_stage`: current retrieval phase — `auto`, `structured_recall`, `primary_evidence`, or `support_context`;
- `card_types`: explicit Qdrant card pool for this request.

Pool resolution order is:

```text
explicit card_types
→ legacy filters.card_type
→ retrieval_stage default pool
→ query_mode compatibility pool
```

`kb_book_id` is the canonical book filter. `book_id` is accepted only as a read-compatibility alias; conflicting values return `CONTRACT_ERROR`.

## Readiness

```http
GET /v1/health
```

HTTP 200 requires all of the following:

- Ollama is reachable;
- the configured embedding model is installed;
- Qdrant is reachable;
- the default collection exists;
- the corpus manifest is valid;
- the manifest collection matches the default collection.

Otherwise the endpoint returns HTTP 503 with `status=degraded`, `ready=false`, and per-check details.

## Corpus metadata

```http
GET /v1/meta
```

A valid manifest returns HTTP 200 and includes:

```json
{
  "meta_status": "ok",
  "schema_version": "corpus-manifest/v1",
  "corpus_version": "20260717T120000Z",
  "ingest_run_id": "ingest_20260717T120000Z",
  "source_manifest_hash": "sha256:...",
  "collection": "local_kb_kaiyuan_v2",
  "managed_by": "local-kb-unified/v2",
  "collection_schema": "passage-v2",
  "run_stats": {}
}
```

Missing or invalid metadata is explicit (`meta_status=missing|invalid`) and returns HTTP 503. Clients must not invent a successful `corpus_version=unknown` state.

## Retrieve

```http
POST /v1/retrieve
Content-Type: application/json
Authorization: Bearer ...
```

Structured recall:

```json
{
  "schema_version": "kb-retrieve/v2",
  "query": "荧惑守心",
  "top_k": 8,
  "collection": "local_kb_kaiyuan_v2",
  "filters": {
    "kb_book_id": "kaiyuan_zhanjing"
  },
  "query_mode": "evidence",
  "retrieval_stage": "structured_recall",
  "card_types": ["zhusu_card", "term_card", "extract_card"],
  "literal_first": true
}
```

Primary-evidence recall:

```json
{
  "schema_version": "kb-retrieve/v2",
  "query": "荧惑守心",
  "top_k": 8,
  "collection": "local_kb_kaiyuan_v2",
  "filters": {
    "kb_book_id": "kaiyuan_zhanjing"
  },
  "query_mode": "evidence",
  "retrieval_stage": "primary_evidence",
  "card_types": ["fenjuan", "fulltext"],
  "literal_first": true
}
```

The response echoes the effective contract:

```json
{
  "schema_version": "kb-retrieve/v2",
  "query_mode": "evidence",
  "retrieval_stage": "primary_evidence",
  "card_types": ["fenjuan", "fulltext"],
  "collection": "local_kb_kaiyuan_v2",
  "filters": {
    "kb_book_id": "kaiyuan_zhanjing"
  },
  "hits": [],
  "retrieved_count": 0,
  "latency_ms": 4
}
```

A primary passage may include:

```text
kb_book_id
book_title
card_type
evidence_level
final_citable
source_locator
source_volume
page_marker
heading_path
paragraph_index
raw_start
raw_end
content_hash
raw_content_hash
normalized_content_hash
source_refs
managed_by
collection_schema
```

## RAG query

```http
POST /v1/rag/query
```

```json
{
  "schema_version": "kb-rag/v2",
  "question": "《開元占經》如何記載熒惑守心？",
  "top_k": 5,
  "collection": "local_kb_kaiyuan_v2",
  "filters": {
    "kb_book_id": "kaiyuan_zhanjing"
  },
  "query_mode": "evidence",
  "retrieval_stage": "primary_evidence",
  "card_types": ["fenjuan", "fulltext"],
  "generate": true,
  "literal_first": true
}
```

The canonical fields are `question` and `top_k`; legacy `query` and `limit` are not emitted by the downstream v2 client.

## Two-stage downstream flow

The downstream app performs:

```text
Stage 1: official Qdrant structured_recall
Stage 2: official Qdrant primary_evidence
filesystem fallback: only when official Stage 2 returns no primary evidence
```

Pending candidate overlays remain `candidate_only`. They may be returned as related research leads, but never as official primary evidence or exact citable hits.

## Error semantics

```text
successful search with no match → HTTP 200, hits=[]
collection missing               → HTTP 404, COLLECTION_NOT_FOUND
invalid filter/contract          → HTTP 422, CONTRACT_ERROR
Qdrant/Ollama unavailable        → HTTP 503, UPSTREAM_UNAVAILABLE
missing/invalid corpus manifest  → HTTP 503 from /v1/meta or /v1/health
```
