# Kaiyuan Twenty-eight Mansion Navigation Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind all 28 existing lunar-mansion navigation cards to the Phase 3 scientific catalog with exact sequence, aliases, members, lines, uncertainty and region provenance.

**Architecture:** Treat the scientific catalog as the only generator input for navigation status and keep classical card prose untouched. Tests discover cards through the overview, resolve each title/alias through the catalog, and compare the complete structured status payload rather than duplicating scientific values in test helpers.

**Tech Stack:** Python 3.12, Pydantic v2, PyYAML, pytest, Markdown/YAML front matter, pinned `asterism-catalog/v1`.

## Global Constraints

- Base remains `stable/kaiyuan-v2@c2e8fcabb04354fd14d0c72b3b6020a47e63a583`; delivery updates Draft PR #65 only.
- Preserve Phase 1–3 catalog identities, regions, completeness states and source hashes.
- Card metadata is a derived navigation view; it must not become raw classical evidence.
- Keep existing filenames and overview links; simplified/traditional names are explicit aliases.
- Do not add unreviewed classical quotations, omen conclusions or weather inference.
- Do not modify raw corpus, Reviewer A/B, PR #54/#64, Qdrant, `local_kb_default`, workflows, B11/B12 or `main`.
- Routine Draft publication does not run Runner and does not merge.

---

### Task 1: Require exact all-card catalog bindings

**Files:**
- Modify: `apps/star-omen/tests/test_mansion_navigation.py`

**Interfaces:**
- Consumes: overview wiki links, all `lunar_mansion_card` front matter, `AsterismCatalogV1`.
- Produces: one table-driven gate covering exactly 28 cards in sequence order.

- [x] **Step 1: Write the failing all-card behavior test**

```python
def test_all_mansion_cards_are_bound_to_the_scientific_catalog() -> None:
    catalog = load_asterism_catalog(CATALOG_PATH).catalog
    cards = overview_cards()
    assert [catalog.asterism(frontmatter(path)["title"]).asterism_id for path in cards] == [
        item.mansion_id for item in sorted(catalog.lunar_mansions, key=lambda item: item.sequence_index)
    ]
    for path in cards:
        metadata = frontmatter(path)
        definition = catalog.asterism(metadata["title"])
        assert metadata["scientific_catalog"] == expected_status(catalog, definition)
```

The test catches missing cards, reordered overview links, stale aliases, truncated members/lines, omitted ambiguity, wrong boundaries or stale source refs.

- [x] **Step 2: Run the navigation test and verify RED**

Run: `../../.venv/bin/python -m pytest tests/test_mansion_navigation.py -q`
Expected: 27 cards fail because only 毕宿 has a scientific status block.

- [x] **Step 3: Keep expectations independent of card bytes**

Build the expected status from the validated catalog objects, then compare it to each card. Assert overview filenames separately so a broken card cannot redefine its own route.

- [x] **Step 4: Commit the failing navigation gate**

```bash
git add apps/star-omen/tests/test_mansion_navigation.py
git commit -m "test: require all mansion navigation bindings"
```

### Task 2: Populate all 28 derived status blocks

**Files:**
- Modify: `apps/star-omen/data/sources/古籍/唐開元占經/逐宿卡/{28 single-mansion cards}.md`

**Interfaces:**
- Consumes: Task 1 exact payload and catalog aliases.
- Produces: `mansion-navigation-status/v1` metadata with catalog/asterism IDs, version, sequence, completeness, members, related and ambiguous IDs, defining star, lines, boundaries, coordinate/boundary/provenance values and deduplicated source refs.

- [x] **Step 1: Generate front matter from the catalog**

For each overview target, preserve existing classical fields and body. Set aliases to every catalog name different from the filename title. Add the exact status payload; never hand-enter a scientific ID independently of the catalog.

- [x] **Step 2: Add bounded human-readable modern-mapping status**

Ensure every card contains exactly one `## 科学目录状态（现代映射）` section. State completeness, member/related HIP IDs, boundary IDs, `derived_region` disclosure and any ambiguous member IDs. Do not change `原文摘录`, `白话解释` or `后续整理清单`.

- [x] **Step 3: Run navigation and focused scientific tests**

Run: `../../.venv/bin/python -m pytest tests/test_mansion_navigation.py tests/video_pipeline/asterisms tests/video_pipeline/astronomy -q`
Expected: all navigation and scientific tests pass.

- [x] **Step 4: Commit**

```bash
git add apps/star-omen/data/sources/古籍/唐開元占經/逐宿卡 apps/star-omen/tests/test_mansion_navigation.py
git commit -m "docs: bind all mansion cards to the scientific catalog"
```

### Task 3: Verify, record and publish Phase 4

**Files:**
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: `docs/superpowers/plans/2026-08-12-kaiyuan-28-mansion-navigation-status.md`

**Interfaces:**
- Consumes: exact all-card implementation head.
- Produces: reproducible local gate evidence and an updated Draft #65 with a remote tree identical to the verified local tree.

- [x] **Step 1: Move Phase 4 to VERIFYING and record RED/GREEN evidence**

Record exact card count, alias variants, scientific denominator, focused/full counts and commits. Keep ASTRO-R01 out of `DONE` because external-media phases remain.

- [x] **Step 2: Run exact-head local gates**

Run governance unit discovery, development-governance against live stable, focused tests, environment-bound root `make downstream-test`, compileall, canonical hashes, diff check, clean-worktree check and forbidden-path scan.

- [x] **Step 3: Review classical-content preservation**

Verify only derived card front matter and the new modern-mapping section changed; raw corpus and existing `原文摘录`/`白话解释`/`后续整理清单` content remains byte-for-byte present.

- [ ] **Step 4: Update Draft PR #65 and read back remote state**

Create a fast-forward remote commit whose tree equals the verified local tree. Update the PR body/title and confirm `open / draft / merged=false`; do not run Runner or merge.

## Plan self-review

- Spec coverage: exact 28-card coverage, order, aliases, members, lines, related objects, ambiguity, boundaries, source refs and modern/classical separation each map to a task.
- Placeholder scan: every action names files, observable behavior and a verification command.
- Type consistency: the status payload is derived from the same `AsterismDefinitionV1` and `LunarMansionDefinitionV1` objects used in Phases 1–3.
