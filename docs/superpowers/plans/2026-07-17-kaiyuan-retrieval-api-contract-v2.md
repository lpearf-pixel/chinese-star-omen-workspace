# Kaiyuan Retrieval API Contract v2 Implementation Plan

> Required workflow: test-driven development, task-by-task execution, and verification before merge.

**Goal:** Align upstream KB Search and downstream two-stage retrieval with explicit intent, stage, and card-pool semantics; add corpus metadata/readiness endpoints; make official Qdrant primary evidence precede filesystem fallback.

**Base:** `stable/kaiyuan-v2`

**Branch:** `codex/kaiyuan-retrieval-contract-v2`

## Constraints

- Do not modify `main`.
- Keep `local_kb_default` untouched.
- Preserve B2 passage ingest and reconciliation.
- Write `kb_book_id`; read `book_id` only as a compatibility alias.
- Missing collection must not look like a successful empty result.
- Candidate overlay remains candidate-only.

## Task 1: Retrieval pool resolution

Files:
- `apps/local-kb-unified/kb-search/app/retrieval_pools.py`
- `apps/local-kb-unified/tests/test_retrieval_contract_v2.py`

Steps:
- [ ] Add failing tests for explicit `card_types`, legacy `filters.card_type`, stage defaults, legacy-mode fallback, and conflicting book aliases.
- [ ] Implement filter canonicalization and one effective card-type condition.
- [ ] Verify evidence intent plus structured stage never adds primary card types.

Required APIs:

```python
def canonicalize_filters(filters): ...
def resolve_card_types(*, query_mode, retrieval_stage, card_types, filters): ...
def build_retrieval_filter(*, filters, query_mode, retrieval_stage, card_types): ...
```

## Task 2: Retrieve and RAG v2

Files:
- `apps/local-kb-unified/kb-search/app/main.py`
- upstream API tests

Steps:
- [ ] Add failing tests for v2 echo fields and passage provenance.
- [ ] Add missing-collection 404 and successful no-hit 200 tests.
- [ ] Add canonical RAG request tests using `question` and `top_k`.
- [ ] Implement structured errors and v2 response metadata.

## Task 3: Metadata and readiness

Files:
- `apps/local-kb-unified/kb-search/app/meta.py`
- `apps/local-kb-unified/kb-search/app/main.py`
- `apps/local-kb-unified/tests/test_meta_health_v2.py`

Steps:
- [ ] Test valid, missing, and invalid corpus manifests.
- [ ] Test absent model, collection, and manifest/collection mismatch.
- [ ] Implement `/v1/meta` and readiness checks.
- [ ] Return 200 only when every readiness check passes; otherwise 503.

## Task 4: Downstream official two-stage retrieval

Files:
- `apps/star-omen/src/connectors/kb_retrieval/core.py`
- `apps/star-omen/src/connectors/kb_retrieval/two_stage.py`
- `apps/star-omen/src/connectors/kb_retrieval/transport.py`
- downstream retrieval tests

Steps:
- [ ] Test stage and card-type payloads.
- [ ] Test Stage 1 structured and Stage 2 primary upstream calls.
- [ ] Test filesystem fallback only when official primary is empty.
- [ ] Test official Stage 2 primary hits are returned as primary exact/candidate hits.
- [ ] Implement canonical RAG and metadata calls.

## Task 5: Integration and documentation

Files:
- API/runtime/downstream README files
- `.github/workflows/kaiyuan-upstream-runtime.yml`
- Qdrant contract integration tests

Steps:
- [ ] Prove structured and primary pools remain separate in ephemeral Qdrant.
- [ ] Prove missing collection and no-hit semantics differ.
- [ ] Run upstream, Qdrant, text-core, contracts, and downstream gates.
- [ ] Update rollout and rollback documentation.

## Task 6: Finish

- [ ] Scan for secrets and machine-local artifacts.
- [ ] Open a draft PR to `stable/kaiyuan-v2`.
- [ ] Fix CI failures by root cause.
- [ ] Merge only after all gates pass.
- [ ] Start B4 for sync errors, citable evidence validation, and golden end-to-end evaluation.
