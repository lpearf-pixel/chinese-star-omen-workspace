# Kaiyuan Twenty-eight Mansion Region Cycle Implementation Plan

**Status:** VERIFYING — Tasks 1–3 implemented; Task 4 exact-head publication remains.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver all twenty-eight source-bound defining stars, a fail-closed closed mansion-region cycle and an offline region-only body assessment without claiming that the other twenty-seven mansion member catalogs are complete.

**Architecture:** Extend the existing `asterism-catalog/v1` with partial asterism shells whose only verified member is the defining star, while retaining the complete 毕宿 gold sample. A catalog containing all twenty-eight mansion definitions must have sequence indices 1–28 exactly and each eastern boundary must equal the next western boundary, including 軫宿 → 角宿. Region-only evaluation consumes target and boundary positions; nearest-member evaluation remains available only when the asterism member set is complete.

**Tech Stack:** Python 3.12, Pydantic v2, PyYAML, Skyfield 1.51, pytest, canonical JSON fixtures, pinned Stellarium commit `3972e97101e4321079279b5e5660b074fafc030a`, CDS VizieR Hipparcos I/239.

## Global Constraints

- Base remains `stable/kaiyuan-v2@c2e8fcabb04354fd14d0c72b3b6020a47e63a583`; delivery updates Draft PR #65 only.
- Preserve the existing `HIP 65474 / Spica = 角宿一` SIMBAD J2000 identity and the complete 毕宿 gold sample.
- Hipparcos I/239 coordinates use ICRS J1991.25 with both proper-motion components.
- Mansion boundaries use apparent equatorial-of-date positions, west-inclusive and east-exclusive.
- A `partial` asterism may expose its verified defining star and no line segments; it must not claim complete membership or nearest-member coverage.
- `临/臨` remains ambiguous; no single-time result emits `犯`, `入`, `守` or `留`.
- Do not modify full member/line coverage, all-card navigation status, external-media contracts, raw corpus, Reviewer A/B, PR #54/#64, official ingest, Qdrant, `local_kb_default`, B11/B12 or `main`.
- Runner remains `NOT RUN` for this routine Draft update.

## Frozen defining-star denominator

| Seq | Mansion ID | Name | Defining HIP | East HIP |
|---:|---|---|---:|---:|
| 1 | `jiao-xiu` | 角宿 | 65474 | 69427 |
| 2 | `kang-xiu` | 亢宿 | 69427 | 72622 |
| 3 | `di-xiu` | 氐宿 | 72622 | 78265 |
| 4 | `fang-xiu` | 房宿 | 78265 | 80112 |
| 5 | `xin-xiu` | 心宿 | 80112 | 82514 |
| 6 | `wei-tail-xiu` | 尾宿 | 82514 | 88635 |
| 7 | `ji-xiu` | 箕宿 | 88635 | 92041 |
| 8 | `dou-xiu` | 斗宿 | 92041 | 100345 |
| 9 | `niu-xiu` | 牛宿 | 100345 | 102618 |
| 10 | `nu-xiu` | 女宿 | 102618 | 106278 |
| 11 | `xu-xiu` | 虚宿 | 106278 | 109074 |
| 12 | `wei-danger-xiu` | 危宿 | 109074 | 113963 |
| 13 | `shi-xiu` | 室宿 | 113963 | 1067 |
| 14 | `bi-wall-xiu` | 壁宿 | 1067 | 4463 |
| 15 | `kui-xiu` | 奎宿 | 4463 | 8903 |
| 16 | `lou-xiu` | 娄宿 | 8903 | 12719 |
| 17 | `wei-stomach-xiu` | 胃宿 | 12719 | 17499 |
| 18 | `mao-xiu` | 昴宿 | 17499 | 20889 |
| 19 | `bi-xiu` | 毕宿 | 20889 | 26207 |
| 20 | `zi-xiu` | 觜宿 | 26207 | 26727 |
| 21 | `shen-xiu` | 参宿 | 26727 | 30343 |
| 22 | `jing-xiu` | 井宿 | 30343 | 41822 |
| 23 | `gui-xiu` | 鬼宿 | 41822 | 42313 |
| 24 | `liu-xiu` | 柳宿 | 42313 | 46390 |
| 25 | `xing-xiu` | 星宿 | 46390 | 48356 |
| 26 | `zhang-xiu` | 张宿 | 48356 | 53740 |
| 27 | `yi-xiu` | 翼宿 | 53740 | 59803 |
| 28 | `zhen-xiu` | 轸宿 | 59803 | 65474 |

The semantic suffixes disambiguate three pinyin collisions (`尾/危/胃`) and the existing `bi-xiu` 毕宿 from 壁宿. Chinese names and aliases remain the user-facing identity.

---

### Task 1: Enforce a complete closed mansion cycle and add source-bound data

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/asterisms/catalog.py`
- Modify: `apps/star-omen/data/video_pipeline/asterism_catalog_v1.yaml`
- Create: `apps/star-omen/data/video_pipeline/sources/stellarium_28_defining_stars_v1.json`
- Create: `apps/star-omen/data/video_pipeline/sources/hipparcos_28_defining_stars_v1.json`
- Create: `tests/fixtures/asterisms/v1/lunar-mansion-cycle.json`
- Modify: `tests/fixtures/asterisms/v1/manifest.json`
- Modify: `apps/star-omen/tests/video_pipeline/asterisms/test_asterism_catalog_v1.py`
- Modify: `apps/star-omen/tests/video_pipeline/asterisms/test_asterism_source_assets_v1.py`

**Interfaces:**
- Consumes: existing `AsterismEntryV1`, `AsterismDefinitionV1`, `LunarMansionDefinitionV1` and pinned source contracts.
- Produces: `lunar_mansion_cycle_status: complete`; exactly 28 ordered
  `lunar_mansions`; 28 unique western boundaries; a closed
  `west[i+1] == east[i]` cycle; `partial` asterism shells with empty
  `line_segments`.

- [x] **Step 1: Write failing catalog and mutation tests**

Add literal assertions for the denominator table above. Mutate a copy of the catalog to remove sequence 12, duplicate sequence 13, replace 毕宿's eastern edge, and replace 軫宿's eastern edge. Each mutation must fail for the intended missing-sequence, duplicate-sequence or broken-cycle reason. Assert a partial 角宿 shell has `member_object_ids == ["hip:65474"]`, `line_segments == []` and does not claim complete membership.

- [x] **Step 2: Verify RED**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms/test_asterism_catalog_v1.py tests/video_pipeline/asterisms/test_asterism_source_assets_v1.py -q`

Expected: failures because only one mansion definition and ten non-Spica entries exist; partial empty-line definitions and a complete cycle are not supported.

- [x] **Step 3: Implement strict cycle validation and literal source data**

Permit empty line segments only when `completeness_status == "partial"`. Add an
explicit top-level `lunar_mansion_cycle_status` whose default is `partial`; when
it is `complete`, require sequence indices `1..28`, exactly 28 distinct western
boundary IDs, and the sorted circular adjacency rule. Add 25 new defining-star
entries; keep existing Spica, 毕宿一 and 觜宿一 entries byte-semantically
compatible. Canonical source snapshots contain the exact 28 fixed-name records
and all 28 Hipparcos rows, including J1991.25 proper motion.

- [x] **Step 4: Verify GREEN and source hashes**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms -q`

Expected: all catalog, cycle, fixture and existing 毕宿/Spica tests pass.

- [x] **Step 5: Commit**

```bash
git add apps/star-omen/src/video_pipeline/asterisms/catalog.py \
  apps/star-omen/data/video_pipeline/asterism_catalog_v1.yaml \
  apps/star-omen/data/video_pipeline/sources/stellarium_28_defining_stars_v1.json \
  apps/star-omen/data/video_pipeline/sources/hipparcos_28_defining_stars_v1.json \
  apps/star-omen/tests/video_pipeline/asterisms \
  tests/fixtures/asterisms/v1
git commit -m "feat: close the twenty-eight mansion region cycle"
```

### Task 2: Separate region-only assessment from member proximity

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/asterisms/mansion_regions.py`
- Modify: `apps/star-omen/src/video_pipeline/asterisms/__init__.py`
- Modify: `apps/star-omen/tests/video_pipeline/asterisms/test_mansion_regions_v1.py`

**Interfaces:**
- Produces: `MansionRegionAssessmentV1` with mansion ID, same-frame target/west/east positions and `in_mansion_region`.
- Produces: `assess_mansion_region(mansion, target, west_boundary, east_boundary) -> MansionRegionAssessmentV1`.
- Preserves: `assess_single_time_relation(...)` for complete member catalogs.

- [x] **Step 1: Write failing pure behavior tests**

Use literal RA cases for an ordinary interval, west equality, east equality and
the actual 室宿 → 壁宿 360/0 wrap. The catalog cycle still closes 軫宿 → 角宿,
but that edge does not cross zero in right ascension. Assert region-only
evaluation has no nearest-member fields. Assert `assess_single_time_relation`
rejects a `partial` asterism with a message directing callers to region-only
evaluation.

- [x] **Step 2: Verify RED**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms/test_mansion_regions_v1.py -q`

Expected: import failure for `MansionRegionAssessmentV1`/`assess_mansion_region`, followed by a missing partial-membership guard.

- [x] **Step 3: Implement the pure region boundary**

Extract the existing circular-interval behavior into the public region evaluator. Reuse it from `assess_single_time_relation`; do not duplicate interval semantics. Require exact object IDs and one reference frame. Before nearest-member calculation, require `complete_gold_sample`; no threshold or classical relation is added.

- [x] **Step 4: Verify GREEN**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms -q`

Expected: region-only, relation, cycle and legacy tests pass.

- [x] **Step 5: Commit**

```bash
git add apps/star-omen/src/video_pipeline/asterisms \
  apps/star-omen/tests/video_pipeline/asterisms
git commit -m "feat: separate mansion regions from member proximity"
```

### Task 3: Add offline provider assessment for every mansion region

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/astronomy/provider.py`
- Modify: `apps/star-omen/tests/video_pipeline/astronomy/test_mansion_relation_provider_v1.py`

**Interfaces:**
- Produces: `MansionRegionObservationV1` binding body ID, UTC, catalog SHA-256 and `MansionRegionAssessmentV1`.
- Produces: `SkyfieldEphemerisProvider.assess_mansion_region(body_id, mansion_id, at_utc, observer)`.
- Preserves: existing complete 毕宿 `assess_mansion_relation` behavior.

- [x] **Step 1: Write failing provider tests**

Using the existing verified local DE421 fixture, assess Mars against 角宿 and 軫宿 at one UTC instant. Assert the provider observes the target and both defining stars at the same time, binds the catalog hash, and returns region-only output without nearest-member claims. Assert the complete 毕宿 relation path still returns its eight-member nearest-star measurement, while a partial mansion relation request fails closed.

- [x] **Step 2: Verify RED**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/astronomy/test_mansion_relation_provider_v1.py -q`

Expected: missing provider method/observation model and missing incomplete-member rejection.

- [x] **Step 3: Implement the smallest offline adapter**

Reuse `_observe_catalog_entry`, the same UTC conversion and the pure region evaluator. Do not fetch data, add thresholds, modify `AstronomyEvent/v1`, or infer members from geometry.

- [x] **Step 4: Verify GREEN and scientific regression**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms tests/video_pipeline/astronomy tests/test_mansion_navigation.py -q`

Expected: all focused scientific and navigation tests pass.

- [x] **Step 5: Commit**

```bash
git add apps/star-omen/src/video_pipeline/astronomy/provider.py \
  apps/star-omen/tests/video_pipeline/astronomy/test_mansion_relation_provider_v1.py
git commit -m "feat: assess bodies across all mansion regions"
```

### Task 4: Record Phase 2 evidence and update Draft PR #65

**Files:**
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: Draft PR #65 metadata after the exact tree is published.

**Interfaces:**
- Consumes: exact-head focused/full/governance evidence.
- Produces: ASTRO-R01 `VERIFYING (phase 2)` with phases 3–6 still unclaimed.

- [x] **Step 1: Run focused and full local gates**

Run the Task 3 focused command, canonical JSON/hash replay, `compileall`, `git diff --check`, governance unit tests, development-governance base-to-head check and `CODEX_PRIMARY_RUNTIME_PYTHON="$PWD/.venv/bin/python" PATH="$PWD/.venv/bin:$PATH" make downstream-test`.

- [x] **Step 2: Review scope and forbidden paths**

Compare `c2e8fcabb04354fd14d0c72b3b6020a47e63a583...HEAD`; reject any raw corpus, Reviewer, Qdrant, workflow, `local_kb_default`, PR #54/#64 or `main` path.

- [x] **Step 3: Record exact evidence**

Update the three governance documents with exact counts, head/tree, source hashes, known partial-member boundary and remaining phases. Keep ASTRO-R01 out of `DONE`.

- [ ] **Step 4: Re-run exact-head verification and publish**

Publish the exact verified tree to `codex/kaiyuan-28-mansions-external-audit-v1`, update Draft PR #65, read it back and confirm Draft/base/head/tree. Runner remains `NOT RUN`; do not merge.

## Plan self-review

- **Spec coverage:** this plan implements only approved delivery phase 2: all defining stars, closed regions and reusable region assessment. Full members/lines, navigation enrichment and external-media evidence remain separate phases.
- **Placeholder scan:** no implementation step contains an unresolved placeholder; the 28-row denominator and mutation cases are literal.
- **Type consistency:** Task 2's `MansionRegionAssessmentV1` is the exact assessment embedded by Task 3; Task 1's mansion IDs and boundary IDs are consumed unchanged by both.
