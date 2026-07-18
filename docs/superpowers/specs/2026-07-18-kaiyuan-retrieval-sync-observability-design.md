# B6-T02 Retrieval and Sync Observability Design

## Scope

B6-T02 adds additive, JSON-safe operational traces to downstream retrieval and candidate sync. It records client-observed stage latency, requested and returned pool sizes, fallback reason, structured sync run errors, upstream corpus version, and effective collection without changing retrieval ordering, hit classification, error taxonomy, manifest transactionality, or evidence status.

Out of scope: external metrics backends, log shipping, tracing daemons, persistent time-series data, alerting, Qdrant mutation, and release/rollback automation (B6-T03).

## Considered approaches

1. **Additive in-band observability envelope (selected).** Results and structured errors carry one versioned envelope. It is testable through existing APIs and requires no service dependency.
2. Log-only events. Logs are useful operationally but do not reach CLI/report callers reliably and are difficult to contract-test.
3. OpenTelemetry/exporter integration. This is appropriate later, but adds dependencies and deployment configuration beyond B6-T02.

## Contract

Every envelope uses `schema_version=kb-observability/v1`, an `operation`, and non-negative finite millisecond values rounded to three decimals. Timing uses a monotonic clock; wall-clock timestamps are not used for durations.

### Single-stage retrieval

Successful `retrieve()` results add:

```json
{
  "observability": {
    "schema_version": "kb-observability/v1",
    "operation": "retrieve",
    "stage": "structured_recall",
    "latency_ms": 1.25,
    "upstream_latency_ms": 0.8,
    "requested_top_k": 8,
    "raw_pool_size": 12,
    "returned_pool_size": 8,
    "card_types": ["zhusu_card", "term_card", "extract_card"],
    "collection": "local_kb_kaiyuan_v2",
    "corpus_version": "20260718T120000Z"
  }
}
```

`raw_pool_size` is the number of upstream raw hits before downstream filtering/reranking; `returned_pool_size` is the final hit count. Missing upstream latency/corpus version remains `null`, never fabricated as zero or `unknown`.

If `retrieve()` raises `KBSearchError`, it still raises. The error's `details.observability` records stage, elapsed time, requested top-k, card types, and effective collection. Existing code/status/retryable fields remain authoritative.

### Two-stage retrieval

`two_stage_retrieve()` adds a top-level envelope with total latency and ordered `stages`. Stage records cover structured recall, official primary evidence (unless support mode skips it), and filesystem fallback when used. Each record includes source, latency, requested/raw/returned pool size, card types, collection, corpus version, and fallback reason where applicable.

Fallback remains legal only after a healthy official primary response with no primary hits. Exceptions propagate with their single-stage trace and never produce a fallback stage.

### Candidate sync

Returned `candidate-sync-report/v2` values add:

- total `latency_ms`;
- `collection` and `corpus_version` copied from healthy upstream meta when available;
- `checked`, `lookup_count`, and `official_hit_count`;
- `run_error`, equal to the existing structured `error` payload on failure and `null` on success.

The envelope is returned to the caller. Successful manifests may retain their existing compact `last_sync_report`; no nondeterministic latency is persisted into manifests. On any run error, manifest bytes remain unchanged.

## Components

- `src/observability.py`: pure helpers for monotonic elapsed milliseconds, upstream optional milliseconds, pool counts, and envelope construction. Invalid/non-finite upstream values become `null`; locally measured values are always finite.
- `kb_retrieval/core.py`: measures a single official request and attaches result/error trace.
- `kb_retrieval/two_stage.py`: measures total and filesystem stages and assembles ordered traces from stage results.
- `candidate_sync.py`: aggregates meta/lookup counts and returns success/error trace without changing manifest planning or writes.

Tests inject or monkeypatch the monotonic clock. No production clock value is asserted exactly.

## Compatibility and failure rules

- All existing fields and schemas remain present; `observability` is additive.
- Structured runtime errors are never converted to `hits=[]`, `pending`, or success.
- `run_error` is not a business status and never appears in candidate item `sync_status`.
- Collection and corpus version come only from effective request/upstream response/meta. Conflicting or missing data is not guessed.
- Envelopes must serialize with `json.dumps(..., allow_nan=False)`.
- No secret, API key, raw response body, machine-local source content, or candidate anchor is recorded.

## Acceptance

1. Successful retrieve and two-stage results expose deterministic ordered traces with correct pool counts and provenance.
2. Official error paths re-raise the same structured error with trace and never execute filesystem fallback.
3. Support mode explicitly records the skipped primary stage/fallback reason without an official primary call.
4. Candidate sync success and every shared error taxonomy code expose run trace while preserving atomic manifests.
5. Missing or invalid upstream timing/version values remain null and strict JSON serialization succeeds.
6. Full repository gates and independent review pass without corpus, candidate content, ingest, Qdrant, `main`, or `local_kb_default` changes.
