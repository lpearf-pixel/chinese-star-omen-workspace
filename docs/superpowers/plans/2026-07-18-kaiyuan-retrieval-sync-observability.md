# Kaiyuan Retrieval and Sync Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add versioned JSON-safe operational traces to downstream retrieval and candidate sync without changing fail-closed behavior.

**Architecture:** Pure helpers create additive observability envelopes from a monotonic clock. Retrieval results/errors and candidate sync reports expose stage timing, pool counts, fallback/error provenance, corpus version, and collection while retaining existing schemas and transaction boundaries.

**Tech Stack:** Python 3.12 downstream runtime, `time.monotonic_ns`, pytest, existing `kb-contracts` error taxonomy.

## Global Constraints

- Target only `stable/kaiyuan-v2` through `codex/kaiyuan-retrieval-observability-v2`; never target `main`.
- Do not write corpus, candidate content on failed sync, Qdrant, or `local_kb_default`.
- Observability is additive and strict JSON-safe; errors still raise/report as errors and never become empty success.
- Record only operational metadata, never secrets, source content, anchors, or raw error bodies.
- Observe and record RED before implementation.

---

### Task 1: JSON-safe observability helpers

**Files:**
- Create: `apps/star-omen/src/observability.py`
- Create: `apps/star-omen/tests/test_observability_v2.py`

**Interfaces:**
- Produces: `elapsed_ms(start_ns, end_ns) -> float`, `optional_ms(value) -> float | None`, and `base_observability(operation, **fields) -> dict[str, Any]`.

- [ ] Write tests for non-negative rounded elapsed values, invalid/non-finite optional upstream timing becoming null, immutable caller inputs, and `json.dumps(envelope, allow_nan=False)`.
- [ ] Run the focused test and observe import failure because `src.observability` does not exist.
- [ ] Implement the pure helpers without broad exception handling or external dependencies.
- [ ] Run the focused test and require all helper tests to pass.

### Task 2: Single-stage and two-stage retrieval traces

**Files:**
- Modify: `apps/star-omen/src/connectors/kb_retrieval/core.py`
- Modify: `apps/star-omen/src/connectors/kb_retrieval/two_stage.py`
- Modify: `apps/star-omen/tests/test_official_two_stage_v2.py`
- Modify: `apps/star-omen/tests/test_transport_error_taxonomy_v2.py`

**Interfaces:**
- Consumes: helper functions from Task 1.
- Produces: result `observability`; error `details.observability`; ordered two-stage `observability.stages`.

- [ ] Add tests with a deterministic monotonic sequence for successful structured/primary stages, filesystem fallback, support-mode skip, missing upstream fields, strict JSON, and an official primary timeout that re-raises without scanning.
- [ ] Run new tests and observe missing envelope assertions.
- [ ] Wrap only the official `_request` boundary in `retrieve()`, re-raising `KBSearchError` after adding safe context. Assemble two-stage trace without catching retrieval failures.
- [ ] Run official two-stage and transport taxonomy tests; require all to pass with unchanged call ordering.

### Task 3: Candidate sync run trace

**Files:**
- Modify: `apps/star-omen/src/candidate_sync.py`
- Modify: `apps/star-omen/tests/test_candidate_sync_errors_v2.py`
- Modify: `apps/star-omen/tests/test_candidate_sync_v1.py`

**Interfaces:**
- Produces: returned report `observability` with latency, meta provenance, counts, and `run_error`.
- Preserves: manifest atomic replacement and existing `error` payload.

- [ ] Add deterministic-clock tests for healthy sync, meta failure, item lookup failure after prior success, every shared error code, null meta provenance, strict JSON, and byte-identical manifests on errors.
- [ ] Run new tests and observe missing `observability` assertions.
- [ ] Thread one start time and aggregate counters through success and `_error_report`; do not persist latency into manifests and do not catch new exception classes.
- [ ] Run candidate sync v1/v2 suites and require all to pass.

### Task 4: Verification, review, and merge

**Files:**
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Produces: exact-head verification and PR evidence for B6-T02.

- [ ] Set B6-T02 to `VERIFYING`, record every RED/GREEN and run `make contracts-test`, `make text-core-test`, `make downstream-test`, and `make upstream-test`.
- [ ] Run governance against base `0632c0a87515b4b6d33ea2476630d62e2b3321d7`, inspect changed files, and confirm no protected data/collection path changed.
- [ ] Publish exact head to draft PR, wait for all three workflows, and request independent review.
- [ ] Reproduce and fix every Critical/Important review issue with tests, then rerun fresh exact-head gates.
- [ ] Mark ready and squash merge only into `stable/kaiyuan-v2`; record actual merge SHA on the B6-T03 feature branch.
