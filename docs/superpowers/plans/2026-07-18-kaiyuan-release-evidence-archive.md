# Kaiyuan Release Evidence Archive Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify sealed release bundles and create a deterministic, content-free retention index without moving or deleting evidence.

**Architecture:** A pure archive module consumes logical names plus exact bundle bytes, delegates every bundle to B7-T03 verification, projects safe provenance, applies deterministic classification, and strictly verifies rebuilt indexes. Thin CLIs own explicit name/path parsing, bounded reads, stable diagnostics, and atomic no-overwrite index publication.

**Tech Stack:** Python 3.9+, stdlib `json`, `hashlib`, `pathlib`, `tempfile`, `os`, pytest; existing `release_evidence_bundle` verifier/parser.

## Global Constraints

- Base and PR target only `stable/kaiyuan-v2`; never `main`.
- No network, file move/delete, routing, rollback, ingest, corpus/candidate, Qdrant, collection, or `local_kb_default` mutation.
- Every indexed bundle must pass exact-byte and semantic B7-T03 verification.
- Index contains no local path, filesystem metadata, observation/content, secret, raw body, hit, snippet, or anchor.
- Index output is deterministic, caller-selected, atomically created, and never overwritten.
- Retention is classification only: `retain|cold_archive_eligible`.

---

### Task 1: Pure deterministic archive index

**Files:**
- Create: `apps/local-kb-unified/release_evidence_archive.py`
- Create: `apps/local-kb-unified/tests/test_release_evidence_archive_v1.py`

**Interfaces:**
- Consumes: `release_evidence_bundle.verify_bundle_bytes`, strict JSON helpers, bundle schema/tool constants.
- Produces: `ReleaseEvidenceArchiveError(code, field)`, `build_archive_index(*, bundles: Mapping[str, bytes], keep_latest: int, pinned_hashes: Sequence[str]) -> dict[str, object]`, and `verify_archive_index(*, index_bytes: bytes, bundles: Mapping[str, bytes]) -> dict[str, object]`.

- [ ] Write happy-path RED using three deterministic synthetic B7 bundles in shuffled input order; require import failure for `release_evidence_archive`.
- [ ] Run `cd apps/local-kb-unified && PYTHONPATH=. /tmp/kaiyuan-b5/bin/pytest -q tests/test_release_evidence_archive_v1.py::test_build_is_deterministic_and_classifies_latest_and_pinned` and record the expected `ModuleNotFoundError`.
- [ ] Implement safe name/hash validation, full bundle verification, safe manifest projection, per-target latest/pin classification, fixed reasons, and stable final ordering.
- [ ] Implement strict verifier rebuild/equality and return only schema/count/classification summary.
- [ ] Run GREEN and commit the pure first cycle.

### Task 2: Fail-closed policy and index boundaries

**Files:**
- Modify: `apps/local-kb-unified/release_evidence_archive.py`
- Modify: `apps/local-kb-unified/tests/test_release_evidence_archive_v1.py`

**Interfaces:**
- Stable codes: `bundle_verification_failed`, `logical_name_error`, `duplicate_bundle_hash`, `policy_error`, `unknown_pin`, `index_contract_error`, and `index_mismatch`.

- [ ] Add RED tests for unsafe/duplicate names, duplicate bundle bytes, malformed/duplicate/unknown pins, bool/zero/negative/string/oversized keep counts, invalid/trailing/tampered bundle, tie ordering, pin/latest overlap, and input-order independence.
- [ ] Add RED verifier tests for duplicate/non-finite/deep/noncanonical JSON, missing/extra bundle binding, extra/missing/reordered keys/entries/reasons, modified policy/classification/hash/provenance, and source-path injection.
- [ ] Implement exact keys/types/order, bounded strict canonical JSON, exact supplied-name set, and deterministic rebuild comparison; normalize all lower-level errors without content leakage.
- [ ] Run focused GREEN and the B7-T03/B7/B6 related regression; commit boundary hardening.

### Task 3: Atomic create and verify CLIs

**Files:**
- Create: `apps/local-kb-unified/scripts/create_release_evidence_archive.py`
- Create: `apps/local-kb-unified/scripts/verify_release_evidence_archive.py`
- Modify: `apps/local-kb-unified/tests/test_release_evidence_archive_v1.py`
- Modify: `apps/local-kb-unified/Makefile`
- Modify: `Makefile`

**Interfaces:**
- Create: repeated `--bundle NAME=PATH`, required `--keep-latest`, repeatable `--pin`, and required `--out`.
- Verify: required `--index` plus repeated `--bundle NAME=PATH`.
- Exit `0` success; invalid/tampered bundle or index mismatch `1`; invocation/read/output contract `2`.

- [ ] Add subprocess RED for missing/duplicate/unsafe bindings, unreadable/oversized input, invalid policy, existing output, exclusive-create race, successful canonical summary/hash, verifier mismatch, safe stderr, and no temp residue.
- [ ] Implement thin bounded-read CLIs and fsynced temporary plus hard-link publication; never serialize paths.
- [ ] Add required-argument Make targets with no defaults and run CLI GREEN plus forbidden operation/import scans.
- [ ] Commit CLI/build entry points.

### Task 4: Runbook, CI, verification, review, and merge

**Files:**
- Modify: `docs/development/B6_RELEASE_ROLLBACK_RUNBOOK.md`
- Modify: `.github/workflows/kaiyuan-upstream-runtime.yml`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- CI runs synthetic archive tests offline; runbook makes classification-only/no-deletion semantics explicit.

- [ ] Document create/verify commands, logical-name binding, policy/reasons, exit codes, index hash recording, and explicit manual authority for any later archive movement.
- [ ] Add named CI focused archive step; move task to `VERIFYING` and record every RED/GREEN/root cause.
- [ ] Run focused and related tests, release drill, contracts, text-core, downstream, upstream, exact-base governance, diff/secret/machine-path/forbidden-scope scans.
- [ ] Publish/update draft PR, require workflows on latest exact head, request independent safety review, and reproduce/fix every Critical/Important issue with RED/GREEN evidence.
- [ ] Mark ready and squash merge only to `stable/kaiyuan-v2` after exact-head gates/review/diff checks; then record actual merge evidence through an independently gated closeout PR.
