# Kaiyuan External-media Audit Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add fail-closed research contracts for external media, atomic claims, evidence links and audits without allowing external content to become classical evidence or an approved omen rule.

**Architecture:** Keep four independently serializable v1 contracts and add one bundle boundary that validates all cross-references and status semantics. Store JSON Schemas in the existing registry and validate canonical synthetic fixtures separately from real creator evidence. Real 祖山觀 records require immutable work URLs and captured hashes; absent locators block ingestion instead of producing placeholders.

**Tech Stack:** Python 3.12, Pydantic v2, JSON Schema 2020-12, canonical JSON, pytest.

## Global Constraints

- Base remains `stable/kaiyuan-v2@c2e8fcabb04354fd14d0c72b3b6020a47e63a583`; delivery updates Draft PR #65 only.
- Preserve all Phase 1–4 scientific and navigation identities.
- External media is a research lead, never a citable classical passage, rule authority or Reviewer A/B substitute.
- A claim span must bind to a captured text/OCR/subtitle hash from the same media source.
- `supported_exact` requires explicit supporting evidence; `contradicted` requires explicit contradicting evidence; `source_missing` cannot carry a synthetic support link.
- `modern_inference_only` cannot masquerade as astronomy, classical or historical support.
- Models may propose candidate splits but cannot approve them without a non-empty human reviewer identity.
- Do not equate 烈风 with typhoon, tropical cyclone or maritime storm.
- Do not modify raw corpus, PR #54/#64, Qdrant, `local_kb_default`, workflows, B11/B12 or `main`.
- Routine Draft publication does not run Runner and does not merge.

---

### Task 1: Define strict external-media contracts

**Files:**
- Create: `apps/star-omen/src/video_pipeline/contracts/external_media_v1.py`
- Modify: `apps/star-omen/src/video_pipeline/contracts/__init__.py`
- Create: `apps/star-omen/tests/video_pipeline/external_media/helpers.py`
- Create: `apps/star-omen/tests/video_pipeline/external_media/test_external_media_contracts_v1.py`

- [x] **Step 1: Write RED model tests**

Require immutable source/work identity, UTC capture metadata, capture hashes,
exact claim spans, human identity for reviewed records, unique IDs and research-only audit flags.

- [x] **Step 2: Run the focused tests and verify RED**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/external_media/test_external_media_contracts_v1.py -q`
Expected: import failure because the four contracts do not exist.

- [x] **Step 3: Implement the minimal strict models**

Add `ExternalMediaSourceV1`, `ExternalClaimV1`, `EvidenceLinkV1`,
`ExternalAuditV1` and the nested capture/span/assessment records. Reject unknown
fields, non-UTC times, malformed hashes, duplicate IDs and review-state contradictions.

- [x] **Step 4: Run GREEN and commit**

Expected: focused model tests pass.

### Task 2: Enforce bundle cross-references and audit semantics

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/contracts/external_media_v1.py`
- Modify: `apps/star-omen/src/video_pipeline/contracts/__init__.py`
- Create: `apps/star-omen/tests/video_pipeline/external_media/test_external_audit_bundle_v1.py`

- [x] **Step 1: Write RED semantic tests**

Cover dangling source/claim/evidence IDs, claim spans bound to absent capture
hashes, unsupported `supported_exact`, uncontradicted `contradicted`, evidence on
`source_missing`, non-modern evidence on `modern_inference_only`, and incomplete
claim assessment coverage.

- [x] **Step 2: Implement `ExternalAuditBundleV1`**

Validate one source, its atomic claims/evidence links and one audit as a closed
research bundle. Keep evidence relationship separate from audit disposition.

- [x] **Step 3: Run mutation-oriented GREEN and commit**

Run the entire `tests/video_pipeline/external_media` suite and confirm each
prohibited semantic mutation fails independently.

### Task 3: Commit schemas, registry entries and canonical fixtures

**Files:**
- Create: `apps/star-omen/schemas/video_pipeline/v1/external-media-source.schema.json`
- Create: `apps/star-omen/schemas/video_pipeline/v1/external-claim.schema.json`
- Create: `apps/star-omen/schemas/video_pipeline/v1/evidence-link.schema.json`
- Create: `apps/star-omen/schemas/video_pipeline/v1/external-audit.schema.json`
- Create: `tests/fixtures/external-media/v1/*.valid.json`
- Create: `tests/fixtures/external-media/v1/manifest.json`
- Modify: `apps/star-omen/schemas/video_pipeline/schema-registry.json`
- Modify: `apps/star-omen/tests/video_pipeline/contracts/test_contract_compatibility_v1.py`
- Modify: `apps/star-omen/tests/video_pipeline/contracts/test_contract_fixture_assets_v1.py`

- [x] **Step 1: Write RED registry/fixture tests**

Require all seven top-level contracts in the registry, exact generated schemas,
one canonical/hash-bound fixture per new schema and no real creator claim in
synthetic contract fixtures.

- [x] **Step 2: Generate deterministic schemas and fixtures**

Use model JSON Schema and canonical contract bytes. The example domain and
`fixture:` IDs must make test-only provenance unambiguous.

- [x] **Step 3: Run contract/external-media tests and commit**

Expected: schemas, manifests, hashes, models and registry agree byte-for-byte.

### Task 4: Import the real 祖山觀 source set only after the source gate opens

**Files:**
- Future create: `apps/star-omen/data/video_pipeline/external_media/祖山觀/*.json`
- Future create: `tests/fixtures/external-media/祖山觀/*`

- [x] **Step 1: Resolve the exact creator/account locator**

Accept only a direct creator page, collection page or one direct work URL whose
account identity can be followed to the source collection. Search snippets and
same-name accounts do not satisfy this gate.

- [x] **Step 2: Capture the exact 23-work denominator and hashes**

Record immutable work IDs/URLs, publication timestamps, captured metadata/text
hashes, rights/capture notes and explicit missing states.

- [x] **Step 3: Audit nine priority works**

Split exact spans into atomic claims and link them to source-bound classical,
astronomical, historical or modern evidence. The 毕宿烈风/海上风暴 work is the
complete sample; no weather equivalence is inferred.

- [x] **Step 4: Verify, record and publish**

Run exact-head governance, full downstream, canonical hashes, compileall, scope
and forbidden-path gates. Publish only an exact-tree fast-forward to Draft #65.

## Current source gate

The gate opened on 2026-08-12 from user-supplied direct Douyin links. The
creator resolves to 祖山觀（無用之人）🌓 / `sec_uid`
`MS4wLjABAAAAAzgxglR-dz-mRK53rZNuTqMwh1HktiIHLXa-3ZSVXCH4zDH0xjcWCN8BKyQ3plyK`,
and the work resolves to the same account and collection
`7664842437629921326`. Freeze the approved denominator as collection episodes
1–23 even though the live collection now reports 40 episodes. Missing
transcripts, OCR or cited classical loci remain explicit rather than inferred.

## Plan self-review

- Placeholder scan: future source files are explicitly gated, not assumed to exist.
- Contract coverage: identity, captures, exact spans, evidence relationships,
  audit dispositions, review authority and cross-reference closure each have a test task.
- Scope: creator capture is isolated from contract implementation so missing
  platform access cannot weaken or contaminate the public v1 models.
