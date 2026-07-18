# Kaiyuan Stable Release and Rollback Drill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a non-mutating, fail-closed verifier and runbook that prove a Kaiyuan v2 collection switch, exact manifest reconciliation, rollback to recorded routing, and unchanged `local_kb_default`.

**Architecture:** A pure Python module validates three supplied observations and emits a versioned strict-JSON report; a thin CLI loads a snapshot file and maps passed/failed/invalid input to exit codes 0/1/2. A synthetic fixture exercises the same contract in CI, while the operator runbook explains how to capture real observations without granting the verifier mutation authority.

**Tech Stack:** Python 3.9+, stdlib `json`, pytest, Make, GitHub Actions, Markdown.

## Global Constraints

- Release base is only `stable/kaiyuan-v2`; never target `main`.
- Never delete, recreate, migrate, or write `local_kb_default`.
- The verifier must not connect to Qdrant, ingest, edit routing, or rewrite corpus/candidate files.
- Missing, invalid, unhealthy, mismatched, or empty retrieval observations fail closed.
- CI uses synthetic observations or random ephemeral collections only.
- Existing ingest, retrieval, evidence, candidate, corpus, and observability contracts remain unchanged.

---

### Task 1: Pure release-drill contract and validator

**Files:**
- Create: `apps/local-kb-unified/tests/test_release_drill_v1.py`
- Create: `apps/local-kb-unified/release_drill.py`

**Interfaces:**
- Consumes: a Python `Mapping[str, object]` with `schema_version`, `target_collection`, `expected_release_manifest`, and three phase observations.
- Produces: `validate_release_drill(document: Mapping[str, object]) -> dict[str, object]` returning `schema_version=kaiyuan-release-drill/v1`, `status`, collection provenance, named checks, and stable errors.

- [ ] **Step 1: Write the failing happy-path and safety tests**

Create helpers that build complete manifest, health, smoke, and collection-fingerprint observations. Assert a correct switch from a recorded prior collection to `local_kb_kaiyuan_v2` and back passes. Assert rollback from/to a prior `local_kb_default` read route passes only when its fingerprint is identical. Assert the report is serializable with `json.dumps(..., allow_nan=False)`.

- [ ] **Step 2: Run tests and observe RED**

Run: `PYTHONPATH=apps/local-kb-unified pytest -q apps/local-kb-unified/tests/test_release_drill_v1.py`

Expected: collection fails because `release_drill` does not exist.

- [ ] **Step 3: Implement the minimal validator**

Define constants for the target/protected collections, required health checks, manifest identity fields, and supported schemas. Validate shape before field access. Add stable errors through one helper and compute these named checks: `target_allowed`, `phase_contracts`, `release_health`, `release_manifest`, `release_smoke`, `rollback_provenance`, `rollback_health`, `rollback_manifest`, `rollback_smoke`, and `protected_collection_unchanged`. A passed report requires every check true and an empty error list.

- [ ] **Step 4: Add fail-closed parameterized tests**

Cover wrong target, missing phase, non-ready health, false health check, invalid manifest status/schema/manager/collection schema, expected-release identity mismatch, structured or primary zero hits, wrong smoke collection, rollback to a different collection, rollback meta mismatch, absent protected snapshot, and protected count/config/existence drift. Assert stable error codes and `status=failed`.

- [ ] **Step 5: Run focused tests GREEN**

Run: `PYTHONPATH=apps/local-kb-unified pytest -q apps/local-kb-unified/tests/test_release_drill_v1.py`

Expected: all release-drill tests pass.

### Task 2: Strict CLI and synthetic drill fixture

**Files:**
- Create: `apps/local-kb-unified/scripts/verify_release_drill.py`
- Create: `apps/local-kb-unified/tests/fixtures/release_drill_v1.json`
- Modify: `apps/local-kb-unified/tests/test_release_drill_v1.py`
- Modify: `apps/local-kb-unified/Makefile`
- Modify: `Makefile`

**Interfaces:**
- Consumes: `python scripts/verify_release_drill.py --input PATH`.
- Produces: strict JSON report on stdout; exit 0 passed, 1 valid failed drill, 2 unreadable/invalid JSON/root contract.

- [ ] **Step 1: Write failing CLI tests**

Use `subprocess.run` to assert the committed fixture exits 0, a semantically failed snapshot exits 1 with a report, malformed JSON exits 2 without a success-shaped report, and output rejects NaN. Verify neither script nor module imports Qdrant or contains mutation verbs used as calls.

- [ ] **Step 2: Run the CLI tests and observe RED**

Run: `PYTHONPATH=apps/local-kb-unified pytest -q apps/local-kb-unified/tests/test_release_drill_v1.py -k cli`

Expected: failures because the CLI and fixture are absent.

- [ ] **Step 3: Implement CLI, fixture, and Make targets**

Parse only `--input`; load UTF-8 JSON; require an object root; call the pure validator; print `json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)`. Add upstream `release-drill` and root `release-drill` Make targets that run the committed fixture.

- [ ] **Step 4: Run focused and upstream regression tests**

Run: `make release-drill`

Expected: JSON report with `status=passed`, exit 0.

Run: `make upstream-test`

Expected: all upstream tests pass, with only established environment skips.

### Task 3: Operator runbook and CI enforcement

**Files:**
- Create: `docs/development/B6_RELEASE_ROLLBACK_RUNBOOK.md`
- Modify: `.github/workflows/kaiyuan-upstream-runtime.yml`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Consumes: real phase observations prepared according to the documented JSON contract.
- Produces: reproducible operator evidence and a CI step named `Non-mutating release rollback drill`.

- [ ] **Step 1: Write the runbook**

Document prerequisites, exact branch/collection boundaries, required snapshot fields, commands to query health/meta and perform structured/primary smoke, manual routing switch boundaries, manifest reconciliation, rollback triggers, rollback verification, artifact hashing, and WORK_LOG evidence. Explicitly state that examples never ingest or mutate `local_kb_default`, and that synthetic CI success is not production-release evidence.

- [ ] **Step 2: Add CI execution**

After upstream unit tests, run `make release-drill`. Keep the job read-only and dependency-free beyond the existing Python installation.

- [ ] **Step 3: Update task evidence to VERIFYING**

Record RED/GREEN commands and results, affected files, safety review, remaining verification, exact head, and draft PR. Change B6-T03 from `IN_PROGRESS` to `VERIFYING` only after focused and related regression tests pass.

- [ ] **Step 4: Run repository gates**

Run: `make contracts-test`

Run: `make text-core-test`

Run: `make downstream-test`

Run: `make upstream-test`

Run: `make release-drill`

Run: `python scripts/check_development_governance.py --base <stable-sha> --head <feature-sha>`

Expected: every command passes on the same feature head.

### Task 4: Review, exact-head CI, and stable merge

**Files:**
- Modify: `docs/development/WORK_LOG.md`
- Modify: `docs/development/TASKS.md` after merge evidence is available on the next stable-based feature branch if required by branch-protection timing.

**Interfaces:**
- Consumes: latest PR head and reviewer findings.
- Produces: ready PR, successful required workflows on latest head, actual squash merge SHA on `stable/kaiyuan-v2`, and durable DONE evidence.

- [ ] **Step 1: Request independent code and safety review**

Check scope, validator determinism, false-positive paths, secret/content leakage, legacy collection protection, and runbook operational ambiguity. Resolve every Critical/Important finding with RED→GREEN evidence.

- [ ] **Step 2: Publish final evidence update**

Record exact focused/full commands and counts, reviewer disposition, PR number, exact head SHA, and remaining risks. Any evidence commit invalidates earlier CI.

- [ ] **Step 3: Verify latest-head gates**

Confirm PR base is `stable/kaiyuan-v2`, non-draft, mergeable, no unresolved Critical/Important thread, no forbidden diff, and Development Governance, Kaiyuan Stable Core, and Kaiyuan Upstream Runtime all succeeded for the actual head SHA.

- [ ] **Step 4: Squash merge and verify actual ref**

Squash merge only to `stable/kaiyuan-v2`; query PR merged state and independently resolve `refs/heads/stable/kaiyuan-v2`. Record the actual merge SHA, never a merge preview SHA.

- [ ] **Step 5: Mark DONE with durable evidence**

Only after WORK_LOG records commands, CI run IDs, final head, PR, review, and merge SHA, set B6-T03 to `DONE`. Confirm `main`, raw corpus, candidates, Qdrant schema/data, and `local_kb_default` were untouched.
