# Kaiyuan Hermetic End-to-End Release Evidence Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic CI test that composes read-only observation capture, release artifact assembly, sealed bundle creation, and offline verification without live service access or mutation of `local_kb_default`.

**Architecture:** A focused pytest module owns deterministic read-only fakes and an explicit operation audit, while importing the existing pure B7 APIs unchanged. The upstream runtime workflow runs the focused gate as a separate named step.

**Tech Stack:** Python 3.9+, pytest, existing release evidence Python modules, GitHub Actions YAML.

## Global Constraints

- Target only `stable/kaiyuan-v2` through a feature PR.
- Never connect to, create, write, delete, or recreate `local_kb_default`; its invariant is supplied only by the hermetic fake inspector required by the existing capture contract.
- Use a random `ephemeral_kaiyuan_release_<hex>` prior collection and perform no collection mutation.
- Synthetic CI evidence must not be described as production-release evidence.
- Any contract or validation error fails closed and must not become an empty healthy result.

---

### Task 1: Successful capture-to-offline-verification gate

**Files:**
- Create: `apps/local-kb-unified/tests/test_release_evidence_e2e_v1.py`

**Interfaces:**
- Consumes: `capture_phase_observation(...)`, `assemble_release_artifact(...)`, `create_bundle_bytes(...)`, `verify_bundle_bytes(bytes)`.
- Produces: deterministic test-local phase builder and end-to-end gate test.

- [x] **Step 1: Write a failing test that imports a not-yet-created `_run_release_evidence_gate` helper and asserts exact verified output.**
- [x] **Step 2: Run `cd apps/local-kb-unified && PYTHONPATH=. pytest -q tests/test_release_evidence_e2e_v1.py`; expect RED from the missing helper.**
- [x] **Step 3: Implement the minimum test-local deterministic health, meta, retrieval, and inspection adapters, capture three phases, assemble, bundle, and verify; assert protected inspection is fake-only and exactly once per phase.**
- [x] **Step 4: Rerun the focused test; expect `1 passed`.**

### Task 2: Fail-closed and forbidden-access proofs

**Files:**
- Modify: `apps/local-kb-unified/tests/test_release_evidence_e2e_v1.py`

**Interfaces:**
- Consumes: Task 1 phase builder and stable exception types.
- Produces: protected fake-inspection audit and tamper regression tests.

- [x] **Step 1: Add tests that fail until the audit confines `local_kb_default` to exactly three fake read inspections and after-switch manifest tampering raises `ReleaseArtifactError(drill_validation_failed)`.**
- [x] **Step 2: Run the focused module and record the expected RED failures.**
- [x] **Step 3: Complete the minimum test fixture audit and preserve the assembly exception; do not catch it as an empty result.**
- [x] **Step 4: Rerun the focused module; expect all tests pass.**

### Task 3: CI registration and release evidence

**Files:**
- Modify: `.github/workflows/kaiyuan-upstream-runtime.yml`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Consumes: focused pytest module.
- Produces: named upstream-runtime gate and auditable lifecycle evidence.

- [x] **Step 1: Add workflow step `Hermetic release evidence end-to-end gate` running the focused module after archive verification.**
- [x] **Step 2: Run all six release-observation/drill/artifact/bundle/archive/e2e modules together and require all pass.**
- [x] **Step 3: Move B8-T02 to VERIFYING; run contracts, text-core, downstream, upstream, release-drill, and governance gates.**
- [ ] **Step 4: Record RED/GREEN commands, exact totals, review findings, final head, PR, workflow runs, and eventual squash merge SHA before DONE.**
