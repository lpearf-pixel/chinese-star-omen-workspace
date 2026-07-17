# Upstream Runtime v2 Runbook

## Safe Defaults

- Release branch: `stable/kaiyuan-v2`
- Trial collection: `local_kb_kaiyuan_v2`
- Qdrant/PostgreSQL data: named Docker volumes
- Ollama: host process on macOS/Apple Silicon
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

`make ingest` creates or upserts the configured trial collection. It does not delete it. B2 will add true passage-level incremental insert/update/delete.

## Service Operations

```bash
make ps
make logs
make kb-search
make restart
make down
```

## Rollback

The existing `local_kb_default` collection remains untouched. To roll back a client, set its collection back to `local_kb_default` and restart the KB Search service. Do not delete either collection during rollback.

## Candidate Boundary

`incoming/downstream_candidates` is never a source tree. Approved cards are promoted into `data/generated` before ingest.
