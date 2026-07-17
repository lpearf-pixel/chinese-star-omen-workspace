# KB Search API — Imported B1 Baseline

Base URL:

```text
http://127.0.0.1:8008
```

Authenticated endpoints accept `Authorization: Bearer <key>` or `X-API-Key: <key>`.

## Health

```http
GET /v1/health
```

Returns HTTP 200 only when both host Ollama and Qdrant are reachable; otherwise HTTP 503 with per-dependency booleans.

## Retrieve

```http
POST /v1/retrieve
Content-Type: application/json
Authorization: Bearer ...
```

```json
{
  "query": "荧惑守心",
  "top_k": 5,
  "collection": "local_kb_kaiyuan_v2",
  "filters": {
    "kb_book_id": "kaiyuan_zhanjing"
  },
  "query_mode": "evidence",
  "literal_first": true
}
```

## RAG Query

```http
POST /v1/rag/query
```

```json
{
  "question": "《開元占經》如何記載熒惑守心？",
  "top_k": 5,
  "collection": "local_kb_kaiyuan_v2",
  "filters": {
    "kb_book_id": "kaiyuan_zhanjing"
  },
  "generate": true,
  "literal_first": true
}
```

## Contract Boundary

This is the imported B1 runtime contract. B3 will make `query_mode`, `retrieval_stage` and `card_types` independent and add `/v1/meta`. Clients must not interpret this baseline as the final v2 contract.
