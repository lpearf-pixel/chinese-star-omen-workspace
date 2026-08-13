# Kaiyuan Bi Mansion Gold Sample Implementation Plan

**Status:** VERIFYING — Tasks 1–4 implemented; exact-head governance remains.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a source-bound 毕宿 eight-star catalog, a reusable lunar-mansion region evaluator and an honest single-time `临毕` assessment without breaking the existing Spica identity.

**Architecture:** Extend `asterism-catalog/v1` additively with asterism and mansion definitions, keeping star records as the only source of coordinates. A pure evaluator calculates circular RA region membership and nearest-member spherical separation; a provider adapter supplies same-time apparent positions. Navigation consumes the resulting status but remains a derived research view.

**Tech Stack:** Python 3.12, Pydantic v2, PyYAML, Skyfield 1.51, pytest, canonical JSON fixtures.

## Global Constraints

- Base is `stable/kaiyuan-v2@c2e8fcabb04354fd14d0c72b3b6020a47e63a583`.
- Do not modify `AstronomyEvent/v1` semantics in place.
- Do not infer identity or membership by nearest-star geometry.
- Use apparent equatorial-of-date positions for mansion-boundary evaluation.
- Keep `临` ambiguous; do not emit `犯`, `入`, `守` or `留` from one sample.
- Preserve raw corpus, PR #54/#64, Reviewer A/B, Qdrant, `local_kb_default` and `main`.

---

### Task 1: Add source-bound asterism and mansion catalog definitions

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/asterisms/catalog.py`
- Modify: `apps/star-omen/src/video_pipeline/asterisms/__init__.py`
- Modify: `apps/star-omen/data/video_pipeline/asterism_catalog_v1.yaml`
- Create: `apps/star-omen/data/video_pipeline/sources/stellarium_bi_xiu_v1.json`
- Create: `apps/star-omen/data/video_pipeline/sources/hipparcos_bi_zi_v1.json`
- Create: `tests/fixtures/asterisms/v1/bi-xiu-membership.json`
- Modify: `tests/fixtures/asterisms/v1/manifest.json`
- Modify: `apps/star-omen/tests/video_pipeline/asterisms/test_asterism_catalog_v1.py`
- Modify: `apps/star-omen/tests/video_pipeline/asterisms/test_asterism_source_assets_v1.py`

**Interfaces:**
- Produces: `AsterismDefinitionV1`, `LunarMansionDefinitionV1`.
- Produces: `AsterismCatalogV1.asterism(asterism_id)` and `.mansion(asterism_id)`.
- Produces: complete 毕宿 members `[hip:20889, hip:20648, hip:20455, hip:20205, hip:21421, hip:20885, hip:20713, hip:18724]` and region edges `hip:20889 → hip:26207`.

- [ ] **Step 1: Write failing catalog behavior tests**

```python
definition = catalog.asterism("bi-xiu")
assert definition.member_object_ids == [
    "hip:20889", "hip:20648", "hip:20455", "hip:20205",
    "hip:21421", "hip:20885", "hip:20713", "hip:18724",
]
assert definition.related_object_ids == ["hip:21683"]
assert catalog.mansion("bi-xiu").east_boundary_object_id == "hip:26207"
assert catalog.resolve("畢宿五").modern_object_id == "hip:21421"
```

- [ ] **Step 2: Verify RED**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms -q`
Expected: failures because the new models/methods and 毕宿 data do not exist.

- [ ] **Step 3: Implement strict additive models and data**

Add frozen Pydantic models that validate referenced IDs, unique members,
disjoint base/related members, valid line-segment endpoints and source refs.
Add canonical source snapshots with the exact pinned revisions and literal
Hipparcos ICRS coordinates at the catalogue epoch J1991.25, including both
proper-motion components.

- [ ] **Step 4: Verify GREEN and compatibility**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms -q`
Expected: all asterism tests pass, including the unchanged Spica assertions.

- [ ] **Step 5: Commit**

```bash
git add apps/star-omen/src/video_pipeline/asterisms \
  apps/star-omen/data/video_pipeline \
  apps/star-omen/tests/video_pipeline/asterisms \
  tests/fixtures/asterisms/v1
git commit -m "feat: add source-bound Bi mansion catalog"
```

### Task 2: Add the pure mansion-region and relation evaluator

**Files:**
- Create: `apps/star-omen/src/video_pipeline/asterisms/mansion_regions.py`
- Modify: `apps/star-omen/src/video_pipeline/asterisms/__init__.py`
- Create: `apps/star-omen/tests/video_pipeline/asterisms/test_mansion_regions_v1.py`

**Interfaces:**
- Consumes: `AsterismDefinitionV1`, `LunarMansionDefinitionV1`.
- Produces: `EquatorialPositionV1`, `MansionRelationAssessmentV1`.
- Produces: `assess_single_time_relation(...) -> MansionRelationAssessmentV1`.

- [ ] **Step 1: Write failing observable behavior tests**

```python
assessment = assess_single_time_relation(
    relation_term="临",
    mansion=bi_mansion,
    target=EquatorialPositionV1(ra_deg=75.0, dec_deg=20.0),
    west_boundary=EquatorialPositionV1(ra_deg=67.0, dec_deg=19.0),
    east_boundary=EquatorialPositionV1(ra_deg=84.0, dec_deg=10.0),
    members=bi_members,
)
assert assessment.in_mansion_region is True
assert assessment.interpretation_status == "ambiguous_relation"
assert assessment.inferred_classical_relation is None
assert assessment.nearest_member_object_id is not None
```

Add separate literal cases for outside, west-inclusive, east-exclusive and a
region that wraps across 360/0 degrees. Mutating interval direction or replacing
spherical separation with Euclidean RA/Dec distance must break at least one test.

- [ ] **Step 2: Verify RED**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms/test_mansion_regions_v1.py -q`
Expected: import failure because `mansion_regions` does not exist.

- [ ] **Step 3: Implement minimal pure evaluator**

Normalize RA to `[0, 360)`, use west-inclusive/east-exclusive circular intervals,
calculate great-circle separation with a clamped cosine, require identical
`reference_frame` values and reject an empty member set.

- [ ] **Step 4: Verify GREEN**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms -q`
Expected: all catalog and evaluator tests pass.

- [ ] **Step 5: Commit**

```bash
git add apps/star-omen/src/video_pipeline/asterisms \
  apps/star-omen/tests/video_pipeline/asterisms
git commit -m "feat: assess lunar mansion regions separately"
```

### Task 3: Connect one-time body observations to the pure evaluator

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/astronomy/provider.py`
- Modify: `apps/star-omen/tests/video_pipeline/astronomy/test_skyfield_provider_integration_v1.py`
- Create: `apps/star-omen/tests/video_pipeline/astronomy/test_mansion_relation_provider_v1.py`

**Interfaces:**
- Consumes: `SkyfieldEphemerisProvider.observe_body`, verified catalog stars and `assess_single_time_relation`.
- Produces: `SkyfieldEphemerisProvider.assess_mansion_relation(body_id, mansion_id, relation_term, at_utc, observer)`.

- [ ] **Step 1: Write failing adapter tests**

Use the existing verified local DE421 fixture. Assert that the adapter obtains
the body, both defining stars and every member at the same UTC instant, passes
apparent-equatorial-of-date positions to the pure evaluator and preserves
`ambiguous_relation` for `临`.

- [ ] **Step 2: Verify RED**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/astronomy/test_mansion_relation_provider_v1.py -q`
Expected: failure because the provider method is missing.

- [ ] **Step 3: Implement the smallest adapter**

Reuse existing verified ephemeris, catalog loading and Star construction. Do not
download data, add thresholds or alter `AstronomyEvent/v1`.

- [ ] **Step 4: Verify GREEN and scientific regression**

Run: `../../.venv/bin/python -m pytest tests/video_pipeline/asterisms tests/video_pipeline/astronomy -q`
Expected: all focused scientific tests pass.

- [ ] **Step 5: Commit**

```bash
git add apps/star-omen/src/video_pipeline/astronomy/provider.py \
  apps/star-omen/tests/video_pipeline/astronomy
git commit -m "feat: evaluate bodies against mansion regions"
```

### Task 4: Enrich the 毕宿 navigation card and validate links

**Files:**
- Modify: `apps/star-omen/data/sources/古籍/唐開元占經/逐宿卡/畢宿.md`
- Modify: `apps/star-omen/data/sources/古籍/唐開元占經/导航/二十八宿總覽.md`
- Create: `apps/star-omen/tests/test_mansion_navigation.py`

**Interfaces:**
- Consumes: the committed catalog and its completeness state.
- Produces: one source-bound 毕宿 status block and a link check that resolves all 28 mansion card targets despite simplified/traditional display aliases.

- [ ] **Step 1: Write the failing navigation behavior test**

Load the overview links and resolve each link to an existing card through an
explicit alias map. Load the 毕宿 card front matter/status block and assert the
eight HIP IDs, defining-star IDs, catalog version and `derived_region` label.

- [ ] **Step 2: Verify RED**

Run: `../../.venv/bin/python -m pytest tests/test_mansion_navigation.py -q`
Expected: failure on broken simplified/traditional link targets and the absent
毕宿 scientific-status block.

- [ ] **Step 3: Implement the minimal navigation correction**

Use existing traditional filenames as canonical targets. Add only source-bound
scientific data; do not fill unreviewed classical quotations or omen outcomes.

- [ ] **Step 4: Verify GREEN and full downstream regression**

Run: `../../.venv/bin/python -m pytest tests/test_mansion_navigation.py tests/video_pipeline/asterisms tests/video_pipeline/astronomy -q`
Then run: `make downstream-test`
Expected: focused and downstream suites pass.

- [ ] **Step 5: Record verification and move ASTRO-R01 phase 1 to VERIFYING**

Update `TASKS.md` and `WORK_LOG.md` with exact commands, counts, changed-file
scope and remaining phases. Do not mark the umbrella ASTRO-R01 task DONE while
the all-28 and external-media phases remain.

## Plan self-review

- Spec coverage: Tasks 1–4 cover source identity, region boundaries, relation
  ambiguity, provider integration, compatibility and navigation. All-28 data and
  external-media contracts remain separately staged by the approved design and
  are not implied complete by this plan.
- Deferred-step scan: every phase-1 implementation action is explicit.
- Type consistency: Task 2 consumes the exact catalog definitions from Task 1;
  Task 3 consumes Task 2's evaluator; Task 4 consumes the committed catalog.
