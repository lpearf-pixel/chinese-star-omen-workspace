# B6-T01 Kaiyuan Primary Passage Cache Design

## Scope

B6-T01 adds a process-local, read-only cache for Kaiyuan primary Markdown sources in `apps/star-omen`. It removes repeated UTF-8 decoding and `kb-text-core` passage parsing from filesystem fallback, evidence resolution, and rule-evidence audit without changing the official two-stage retrieval order, citation rules, source bytes, or Qdrant state.

Out of scope: persistent cache files, background watchers, Qdrant writes, corpus rewriting, query-result caching, and B6-T02 telemetry export.

## Considered approaches

1. **Process-local source/passage cache (selected).** Cache immutable source snapshots and parsed passages by canonical path plus parser identity. It is dependency-free, bounded, testable, and cannot outlive the process.
2. Persistent SQLite/JSON index. This improves cold starts but adds migration, locking, stale-artifact, and cleanup risks that are disproportionate to B6-T01.
3. Cache complete query results. This is faster for repeated identical terms but couples the cache to ranking and query variants, and does not help evidence resolution. It is rejected.

## Architecture

Create `src/connectors/primary_passage_cache.py` with a bounded, thread-safe LRU cache. A cached snapshot contains:

- resolved source path;
- strict UTF-8 source text;
- `mtime_ns` and byte size from the file stat;
- SHA-256 of the exact source bytes;
- parser identity (`card_type`, `kb_book_id`, `book_title`);
- an immutable tuple of `KaiyuanPassage` values produced only by `kb-text-core`.

The cache key is the resolved path plus parser identity. A lookup stats and reads the source strictly, hashes the exact bytes, and reuses parsed passages only when the content hash and parser identity match. `mtime_ns` and size are retained for invalidation trace and B6-T02 metrics, but they are not trusted instead of the hash. This deliberately still reads bytes: it avoids the materially more expensive full passage parse while detecting content changes even when a caller preserves timestamps.

The default cache is process-local and bounded (128 source/parser entries). Tests may inject an isolated cache. Eviction is deterministic least-recently-used. No cache file is written under the corpus or elsewhere.

## Integration

- `evidence_resolver.resolve_evidence()` loads the source snapshot and passages from the cache, then performs every existing path, book, locator, page, paragraph, heading, anchor, and hash check on each call. A cached snapshot never caches `citable` status.
- `primary_file_scanner.scan_primary_files()` loads each eligible source through the same cache. Matching and ranking continue to use the exact cached source text, so offsets, excerpts, ordering, and full-scan-before-limit behavior remain compatible.
- `rule_evidence_migration._load_primary_passages()` uses the cache for source decoding/parsing while independently recomputing its aggregate corpus fingerprint from snapshot hashes. Migration remains fail-closed and read-only unless its existing explicit apply path is used.

## Failure semantics

- Missing, unreadable, or invalid UTF-8 sources are never served from stale entries.
- A read/stat race is retried once; if a stable snapshot cannot be obtained, a typed `PrimarySourceReadError` is raised.
- Resolver maps source read failure to its existing `missing_source/source_read_failed` result. Scanner preserves its existing per-file read-error behavior. Migration audit fails the run rather than reporting a healthy empty corpus.
- Parse errors propagate and never become empty passages.
- Cache operations never mutate a source, candidate manifest, Qdrant collection, or `local_kb_default`.

## Acceptance tests

1. Two loads of unchanged bytes call `parse_kaiyuan_passages()` once and return the same immutable passage tuple.
2. Content changes invalidate the entry even when size and mtime are preserved.
3. Parser identity changes do not reuse an incompatible entry.
4. Missing/invalid UTF-8/read-race cases do not return stale data.
5. LRU capacity is enforced deterministically.
6. Repeated filesystem scans and repeated evidence resolution parse unchanged sources once while preserving existing output.
7. Existing downstream, text-core, contracts, and upstream gates remain green.

## Safety and compatibility

The cache lives only in `apps/star-omen`; `kb-text-core` remains the unique parser and locator authority. Official retrieval is still attempted before filesystem fallback. No raw corpus, candidate state, ingest path, Qdrant schema, collection, or release target changes.
