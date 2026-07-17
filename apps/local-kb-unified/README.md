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

## Passage-Level Ingest

The default target is `local_kb_kaiyuan_v2`. Kaiyuan `fenjuan` and `fulltext` are parsed through `packages/kb-text-core` into page/paragraph evidence passages. Split-volume evidence wins over duplicate fulltext passages while retaining duplicate provenance.

```bash
# calculate desired/current reconciliation without embedding or mutation
make ingest-dry-run

# default: skip unchanged, upsert new/changed, then delete stale v2-managed points
make ingest

# re-embed all desired v2-managed points without collection recreation
make ingest-full

# destructive recreation, only when explicitly intended
make ingest-recreate
```

Each v2-managed point carries:

```text
managed_by=local-kb-unified/v2
collection_schema=passage-v2
```

Primary passage UUIDv5 identity is based on:

```text
kb_book_id + source_locator + page_marker + paragraph_index + normalized_content_hash
```

Incremental deletion is scoped to the managed marker. Empty desired corpora abort. Stale IDs are deleted only after every required embedding/upsert succeeds.

## Knowledge Sources

Official roots are configured with:

```env
KB_SOURCES_ROOT=./data/sources
KB_GENERATED_ROOT=./data/generated
```

Only approved/official cards under `data/generated` are collected. Pending candidates are excluded.

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

## Corpus Manifest

A successful reconciliation atomically updates `data/corpus_manifest.json` with:

```text
corpus_version
ingest_run_id
source_manifest_hash
collection
managed_by
collection_schema
run_stats: desired/new/changed/unchanged/stale/upserted/deleted/errors/elapsed_ms
```

Failed embedding/upsert runs do not publish a successful manifest and do not delete stale points.

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

CI additionally runs an ephemeral Qdrant integration test covering initial insert, unchanged second reconciliation, changed passage update and stale passage deletion. It also validates Docker Compose and rejects `.env`, model files, database/vector data, `.DS_Store` and machine-specific absolute paths.
