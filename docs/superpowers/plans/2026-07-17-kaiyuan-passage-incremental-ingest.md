# Kaiyuan Passage-Level Incremental Ingest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development and superpowers:executing-plans (or subagent-driven-development) task by task.

**Goal:** Build a deterministic passage-oriented official ingest pipeline for `local_kb_kaiyuan_v2` that skips unchanged points, embeds only new/changed passages and deletes stale managed points without collection recreation.

**Base branch:** `stable/kaiyuan-v2`

**Feature branch:** `codex/kaiyuan-passage-ingest-v2`

## Constraints

- Never target or merge into `main`.
- Never mutate `local_kb_default`.
- Reuse `packages/kb-text-core` for Kaiyuan page, heading, offset and normalization semantics.
- Do not stale-delete points that lack `managed_by=local-kb-unified/v2`.
- Do not delete stale points until parsing and every required upsert succeed.
- Abort on an unexpectedly empty desired corpus.
- Do not claim the final B3 HTTP retrieval-stage contract in B2.

---

### Task 1: Add passage parser tests and model

**Files:**
- Create: `packages/kb-text-core/tests/test_passage_ingest_v2.py`
- Modify: `packages/kb-text-core/python/kb_text_core/models.py`
- Create: `packages/kb-text-core/python/kb_text_core/passages.py`
- Modify: `packages/kb-text-core/python/kb_text_core/__init__.py`

- [ ] Write failing tests proving that a split-volume page becomes deterministic passages with canonical locator, page marker, nested heading path, raw offsets and hashes.
- [ ] Write a failing test proving fulltext page markers map to the same canonical volume locator.
- [ ] Write a failing test proving fenjuan/fulltext duplicate passages prefer fenjuan and retain duplicate provenance.
- [ ] Run the new test file and confirm failure is caused by missing passage APIs.
- [ ] Implement the minimum passage dataclass/parser/dedupe functions.
- [ ] Run all text-core tests and commit.

Required public APIs:

```python
def parse_kaiyuan_passages(
    text: str,
    *,
    source_path: str,
    card_type: str,
    kb_book_id: str = "kaiyuan_zhanjing",
    book_title: str = "唐開元占經",
) -> list[KaiyuanPassage]: ...

def dedupe_kaiyuan_passages(passages: list[KaiyuanPassage]) -> list[KaiyuanPassage]: ...

def canonical_source_locator(source_path: str, page_marker: str | None = None) -> str: ...
```

### Task 2: Add pure incremental planner tests

**Files:**
- Create: `apps/local-kb-unified/index-jobs/incremental.py`
- Create: `apps/local-kb-unified/tests/test_incremental_ingest_v2.py`

- [ ] Write failing tests for stable UUIDv5 point IDs.
- [ ] Write failing tests for `insert`, `unchanged`, `update` and `stale` planning.
- [ ] Write a failing test proving full mode schedules every desired item for upsert.
- [ ] Write a failing test proving unmanaged existing points are ignored.
- [ ] Write a failing test proving an empty desired set raises instead of planning mass deletion.
- [ ] Run focused tests and verify RED.
- [ ] Implement pure deterministic planning functions.
- [ ] Run focused tests and commit.

Required public APIs:

```python
def stable_point_key(item: dict[str, Any]) -> str: ...
def point_id_for_item(item: dict[str, Any]) -> str: ...
def plan_reconciliation(
    desired: list[dict[str, Any]],
    existing: dict[str, dict[str, Any]],
    *,
    mode: str,
) -> ReconciliationPlan: ...
```

### Task 3: Integrate passages and reconciliation into ingest

**Files:**
- Modify: `apps/local-kb-unified/index-jobs/ingest.py`
- Modify: `apps/local-kb-unified/index-jobs/sources/obsidian_adapter.py`
- Create/modify: `apps/local-kb-unified/tests/test_ingest_execution_v2.py`

- [ ] Write a failing execution test using fake embed/Qdrant dependencies: unchanged items must not call embedding.
- [ ] Write a failing execution test: stale deletion happens only after successful upsert.
- [ ] Write a failing execution test: upsert failure prevents stale deletion.
- [ ] Parse Kaiyuan `fenjuan/fulltext` through `kb-text-core`; retain generic chunking for structured/non-primary files.
- [ ] Add `managed_by`, `collection_schema`, stable point key, raw/normalized hashes and passage provenance to payloads.
- [ ] Scroll existing managed points and execute the pure reconciliation plan.
- [ ] Ensure `--mode incremental` is the default Makefile ingest mode; retain explicit `full` and `recreate` operations.
- [ ] Run upstream tests and commit.

### Task 4: Add integration and observability gates

**Files:**
- Modify: `apps/local-kb-unified/Makefile`
- Modify: `apps/local-kb-unified/README.md`
- Modify: `apps/local-kb-unified/docs/runtime-v2.md`
- Modify: `.github/workflows/kaiyuan-upstream-runtime.yml`
- Create: `apps/local-kb-unified/tests/test_qdrant_incremental_integration.py`

- [ ] Add a Qdrant service to an integration CI job.
- [ ] Test first ingest, unchanged second ingest, changed passage update and removed passage deletion.
- [ ] Expose deterministic run statistics: desired/new/changed/unchanged/stale/upserted/deleted/errors.
- [ ] Document rollback and collection safety.
- [ ] Run all upstream/workspace regression gates.

### Task 5: Finish B2 branch

- [ ] Confirm no `.env`, model, database/vector data or machine-local paths are present.
- [ ] Open a draft PR targeting `stable/kaiyuan-v2`.
- [ ] Wait for CI and fix failures.
- [ ] Mark ready and merge only after every gate passes.
- [ ] Start B3 from the updated `stable/kaiyuan-v2` for the final API contract.
