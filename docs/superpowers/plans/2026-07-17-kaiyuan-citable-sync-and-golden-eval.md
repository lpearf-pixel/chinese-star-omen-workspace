# Kaiyuan Citable Sync and Golden Evaluation v2 Implementation Plan

> Required workflow: test-driven development, root-cause debugging, and verification before merge.

**Goal:** Make candidate sync atomic and error-aware, require source/page/anchor/hash verification for final citations, and add a golden end-to-end retrieval/promotion/sync gate.

**Base:** `stable/kaiyuan-v2`

**Branch:** `codex/kaiyuan-citable-sync-v2`

## Constraints

- Never modify or merge into `main`.
- Never delete, recreate, or write `local_kb_default`.
- Preserve raw corpus bytes and `&KRxxxx;` entities.
- Reuse `kb-text-core`; do not duplicate Kaiyuan locator/page/normalization semantics.
- An upstream error must preserve existing candidate manifest/item statuses.
- A missing or mismatched source can never be citable.
- CText comparison is targeted/manual only; no bulk downloader.

---

## Task 1: Shared sync error contract

**Files:**
- Create/modify: `packages/kb-contracts/python/kb_contracts/sync.py`
- Modify: `packages/kb-contracts/python/kb_contracts/__init__.py`
- Create: `packages/kb-contracts/tests/test_sync_contract_v2.py`

- [ ] Write failing tests for canonical error codes, retryability, and serialization.
- [ ] Verify RED because the shared types do not exist.
- [ ] Implement `SyncErrorCode`, `SyncRunStatus`, and `sync_error_payload`.
- [ ] Run contracts tests and commit.

## Task 2: Structured downstream transport errors

**Files:**
- Modify: `apps/star-omen/src/connectors/kb_retrieval/transport.py`
- Create: `apps/star-omen/tests/test_transport_error_taxonomy_v2.py`

- [ ] Test 401/403 authentication classification.
- [ ] Test 404 collection-not-found and 422 contract-error response parsing.
- [ ] Test timeout/connectivity/5xx classification and retryability.
- [ ] Test invalid JSON/shape classification.
- [ ] Verify RED.
- [ ] Extend `KBSearchError` without breaking legacy string usage.
- [ ] Run focused and downstream tests.

## Task 3: Atomic candidate sync

**Files:**
- Refactor: `apps/star-omen/src/candidate_cards.py`
- Create: `apps/star-omen/src/candidate_sync.py`
- Create: `apps/star-omen/tests/test_candidate_sync_errors_v2.py`
- Update: `apps/star-omen/tests/test_candidate_sync_v1.py`

- [ ] Test healthy no-hit becomes `pending`.
- [ ] Test promoted official extract-card hash becomes `merged`.
- [ ] Test different official hash becomes `needs_review`.
- [ ] Test local anchor/hash drift becomes `stale`.
- [ ] Test auth, timeout, unavailable, contract, collection, and invalid-response errors preserve the entire manifest byte-for-byte.
- [ ] Test multi-item failure does not partially write earlier classifications.
- [ ] Implement in-memory planning plus atomic manifest replace.
- [ ] Use authenticated B3 `structured_recall` / `extract_card` retrieval rather than unauthenticated raw urllib.
- [ ] Return `candidate-sync-report/v2`.
- [ ] Run focused and downstream tests.

## Task 4: Strong citable evidence resolver

**Files:**
- Modify: `apps/star-omen/src/connectors/evidence_resolver.py`
- Modify: `apps/star-omen/src/connectors/kb_contract.py`
- Create: `apps/star-omen/tests/test_citable_evidence_v2.py`
- Update: `apps/star-omen/tests/test_evidence_resolver.py`

- [ ] Test a fully matched fenjuan passage is citable.
- [ ] Test fulltext page marker canonicalizes to the same volume locator.
- [ ] Test path traversal, missing source, wrong book, wrong card type, wrong locator, missing/wrong page, wrong paragraph, wrong heading, missing anchor, anchor mismatch, and hash mismatch.
- [ ] Test raw and normalized anchor behavior without mutating source text.
- [ ] Test `is_citable_evidence` only accepts verified v2 evidence.
- [ ] Verify RED.
- [ ] Implement passage-backed validation and trace.
- [ ] Run resolver, matcher, CLI, and downstream tests.

## Task 5: Rule audit and strict CLI reporting

**Files:**
- Modify: `apps/star-omen/src/cli.py`
- Create/modify: CLI tests

- [ ] Test `resolve-evidence --strict` reports exact validation status.
- [ ] Test `audit-rules` counts all statuses and includes reasons/check traces.
- [ ] Test rule matching never treats mismatch states as primary.
- [ ] Implement status-aware reports while preserving command names.
- [ ] Run downstream tests.

## Task 6: Golden evaluation v2

**Files:**
- Modify: `apps/star-omen/src/eval/corpus_eval.py`
- Replace/extend: `apps/star-omen/eval/corpus_eval_cases.yaml`
- Create: `apps/star-omen/tests/test_golden_retrieval_eval_v2.py`

- [ ] Add failing deterministic cases for structured pools, official primary usage, source locator/page/heading, citable fields, forbidden pollution, and fallback policy.
- [ ] Implement richer per-case metrics and aggregate failure reasons.
- [ ] Preserve old case fields as compatibility aliases.
- [ ] Run focused and downstream tests.

## Task 7: Promotion/ingest/retrieve/sync integration

**Files:**
- Create: `apps/local-kb-unified/tests/test_candidate_roundtrip_v2.py`
- Modify: `.github/workflows/kaiyuan-upstream-runtime.yml`
- Add helper fixtures only where necessary.

- [ ] Start ephemeral Qdrant.
- [ ] Generate and approve/promote one candidate fixture.
- [ ] Verify pending candidates are excluded and approved official cards are collected.
- [ ] Reconcile with deterministic fake embedding.
- [ ] Retrieve official `extract_card` through structured recall.
- [ ] Sync downstream status to `merged`.
- [ ] Simulate upstream error and prove manifest preservation.
- [ ] Validate the linked primary fixture as citable.
- [ ] Add a dedicated CI job.

## Task 8: Targeted CText comparison record

**Files:**
- Create: `corpus/kaiyuan_zhanjing/ctext_spot_checks.json`
- Create: `scripts/audit_kaiyuan_spot_checks.py`
- Create tests for the local, non-network comparison routine.

- [ ] Record manually reviewed CText excerpts with page/locator, access date, and expected local normalized text.
- [ ] Compare only supplied reference excerpts; do not fetch or crawl CText.
- [ ] Report exact/normalized/mismatch without rewriting corpus.
- [ ] Include the spot-check report in release documentation.

## Task 9: Documentation and release gates

**Files:**
- Update root/upstream/downstream docs and runbook.
- Update B4 spec/plan status.

- [ ] Document sync error semantics, atomicity, citation statuses, repair workflow, golden metrics, and CText spot-check policy.
- [ ] Run contracts, text-core Python 3.9/3.12, upstream, downstream, Qdrant incremental, Qdrant retrieval contract, candidate roundtrip, and secret/artifact gates.
- [ ] Open draft PR to `stable/kaiyuan-v2`.
- [ ] Fix failures by root cause.
- [ ] Mark ready and merge only after every gate passes.
