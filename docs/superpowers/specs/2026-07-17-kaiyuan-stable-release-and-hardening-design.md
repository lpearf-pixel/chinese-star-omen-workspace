# Kaiyuan Stable Release and Hardening Design

## Decision

`main` remains the historical workspace branch and is not the release target for the Kaiyuan v2 line.

The release base is:

```text
stable/kaiyuan-v2
```

Development continues through short-lived branches and pull requests targeting `stable/kaiyuan-v2`. `dev-test` remains an integration/reference branch and is not promoted to `main` as part of this release line.

## Current Baseline

`stable/kaiyuan-v2` starts from the current `dev-test` state after PR #6, which already contains:

- immutable combined-text and 121-volume corpus auditing;
- `packages/kb-text-core`;
- exact/raw/normalized/loose/heading match semantics;
- original-offset-preserving fallback excerpts;
- fenjuan-first ranking and fulltext deduplication;
- page-level candidate generation;
- Python 3.12 CI and Python 3.9 enum compatibility.

## Phase A.1: Corpus and Locator Hardening

Branch:

```text
codex/kaiyuan-corpus-hardening-v2
```

This phase ports only the post-PR-#6 hardening delta onto the stable base:

- canonical fulltext page marker to volume locator mapping;
- nested ancient heading preservation;
- real chapter headings in `matched_headings`;
- heading-only matches kept out of exact primary evidence;
- stricter loose-term ordering;
- strict 121-section, page-marker and volume consistency auditing;
- immutable baseline metadata and provenance status;
- regression tests and package metadata.

No Qdrant runtime changes belong in A.1.

## Phase B: Real Upstream RAG

Phase B starts only after A.1 is merged into `stable/kaiyuan-v2`.

The real runtime snapshot supplied from `/Users/kandysmith/local-kb-unified` is imported as a reviewed baseline into `apps/local-kb-unified`. Secrets, data volumes, model files, caches and machine-local configuration are excluded.

Phase B is split into independently reviewable pull requests:

1. **B1 Runtime import:** Docker Compose, real KB Search service, ingest jobs, tests and sanitized configuration.
2. **B2 Passage ingest:** `kb-text-core` passage parsing, stable point identity, hash-based incremental insert/update/delete, and parallel collection `local_kb_kaiyuan_v2`.
3. **B3 API contract:** `/v1/retrieve`, `/v1/rag/query`, `/v1/meta`, real health checks, explicit `query_mode` / `retrieval_stage` / `card_types` semantics.
4. **B4 Integration hardening:** candidate sync error states, citable evidence validation, golden retrieval evaluation and end-to-end CI.

## Branch and Release Policy

- Release PRs target `stable/kaiyuan-v2`.
- `main` is not modified by this work.
- Existing `local_kb_default` is never deleted or overwritten.
- New ingest trials use `local_kb_kaiyuan_v2`.
- Switching the default collection requires passing corpus audit, golden retrieval and candidate-sync integration gates.
- No `.env`, API key, Qdrant/PostgreSQL volume, local model or machine-specific absolute path is committed.

## Evidence Contract

Canonical book metadata is written as `kb_book_id`; `book_id` is read only as a compatibility alias.

A citable primary hit ultimately requires:

- `card_type` in `fenjuan | fulltext`;
- an existing source file;
- canonical `source_locator`;
- valid `page_marker` when available;
- an anchor that can be re-located in the source;
- matching content hash;
- matching `kb_book_id`.

## Verification Gates

### A.1

- contracts, text-core and downstream tests pass on Python 3.12;
- strict corpus audit passes for 121 sections and 3435 page markers;
- fulltext page `KR3g0018_WYG_031-17a` maps to `KR3g0018_031`;
- heading-only is never returned as exact primary evidence;
- “荧惑守心” still ranks volume 31 fenjuan passages ahead of fulltext.

### B

- Docker services start without modifying `local_kb_default`;
- incremental ingest skips unchanged passages and deletes stale points;
- `/v1/health` checks API, Qdrant, collection, embedding service and corpus manifest;
- Stage 1 and Stage 2 card pools do not conflict;
- upstream failures do not become false `pending` candidate states;
- golden retrieval and end-to-end candidate promotion/sync pass.
