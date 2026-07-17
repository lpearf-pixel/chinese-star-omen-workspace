# Index Jobs

`ingest.py` builds a complete desired corpus from the official source tree, approved generated cards and the optional Obsidian tree, then reconciles v2-managed points in Qdrant.

```bash
cd apps/local-kb-unified
make setup
make ingest-dry-run
make ingest
```

## Primary Passages

Kaiyuan `fenjuan` and `fulltext` Markdown use `packages/kb-text-core` rather than fixed-size character windows. The parser records:

```text
kb_book_id
source_locator/source_volume
page_marker
heading_path
paragraph_index
raw_start/raw_end
raw_text/normalized_text
raw_content_hash/normalized_content_hash
```

Equivalent split-volume and combined-fulltext passages are deduplicated; `fenjuan` is retained and the fulltext path is recorded as duplicate provenance.

## Reconciliation

The default collection is `local_kb_kaiyuan_v2`.

```bash
make ingest          # incremental
make ingest-full     # re-embed all desired managed points
make ingest-recreate # explicitly delete/recreate collection
```

Incremental mode:

1. collects and validates the non-empty desired corpus;
2. scrolls only points with `managed_by=local-kb-unified/v2`;
3. plans new, changed, unchanged and stale IDs;
4. embeds only new/changed items;
5. upserts required batches;
6. deletes stale managed IDs only after every upsert succeeds;
7. atomically writes the corpus manifest.

Generic structured cards use stable source-root labels, relative paths, chunk indexes and chunk hashes. Primary passages use canonical volume/page/paragraph identity and normalized content hashes.

The candidate inbox `incoming/downstream_candidates` is excluded. Under `data/generated`, only approved/official cards enter the desired corpus.
