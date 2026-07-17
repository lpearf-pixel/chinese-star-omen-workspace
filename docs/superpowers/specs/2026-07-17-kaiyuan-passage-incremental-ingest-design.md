# Kaiyuan Passage-Level Incremental Ingest Design

## Goal

Make `local_kb_kaiyuan_v2` a deterministic, passage-oriented Qdrant collection that reuses the same Kaiyuan parser and provenance model as filesystem fallback. Re-ingest must skip unchanged passages, upsert new/changed passages, and delete stale managed points without recreating the collection.

## Scope

B2 changes official ingest only. It does not redesign the HTTP retrieval-stage contract; that remains B3.

## Passage Model

Kaiyuan primary sources (`fenjuan` and `fulltext`) are parsed into page/paragraph passages with:

```text
kb_book_id
book_title
card_type
source_locator
source_volume
page_marker
heading_path
paragraph_index
raw_start
raw_end
raw_text
normalized_text
raw_content_hash
normalized_content_hash
```

The combined fulltext and split volumes describe the same pages. When both produce the same logical passage, `fenjuan` wins and the fulltext path is recorded as duplicate provenance.

## Stable Identity

Each managed point has a deterministic logical key:

```text
kb_book_id
+ source_locator
+ page_marker-or-no-page
+ paragraph_index
+ normalized_content_hash
```

The Qdrant point ID is UUIDv5 over the logical key. The normalized hash intentionally changes when the substantive passage changes; the prior point then becomes stale and is deleted during incremental reconciliation.

Generic structured cards retain deterministic path/chunk identity and content hashes. They do not use primary-passage semantics unless their path/card type identifies them as Kaiyuan `fenjuan` or `fulltext`.

## Managed Scope

All B2 points include:

```text
managed_by: local-kb-unified/v2
collection_schema: passage-v2
```

Incremental deletion only considers points carrying that managed marker. It never deletes unrelated legacy points from another producer.

## Incremental Algorithm

1. Parse configured sources into desired work items.
2. Deduplicate desired work items, preferring `fenjuan` over duplicate `fulltext`.
3. Scroll existing managed points and collect point ID + content hash.
4. Build a pure reconciliation plan:
   - desired ID absent -> insert;
   - desired ID present with same content hash -> unchanged/skip embedding;
   - desired ID present with different content hash -> update;
   - existing managed ID absent from desired -> stale/delete.
5. Embed only insert/update items.
6. Upsert in batches.
7. Delete stale managed IDs.
8. Write corpus manifest/run statistics only after successful reconciliation.

## Modes

- `--mode incremental`: skip unchanged, upsert changed/new, delete stale.
- `--mode full`: re-embed/upsert all desired managed points, then delete stale.
- `--recreate`: explicit destructive collection recreation followed by full ingest.
- `--dry-run`: calculate source and reconciliation counts without embedding or mutation.

## Failure Safety

- No stale deletion occurs before all desired items are parsed successfully.
- If embedding/upsert fails, stale deletion is not performed.
- Collection recreation remains explicit.
- Existing `local_kb_default` remains untouched.
- Empty desired corpus aborts rather than deleting all managed points.

## Verification

- pure planner tests cover new/unchanged/changed/stale;
- stable IDs are deterministic and differ on substantive content changes;
- fenjuan/fulltext dedupe prefers fenjuan and records duplicate path;
- page markers and headings match filesystem fallback;
- unchanged points never call embedding in incremental mode;
- stale deletion is scoped to `managed_by=local-kb-unified/v2`;
- Qdrant integration test uses an ephemeral collection/service;
- all existing upstream/downstream/text-core tests remain green.
