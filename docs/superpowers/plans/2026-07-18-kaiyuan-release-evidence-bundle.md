# Kaiyuan Release Evidence Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create and offline-verify a deterministic, atomically published release evidence bundle whose bytes and B6/B7 semantics are fail-closed.

**Architecture:** A pure `release_evidence_bundle` module canonicalizes validated inputs, builds a strict inventory, writes deterministic ZIP bytes, and verifies archive plus semantic contracts without extraction. Thin create/verify CLIs own strict file parsing, stable exit codes, and atomic no-overwrite publication while reusing B7-T02 assembly and B6 validation.

**Tech Stack:** Python 3.9+, stdlib `json`, `hashlib`, `zipfile`, `io`, `pathlib`, `tempfile`, `os`, pytest.

## Global Constraints

- Base and PR target only `stable/kaiyuan-v2`; never `main`.
- No network, routing, rollback, ingest, corpus/candidate, Qdrant, collection, or `local_kb_default` mutation.
- Strict UTF-8 JSON rejects duplicate keys, non-finite values, excessive depth, and excessive nodes.
- Bundle members are content-free allowlisted projections; no API key, raw body, hit, snippet, path, anchor, payload, or source content.
- Output is deterministic, caller-selected, atomically created, and never overwritten.
- Verification performs no extraction and reruns B7-T02 assembly plus B6 validation.

---

### Task 1: Pure canonical bundle contract

**Files:**
- Create: `apps/local-kb-unified/release_evidence_bundle.py`
- Create: `apps/local-kb-unified/tests/test_release_evidence_bundle_v1.py`

**Interfaces:**
- Consumes: `release_artifact.assemble_release_artifact`, observation/schema constants, and `release_drill.validate_release_drill`.
- Produces: `ReleaseEvidenceBundleError(code: str, field: str)`, `create_bundle_bytes(*, observations, expected_manifest, assembled_document, release_head, created_at) -> tuple[bytes, dict[str, object]]`, and `verify_bundle_bytes(data: bytes) -> dict[str, object]`.

- [ ] **Step 1: Write the failing happy-path test** that builds valid observations from `tests/fixtures/release_drill_v1.json`, calls `create_bundle_bytes`, inspects the exact seven member names, and passes the bytes to `verify_bundle_bytes`.
- [ ] **Step 2: Run RED** with `cd apps/local-kb-unified && PYTHONPATH=. /tmp/kaiyuan-b5/bin/pytest -q tests/test_release_evidence_bundle_v1.py::test_create_and_verify_deterministic_bundle`; expect `ModuleNotFoundError: release_evidence_bundle`.
- [ ] **Step 3: Implement the minimum pure creator** with schema `kaiyuan-release-evidence-bundle/v1`, tool `local-kb-unified/release-evidence-bundle`, version `1`, canonical sorted finite JSON, exact member order, fixed `ZipInfo`, allowlisted manifest projection, assembly equality, and internally generated report.
- [ ] **Step 4: Implement the minimum pure verifier** that reads without extraction, checks exact names/metadata/inventory hashes and sizes, reruns assembly/validation, and returns a content-free success summary.
- [ ] **Step 5: Run GREEN** for the focused happy path and require two invocations with identical inputs to return identical bytes.
- [ ] **Step 6: Commit** pure creator/verifier and the first test cycle.

### Task 2: Fail-closed archive, provenance, and tamper boundaries

**Files:**
- Modify: `apps/local-kb-unified/release_evidence_bundle.py`
- Modify: `apps/local-kb-unified/tests/test_release_evidence_bundle_v1.py`

**Interfaces:**
- Creator accepts only lowercase 40-hex `release_head` and canonical UTC `created_at` matching `YYYY-MM-DDTHH:MM:SS[.ffffff]Z`.
- Verifier enforces exact member metadata, maximum archive/member sizes, exact manifest keys/order, and codes `archive_contract_error`, `bundle_manifest_error`, `inventory_mismatch`, `member_size_mismatch`, `member_hash_mismatch`, `assembly_mismatch`, and `drill_validation_failed`.

- [ ] **Step 1: Add RED provenance tests** for uppercase/short/symbolic head, offset/non-date timestamp, extra manifest fields, invalid tool/schema/version/target, and non-finite or duplicate JSON.
- [ ] **Step 2: Run focused provenance tests** and confirm failures arise from missing strict checks.
- [ ] **Step 3: Add RED archive tests** for duplicate, missing, unexpected, traversal, compressed, encrypted-flag, commented, extra-field, non-regular, oversized member/archive, reordered inventory, size/hash tampering, and duplicate inventory name.
- [ ] **Step 4: Add RED semantic tamper tests** that recompute inventory after changing an observation, assembled input, or report, proving byte hashes alone are insufficient.
- [ ] **Step 5: Implement bounded strict JSON parsing and all archive/inventory/provenance/semantic checks** with content-free stable errors and no extraction.
- [ ] **Step 6: Run GREEN** for the complete focused module suite, then rerun the 83-test B6/B7 baseline.
- [ ] **Step 7: Commit** fail-closed boundary hardening.

### Task 3: Atomic create and offline verify CLIs

**Files:**
- Create: `apps/local-kb-unified/scripts/create_release_evidence_bundle.py`
- Create: `apps/local-kb-unified/scripts/verify_release_evidence_bundle.py`
- Modify: `apps/local-kb-unified/tests/test_release_evidence_bundle_v1.py`
- Modify: `apps/local-kb-unified/Makefile`
- Modify: `Makefile`

**Interfaces:**
- Create arguments: `--before-switch`, `--after-switch`, `--after-rollback`, `--expected-manifest`, `--assembled-input`, `--release-head`, `--created-at`, `--out`.
- Verify arguments: `--bundle`.
- Creator exit `0` on atomic creation, `1` for semantic validation failure, `2` for invocation/input/output errors. Verifier exit `0` on success, `1` for invalid/tampered bundle, `2` for invocation/read failure.

- [ ] **Step 1: Add subprocess RED tests** for missing arguments, invalid UTF-8/duplicate/non-finite/deep JSON, supplied artifact mismatch, existing output, exclusive-create race, successful exact SHA summary, verifier unreadable/invalid/tampered input, and no temporary residue.
- [ ] **Step 2: Run CLI-focused tests** and confirm missing scripts/targets are the expected failures.
- [ ] **Step 3: Implement thin CLIs** using one shared strict loader from the pure module, same-directory fsynced temporary file plus hard link, safe parser errors, bounded archive reads, and content-free JSON summaries.
- [ ] **Step 4: Add Make targets** `create-release-evidence-bundle` and `verify-release-evidence-bundle`, requiring every creator input and providing no credentials or output defaults.
- [ ] **Step 5: Run GREEN**, `git diff --check`, and production scans for HTTP/Qdrant/ingest/routing/mutation imports or calls.
- [ ] **Step 6: Commit** CLI and build entry points.

### Task 4: Runbook, CI, verification, review, and merge

**Files:**
- Modify: `docs/development/B6_RELEASE_ROLLBACK_RUNBOOK.md`
- Modify: `.github/workflows/kaiyuan-upstream-runtime.yml`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- CI runs the synthetic evidence-bundle suite without network or collection access.
- Runbook records explicit creation and offline verification commands and states that a passing bundle does not authorize switching or rollback.

- [ ] **Step 1: Document operator commands**, provenance ownership, exit semantics, portability, hash recording, and the no-authorization/no-mutation boundary.
- [ ] **Step 2: Add a named CI step** running `PYTHONPATH=. pytest -q tests/test_release_evidence_bundle_v1.py`.
- [ ] **Step 3: Move B7-T03 to `VERIFYING`** and record every observed RED/GREEN, failure root cause, and focused result in `WORK_LOG.md`.
- [ ] **Step 4: Run final local gates**: focused bundle tests; release drill; contracts; text-core; downstream; upstream; governance against exact base/head; `git diff --check`; secret/machine-path scan; forbidden-scope diff scan.
- [ ] **Step 5: Publish a draft PR targeting only `stable/kaiyuan-v2`**, verify actual metadata and changed files, and wait for all workflows on the latest exact head.
- [ ] **Step 6: Request independent safety review**, reproduce every Critical/Important finding with RED before fixing, rerun affected regressions and all new-head workflows, and resolve review threads.
- [ ] **Step 7: Mark ready and squash merge** only after exact-head required gates are green, no critical/important review remains, and the diff has no forbidden scope.
- [ ] **Step 8: Create a closeout branch from actual merged stable**, record final feature head/run IDs/actual squash SHA in TASKS/WORK_LOG, mark DONE, pass closeout gates, and squash merge the closeout PR only to `stable/kaiyuan-v2`.
