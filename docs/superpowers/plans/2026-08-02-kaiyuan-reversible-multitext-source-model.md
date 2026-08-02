# Kaiyuan Reversible Multi-text Source Model Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Build a tested, reversible research-only projection from the 16 fixed Wikisource accessions and 20 Core14 mappings into a WorkCandidate–TextVersionCandidate–Carrier–SourceObject graph without changing any source bytes, candidate/rule identity, human-review decision, or production schema.

**Architecture:** Layer A remains the immutable accession package already merged at stable commit 090f1b95d1c0b798077162408cea3d3bedd975a5. A strict compatibility loader joins the compact central manifest to the detailed per-family accession records by accession_id. Layer B is a deterministic, rebuildable shadow graph whose assertions carry explicit epistemic status. Layer C integration with RuleCandidate/OmenRule is forbidden in this plan and remains gated by B10-PR-F plus human approval.

**Tech Stack:** Python 3.11+, Pydantic v2, pathlib, hashlib, json, pytest, existing kb-contracts and apps/star-omen test conventions.

## Global Constraints

- Work only on branch codex/kaiyuan-b10-multitext-source-model-v1, based on stable/kaiyuan-v2 commit 090f1b95d1c0b798077162408cea3d3bedd975a5.
- Do not modify the 16 raw wikitext files, the 16 detailed accession records, accession-manifest.json, or core14-mapping.json.
- Do not access or write Qdrant or local_kb_default.
- Do not modify Reviewer A/B files or claim that AI output is human review.
- Do not start B10-PR-D, B10-PR-E, or B10-PR-F.
- Do not derive work identity from normalized-title equality.
- All unknown edition, carrier, genealogy, and independent-witness facts remain explicit unknown or deferred values.
- Every generated JSON file uses UTF-8, sorted keys, two-space indentation, and one terminal newline.
- Each task starts with a failing test, ends with a focused test run, and is committed before the next task starts.

---

## Task 1: Freeze the research-accession/v1 compatibility contract

**Files:**

- Create: packages/kb-contracts/python/kb_contracts/research_accession_v1.py
- Modify: packages/kb-contracts/python/kb_contracts/__init__.py
- Create: packages/kb-contracts/tests/test_research_accession_v1.py

- [ ] Step 1: Write failing contract tests

Create tests that instantiate one complete accession and assert all of these behaviors:

~~~python
from copy import deepcopy

import pytest
from pydantic import ValidationError

from kb_contracts import CaptureStatus, ResearchAccessionV1

BASE = {
    "schema_version": "research-accession/v1",
    "accession_id": "zhws-yisizhan-5-r854562",
    "family_id": "yisizhan",
    "work_printed": "乙巳占",
    "work_normalized_candidate": "乙巳占",
    "page_title": "乙巳占/5",
    "oldid": 854562,
    "permanent_url": "https://zh.wikisource.org/w/index.php?title=%E4%B9%99%E5%B7%B3%E5%8D%A0/5&oldid=854562",
    "floating_url": "https://zh.wikisource.org/wiki/%E4%B9%99%E5%B7%B3%E5%8D%A0/5",
    "revision_timestamp": "2017-04-16T03:54:43Z",
    "accessed_on": "2026-08-01",
    "locator": "卷五",
    "version_family": "Wikisource transcription; print edition unknown.",
    "author_or_compiler": "李淳風",
    "license_note": "CC BY-SA site metadata; ancient text separately public-domain.",
    "independent_witness_note": "No independent witness established.",
    "core14_cases": ["C09", "C13"],
    "relevant_excerpt": "火逆行氐，失地。",
    "excerpt_locator": "raw line 11",
    "raw_path": "corpus/research_sources/related-wikisource/p0/yisizhan/raw/yisizhan-5-oldid-854562.wikitext",
    "raw_sha256": "15d1774880be1178b7d61bdbcca45bedd9611fd60925e3e9b35c909cae435078",
    "raw_byte_count": 31158,
    "capture_status": "complete",
    "capture_note": "complete_separable_page_wikitext",
}

def test_complete_accession_is_frozen_and_canonical() -> None:
    item = ResearchAccessionV1.model_validate(BASE)
    assert item.capture_status is CaptureStatus.COMPLETE
    assert item.canonical_json_bytes() == item.canonical_json_bytes()
    with pytest.raises(ValidationError):
        item.oldid = 1

@pytest.mark.parametrize("field,value", [
    ("accession_id", "乙巳占"),
    ("oldid", 0),
    ("raw_sha256", "bad"),
    ("raw_byte_count", -1),
    ("core14_cases", ["C13", "C09"]),
])
def test_complete_accession_rejects_invalid_identity_or_order(field: str, value: object) -> None:
    payload = deepcopy(BASE)
    payload[field] = value
    with pytest.raises(ValidationError):
        ResearchAccessionV1.model_validate(payload)

def test_complete_accession_requires_oldid_in_permanent_url() -> None:
    payload = deepcopy(BASE)
    payload["permanent_url"] = "https://zh.wikisource.org/wiki/乙巳占/5"
    with pytest.raises(ValidationError):
        ResearchAccessionV1.model_validate(payload)

def test_partial_accession_requires_reason_and_forbids_fake_raw_object() -> None:
    payload = deepcopy(BASE)
    payload.update({
        "capture_status": "partial_with_reason",
        "failure_reason": "revision replay returned only a partial carrier page",
        "raw_path": None,
        "raw_sha256": None,
        "raw_byte_count": None,
    })
    item = ResearchAccessionV1.model_validate(payload)
    assert item.failure_reason
~~~

- [ ] Step 2: Run the test and confirm the import fails

Run:

~~~bash
PYTHONPATH=packages/kb-contracts/python pytest -q packages/kb-contracts/tests/test_research_accession_v1.py
~~~

Expected result: FAIL because research_accession_v1 and its exports do not exist.

- [ ] Step 3: Implement the smallest strict model

Implement:

- CaptureStatus values complete, unavailable, partial_with_reason.
- Frozen Pydantic model with extra fields forbidden.
- ASCII accession_id and family_id.
- oldid greater than zero for complete captures.
- lowercase 64-hex raw_sha256 and nonnegative raw_byte_count for complete captures.
- exact accession oldid present in permanent_url.
- sorted unique core14_cases matching C followed by two digits.
- repository-relative raw_path under corpus/research_sources/related-wikisource.
- failure_reason required for non-complete captures.
- canonical_json_bytes using model_dump(mode="json"), json.dumps with sort_keys=True, separators=(",", ":"), ensure_ascii=False, then UTF-8 encoding.
- Export CaptureStatus and ResearchAccessionV1 from kb_contracts.__init__.

Do not add any rule-approval, reviewer, production-ingest, normalized-text, or witness-independence boolean field.

- [ ] Step 4: Run focused and regression tests

Run:

~~~bash
PYTHONPATH=packages/kb-contracts/python pytest -q packages/kb-contracts/tests/test_research_accession_v1.py
make contracts-test
~~~

Expected result: both commands PASS.

- [ ] Step 5: Commit

~~~bash
git add packages/kb-contracts/python/kb_contracts/research_accession_v1.py packages/kb-contracts/python/kb_contracts/__init__.py packages/kb-contracts/tests/test_research_accession_v1.py
git commit -m "feat(contracts): add research accession v1"
~~~

## Task 2: Build the lossless Layer-A inventory loader

**Files:**

- Create: apps/star-omen/src/research_sources/__init__.py
- Create: apps/star-omen/src/research_sources/source_inventory.py
- Create: apps/star-omen/tests/research_sources/test_source_inventory.py

- [ ] Step 1: Write a failing test against the merged package

The test must load repository root corpus/research_sources/related-wikisource and assert:

~~~python
def test_inventory_joins_compact_manifest_to_detailed_records(repo_root):
    inventory = load_source_inventory(
        repo_root / "corpus/research_sources/related-wikisource"
    )
    assert len(inventory.accessions) == 16
    assert inventory.total_raw_byte_count == 645044
    assert inventory.accession_ids == tuple(sorted(inventory.accession_ids))
    assert inventory.get("zhws-yisizhan-5-r854562").family_id == "yisizhan"
    assert inventory.get("zhws-yisizhan-5-r854562").core14_cases == ("C09", "C13")
    assert inventory.get("zhws-houhanshu-100-r1753568").oldid == 1753568
~~~

Add negative tests using temporary copies for:

- a central accession without a detailed record;
- a detailed record without a central accession;
- mismatched oldid, raw path, SHA-256, byte count, or capture status;
- duplicate accession_id;
- a raw file whose actual SHA-256 or byte count differs;
- a central family count or total byte count that does not recompute.

- [ ] Step 2: Run and confirm the loader import fails

~~~bash
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q tests/research_sources/test_source_inventory.py
~~~

Expected result: FAIL because source_inventory does not exist.

- [ ] Step 3: Implement deterministic joining and replay validation

Implement SourceInventory as an immutable dataclass or frozen Pydantic model. load_source_inventory must:

1. Read accession-manifest.json.
2. Read every families[].accession_metadata_path.
3. Join compact and detailed records only by exact accession_id.
4. Add schema_version and family_id from the manifest side before ResearchAccessionV1 validation.
5. Require compact/detailed equality for page_title, oldid, raw_path, raw_sha256, raw_byte_count, and capture_status.
6. Read every complete raw_path as bytes and recompute SHA-256 and byte count.
7. Recompute family_count, accession_count, raw_file_count, and total_raw_byte_count.
8. Return records sorted by accession_id.
9. Raise SourceInventoryError with the accession_id and field name for every mismatch.
10. Never mutate or rewrite a source file.

- [ ] Step 4: Run focused tests and compile checks

~~~bash
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q tests/research_sources/test_source_inventory.py
python -m compileall -q src/research_sources
~~~

Expected result: PASS.

- [ ] Step 5: Commit

~~~bash
git add apps/star-omen/src/research_sources apps/star-omen/tests/research_sources/test_source_inventory.py
git commit -m "feat(research): load immutable source inventory"
~~~

## Task 3: Add the rebuildable Layer-B graph contract and projector

**Files:**

- Create: apps/star-omen/src/research_sources/source_graph.py
- Create: apps/star-omen/src/research_sources/projector.py
- Create: apps/star-omen/tests/research_sources/test_source_graph_v0.py
- Create: apps/star-omen/tests/research_sources/test_projector_roundtrip.py

- [ ] Step 1: Write failing graph-model tests

Cover these exact types and invariants:

- NodeKind: work_candidate, text_version_candidate, carrier, source_object.
- AssertionStatus: observed, hypothesized, accepted, rejected, deferred.
- SourceGraphNode with graph-local node_id, kind, printed_label, normalized_label_candidate, status, evidence_accession_ids, and notes.
- SourceGraphEdge with edge_id, source_node_id, target_node_id, relation_type, status, evidence_accession_ids, and notes.
- SourceGraphV0 with schema_version source-graph-pilot/v0, sorted unique nodes and edges, source_manifest_sha, source_mapping_sha, generated_from_accession_ids, generated_from_mapping_ids, pilot_case_ids, and forbidden_side_effects.

Tests must prove:

- normalized_label_candidate equality does not merge two node IDs;
- accepted and hypothesized are different serialized values;
- every edge endpoint exists;
- every evidence accession exists in generated_from_accession_ids;
- stable canonical JSON is independent of input ordering;
- unknown edition and unknown genealogy are represented by deferred assertions, not omitted;
- fields named rule_status, reviewer_decision, citation_eligible, canonical_text, or independent_witness are rejected as extras.

- [ ] Step 2: Write failing projector round-trip tests

Project the real Layer-A inventory plus core14-mapping.json and assert:

~~~python
assert projection.source_object_count == 16
assert projection.mapping_edge_count == 20
assert projection.generated_from_accession_ids == inventory.accession_ids
assert projection.generated_from_mapping_ids == tuple(
    f"B10-R03-M{number:02d}" for number in range(1, 21)
)
assert projection.pilot_case_ids == ("C14", "C45", "C47")
assert projection.unresolved_title_merges == ()
assert projection.unreviewed_independent_witness_assertions == ()
~~~

Also assert:

- C45 keeps 御坐 and 帝坐 evidence in distinct source objects within the same received-history family.
- C47 keeps 謀/誅 and 時/無時 as source-specific material variants.
- C14 keeps citation_source, material_variant, historical_note_parallel, and locator_support distinct.
- Deleting the generated graph and rebuilding it produces byte-identical canonical JSON.
- Hashes of every Layer-A JSON/raw file are unchanged before and after projection.
- Hashes of the current RuleCandidate/OmenRule fixture files are unchanged before and after projection.

- [ ] Step 3: Implement graph models

Use frozen Pydantic models with extra="forbid". Node and edge IDs must be deterministic ASCII slugs derived from accession IDs and mapping IDs, never from normalized-title equality. Validate sorted unique tuples and endpoint closure.

The graph is research-only. Do not import or instantiate RuleCandidateV2 or OmenRuleV2 in production code.

- [ ] Step 4: Implement the projector

project_source_graph(inventory, mapping_document, source_manifest_sha, source_mapping_sha) must:

1. Create one source_object node per accession.
2. Create graph-local work_candidate and text_version_candidate nodes using family_id as a reversible local grouping hint, with status deferred unless an explicit source note supports observed.
3. Create a carrier node per Wikisource fixed-revision source object.
4. Preserve each mapping as a distinct edge carrying mapping_id, relation_type, mapping_scope, target case/atom IDs, evidence locator, evidence excerpt, and research note.
5. Restrict pilot_case_ids to C14, C45, C47 while retaining all 20 source-to-case mapping edges for round-trip validation.
6. Emit explicit deferred assertions for edition identity, genealogy, and independent-witness status.
7. Sort all nodes, edges, IDs, case IDs, and evidence IDs.
8. Raise SourceProjectionError on orphan mappings, duplicate IDs, missing cases, or any attempt to set a production/human-review field.

- [ ] Step 5: Run focused tests

~~~bash
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q tests/research_sources/test_source_graph_v0.py tests/research_sources/test_projector_roundtrip.py
~~~

Expected result: PASS with 16 source objects, 20 mapping edges, and pilot cases C14/C45/C47.

- [ ] Step 6: Commit

~~~bash
git add apps/star-omen/src/research_sources/source_graph.py apps/star-omen/src/research_sources/projector.py apps/star-omen/tests/research_sources/test_source_graph_v0.py apps/star-omen/tests/research_sources/test_projector_roundtrip.py
git commit -m "feat(research): project reversible source graph"
~~~

## Task 4: Generate and independently verify the pilot artifact

**Files:**

- Create: scripts/build_b10_r04_source_graph.py
- Create: corpus/research_sources/related-wikisource/source-graph-pilot-v0.json
- Create: corpus/research_sources/related-wikisource/source-graph-pilot-report.json
- Create: docs/research/B10_R04_SOURCE_GRAPH_PILOT_REPORT.md
- Create: apps/star-omen/tests/research_sources/test_pilot_artifact.py

- [ ] Step 1: Write a failing artifact test

The test must read the committed graph and report and assert:

- schema version source-graph-pilot/v0;
- 16/16 accession IDs and 20/20 mapping IDs;
- source_manifest_sha equals SHA-256 of accession-manifest.json;
- source_mapping_sha equals SHA-256 of core14-mapping.json;
- every source-object raw SHA and byte count matches Layer A;
- every mapping target case and atom exists in the merged Core14 audit JSON;
- pilot cases are exactly C14, C45, C47;
- zero title-based merges;
- zero orphan nodes or edges;
- zero independent-witness assertions with status accepted;
- forbidden side effects all equal NOT_RUN;
- rebuilding with the script produces byte-identical JSON.

- [ ] Step 2: Run and confirm artifact absence fails

~~~bash
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q tests/research_sources/test_pilot_artifact.py
~~~

Expected result: FAIL because the artifact and builder do not exist.

- [ ] Step 3: Implement the deterministic builder

The script must accept only:

~~~bash
python scripts/build_b10_r04_source_graph.py --repo-root . --check
python scripts/build_b10_r04_source_graph.py --repo-root . --write
~~~

Behavior:

- --check builds in memory and fails if committed artifact bytes differ.
- --write writes only source-graph-pilot-v0.json and source-graph-pilot-report.json.
- Unknown CLI flags fail.
- The report records 16/16 replay, 20/20 round-trip, C14/C45/C47 case checks, zero title merges, zero accepted independent-witness assertions, Layer-A before/after hashes, and RuleCandidate/OmenRule fixture before/after hashes.
- No network access is allowed in the builder.

- [ ] Step 4: Generate artifacts and write the research report

Run:

~~~bash
PYTHONPATH=apps/star-omen/src:packages/kb-contracts/python:packages/kb-text-core/python python scripts/build_b10_r04_source_graph.py --repo-root . --write
~~~

Write B10_R04_SOURCE_GRAPH_PILOT_REPORT.md with these sections:

1. Scope and non-goals.
2. Immutable Layer-A denominator.
3. Selected A+B+C architecture.
4. C14 stress result.
5. C45 stress result.
6. C47 stress result.
7. Round-trip and hash evidence.
8. Explicit unknowns and deferred decisions.
9. Stage-gate result.
10. Next bounded acquisition batch: 15 fixed-revision accessions only after this pilot is reviewed.

The report must not claim a production schema, canonical edition, independent witness, human review, or formal rule approval.

- [ ] Step 5: Run artifact and focused tests

~~~bash
PYTHONPATH=apps/star-omen/src:packages/kb-contracts/python:packages/kb-text-core/python python scripts/build_b10_r04_source_graph.py --repo-root . --check
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q tests/research_sources/test_source_inventory.py tests/research_sources/test_source_graph_v0.py tests/research_sources/test_projector_roundtrip.py tests/research_sources/test_pilot_artifact.py
~~~

Expected result: PASS and no file changes after --check.

- [ ] Step 6: Commit

~~~bash
git add scripts/build_b10_r04_source_graph.py corpus/research_sources/related-wikisource/source-graph-pilot-v0.json corpus/research_sources/related-wikisource/source-graph-pilot-report.json docs/research/B10_R04_SOURCE_GRAPH_PILOT_REPORT.md apps/star-omen/tests/research_sources/test_pilot_artifact.py
git commit -m "feat(research): add B10 R04 source graph pilot"
~~~

## Task 5: Run full gates, record evidence, and open the Draft PR

**Files:**

- Modify: docs/development/TASKS.md
- Modify: docs/development/PROJECT_MEMORY.md
- Modify: docs/development/WORK_LOG.md
- Modify: docs/superpowers/plans/2026-08-02-kaiyuan-reversible-multitext-source-model.md
- Create: docs/research/b10-r04-reviews/final-branch-review.md

- [ ] Step 1: Run the complete verification suite

~~~bash
make contracts-test
make downstream-test
python scripts/check_development_governance.py
PYTHONPATH=apps/star-omen/src:packages/kb-contracts/python:packages/kb-text-core/python python scripts/build_b10_r04_source_graph.py --repo-root . --check
python -m compileall -q packages/kb-contracts/python apps/star-omen/src/research_sources scripts/build_b10_r04_source_graph.py
git diff --check
git status --short
~~~

Record exact commands, exit codes, and test counts. Any failure returns the task to IN_PROGRESS; do not edit the expected result to fit the failure.

- [ ] Step 2: Perform an independent branch review

Review every changed path against stable commit 090f1b95d1c0b798077162408cea3d3bedd975a5. The review must independently recompute:

- 16/16 raw SHA-256 and byte counts;
- 16/16 compact-to-detailed accession joins;
- 20/20 mapping round-trip;
- all graph endpoint and target closure;
- exact C14/C45/C47 distinctions;
- zero title-based identity merges;
- zero accepted independent-witness assertions;
- zero changes to Layer-A source bytes and metadata;
- zero changes to RuleCandidate/OmenRule fixtures;
- zero Qdrant/local_kb_default access;
- zero Reviewer A/B changes;
- no start of B10-PR-D/E/F.

Write Critical, Important, and Minor counts plus Ready: YES or NO to final-branch-review.md. Any Critical or Important finding must be fixed and re-reviewed before proceeding.

- [ ] Step 3: Update governance documents

After review reaches Critical 0 / Important 0:

- Mark B10-R04 as VERIFYING, not DONE.
- Record the exact branch head, review result, gate commands, and NOT_RUN safety fields in WORK_LOG.md.
- Update PROJECT_MEMORY.md to identify the Draft PR and state that production schema and 15-accession expansion remain pending.
- Check every completed checkbox in this plan. Leave the final merge checkbox unchecked.
- Do not mark B10-PR-D/E/F started.

- [ ] Step 4: Commit completion evidence

~~~bash
git add docs/development/TASKS.md docs/development/PROJECT_MEMORY.md docs/development/WORK_LOG.md docs/superpowers/plans/2026-08-02-kaiyuan-reversible-multitext-source-model.md docs/research/b10-r04-reviews/final-branch-review.md
git commit -m "docs(research): verify B10 R04 source graph pilot"
~~~

- [ ] Step 5: Open a Draft PR to stable/kaiyuan-v2

Title:

B10-R04: pilot reversible multi-text source graph

The PR body must include:

- exact stable base SHA 090f1b95d1c0b798077162408cea3d3bedd975a5;
- 16 accessions, 20 mappings, pilot cases C14/C45/C47;
- commands and test counts;
- independent review result;
- explicit statement that production schema, 15-accession acquisition, human review, official KB ingest, Qdrant, and local_kb_default are not run.

Do not mark the PR ready or merge it in this task.

- [ ] Step 6: Verify the remote Draft PR

Confirm:

- base branch is stable/kaiyuan-v2;
- head branch is codex/kaiyuan-b10-multitext-source-model-v1;
- Draft is true;
- changed paths are limited to contracts, research-source code/tests, generated research artifacts, report/spec/plan, and governance logs;
- all required GitHub Actions pass;
- review threads and formal reviews are zero or resolved;
- remote file contents and artifact hashes match the reviewed head.

Record the PR number and workflow run IDs in WORK_LOG.md in one final documentation-only commit. Rerun Development Governance for that exact head. Keep B10-R04 at VERIFYING until the user authorizes merge or the project workflow explicitly permits the recommended merge step.
