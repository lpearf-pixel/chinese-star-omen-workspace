# Kaiyuan Retrieval API Contract v2 Design

## Goal

Make upstream Qdrant retrieval and downstream two-stage retrieval agree on one explicit contract. `query_mode` describes user intent and ranking semantics; it must no longer silently impose a card-type pool that conflicts with a requested retrieval stage.

## Release Boundary

- Base branch: `stable/kaiyuan-v2`
- Feature branch: `codex/kaiyuan-retrieval-contract-v2`
- `main` remains untouched.
- Default trial collection remains `local_kb_kaiyuan_v2`.

## Contract Concepts

### `query_mode`

User intent:

```text
evidence
knowledge
support
```

It controls defaults such as literal-first behavior and client-side interpretation. In v2 it does not add a second hidden `card_type` filter when an explicit stage or card pool is supplied.

### `retrieval_stage`

The role of one retrieval call:

```text
structured_recall
primary_evidence
support_context
auto
```

Default pools:

```text
structured_recall:
  xingguan_card, zhusu_card, term_card, extract_card,
  topic_index, chapter_summary

primary_evidence:
  fenjuan, fulltext

support_context:
  topic_index, chapter_summary, nav
```

### `card_types`

An optional explicit allow-list. It has the highest precedence. The legacy `filters.card_type` field is accepted, removed from generic filters, and treated as `card_types` during the transition.

Precedence:

```text
explicit card_types
→ legacy filters.card_type
→ retrieval_stage default pool
→ legacy query_mode pool only when no v2 stage/pool is supplied
```

Conflicting explicit pools are rejected rather than AND-ed into zero hits.

## Retrieve Request v2

```json
{
  "schema_version": "kb-retrieve/v2",
  "query": "荧惑守心",
  "top_k": 8,
  "collection": "local_kb_kaiyuan_v2",
  "query_mode": "evidence",
  "retrieval_stage": "structured_recall",
  "card_types": ["zhusu_card", "term_card", "extract_card"],
  "filters": {
    "kb_book_id": "kaiyuan_zhanjing"
  },
  "literal_first": true,
  "literal_pool_factor": 12
}
```

The wire contract writes only `kb_book_id`. `book_id` remains a read compatibility alias and conflicting aliases return a 422 contract error.

## Retrieve Response v2

The response echoes the effective contract:

```json
{
  "schema_version": "kb-retrieve/v2",
  "query_mode": "evidence",
  "retrieval_stage": "structured_recall",
  "card_types": ["zhusu_card", "term_card", "extract_card"],
  "collection": "local_kb_kaiyuan_v2",
  "hits": [],
  "retrieved_count": 0,
  "latency_ms": 12
}
```

Primary hits expose passage provenance when available:

```text
kb_book_id
book_title
card_type
evidence_level
final_citable
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

## Two-Stage Downstream Flow

```text
Stage 1 official Qdrant:
  retrieval_stage=structured_recall
  explicit structured card_types

Stage 2 official Qdrant:
  retrieval_stage=primary_evidence
  card_types=fenjuan,fulltext

Stage 2 filesystem fallback:
  only when official primary evidence is empty or unavailable under an explicitly recoverable policy

Candidate overlay:
  candidate-only related evidence; never official exact primary
```

Official Stage 2 hits are preferred over filesystem duplicates. Filesystem fallback remains an offline safety path and uses the same `kb-text-core` passage provenance.

## Metadata Endpoint

```http
GET /v1/meta
```

Returns the committed successful ingest manifest:

```text
corpus_version
ingest_run_id
source_manifest_hash
collection
managed_by
collection_schema
run_stats
```

Missing or invalid manifest is explicit (`meta_status=missing|invalid`); it is never represented as a successful unknown version.

## Readiness Health

```http
GET /v1/health
```

Checks:

```text
api
ollama
embedding_model
qdrant
default_collection
corpus_manifest
manifest_collection_match
```

HTTP 200 requires every readiness check. Otherwise HTTP 503 with `status=degraded` and per-check details. Health includes current corpus metadata when valid.

## Error Semantics

```text
401 UNAUTHORIZED
404 COLLECTION_NOT_FOUND
422 CONTRACT_ERROR
503 UPSTREAM_UNAVAILABLE
```

A missing collection is not returned as an empty successful result. A successful search with no matches remains HTTP 200 and `hits=[]`.

## RAG Contract

Canonical request fields:

```text
question
top_k
collection
filters
query_mode
retrieval_stage
card_types
generate
literal_first
literal_pool_factor
```

Legacy downstream `query`/`limit` is removed from the v2 wire call. RAG citations use the same provenance fields as retrieve hits.

## Verification Gates

- evidence intent + structured stage produces structured card types only;
- evidence intent + primary stage produces fenjuan/fulltext only;
- legacy `filters.card_type` does not conflict with query mode;
- downstream performs both official stages before filesystem fallback;
- missing collection is distinguishable from no hits;
- `/v1/meta` reflects the successful B2 corpus manifest;
- readiness fails on absent collection, model, Qdrant or manifest mismatch;
- all B2 incremental, corpus, downstream and Qdrant integration tests remain green.
