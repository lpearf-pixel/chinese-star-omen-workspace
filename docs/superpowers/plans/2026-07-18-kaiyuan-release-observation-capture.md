# Kaiyuan Release Observation Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture one fail-closed, content-free B6 release phase observation from live read-only KB Search and Qdrant interfaces.

**Architecture:** A pure module validates injected adapter results and constructs the phase payload; a separate CLI owns requests/Qdrant adapters, secret loading, error taxonomy, and atomic output. The existing B6 verifier remains unchanged and is used for integration proof.

**Tech Stack:** Python 3.9+, requests, qdrant-client, pytest, stdlib JSON/hashlib/pathlib.

## Global Constraints

- Base and PR target only `stable/kaiyuan-v2`; never `main`.
- Never mutate, delete, recreate, migrate, or ingest `local_kb_default`.
- No raw HTTP body, hit, snippet, path, anchor, payload, source content, or API key in output/errors.
- Every transport/auth/timeout/contract/collection/parse failure aborts without partial output.
- Output path is explicit, atomically created, and never overwritten.

---

### Task 1: Pure observation builder

**Files:**
- Create: `apps/local-kb-unified/tests/test_release_observation_v1.py`
- Create: `apps/local-kb-unified/release_observation.py`

**Interfaces:**
- Produces: `capture_phase_observation(*, active_collection: str, query: str, fetch_health, fetch_meta, retrieve, inspect_collection, captured_at: str) -> dict[str, object]`.
- Produces: `ReleaseObservationError(code: str, operation: str)` with no copied upstream message/body.

- [ ] Write a failing happy-path test with injected fakes and assert exact health/meta/smoke/fingerprint output contains no hit content or secret.
- [ ] Run `PYTHONPATH=. pytest -q tests/test_release_observation_v1.py` and observe missing-module RED.
- [ ] Implement minimal typed validation and phase construction using B6 constants.
- [ ] Add failing tests for health/meta disagreement, zero hits, wrong stage/pool/collection, missing collections, invalid counts, non-finite config, and stable safe errors.
- [ ] Implement canonical allowlisted config hashing and error mapping; run focused GREEN.

### Task 2: HTTP and Qdrant read adapters

**Files:**
- Create: `apps/local-kb-unified/release_observation_live.py`
- Modify: `apps/local-kb-unified/tests/test_release_observation_v1.py`

**Interfaces:**
- Produces: `KBSearchReadClient(base_url: str, api_key: str, timeout_seconds: float)` with `health()`, `meta()`, `retrieve(...)`.
- Produces: `QdrantCollectionReader(client)` with `inspect(collection: str)`.

- [ ] Write adapter RED tests for authorization header, exact JSON request, 401/403, timeout, 5xx, invalid JSON/shape, and collection missing.
- [ ] Implement requests adapters with explicit status taxonomy and no raw-body propagation.
- [ ] Implement Qdrant adapter calling only `collection_exists`, `get_collection`, and exact `count`; serialize only the design allowlist.
- [ ] Add source-safety assertion that production modules contain no ingest/upsert/delete/create/recreate calls; run focused GREEN.

### Task 3: Atomic CLI

**Files:**
- Create: `apps/local-kb-unified/scripts/capture_release_observation.py`
- Modify: `apps/local-kb-unified/tests/test_release_observation_v1.py`
- Modify: `apps/local-kb-unified/Makefile`
- Modify: `Makefile`

**Interfaces:**
- CLI: `--phase`, `--active-collection`, `--query`, `--base-url`, `--qdrant-url`, `--api-key-env`, `--out`, `--timeout`.
- Exit: 0 success; 1 runtime observation failure; 2 invocation/secret/output contract failure.

- [ ] Write subprocess RED tests for missing env secret, safe stderr, successful atomic create, refusal to overwrite, and strict JSON output.
- [ ] Implement CLI dependency wiring and same-directory temporary-file plus exclusive final creation/rename semantics.
- [ ] Add Make help target that requires caller arguments and never embeds credentials or a production output path.
- [ ] Run focused tests and confirm no temp artifact remains after failure.

### Task 4: B6 integration, documentation, and gates

**Files:**
- Modify: `apps/local-kb-unified/tests/test_release_observation_v1.py`
- Modify: `docs/development/B6_RELEASE_ROLLBACK_RUNBOOK.md`
- Modify: `.github/workflows/kaiyuan-upstream-runtime.yml`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Captured phase payload replaces one phase in a synthetic three-phase B6 input and passes `validate_release_drill`.

- [ ] Write integration RED proving a collector-shaped phase is not yet available, then wire the builder output into the B6 verifier fixture.
- [ ] Document three explicit capture invocations around operator-controlled switch/rollback and artifact assembly; state that capture does not authorize or perform those actions.
- [ ] Add a synthetic read-adapter CI test without network or `local_kb_default` access.
- [ ] Move B7-T01 to VERIFYING and record observed RED/GREEN plus focused results.
- [ ] Run `make contracts-test`, `make text-core-test`, `make downstream-test`, `make upstream-test`, governance, diff/secret scans, and all latest-head workflows.
- [ ] Request independent safety review, resolve Critical/Important findings with RED/GREEN evidence, mark ready, squash merge only to stable, and record actual merge SHA before DONE.
