# Kaiyuan Release Artifact Assembly Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Assemble three strict B7 observations and one approved manifest into an atomically created B6 release-drill input that already passes the existing validator.

**Architecture:** A pure module owns envelope/manifest/timestamp validation and calls `validate_release_drill`; a thin CLI owns strict file parsing, stable exit semantics, hashing, and exclusive atomic output. Existing B6 validation and B7 capture behavior remain unchanged.

**Tech Stack:** Python 3.9+, stdlib `json`, `datetime`, `hashlib`, `pathlib`, `tempfile`, pytest.

## Global Constraints

- Base and PR target only `stable/kaiyuan-v2`; never `main`.
- No network, routing, rollback, ingest, corpus/candidate, Qdrant, collection, or `local_kb_default` mutation.
- Strict UTF-8 JSON rejects duplicate keys and `NaN`/`Infinity`.
- Output is caller-selected, atomically created, and never overwritten.
- Any input or B6 validation failure leaves no final or temporary artifact.
- Final output contains no API key, raw HTTP body, hit, snippet, path, anchor, payload, or source content.

---

### Task 1: Pure assembler contract

**Files:**
- Create: `apps/local-kb-unified/release_artifact.py`
- Create: `apps/local-kb-unified/tests/test_release_artifact_v1.py`

**Interfaces:**
- Consumes: `release_drill.INPUT_SCHEMA`, `TARGET_COLLECTION`, `MANIFEST_IDENTITY_FIELDS`, and `validate_release_drill`.
- Produces: `ReleaseArtifactError(code: str, field: str)` and `assemble_release_artifact(*, observations: Mapping[str, object], expected_manifest: Mapping[str, object]) -> tuple[dict[str, object], dict[str, object]]`.

- [ ] Write a happy-path test loading `tests/fixtures/release_drill_v1.json`, wrapping each fixture phase in its exact B7 envelope, and expecting import RED for `release_artifact`.
- [ ] Run `cd apps/local-kb-unified && PYTHONPATH=. pytest -q tests/test_release_artifact_v1.py` and record `ModuleNotFoundError`.
- [ ] Implement `ReleaseArtifactError`, exact observation key/schema/slot checks, manifest identity projection, document construction, and existing-validator call; return `(document, report)` only when `report.status=passed`.
- [ ] Run the focused happy-path test and require the returned document keys to equal `{schema_version,target_collection,expected_release_manifest,before_switch,after_switch,after_rollback}` and report status `passed`.
- [ ] Commit the first pure assembler cycle.

### Task 2: Fail-closed envelope, chronology, and manifest validation

**Files:**
- Modify: `apps/local-kb-unified/release_artifact.py`
- Modify: `apps/local-kb-unified/tests/test_release_artifact_v1.py`

**Interfaces:**
- Produces canonical timestamp validation accepting only `YYYY-MM-DDTHH:MM:SS[.ffffff]Z` and requiring `before < after < rollback`.
- Produces error codes `observation_contract_error`, `timestamp_error`, `manifest_contract_error`, and `drill_validation_failed` without copying input values.

- [ ] Add parameterized RED tests for missing/extra observation keys, wrong schema, swapped or duplicate `phase_name`, non-mapping phase, timezone offset/non-date timestamp, non-increasing chronology, missing/empty/non-string identity, wrong target collection/schema/manager/collection schema, and a well-formed document rejected by B6.
- [ ] Run focused tests and confirm each failure is caused by absent validation, not fixture syntax.
- [ ] Implement exact key equality, `datetime.strptime` UTC parsing, strict chronological comparison, allowlisted identity projection, and content-free B6 failure wrapping that retains only the safe report.
- [ ] Run focused tests and confirm every failure raises the exact stable code/field and returns no document.
- [ ] Commit the validation cycle.

### Task 3: Strict atomic CLI

**Files:**
- Create: `apps/local-kb-unified/scripts/assemble_release_artifact.py`
- Modify: `apps/local-kb-unified/tests/test_release_artifact_v1.py`
- Modify: `apps/local-kb-unified/Makefile`
- Modify: `Makefile`

**Interfaces:**
- CLI arguments: `--before-switch`, `--after-switch`, `--after-rollback`, `--expected-manifest`, `--out`.
- Exit `0`: created validated artifact and printed safe SHA-256 summary; exit `1`: B6 validation failure with safe report; exit `2`: invocation/input/output contract failure.

- [ ] Add subprocess/unit RED tests for duplicate keys, non-finite JSON, invalid UTF-8, missing file, existing output, exclusive-create race, B6 failure, successful strict JSON, exact SHA-256, and no temp residue.
- [ ] Run CLI-focused tests and confirm missing script/function failures.
- [ ] Implement shared `_load_strict_json`, `_write_new_atomic`, stable stderr codes, safe validation report output, and SHA-256 over exact final bytes.
- [ ] Add root and upstream `assemble-release-artifact` Make targets requiring every caller argument and embedding no credential or output default.
- [ ] Run focused tests; scan production source for HTTP/Qdrant/ingest and mutation calls; commit the CLI cycle.

### Task 4: Runbook, CI, and full verification

**Files:**
- Modify: `docs/development/B6_RELEASE_ROLLBACK_RUNBOOK.md`
- Modify: `.github/workflows/kaiyuan-upstream-runtime.yml`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- CI runs the synthetic assembler suite without network or collection access.
- Runbook uses assembler output directly with `verify_release_drill.py` and distinguishes input schema from report schema.

- [ ] Document one explicit assembly command after the three captures, validation command, exit semantics, output hashing, and statement that assembly does not authorize switching/rollback.
- [ ] Add a named CI step running `PYTHONPATH=. pytest -q tests/test_release_artifact_v1.py`.
- [ ] Move B7-T02 to `VERIFYING`; record every observed RED/GREEN and focused result in `WORK_LOG.md`.
- [ ] Run focused tests, `make release-drill`, `make contracts-test`, `make text-core-test`, `make downstream-test`, `make upstream-test`, governance, `git diff --check`, secret/machine-path scan, and forbidden-scope diff scan.
- [ ] Publish the exact head, update PR #22, wait for all latest-head workflows, request independent safety review, resolve every Critical/Important finding with RED/GREEN evidence, mark ready, and squash merge only to `stable/kaiyuan-v2`.
- [ ] On a closeout branch, record final head/run IDs/actual squash SHA in TASKS/WORK_LOG, mark DONE, pass closeout gates, and squash merge the closeout PR.
