# Kaiyuan Citable Sync and Golden Evaluation v2 Design

## Goal

Make candidate synchronization, rule evidence resolution, and retrieval evaluation fail closed and use one traceable provenance model. Network failures must never become ordinary `pending` results, and a rule must not be called citable merely because it names a primary card type.

## Release boundary

- Base branch: `stable/kaiyuan-v2`
- Feature branch: `codex/kaiyuan-citable-sync-v2`
- Never target or merge into `main`.
- Never mutate or recreate `local_kb_default`.
- Preserve B2 passage identity and B3 retrieval-stage semantics.
- Raw corpus text remains immutable and unproofread.
- CText comparison remains manual or targeted; no automatic bulk download.

## 1. Candidate sync transaction

### Problem

The current candidate sync path turns transport/authentication failures into an empty hit list. Empty hits are then written as `sync_status=pending`, which is indistinguishable from a healthy upstream search that genuinely found no promoted card.

### Error taxonomy

Shared error codes:

```text
authentication_failed
upstream_unavailable
timeout
contract_error
collection_not_found
invalid_response
```

`KBSearchError` carries:

```text
code
message
status_code
retryable
details
```

HTTP mapping:

```text
401/403                      -> authentication_failed
404 COLLECTION_NOT_FOUND     -> collection_not_found
408 or client timeout        -> timeout
422 CONTRACT_ERROR           -> contract_error
429/5xx/connectivity failure -> upstream_unavailable
invalid JSON/shape           -> invalid_response
```

### Atomic sync algorithm

1. Load every candidate manifest without mutating it.
2. Read `/v1/meta`; classify any failure and stop.
3. For every item, validate the local source anchor/hash and query official structured `extract_card` evidence.
4. Build all proposed item statuses in memory.
5. If any upstream request fails, return `run_status=error`, preserve every existing manifest/item status, and write nothing.
6. Only after every item is classified successfully, update metadata/statuses and atomically replace manifests.

A successful HTTP 200 with no matching promoted item remains a normal `pending` result.

Sync report:

```text
schema_version=candidate-sync-report/v2
run_status=ok|error
error={code,message,status_code,retryable}
checked
preserved
updated={merged,needs_review,pending,stale}
upstream_meta
manifests
```

## 2. Citable evidence validation

### Problem

The current resolver marks any primary card with a relative path as citable, even when the file is missing, the quote is absent, the locator points to another volume, or the hash is stale.

### Required checks

For a final citable primary evidence object:

```text
card_type is fenjuan/fulltext
relative_path is present and confined under kb_root
source file exists
kb_book_id matches path/source metadata
source_locator matches canonical path/page locator
page_marker exists and belongs to the locator
paragraph_index identifies a parsed passage when supplied
anchor_text/quote is present in the selected passage
content_hash/raw_content_hash matches the anchor or selected raw passage
heading_path matches the selected passage when supplied
```

The resolver reuses `packages/kb-text-core` for canonical locators, page/paragraph parsing, conservative normalization, and hashes.

### Validation status

```text
citable
candidate_only
missing_source
source_outside_root
book_mismatch
card_type_mismatch
locator_mismatch
page_mismatch
paragraph_mismatch
anchor_mismatch
hash_mismatch
```

`candidate_only` is reserved for non-primary cards or references that have not yet supplied enough primary fields. A reference that once names a concrete primary source but no longer matches it receives the precise stale/mismatch status rather than being silently downgraded.

The resolver returns a check trace:

```text
validation_version=citable-evidence/v2
checks={path,card_type,book,locator,page,paragraph,heading,anchor,hash}
matched_passage={source_locator,page_marker,paragraph_index,raw_start,raw_end,hashes}
```

`is_citable_evidence()` accepts only `status=citable` for resolved v2 evidence.

## 3. Rule and CLI behavior

- `resolve-evidence --strict` fails for every status other than `citable` and reports the exact status/reason.
- `audit-rules` counts every validation status, not just citable/candidate-only.
- Rule matching treats only `citable` as primary evidence; mismatch statuses remain non-final and are surfaced in the evidence summary.
- Legacy minimal references remain loadable but are candidate-only until strengthened.

## 4. Golden retrieval evaluation

Golden cases validate more than query mode and path fragments:

```text
expected_query_mode
expected_stage1_card_types
must_use_official_primary
allow_filesystem_fallback
expected_primary_card_type
expected_source_locator
expected_page_marker
expected_heading_contains
require_final_citable
forbidden_card_types
```

Per-case output includes:

```text
stage1_pool_match
stage2_pool_match
official_primary_used
fallback_used
source_locator_match
page_marker_match
heading_match
citable_fields_present
pollution_detected
pass
```

The evaluation fails when a pending candidate, prompt/nav/example card, wrong volume, missing page marker, or filesystem fallback appears where official primary evidence is required.

## 5. End-to-end gate

An ephemeral test covers:

1. generate a candidate from a real primary fixture;
2. validate and approve/promote it upstream;
3. collect approved generated material into the desired corpus;
4. reconcile it into ephemeral Qdrant;
5. retrieve the official structured card with the v2 contract;
6. sync the downstream manifest to `merged`;
7. verify a network/auth failure preserves the prior manifest status;
8. validate the linked primary passage as citable using locator/page/anchor/hash.

The test uses fake deterministic embeddings and an ephemeral Qdrant service. It never writes the legacy collection.

## 6. Rollout and compatibility

- Existing sync statuses remain `pending`, `merged`, `needs_review`, `stale`; transport errors are separate run errors.
- Candidate manifests remain v1-compatible; optional `last_sync_report` and item validation fields are additive.
- Legacy `book_id` remains read-compatible but all writes use `kb_book_id`.
- The stable release is merged only after upstream, downstream, Python 3.9/3.12, incremental Qdrant, retrieval-contract, sync/evidence, and golden evaluation gates pass.
