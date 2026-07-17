# KB Search Service

FastAPI service backed by Qdrant and host Ollama.

## Endpoints

```text
GET  /v1/health
POST /v1/retrieve
POST /v1/rag/query
```

`/v1/retrieve` and `/v1/rag/query` require either:

```text
Authorization: Bearer <KB_SEARCH_API_KEY>
```

or:

```text
X-API-Key: <KB_SEARCH_API_KEY>
```

## Development

```bash
cd apps/local-kb-unified
bash scripts/run_kb_search.sh
```

The default collection is `local_kb_kaiyuan_v2`. The final v2 retrieval-stage contract and `/v1/meta` are implemented in B3.
