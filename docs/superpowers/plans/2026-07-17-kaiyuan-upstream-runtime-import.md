# Kaiyuan Upstream Runtime Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development and superpowers:executing-plans (or subagent-driven-development) for each task.

**Goal:** Import the real Local-KB-Unified runtime into `apps/local-kb-unified`, safely runnable against a parallel `local_kb_kaiyuan_v2` collection, without touching `main` or weakening the candidate workflow.

**Base branch:** `stable/kaiyuan-v2`

**Feature branch:** `codex/kaiyuan-upstream-runtime-v2`

## Constraints

- Do not commit secrets, `.env`, local model files, Qdrant/PostgreSQL data, `.DS_Store`, caches or `/Users/...` paths.
- Preserve existing candidate validation/promotion and corpus-manifest scripts.
- Do not implement destructive default ingest.
- Do not claim true incremental ingestion in B1.
- Do not change `main`.

---

### Task 1: Add failing runtime safety tests

**Files:**
- Create: `apps/local-kb-unified/tests/test_runtime_import_v2.py`

- [ ] Assert required runtime files and services exist.
- [ ] Assert Compose uses named Qdrant/PostgreSQL volumes.
- [ ] Assert `.env.example` defaults to `local_kb_kaiyuan_v2` and contains only placeholders.
- [ ] Assert `make ingest` does not contain `--recreate` and an explicit `ingest-recreate` target exists.
- [ ] Assert candidate inbox remains excluded from corpus sources.
- [ ] Run focused tests and confirm they fail because runtime files are still missing/stubbed.

### Task 2: Import sanitized runtime baseline

**Files:**
- Modify: `apps/local-kb-unified/Makefile`
- Create/modify: `apps/local-kb-unified/docker-compose.yml`
- Create/modify: `apps/local-kb-unified/.env.example`
- Create: `apps/local-kb-unified/.gitignore`
- Create: `apps/local-kb-unified/RUNTIME_BASELINE.json`
- Create: `apps/local-kb-unified/kb-search/**`
- Create: `apps/local-kb-unified/index-jobs/**`
- Create: selected `apps/local-kb-unified/scripts/**`
- Create: selected `apps/local-kb-unified/docs/**`

- [ ] Import only reviewed runtime files from the supplied archive.
- [ ] Replace bind-mounted database paths with named volumes.
- [ ] Set the trial collection default to `local_kb_kaiyuan_v2`.
- [ ] Preserve and expose candidate/corpus commands.
- [ ] Make `ingest` non-destructive and add `ingest-recreate` explicitly.
- [ ] Record source HEAD and archive hash in `RUNTIME_BASELINE.json`.

### Task 3: Make the imported service testable without live dependencies

**Files:**
- Create: `apps/local-kb-unified/tests/test_kb_search_runtime_v2.py`
- Modify only as required: `apps/local-kb-unified/kb-search/app/config.py`
- Modify only as required: `apps/local-kb-unified/kb-search/app/main.py`

- [ ] Write tests for API key validation, unknown collection behavior, and health response with mocked Ollama/Qdrant.
- [ ] Verify tests fail for missing seams or import problems.
- [ ] Add the minimum dependency injection/error handling required for tests.
- [ ] Keep final v2 API-contract redesign out of B1.

### Task 4: Add CI and documentation

**Files:**
- Create: `.github/workflows/kaiyuan-upstream-runtime.yml`
- Modify: root `README.md`
- Modify: `apps/local-kb-unified/README.md`

- [ ] Install upstream runtime/test dependencies on Python 3.12.
- [ ] Run upstream tests, Compose config validation and forbidden-file scan.
- [ ] Document `make setup`, `make up`, `make ingest`, `make ingest-recreate`, `make health` and rollback boundaries.

### Task 5: Verify and open PR

- [ ] Run upstream tests.
- [ ] Run existing contracts, text-core and downstream tests.
- [ ] Validate `docker compose config` with a generated non-secret test environment.
- [ ] Scan the diff for secrets, data volumes, model files and absolute paths.
- [ ] Open a draft PR to `stable/kaiyuan-v2`.
- [ ] Merge only after all CI gates pass.

After B1 merges, create B2 from the updated stable branch for passage-level incremental ingest.
