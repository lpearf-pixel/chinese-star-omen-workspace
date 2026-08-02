# Kaiyuan Reversible Multi-text Source Model Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Build a tested, reversible research-only projection from the 16 fixed Wikisource accessions and 20 Core14 mappings into a WorkCandidate–TextVersionCandidate–Carrier–SourceObject graph without changing any source bytes, candidate/rule identity, human-review decision, or production schema.

**Architecture:** Layer A remains the immutable accession package already merged at stable commit 090f1b95d1c0b798077162408cea3d3bedd975a5. A strict compatibility loader joins the compact central manifest to the detailed per-family accession records by accession_id. Layer B contains two separate deterministic sidecars: a four-layer bibliographic graph and research evidence links to Core14; a compatibility projector must reconstruct the central manifest and mapping without rereading either original JSON document. Layer C integration with RuleCandidate/OmenRule is forbidden in this plan and remains gated by B10-PR-F plus human approval.

**Tech Stack:** Python 3.11+, Pydantic v2, pathlib, hashlib, json, pytest, existing kb-contracts and apps/star-omen test conventions.

## Global Constraints

- Work only on branch codex/kaiyuan-b10-multitext-source-model-v1, based on stable/kaiyuan-v2 commit 090f1b95d1c0b798077162408cea3d3bedd975a5.
- Do not modify the 16 raw wikitext files, the 16 detailed accession records, accession-manifest.json, or core14-mapping.json.
- Do not access or write Qdrant or local_kb_default.
- Do not modify Reviewer A/B files or claim that AI output is human review.
- Do not start B10-PR-D, B10-PR-E, or B10-PR-F.
- Do not derive work identity from normalized-title equality.
- Treat work_normalized_candidate, version_family, independent_witness_note, and uncertain author_or_compiler strings as compatibility-preserved legacy hypotheses, never as authoritative preservation facts.
- All unknown edition, carrier, genealogy, and independent-witness facts remain explicit unknown or deferred values.
- Every generated JSON file uses UTF-8, sorted keys, two-space indentation, and one terminal newline.
- Each task starts with a failing test, ends with a focused test run, and is committed before the next task starts.

---

## Task 1: Freeze the research-accession/v1 compatibility contract

**Files:**

- Create: packages/kb-contracts/python/kb_contracts/research_accession_v1.py
- Modify: packages/kb-contracts/python/kb_contracts/__init__.py
- Create: packages/kb-contracts/tests/test_research_accession_v1.py

- [x] Step 1: Write failing contract tests

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

- [x] Step 2: Run the test and confirm the import fails

Run:

~~~bash
PYTHONPATH=packages/kb-contracts/python pytest -q packages/kb-contracts/tests/test_research_accession_v1.py
~~~

Expected result: FAIL because research_accession_v1 and its exports do not exist.

- [x] Step 3: Implement the smallest strict model

Implement:

- CaptureStatus values complete, unavailable, partial_with_reason.
- Frozen Pydantic model with extra fields forbidden.
- ASCII accession_id and family_id.
- oldid greater than zero for complete captures.
- lowercase 64-hex raw_sha256 and nonnegative raw_byte_count for complete captures.
- exact accession oldid present in permanent_url.
- sorted unique core14_cases matching C followed by two digits.
- repository-relative raw_path under corpus/research_sources/related-wikisource.
- complete requires oldid, one HTTPS permanent_url with exactly one matching oldid query value, revision_timestamp, and the complete raw identity triple; failure_reason must be absent.
- unavailable requires failure_reason and forbids the raw identity triple; oldid/permanent_url/revision_timestamp may be absent.
- partial_with_reason requires failure_reason and permits the raw identity triple only when all three raw fields are present; half-present raw identity is forbidden.
- canonical_json_bytes using model_dump(mode="json"), json.dumps with sort_keys=True, separators=(",", ":"), ensure_ascii=False, then UTF-8 encoding.
- Export CaptureStatus and ResearchAccessionV1 from kb_contracts.__init__.

Do not add any rule-approval, reviewer, production-ingest, normalized-text, or witness-independence boolean field.

- [x] Step 4: Run focused and regression tests

Run:

~~~bash
PYTHONPATH=packages/kb-contracts/python pytest -q packages/kb-contracts/tests/test_research_accession_v1.py
make contracts-test
~~~

Expected result: both commands PASS.

- [x] Step 5: Commit

~~~bash
git add packages/kb-contracts/python/kb_contracts/research_accession_v1.py packages/kb-contracts/python/kb_contracts/__init__.py packages/kb-contracts/tests/test_research_accession_v1.py
git commit -m "feat(contracts): add research accession v1"
~~~

## Task 2: Build the lossless Layer-A inventory loader

**Files:**

- Create: apps/star-omen/src/research_sources/__init__.py
- Create: apps/star-omen/src/research_sources/source_inventory.py
- Create: apps/star-omen/tests/research_sources/test_source_inventory.py

- [x] Step 1: Write a failing test against the merged package

Define the repository root inside the test file; do not assume a global fixture:

~~~python
from pathlib import Path

import pytest

from research_sources import load_source_inventory

@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]

def test_inventory_joins_compact_manifest_to_detailed_records(repo_root: Path):
    inventory = load_source_inventory(repo_root)
    assert len(inventory.accessions) == 16
    assert inventory.family_count == 7
    assert inventory.raw_file_count == 16
    assert inventory.total_raw_byte_count == 645044
    assert inventory.accession_ids == tuple(sorted(inventory.accession_ids))
    assert inventory.get("zhws-yisizhan-5-r854562").family_id == "yisizhan"
    assert inventory.get("zhws-yisizhan-5-r854562").core14_cases == ("C09", "C13")
    assert inventory.get("zhws-houhanshu-100-r1753568").oldid == 1753568
~~~

Add negative tests using complete temporary repositories rooted at tmp/repo for:

- a central accession without a detailed record;
- a detailed record without a central accession;
- mismatched oldid, raw path, SHA-256, byte count, or capture status;
- duplicate accession_id within or across families;
- a compact accession whose family_id differs from its detailed container;
- a raw file whose actual SHA-256 or byte count differs;
- a central family count, accession count, raw count, family count, or total byte count that does not recompute;
- complete with failure_reason, unavailable with any raw field, partial with a half-present raw triple, and partial with a complete raw triple whose bytes/hash/count must replay;
- wrong, duplicate, non-HTTPS, wrong-host, userinfo-bearing, or page-title-mismatched Wikisource URLs;
- absolute, traversal, and symlink escape in metadata or raw paths;
- malformed JSON and non-array family metadata;
- before/after hashes proving the loader is read-only.

- [x] Step 2: Run the test and confirm the loader import fails

~~~bash
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q tests/research_sources/test_source_inventory.py
~~~

Expected result: FAIL because research_sources.source_inventory does not exist.

- [x] Step 3: Implement deterministic joining and replay validation

Expose:

~~~python
class SourceInventoryError(ValueError):
    code: str
    accession_id: str
    field: str
    expected: object
    actual: object

@dataclass(frozen=True, slots=True)
class SourceInventory:
    accessions: tuple[ResearchAccessionV1, ...]
    family_count: int
    raw_file_count: int
    total_raw_byte_count: int

    @property
    def accession_ids(self) -> tuple[str, ...]: ...
    def get(self, accession_id: str) -> ResearchAccessionV1: ...

def load_source_inventory(repo_root: Path) -> SourceInventory: ...
~~~

load_source_inventory must:

1. Resolve package_root as repo_root/corpus/research_sources/related-wikisource.
2. Read accession-manifest.json.
3. Resolve every repository-relative metadata and raw path against repo_root, then require the resolved target to remain beneath package_root; reject absolute paths, traversal, and symlink escape.
4. Reject duplicate family IDs, metadata paths, compact IDs, detailed IDs, and raw paths.
5. Read every families[].accession_metadata_path and record the containing family_id.
6. Require exact equality of compact and detailed accession ID sets.
7. Require compact/detailed equality for page_title, oldid, raw_path, raw_sha256, raw_byte_count, and capture_status.
8. Add schema_version and family_id before ResearchAccessionV1 validation.
9. For every accession with a raw identity triple, regardless of capture_status, read raw_path as bytes and recompute SHA-256 and byte count.
10. Recompute every family accession_count plus manifest family_count and accession_count; raw_file_count counts every accession with raw_path, and total_raw_byte_count sums every accession with raw_byte_count.
11. Return records sorted by accession_id.
12. Never mutate or rewrite any source file.

Use deterministic messages:

source-inventory[{code}] accession_id='{id}' field='{field}' expected={expected!r} actual={actual!r}

Messages must use repository-relative paths and must not expose machine-absolute paths.

- [x] Step 4: Run focused tests and compile checks

~~~bash
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q tests/research_sources/test_source_inventory.py
python -m compileall -q src/research_sources
~~~

Expected result: PASS.

- [x] Step 5: Commit

~~~bash
git add apps/star-omen/src/research_sources apps/star-omen/tests/research_sources/test_source_inventory.py
git commit -m "feat(research): load immutable source inventory"
~~~

## Task 3: Add the rebuildable Layer-B bibliography, evidence links, and true round-trip projector

**Files:**

- Create: apps/star-omen/src/research_sources/core14_index.py
- Create: apps/star-omen/src/research_sources/source_graph.py
- Create: apps/star-omen/src/research_sources/projector.py
- Create: apps/star-omen/tests/research_sources/test_source_graph_v0.py
- Create: apps/star-omen/tests/research_sources/test_projector_roundtrip.py

- [x] Step 1: Write failing model tests

Define these separate contracts:

- NodeKind: work_candidate, text_version_candidate, carrier, source_object.
- AssertionStatus: observed, hypothesized, deferred. This pilot does not implement accepted or rejected research decisions.
- SourceGraphNodeV0 for graph-local identity only.
- SourceGraphEdgeV0 for bibliographic relations whose endpoints are both graph nodes.
- ResearchAssertionV0 with assertion_id, subject_node_id, predicate, value, status, confidence_level (unknown, low, medium, high), confidence_note, supporting_accession_ids, contradicting_accession_ids, rationale, and verification_method.
- ResearchEvidenceLinkV0 with every per-mapping key: mapping_id, direction, source_accession_id, source_object_id, target_case_id, target_atom_ids, relation_type, mapping_scope, evidence_locator, evidence_excerpt, target_whole_row_citation_eligible, research_note, status, confidence_level, confidence_note, supporting_accession_ids, and contradicting_accession_ids. The legacy target_whole_row_citation_eligible value is compatibility-preserved research data, not formal approval.
- SourceObjectRefV0 with the compact manifest accession fields needed for reverse projection.
- SourcePackageMetadataV0 with every non-accession central-manifest field and family descriptor needed for reverse projection.
- MappingPackageMetadataV0 with every top-level mapping field other than mappings, including mapping_id, status, access_date, direction, relation_types, and scope_note.
- Core14TargetIndexV0 with unique case IDs, unique atom IDs, three audit file SHA-256 values, and the b10-core14 accession-manifest SHA-256.
- SourceProjectionBundleV0 containing the bibliographic graph, assertions, source objects, package metadata, evidence links, source document hashes, pilot case IDs, and forbidden side effects.

Tests must prove:

- normalized-title candidate equality does not merge two work_candidate node IDs;
- observed, hypothesized, and deferred serialize distinctly;
- every bibliographic edge endpoint exists;
- every assertion subject exists;
- every evidence link points to a source_object and a known generated accession;
- every input mapping object and reverse-projected mapping object have identical key sets, including direction and target_whole_row_citation_eligible;
- stable canonical JSON is independent of input ordering;
- unknown edition, genealogy, and independent-witness state are explicit deferred assertions;
- printed labels are observations while normalized candidates remain hypothesized or deferred;
- fields named rule_status, reviewer_decision, citation_eligible, canonical_text, or independent_witness are rejected as extras.

- [x] Step 2: Write failing projector and reverse-projector tests

Load Core14TargetIndexV0 from the repository and project the real Layer-A inventory plus core14-mapping.json and assert:

~~~python
assert bundle.source_object_count == 16
assert bundle.evidence_link_count == 20
assert bundle.generated_from_accession_ids == inventory.accession_ids
assert bundle.generated_from_mapping_ids == tuple(
    f"B10-R03-M{number:02d}" for number in range(1, 21)
)
assert bundle.pilot_case_ids == ("C14", "C45", "C47")
assert bundle.title_based_merges == ()
assert bundle.accepted_independent_witness_assertions == ()
assert bundle.deferred_independent_witness_assertion_count > 0
~~~

The test must load the expected manifest and mapping once, construct the bundle, discard the original input objects, then call:

~~~python
projection = project_compatibility(bundle)
assert projection.manifest_document == expected_manifest
assert projection.mapping_document == expected_mapping
~~~

project_compatibility accepts only SourceProjectionBundleV0. It must not accept a path, inventory, original manifest, or original mapping and must not perform file reads. This is the B→A proof.

Also assert:

- C45 keeps 御坐 and 帝坐 in distinct source objects within one received-history family.
- C47 keeps 謀/誅 and 時/無時 as source-specific evidence.
- C14 keeps citation_source, material_variant, historical_note_parallel, and locator_support distinct.
- Carrier identity is provider plus floating page identity/page_title and never includes oldid; multiple revisions of the same page can share one carrier.
- SourceObject identity remains accession/oldid-bound.
- Deleting generated bytes and rebuilding produces byte-identical canonical bytes.
- Hashes of every Layer-A JSON/raw file remain unchanged.
- Hashes of current RuleCandidate/OmenRule fixtures remain unchanged.
- load_core14_target_index(repo_root) loads exactly corpus/research_sources/b10-core14/audit-early.json, audit-middle.json, and audit-late.json, recomputes the SHA-256 values declared by b10-core14/accession-manifest.json, binds the accession-manifest SHA itself, and rejects duplicate case or atom IDs.

- [x] Step 3: Implement strict bibliography and evidence contracts

Use frozen Pydantic models with extra="forbid". Bibliographic node and edge IDs must be deterministic ASCII slugs. Carrier IDs derive from provider plus page_title/floating identity and exclude oldid. SourceObject IDs derive from accession IDs. Work and TextVersion candidates use graph-local IDs and never merge on normalized-title equality.

ResearchAssertionV0 preserves supporting and contradicting evidence separately and requires a non-empty confidence_note; confidence_level is descriptive research metadata and never a promotion threshold. Existing legacy work_normalized_candidate, version_family, independent_witness_note, and uncertain author_or_compiler strings enter assertions only as hypothesized or deferred compatibility evidence; their mere presence never creates an observed fact.

ResearchEvidenceLinkV0 is not a bibliographic edge. It preserves every original mapping key required for exact reverse projection, including direction and target_whole_row_citation_eligible, while keeping formal approval semantics forbidden. No accepted/rejected decision record exists in pilot-v0.

load_core14_target_index(repo_root) is the only path-aware Core14 loader. project_source_bundle receives the resulting immutable Core14TargetIndexV0 explicitly and never infers paths from CWD.

- [x] Step 4: Implement both directions

project_source_bundle(inventory, manifest_document, mapping_document, source_manifest_sha, source_mapping_sha, core14_index) must:

1. Create one SourceObjectRefV0 and one source_object node per accession.
2. Create/reuse carrier nodes by provider plus page identity, excluding oldid.
3. Create graph-local work_candidate and text_version_candidate nodes using family_id only as a reversible local grouping hint.
4. Create bibliographic edges only among four-layer nodes.
5. Preserve each Core14 mapping as a distinct ResearchEvidenceLinkV0 with every source field needed for exact reconstruction.
6. Emit deferred assertions for edition identity, genealogy, and independent-witness state.
7. Preserve every central manifest header/family field in SourcePackageMetadataV0 and every mapping header field in MappingPackageMetadataV0, including mapping_id and status.
8. Sort every collection deterministically.
9. Verify every evidence-link case and atom through the explicit Core14TargetIndexV0 and bind the index input hashes into the bundle.
10. Raise SourceProjectionError on orphans, duplicates, missing targets, title-based merging, key-set loss, or production/human-review fields.

project_compatibility(bundle) must reconstruct accession-manifest.json and core14-mapping.json as in-memory JSON objects from the bundle alone. It must not read files. Canonical JSON equality and identical recursive object-key sets with the original objects are the round-trip gates.

- [x] Step 5: Run focused tests

~~~bash
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q tests/research_sources/test_source_graph_v0.py tests/research_sources/test_projector_roundtrip.py
~~~

Expected result: PASS with 16 source objects, 20 evidence links, exact reverse projection, and pilot cases C14/C45/C47.

- [x] Step 6: Commit

~~~bash
git add apps/star-omen/src/research_sources apps/star-omen/tests/research_sources/test_source_graph_v0.py apps/star-omen/tests/research_sources/test_projector_roundtrip.py
git commit -m "feat(research): project reversible source bundle"
~~~

## Task 4: Generate and independently verify the pilot artifact

**Files:**

- Create: scripts/build_b10_r04_source_projection.py
- Create: corpus/research_sources/related-wikisource/source-projection-pilot-v0.json
- Create: docs/research/B10_R04_SOURCE_GRAPH_PILOT_REPORT.md
- Create: apps/star-omen/tests/research_sources/test_pilot_artifact.py

- [x] Step 1: Write a failing artifact test

The test must read the committed bundle and report and assert:

- schema version source-projection-bundle/pilot-v0;
- 16/16 accession IDs and 20/20 mapping IDs;
- source_manifest_sha equals SHA-256 of accession-manifest.json;
- source_mapping_sha equals SHA-256 of core14-mapping.json;
- every source-object raw SHA and byte count matches Layer A;
- every mapping target exists in the three verified Core14 audit files;
- pilot cases are exactly C14, C45, C47;
- zero title-based merges;
- zero orphan graph nodes, graph edges, assertions, or evidence links;
- zero accepted independent-witness assertions and a positive deferred count;
- forbidden side effects all equal NOT_RUN;
- the embedded validation_report contains the replay, reverse-projection, pilot-case, deferred, hash, and forbidden-side-effect evidence;
- project_compatibility(bundle) reconstructs both original JSON documents without file reads;
- rebuilding produces byte-identical canonical bytes.

- [x] Step 2: Run and confirm artifact absence fails

~~~bash
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q tests/research_sources/test_pilot_artifact.py
~~~

Expected result: FAIL because the artifact and builder do not exist.

- [x] Step 3: Implement a deterministic no-overwrite builder

The script accepts only:

~~~bash
python scripts/build_b10_r04_source_projection.py --repo-root . --check
python scripts/build_b10_r04_source_projection.py --repo-root . --write-new
~~~

Behavior:

- --check builds in memory and fails if committed artifact bytes differ.
- --write-new creates only source-projection-pilot-v0.json and fails if it already exists.
- The bundle contains an embedded validation_report; no sibling JSON report is published.
- Publication writes and fsyncs a temporary sibling, then uses an exclusive same-filesystem hard link to create the final path without overwrite and unlinks the temporary name. On any failure, remove only the temporary path; never remove or replace a pre-existing final artifact.
- Unknown CLI flags fail.
- canonical_hash_bytes uses compact sorted JSON; artifact_file_bytes uses sorted keys, two-space indentation, UTF-8, and one terminal newline.
- The embedded validation_report records 16/16 replay, 20/20 reverse projection, C14/C45/C47 checks, zero title merges, zero accepted independent-witness assertions, positive deferred count, Core14 index hashes, Layer-A before/after hashes, and RuleCandidate/OmenRule fixture before/after hashes.
- Tests cover an existing final target and a concurrent final-path placeholder and prove no partial final artifact is left or overwritten.
- No network access is allowed.

- [x] Step 4: Generate artifacts and write the research report

Run once:

~~~bash
PYTHONPATH=apps/star-omen/src:packages/kb-contracts/python:packages/kb-text-core/python python scripts/build_b10_r04_source_projection.py --repo-root . --write-new
~~~

Write B10_R04_SOURCE_GRAPH_PILOT_REPORT.md with these sections:

1. Scope and non-goals.
2. Immutable Layer-A denominator.
3. A preservation plus B pilot implemented; C remains deferred.
4. C14 stress result.
5. C45 stress result.
6. C47 stress result.
7. True B→A reverse projection and hash evidence.
8. Explicit unknowns and deferred decisions.
9. Stage-gate result.
10. Next bounded acquisition batch: 15 fixed-revision accessions only after review.

The report must not claim a production schema, canonical edition, independent witness, human review, formal rule approval, or implemented Layer C.

- [x] Step 5: Run artifact and focused tests

~~~bash
PYTHONPATH=apps/star-omen/src:packages/kb-contracts/python:packages/kb-text-core/python python scripts/build_b10_r04_source_projection.py --repo-root . --check
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q tests/research_sources/test_source_inventory.py tests/research_sources/test_source_graph_v0.py tests/research_sources/test_projector_roundtrip.py tests/research_sources/test_pilot_artifact.py
~~~

Expected result: PASS and no file changes after --check.

- [x] Step 6: Commit

~~~bash
git add scripts/build_b10_r04_source_projection.py corpus/research_sources/related-wikisource/source-projection-pilot-v0.json docs/research/B10_R04_SOURCE_GRAPH_PILOT_REPORT.md apps/star-omen/tests/research_sources/test_pilot_artifact.py
git commit -m "feat(research): add B10 R04 source projection pilot"
~~~

## Task 5: Run full gates, bind review to the intended head, and open the Draft PR

**Files:**

- Modify: docs/development/TASKS.md
- Modify: docs/development/PROJECT_MEMORY.md
- Modify: docs/development/WORK_LOG.md
- Modify: docs/superpowers/plans/2026-08-02-kaiyuan-reversible-multitext-source-model.md
- Create: docs/research/b10-r04-reviews/final-branch-review.md

- [x] Step 1: Enter VERIFYING before final gates

- Mark B10-R04 as VERIFYING, not DONE.
- Record the completed implementation scope and all NOT_RUN safety fields in WORK_LOG.md.
- Update PROJECT_MEMORY.md to state that production schema and 15-accession expansion remain pending.
- Check completed plan boxes through Task 4.
- Commit all implementation, artifacts, report, and governance state before independent review.

- [ ] Step 2: Run the complete suite on the intended implementation head

~~~bash
make contracts-test
make downstream-test
python scripts/check_development_governance.py
PYTHONPATH=apps/star-omen/src:packages/kb-contracts/python:packages/kb-text-core/python python scripts/build_b10_r04_source_projection.py --repo-root . --check
python -m compileall -q packages/kb-contracts/python apps/star-omen/src/research_sources scripts/build_b10_r04_source_projection.py
git diff --check
git status --short
~~~

Record the exact implementation commit SHA, commands, exit codes, and test counts. Any failure returns B10-R04 to IN_PROGRESS.

- [ ] Step 3: Perform an independent review of that exact implementation SHA

Independently recompute:

- 16/16 raw SHA-256 and byte counts;
- 16/16 compact-to-detailed joins;
- 20/20 true reverse projection without reading original manifest/mapping;
- all graph endpoint, assertion subject, evidence-link source, case, and atom closure;
- exact C14/C45/C47 distinctions;
- carrier IDs independent of oldid;
- zero title-based identity merges;
- zero accepted independent-witness assertions and explicit deferred count;
- zero Layer-A source/metadata changes;
- zero RuleCandidate/OmenRule fixture changes;
- zero Qdrant/local_kb_default access;
- zero Reviewer A/B changes;
- no start of B10-PR-D/E/F.

Write the reviewed implementation SHA, Critical/Important/Minor counts, and Ready: YES or NO to final-branch-review.md. Fix and repeat until Critical 0 / Important 0.

- [ ] Step 4: Commit the immutable review record and governance evidence

Commit only the review record and governance documents:

~~~bash
git add docs/development/TASKS.md docs/development/PROJECT_MEMORY.md docs/development/WORK_LOG.md docs/superpowers/plans/2026-08-02-kaiyuan-reversible-multitext-source-model.md docs/research/b10-r04-reviews/final-branch-review.md
git commit -m "docs(research): verify B10 R04 source projection pilot"
~~~

The review record binds the immediately preceding implementation SHA. After this commit, no source, test, artifact, or report file may change without a new full review.

- [ ] Step 5: Open a Draft PR to stable/kaiyuan-v2

Title:

B10-R04: pilot reversible multi-text source projection

The PR body must include the exact stable base SHA, reviewed implementation SHA, final docs-only head SHA, 16 accessions, 20 evidence links, C14/C45/C47, gate commands/test counts, review result, and explicit NOT_RUN statements. Do not mark ready or merge.

- [ ] Step 6: Verify and annotate the exact final PR head without further branch commits

Confirm:

- base stable/kaiyuan-v2 and expected feature head;
- Draft true;
- changed paths remain within contracts, research-source code/tests, research artifacts, report/spec/plan, and governance logs;
- all required GitHub Actions pass for the exact final head;
- review threads and formal reviews are zero or resolved;
- remote file contents and artifact hashes match;
- compare the final docs-only commit to the reviewed implementation SHA and verify it changes only the five review/governance paths;
- independently confirm those five files do not alter scope, the reviewed implementation SHA, NOT_RUN boundaries, recorded commands, test counts, or review conclusion.

Add a top-level PR comment recording the exact final head SHA, workflow run IDs, targeted docs-only re-review result, and Ready-for-user-review status. Do not mutate the branch after that comment. Keep B10-R04 at VERIFYING until the user authorizes merge or project workflow explicitly permits the recommended merge step.
