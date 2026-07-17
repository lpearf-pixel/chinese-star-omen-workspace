# Index Jobs

`ingest.py` scans the configured primary source and optional Obsidian source, chunks text, obtains embeddings from host Ollama, and upserts points into Qdrant.

```bash
cd apps/local-kb-unified
make setup
make ingest-dry-run
make ingest
```

The default collection is `local_kb_kaiyuan_v2`. `make ingest` is non-destructive; `make ingest-recreate` is the explicit destructive operation.

B1 preserves the source runtime's full-scan/upsert implementation. True passage-level hash-based incremental insert/update/delete is the scope of B2 and must not be inferred from the retained `--mode incremental` compatibility option.

The candidate inbox `incoming/downstream_candidates` is excluded from source scanning. Only approved/promoted material under `data/generated` belongs in the official ingest set.
