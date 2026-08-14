# Kaiyuan Twenty-eight Mansion Membership and Lines Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 27 defining-star-only shells with source-bound member and line identities for every lunar mansion while preserving explicit uncertainty and the existing 毕宿 gold sample.

**Architecture:** Filter the exact 28 named asterisms from pinned Stellarium `index.json` and their base fixed-name records from `star_names.zh_CN.fab`, then bind every referenced HIP object to CDS VizieR I/239 coordinates at J1991.25. The catalog adds a generic `complete` state for fully verified member sets, retains `complete_gold_sample` for 毕宿, and keeps 翼宿 `ambiguous`; member-proximity evaluation accepts only the two complete states.

**Tech Stack:** Python 3.12, Pydantic v2, PyYAML, Skyfield 1.51, pytest, canonical JSON fixtures, pinned Stellarium commit `3972e97101e4321079279b5e5660b074fafc030a`, CDS VizieR Hipparcos I/239.

## Global Constraints

- Base remains `stable/kaiyuan-v2@c2e8fcabb04354fd14d0c72b3b6020a47e63a583`; delivery updates Draft PR #65 only.
- Preserve the Phase 1 毕宿 gold sample, Phase 2 closed region cycle, and existing Spica/SIMBAD J2000 identity.
- Hipparcos I/239 coordinates use ICRS J1991.25 with both proper-motion components.
- Membership comes only from exact fixed-name records; line geometry never invents membership.
- Line endpoints outside the named mansion member set are `related_object_ids`, not extra members.
- Stellarium status-2 names remain `ambiguous`; no uncertain identity is promoted to verified.
- `临/臨` remains ambiguous; no single-time result emits `犯`, `入`, `守` or `留`.
- Do not modify raw corpus, Reviewer A/B, PR #54/#64, Qdrant, `local_kb_default`, workflows, B11/B12 or `main`.
- Routine Draft publication does not run Runner and does not merge.

---

### Task 1: Bind the all-mansion source denominator

**Files:**
- Create: `apps/star-omen/data/video_pipeline/sources/stellarium_28_mansion_member_names_v1.json`
- Create: `apps/star-omen/data/video_pipeline/sources/stellarium_28_mansion_lines_v1.json`
- Create: `apps/star-omen/data/video_pipeline/sources/hipparcos_28_mansion_members_v1.json`
- Create: `tests/fixtures/asterisms/v1/lunar-mansion-membership-lines.json`
- Modify: `tests/fixtures/asterisms/v1/manifest.json`
- Modify: `apps/star-omen/tests/video_pipeline/asterisms/test_asterism_source_assets_v1.py`

**Interfaces:**
- Consumes: pinned Stellarium blobs `14eea850...` and `fe876157...`; VizieR `I/239/hip_main`.
- Produces: separate canonical fixed-name and line inventories, 162 unique HIP coordinate records, and a fixture binding 157 members, five related endpoints and 57 lines.

- [x] **Step 1: Write failing source-denominator tests**

```python
def test_all_mansion_member_sources_bind_exact_denominators() -> None:
    names = load_json_source("source:stellarium-28-mansion-member-names")
    lines = load_json_source("source:stellarium-28-mansion-lines")
    coordinates = load_json_source("source:hipparcos-i-239-mansion-members")
    assert len(names["mansion_records"]) == len(lines["mansion_records"]) == 28
    assert sum(len(item["member_records"]) for item in names["mansion_records"]) == 157
    assert sum(len(item["line_segments"]) for item in lines["mansion_records"]) == 57
    assert len(coordinates["records"]) == 162
```

This test catches a missing mansion, dropped fixed-name member, cross-asterism endpoint misclassified as a member, missing line, or incomplete coordinate denominator. Expected values are literal source-audit totals rather than values derived by the catalog loader.

- [x] **Step 2: Run the source test and verify RED**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms/test_asterism_source_assets_v1.py -q`
Expected: fail because the two source IDs, snapshots and fourth fixture do not exist.

- [x] **Step 3: Add canonical pinned snapshots and fixture**

Store exact native names, fixed-name status, ordered member HIP IDs and related HIP IDs in the fixed-name snapshot; store ordered line segments in the separate `index.json` snapshot. Bind each snapshot to its one exact upstream blob ID and omit query timestamps so canonical bytes are stable. Store I/239 RA, Dec, `pmRA*cos(dec)` and `pmDE` for all 162 unique HIP IDs.

- [x] **Step 4: Run source tests and verify GREEN**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms/test_asterism_source_assets_v1.py -q`
Expected: all source and fixture tests pass with four manifest entries.

- [x] **Step 5: Commit**

```bash
git add apps/star-omen/data/video_pipeline/sources \
  apps/star-omen/tests/video_pipeline/asterisms/test_asterism_source_assets_v1.py \
  tests/fixtures/asterisms/v1
git commit -m "data: bind all mansion members and lines"
```

### Task 2: Promote exact asterism definitions and preserve uncertainty

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/asterisms/catalog.py`
- Modify: `apps/star-omen/data/video_pipeline/asterism_catalog_v1.yaml`
- Modify: `apps/star-omen/tests/video_pipeline/asterisms/test_asterism_catalog_v1.py`

**Interfaces:**
- Consumes: Task 1 source snapshots and fixture.
- Produces: `AsterismDefinitionV1.completeness_status` values `partial | complete | complete_gold_sample | ambiguous`; catalog denominator `162 entries / 28 asterisms / 28 lunar_mansions`.

- [x] **Step 1: Write failing catalog behavior tests**

```python
def test_catalog_exposes_complete_members_and_related_lines() -> None:
    catalog = load_catalog()
    assert catalog.asterism("角宿").member_object_ids == ["hip:65474", "hip:66249"]
    assert catalog.asterism("井宿").related_object_ids == ["hip:29655"]
    assert catalog.asterism("轸宿").related_object_ids == [
        "hip:60189", "hip:61174", "hip:59199"
    ]
    assert catalog.asterism("角宿").completeness_status == "complete"

def test_catalog_keeps_uncertain_wing_members_ambiguous() -> None:
    catalog = load_catalog()
    assert catalog.resolve("翼宿十一?").status is AsterismStatus.AMBIGUOUS
    assert catalog.asterism("翼宿").completeness_status == "ambiguous"
```

These tests catch truncating a mansion to its defining star, turning related stars into members, or upgrading Stellarium status-2 identities.

- [x] **Step 2: Run catalog tests and verify RED**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms/test_asterism_catalog_v1.py -q`
Expected: failures because `complete` is not accepted and the new identities are absent.

- [x] **Step 3: Implement strict completeness validation and catalog data**

Allow `complete`, require every `complete` or `complete_gold_sample` member to be verified, require an `ambiguous` definition to contain at least one ambiguous member, and reject ambiguous members from a complete definition. Add all source-bound entries, ordered members, related objects and lines without changing the 28-region cycle.

- [x] **Step 4: Run all asterism tests and verify GREEN**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms -q`
Expected: all asterism tests pass; exact denominator is `162 / 28 / 28`.

- [x] **Step 5: Commit**

```bash
git add apps/star-omen/src/video_pipeline/asterisms/catalog.py \
  apps/star-omen/data/video_pipeline/asterism_catalog_v1.yaml \
  apps/star-omen/tests/video_pipeline/asterisms
git commit -m "feat: complete source-bound mansion memberships"
```

### Task 3: Enable proximity only for verified complete member sets

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/asterisms/mansion_regions.py`
- Modify: `apps/star-omen/tests/video_pipeline/asterisms/test_mansion_regions_v1.py`
- Modify: `apps/star-omen/tests/video_pipeline/astronomy/test_mansion_relation_provider_v1.py`

**Interfaces:**
- Consumes: Task 2 `complete` definitions.
- Produces: `assess_single_time_relation` and `SkyfieldEphemerisProvider.assess_mansion_relation` support for 角宿 and all other exact complete definitions; `ambiguous` 翼宿 stays blocked from member proximity.

- [x] **Step 1: Write failing relation and provider tests**

```python
def test_complete_non_gold_mansion_supports_member_proximity() -> None:
    observation = provider.assess_mansion_relation(
        body_id="mars", mansion_id="jiao-xiu", relation_term="临",
        at_utc=AT, observer=OBSERVER,
    )
    assert observation.assessment.nearest_member_object_id in {"hip:65474", "hip:66249"}

def test_ambiguous_mansion_remains_region_only() -> None:
    with pytest.raises(ValueError, match="verified complete member catalog"):
        provider.assess_mansion_relation(
            body_id="mars", mansion_id="yi-xiu", relation_term="临",
            at_utc=AT, observer=OBSERVER,
        )
```

These tests catch a gold-sample-only gate after complete data exists and catch unsafe use of uncertain members.

- [x] **Step 2: Run focused tests and verify RED**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms/test_mansion_regions_v1.py tests/video_pipeline/astronomy/test_mansion_relation_provider_v1.py -q`
Expected: 角宿 relation fails because only `complete_gold_sample` is accepted.

- [x] **Step 3: Implement the minimal completeness gate**

Accept only `complete` and `complete_gold_sample`; preserve the same measurement/result contracts and error on `partial` or `ambiguous` definitions.

- [x] **Step 4: Run scientific regression and verify GREEN**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms tests/video_pipeline/astronomy tests/test_mansion_navigation.py -q`
Expected: all focused scientific and navigation tests pass.

- [x] **Step 5: Commit**

```bash
git add apps/star-omen/src/video_pipeline/asterisms/mansion_regions.py \
  apps/star-omen/tests/video_pipeline/asterisms/test_mansion_regions_v1.py \
  apps/star-omen/tests/video_pipeline/astronomy/test_mansion_relation_provider_v1.py
git commit -m "feat: assess complete mansion member proximity"
```

### Task 4: Record Phase 3 evidence and publish the exact tree

**Files:**
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: `docs/superpowers/plans/2026-08-12-kaiyuan-28-mansion-membership-lines.md`

**Interfaces:**
- Consumes: exact implementation head from Tasks 1–3.
- Produces: reproducible gate evidence and an updated Draft PR #65 whose remote tree equals the verified local tree.

- [x] **Step 1: Move ASTRO-R01 to VERIFYING and record the implementation denominator**

Record exact entries/asterisms/mansions, complete/gold/ambiguous counts, source hashes, RED/GREEN evidence and commits. Keep the umbrella task out of `DONE` because Phases 4–6 remain.

- [x] **Step 2: Run exact-head local gates**

Run governance unit discovery, development-governance against live stable, focused scientific/navigation tests, root `make downstream-test`, compileall, canonical-source hashes, diff check and forbidden-path scan. Expected: every command exits zero and the worktree is clean after the evidence commit.

- [x] **Step 3: Review scope and mutation coverage**

Verify no corpus, Reviewer, Qdrant, `local_kb_default`, workflow, PR #54/#64 or `main` path changed. Confirm tests fail conceptually for a dropped member, misclassified related endpoint, promoted status-2 identity, broken line endpoint or `ambiguous` proximity access.

- [ ] **Step 4: Update Draft PR #65 and read back exact remote state**

Create a fast-forward remote commit whose tree equals the locally verified tree, update the PR body/title, and read back Draft/open/unmerged state, head SHA and tree SHA. Do not run Runner and do not merge.

## Plan self-review

- Spec coverage: member identity, related-star separation, line geometry, coordinate provenance, ambiguity, provider behavior, compatibility and governance each map to a task. Navigation-card enrichment and external-media auditing remain intentionally in Phases 4–6.
- Placeholder scan: every step names concrete files, behavior and verification evidence.
- Type consistency: Task 2 introduces the exact `complete` value consumed by Task 3; `complete_gold_sample` remains compatible; `ambiguous` is explicitly rejected by Task 3.
