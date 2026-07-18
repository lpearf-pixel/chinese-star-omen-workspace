# Kaiyuan Primary Passage Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bounded read-only path/mtime/hash passage cache that avoids repeated Kaiyuan Markdown parsing while preserving fail-closed evidence semantics.

**Architecture:** A process-local LRU stores strict source snapshots and immutable `kb-text-core` passages by resolved path and parser identity. Scanner, resolver, and migration reuse it, but all query ranking and citation validation still run on every call.

**Tech Stack:** Python 3.9+, `pathlib`, `hashlib`, `threading.RLock`, `collections.OrderedDict`, pytest, `kb-text-core`.

## Global Constraints

- Target only `stable/kaiyuan-v2` through `codex/kaiyuan-primary-passage-cache-v2` and a PR; never target `main`.
- Never write raw corpus, Qdrant, candidates, or `local_kb_default`.
- Strict read/parse failures must not become healthy empty results or stale cache hits.
- `kb-text-core` remains the only passage parser and locator authority.
- Observe RED before each behavior implementation and record exact commands in `WORK_LOG.md`.

---

### Task 1: Cache core and invalidation

**Files:**
- Create: `apps/star-omen/src/connectors/primary_passage_cache.py`
- Create: `apps/star-omen/tests/test_primary_passage_cache_v2.py`

**Interfaces:**
- Produces: `PrimaryPassageCache(max_entries: int = 128)`, `load(path, *, card_type, kb_book_id, book_title) -> PrimarySourceSnapshot`, `clear()`, and module singleton `primary_passage_cache`.
- `PrimarySourceSnapshot` exposes `path`, `mtime_ns`, `size_bytes`, `content_hash`, `text`, and immutable `passages`.

- [ ] Write tests that monkeypatch the module parser and assert one parse for two unchanged loads, hash invalidation with preserved mtime/size, parser-identity separation, deterministic LRU eviction, invalid UTF-8 failure, deleted-file stale rejection, and constructor rejection of non-positive capacity.
- [ ] Run `PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python /tmp/kaiyuan-b5/bin/pytest -q tests/test_primary_passage_cache_v2.py` from `apps/star-omen`; expect import failure because the module does not exist.
- [ ] Implement frozen snapshot data, `PrimarySourceReadError`, strict stable byte loading, SHA-256 fingerprinting, locked LRU lookup/insert, and capacity eviction. Do not catch parser exceptions.
- [ ] Run the focused test; expect all cache-core tests to pass.

### Task 2: Filesystem fallback integration

**Files:**
- Modify: `apps/star-omen/src/connectors/primary_file_scanner.py`
- Modify: `apps/star-omen/tests/test_kaiyuan_retrieval_v2.py`

**Interfaces:**
- Consumes: `primary_passage_cache.load(...)` and snapshot `text`.
- Preserves: `scan_primary_files(...) -> (hits, stats)` output and ranking.

- [ ] Add an integration test that replaces the scanner cache with an isolated instance, performs two scans, and asserts the parser is called once while hits, offsets, headings, and fenjuan preference remain identical.
- [ ] Run only the new test; expect failure because scanner still calls `Path.read_text()` and never fills the passage cache.
- [ ] Replace direct source reads with cache snapshot loads. Infer metadata before loading and map `PrimarySourceReadError` into the existing scanner read-error path without broad exception swallowing.
- [ ] Run `tests/test_kaiyuan_retrieval_v2.py`; expect all retrieval fallback tests to pass.

### Task 3: Evidence resolver and migration integration

**Files:**
- Modify: `apps/star-omen/src/connectors/evidence_resolver.py`
- Modify: `apps/star-omen/src/rule_engine/rule_evidence_migration.py`
- Modify: `apps/star-omen/tests/test_citable_evidence_v2.py`
- Modify: `apps/star-omen/tests/test_rule_evidence_migration_v2.py`

**Interfaces:**
- Consumes: shared cache snapshot `passages` and `content_hash`.
- Preserves: resolver validation statuses and migration source fingerprint contract.

- [ ] Add resolver tests proving repeated resolution parses once, a same-mtime content mutation invalidates and produces the appropriate mismatch, and a deleted source never uses stale passages. Add migration test proving two audit loads reuse parsing while fingerprint remains based on exact source hashes.
- [ ] Run the new tests; expect parser-call-count failures with the current direct parser calls.
- [ ] Load passages from the cache in resolver, mapping only `PrimarySourceReadError` to existing `missing_source/source_read_failed`. Load migration sources through the cache and feed snapshot hashes into its aggregate fingerprint in sorted path order.
- [ ] Run focused cache, resolver, migration, and retrieval tests; expect all to pass.

### Task 4: Verification, review, and release evidence

**Files:**
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Produces: exact local/CI evidence for B6-T01 and a reviewable PR to `stable/kaiyuan-v2`.

- [ ] Run focused tests, then `make contracts-test`, `make text-core-test`, `make downstream-test`, and `make upstream-test`; record exact results.
- [ ] Inspect the branch diff and run `python scripts/check_development_governance.py --base 6dd0910a2d6b825904ae8e0dcc7d3f1a75557775 --head HEAD`.
- [ ] Set B6-T01 to `VERIFYING`, update `WORK_LOG.md`, publish the exact head, and require fresh Development Governance, Kaiyuan Stable Core, and Kaiyuan Upstream Runtime runs.
- [ ] Request independent code review, resolve Critical/Important findings with new RED tests, rerun all gates on the new head, mark ready, and squash merge only into `stable/kaiyuan-v2`.
- [ ] On the next feature branch, record the actual merge SHA and set B6-T01 to `DONE`; then start B6-T02.
