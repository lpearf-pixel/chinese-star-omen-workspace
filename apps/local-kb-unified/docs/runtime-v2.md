# Upstream Runtime v2 Runbook

## Safe Defaults

- Release branch: `stable/kaiyuan-v2`
- Trial collection: `local_kb_kaiyuan_v2`
- Qdrant/PostgreSQL data: named Docker volumes
- Ollama: host process on macOS/Apple Silicon
- Default ingest: passage-level incremental reconciliation
- Destructive recreation: explicit `make ingest-recreate` only

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

The existing `local_kb_default` collection remains untouched. To roll back a client, set its collection back to `local_kb_default` and restart the KB Search service. Do not delete either collection during rollback.

## Candidate Boundary

`incoming/downstream_candidates` is never a source tree. Approved cards are promoted into `data/generated` before ingest; pending candidates remain excluded.
