# Local KB Unified — Kaiyuan v2 Runtime

This app is the upstream source of truth for the Chinese Star Omen workspace. It owns Docker services, official Qdrant ingestion, the KB Search API, candidate promotion and corpus metadata.

## Release Boundary

- Release base: `stable/kaiyuan-v2`
- Trial collection: `local_kb_kaiyuan_v2`
- Existing `local_kb_default` is not deleted or recreated by default.
- Downstream `apps/star-omen` remains read-only with respect to Qdrant.
- Candidate cards enter through `incoming/downstream_candidates`, require validation and approval, and are promoted before ingest.

The imported runtime provenance is recorded in `RUNTIME_BASELINE.json`.

## Stack

- Host Ollama on macOS/Apple Silicon for Metal acceleration
- Qdrant
- PostgreSQL/pgvector
- KB Search FastAPI service
- OpenWebUI
- Docker Compose

Qdrant and PostgreSQL use named Docker volumes. Secrets and machine-local paths belong in `.env`, which is ignored by Git.

## Setup

```bash
cp .env.example .env
# replace all placeholder secrets in .env
make setup
make pull-models
make up
make health
```

## Ingest Safety

The default target is `local_kb_kaiyuan_v2`.

```bash
# inspect configured sources without embedding
make ingest-dry-run

# non-destructive collection create/upsert
make ingest

# destructive recreation, only when explicitly intended
make ingest-recreate
```

B1 restores the real runtime but does not claim true hash-based incremental insert/update/delete semantics. That behavior is implemented in the following B2 phase.

## Knowledge Sources

The primary source is configured with:

```env
KB_SOURCES_ROOT=./data/sources
```

An optional Obsidian source can be enabled locally:

```env
KB_ENABLE_OBSIDIAN_SOURCE=true
KB_OBSIDIAN_ROOT="/path/to/your/_kb-ingest"
```

The inbox `incoming/downstream_candidates` is never a direct ingest source.

## Candidate Workflow

```bash
make validate-candidates
# manually approve reviewed cards
make promote-candidates
make ingest
```

Promotion preserves provenance while changing candidate evidence into approved official evidence. Promotion never triggers ingest automatically.

## API

The Compose stack exposes the KB Search service at `http://127.0.0.1:8008` by default.

```bash
bash scripts/kb_retrieve_smoke.sh
```

Current runtime endpoints:

```text
GET  /v1/health
POST /v1/retrieve
POST /v1/rag/query
```

The final v2 retrieval-stage contract and `/v1/meta` integration are completed in B3.

## Tests

From the workspace root:

```bash
make upstream-test
```

The upstream runtime CI also validates Docker Compose configuration and rejects `.env`, model files, database/vector data, `.DS_Store` and machine-specific absolute paths.
