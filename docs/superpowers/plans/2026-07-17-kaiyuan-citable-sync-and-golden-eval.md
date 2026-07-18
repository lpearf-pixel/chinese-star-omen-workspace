# Kaiyuan Citable Sync and Golden Evaluation v2 Implementation Plan

> Required workflow: test-driven development, root-cause debugging, and verification before merge.

**Goal:** Make candidate sync atomic and error-aware, require source/page/anchor/hash verification for final citations, and add a golden end-to-end retrieval/promotion/sync gate.

**Base:** `stable/kaiyuan-v2`

**Branch:** `codex/kaiyuan-citable-sync-v2`

**Task ledger:** `docs/development/TASKS.md`

**Work log:** `docs/development/WORK_LOG.md`

**Runbook:** `docs/development/B4_RELEASE_RUNBOOK.md`

## Constraints

- Never modify or merge into `main`.
- Never delete, recreate, or write `local_kb_default`.
- Preserve raw corpus bytes and `&KRxxxx;` entities.
- Reuse `kb-text-core`; do not duplicate Kaiyuan locator/page/normalization semantics.
- An upstream error must preserve existing candidate manifest/item statuses.
- A missing or mismatched source can never be citable.
- CText comparison is targeted/manual only; no bulk downloader.

## Verification snapshot

The implementation tasks below were verified at:

```text
head: 6152acc6bd9e3dbb07af97b10df42577ff87af54
Development Governance: 29623960771 success
Kaiyuan Stable Core: 29623960806 success
Kaiyuan Upstream Runtime: 29623960814 success
```

Documentation/status commits after that snapshot must receive a fresh final gate before merge.

---

## Task 1: Shared sync error contract

**Files:**
- Create/modify: `packages/kb-contracts/python/kb_contracts/sync.py`
- Modify: `packages/kb-contracts/python/kb_contracts/__init__.py`
- Create: `packages/kb-contracts/tests/test_sync_contract_v2.py`

- [x] Write failing tests for canonical error codes, retryability, and serialization.
- [x] Verify RED because the shared types do not exist.
- [x] Implement `SyncErrorCode`, `SyncRunStatus`, and `sync_error_payload`.
- [x] Run contracts tests and commit.

## Task 2: Structured downstream transport errors

**Files:**
- Modify: `apps/star-omen/src/connectors/kb_retrieval/transport.py`
- Create: `apps/star-omen/tests/test_transport_error_taxonomy_v2.py`

- [x] Test 401/403 authentication classification.
- [x] Test 404 collection-not-found and 422 contract-error response parsing.
- [x] Test timeout/connectivity/5xx classification and retryability.
- [x] Test invalid JSON/shape classification.
- [x] Verify RED.
- [x] Extend `KBSearchError` without breaking legacy string usage.
- [x] Run focused and downstream tests.

## Task 3: Atomic candidate sync

**Files:**
- Refactor: `apps/star-omen/src/candidate_cards.py`
- Create: `apps/star-omen/src/candidate_sync.py`
- Create: `apps/star-omen/tests/test_candidate_sync_errors_v2.py`
- Update: `apps/star-omen/tests/test_candidate_sync_v1.py`

- [x] Test healthy no-hit becomes `pending`.
- [x] Test promoted official extract-card hash becomes `merged`.
- [x] Test different official hash becomes `needs_review`.
- [x] Test local anchor/hash drift becomes `stale`.
- [x] Test auth, timeout, unavailable, contract, collection, and invalid-response errors preserve the entire manifest byte-for-byte.
- [x] Test multi-item failure does not partially write earlier classifications.
- [x] Implement in-memory planning plus atomic manifest replace.
- [x] Use authenticated B3 `structured_recall` / `extract_card` retrieval rather than unauthenticated raw urllib.
- [x] Return `candidate-sync-report/v2`.
- [x] Run focused and downstream tests.

## Task 4: Strong citable evidence resolver

**Files:**
- Modify: `apps/star-omen/src/connectors/evidence_resolver.py`
- Modify: `apps/star-omen/src/connectors/kb_contract.py`
- Create: `apps/star-omen/tests/test_citable_evidence_v2.py`
- Update: `apps/star-omen/tests/test_evidence_resolver.py`

- [x] Test a fully matched fenjuan passage is citable.
- [x] Test fulltext page marker canonicalizes to the same volume locator.
- [x] Test path traversal, missing source, wrong book, wrong card type, wrong locator, missing/wrong page, wrong paragraph, wrong heading, missing anchor, anchor mismatch, and hash mismatch.
- [x] Test raw and normalized anchor behavior without mutating source text.
- [x] Test `is_citable_evidence` only accepts verified v2 evidence.
- [x] Verify RED.
- [x] Implement passage-backed validation and trace.
- [x] Run resolver, matcher, CLI, and downstream tests.

## Task 5: Rule audit and strict CLI reporting

**Files:**
- Modify: `apps/star-omen/src/cli.py`
- Create/modify: CLI tests

- [x] Test `resolve-evidence --strict` reports exact validation status.
- [x] Test `audit-rules` counts all statuses and includes reasons/check traces.
- [x] Test rule matching never treats mismatch states as primary.
- [x] Implement status-aware reports while preserving command names.
- [x] Run downstream tests.

## Task 6: Golden evaluation v2

**Files:**
- Modify: `apps/star-omen/src/eval/corpus_eval.py`
- Replace/extend: `apps/star-omen/eval/corpus_eval_cases.yaml`
- Create: `apps/star-omen/tests/test_golden_retrieval_eval_v2.py`

- [x] Add failing deterministic cases for structured pools, official primary usage, source locator/page/heading, citable fields, forbidden pollution, and fallback policy.
- [x] Implement richer per-case metrics and aggregate failure reasons.
- [x] Preserve old case fields as compatibility aliases.
- [x] Run focused and downstream tests.

## Task 7: Promotion/ingest/retrieve/sync integration

**Files:**
- Create: `apps/local-kb-unified/tests/test_candidate_roundtrip_v2.py`
- Modify: `.github/workflows/kaiyuan-upstream-runtime.yml`
- Add helper fixtures only where necessary.

- [x] Start ephemeral Qdrant.
- [x] Generate and approve/promote one candidate fixture.
- [x] Verify pending candidates are excluded and approved official cards are collected.
- [x] Reconcile with deterministic fake embedding.
- [x] Retrieve official `extract_card` through structured recall.
- [x] Sync downstream status to `merged`.
- [x] Simulate upstream error and prove manifest preservation.
- [x] Validate the linked primary fixture as citable.
- [x] Add a dedicated CI job.

## Task 8: Targeted CText comparison record

**Files:**
- Create: `corpus/kaiyuan_zhanjing/ctext_spot_checks.json`
- Create: `scripts/audit_kaiyuan_spot_checks.py`
- Create tests for the local, non-network comparison routine.

- [x] Record manually reviewed CText excerpts with page/locator, access date, and expected local normalized text.
- [x] Compare only supplied reference excerpts; do not fetch or crawl CText.
- [x] Report exact/normalized/mismatch without rewriting corpus.
- [x] Include the spot-check policy and execution in release documentation.

## Task 9: Documentation and release gates

**Files:**
- Update root/upstream/downstream docs and runbook.
- Update B4 spec/plan status.
- Maintain `AGENTS.md` and `docs/development/*`.

- [x] Document sync error semantics, atomicity, citation statuses, repair workflow, golden metrics, and CText spot-check policy.
- [x] Add development governance manual, task ledger, decision record, work log, checker, tests, and CI.
- [x] Run contracts, text-core Python 3.9/3.12, upstream, downstream, Qdrant incremental, Qdrant retrieval contract, candidate roundtrip, CText, governance, and secret/artifact gates on the implementation head.
- [x] Open draft PR to `stable/kaiyuan-v2`.
- [x] Fix observed failures by root cause without weakening fail-closed behavior.
- [ ] Run the same required gates on the final documentation/status head.
- [ ] Mark ready and squash merge only after every final-head gate passes.
