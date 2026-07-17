# Upstream Runtime v2 Runbook

## Safe Defaults

- Release branch: `stable/kaiyuan-v2`
- Trial collection: `local_kb_kaiyuan_v2`
- Legacy collection: `local_kb_default`, never recreated by default
- Qdrant/PostgreSQL data: named Docker volumes
- Ollama: host process on macOS/Apple Silicon
- Default ingest: passage-level incremental reconciliation
- Destructive recreation: explicit `make ingest-recreate` only
- Release line does not merge into `main`

## Bootstrap

```bash
cp .env.example .env
# replace placeholder secrets
make setup
make pull-models
make up
make health
```

## Source Inspection and Ingest

```bash
make ingest-dry-run
make ingest
```

`make ingest-dry-run` parses the complete desired corpus and compares it with current v2-managed Qdrant points without embedding or mutation.

`make ingest`:

```text
skip unchanged
embed/upsert new and changed
then delete stale v2-managed point IDs
then atomically publish corpus_manifest.json
```

Additional modes:

```bash
make ingest-full     # re-embed desired managed points, no collection deletion
make ingest-recreate # explicitly delete/recreate the trial collection
```

An empty desired corpus aborts. An embedding/upsert failure prevents stale deletion and successful-manifest publication.

## Sources

```env
KB_SOURCES_ROOT=./data/sources
KB_GENERATED_ROOT=./data/generated
```

Only approved/official generated cards are collected. The incoming candidate inbox is not a source. Optional Obsidian input is enabled only through local `.env` configuration.

## Retrieval rollout

Before switching a client to `local_kb_kaiyuan_v2`:

```bash
make health
curl -fsS http://127.0.0.1:8008/v1/meta
bash scripts/kb_retrieve_smoke.sh
```

The readiness endpoint must report:

```text
ready=true
ollama=true
embedding_model=true
qdrant=true
default_collection=true
corpus_manifest=true
manifest_collection_match=true
```

Then verify both official stages:

```text
structured_recall → structured card types only
primary_evidence  → fenjuan/fulltext only
```

The downstream client calls official Qdrant in that order. A filesystem scan is allowed only when official `primary_evidence` returns no primary hits.

## Retrieval contract checks

Use the canonical fields:

```text
query_mode
retrieval_stage
card_types
filters.kb_book_id
```

Expected error distinction:

```text
no semantic match      → HTTP 200 with hits=[]
collection missing     → HTTP 404 COLLECTION_NOT_FOUND
invalid contract       → HTTP 422 CONTRACT_ERROR
runtime dependency bad → HTTP 503 UPSTREAM_UNAVAILABLE
```

`GET /v1/meta` must return an explicit `meta_status`. Missing or invalid manifests are not represented as successful `unknown` versions.

## Service Operations

```bash
make ps
make logs
make kb-search
make restart
make down
```

## Run Statistics

Successful ingest prints and records:

```text
desired
new
changed
unchanged
stale
upserted
deleted
errors
elapsed_ms
source_manifest_hash
```

The source manifest hash is deterministic over desired managed point IDs and content hashes.

## Rollback

The existing `local_kb_default` collection remains untouched.

To roll back retrieval without deleting data:

1. set the client or service collection to `local_kb_default`;
2. restart KB Search and the affected client;
3. confirm `/v1/health` and a smoke query;
4. retain `local_kb_kaiyuan_v2` for diagnosis—do not delete either collection during rollback.

If the v2 API contract itself must be rolled back, deploy the prior `stable/kaiyuan-v2` commit while keeping both named volumes and both collections intact. No rollback step requires merging into `main`.

## Candidate Boundary

`incoming/downstream_candidates` is never a source tree. Approved cards are promoted into `data/generated` before ingest; pending candidates remain excluded.

Candidate generation may run offline from the filesystem. When `/v1/meta` cannot be reached it records `base_meta_status=unavailable`; it does not pretend to have a valid upstream corpus version. Candidate sync remains a separate online operation.
