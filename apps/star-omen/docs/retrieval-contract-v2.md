# Downstream Retrieval Contract v2

`apps/star-omen` is a read-only consumer of the official Local-KB-Unified service. It never writes Qdrant.

## Two-stage flow

For evidence and knowledge queries:

```text
1. POST /v1/retrieve
   retrieval_stage=structured_recall
   card_types=<mode-specific structured pool>

2. POST /v1/retrieve
   retrieval_stage=primary_evidence
   card_types=[fenjuan, fulltext]

3. Only when step 2 returns no primary hits:
   read-only filesystem primary fallback
```

Support queries use the support pool and do not trigger primary filesystem scanning.

## Pools

```text
evidence stage 1: zhusu_card, term_card, extract_card
knowledge stage 1: xingguan_card, zhusu_card, term_card,
                   extract_card, topic_index, chapter_summary
support stage 1: topic_index, chapter_summary, extract_card
stage 2: fenjuan, fulltext
```

`query_mode` describes intent. `retrieval_stage` describes the current call. `card_types` is the actual pool. These fields must not be collapsed into one implicit filter.

## Canonical filters

The client writes:

```json
{
  "filters": {
    "kb_book_id": "kaiyuan_zhanjing"
  }
}
```

It accepts `book_id` from old callers, rejects conflicting aliases, and removes the legacy alias from the real HTTP wire.

## Primary evidence

Official primary hits preserve, when available:

```text
source_locator
source_volume
page_marker
heading_path
paragraph_index
raw_start/raw_end
content_hash
raw_content_hash
normalized_content_hash
source_refs
managed_by
collection_schema
```

An official Stage 2 hit is preferred to the local fallback. The fallback remains a resilience mechanism, not the normal primary retrieval path.

## Candidate overlay

Pending candidate cards are never inserted into `primary_candidates` or `exact_hits`. When enabled they appear under:

```text
candidate_overlay_hits
related_hits
status=candidate_only
```

## Metadata and offline extraction

Online metadata comes only from:

```http
GET /v1/meta
```

The client preserves `meta_status=missing|invalid` rather than inventing an `unknown` successful version.

Candidate generation itself may run offline because it reads primary files locally. If `/v1/meta` is unavailable, generated cards record:

```text
base_meta_status=unavailable
base_corpus_version=unavailable
base_ingest_run_id=unavailable
```

Candidate sync is still an online operation and must not treat authentication, timeout, or service failures as a normal pending result; detailed sync error taxonomy is the B4 scope.

## Error handling

```text
HTTP 200 + hits=[]          → valid no-match
HTTP 404 COLLECTION_NOT_FOUND → collection/configuration error
HTTP 422 CONTRACT_ERROR       → invalid request/filter contract
HTTP 503 UPSTREAM_UNAVAILABLE → runtime dependency failure
```

Only the valid no-match case permits the normal filesystem fallback decision. Service and contract failures must surface as errors.
