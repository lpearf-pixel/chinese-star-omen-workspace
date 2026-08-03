# B10-R05 Bounded Source Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add exactly 15 fixed-revision Wikisource accession/raw objects to the seven-family research package, expand the reversible projection from 16 to 31 source objects, and preserve the original 16 objects plus all 20 Core14 mappings byte-for-byte or value-for-value.

**Architecture:** Layer A remains the immutable accession/raw/hash authority. The Work–TextVersion–Carrier–SourceObject graph remains a rebuildable Layer-B projection. The new objects have no inferred Core14 cases and no formal rule authority. Git history pins the R04 pilot; R05 rebuilds the current deterministic artifact and records the transition explicitly.

**Tech Stack:** Python 3.9+, Pydantic v2, pytest, JSON, MediaWiki `action=raw`, SHA-256, GitHub Actions.

## Global Constraints

- Target only `stable/kaiyuan-v2`; never `main`.
- Add exactly the 15 registered accession IDs below—no provider-wide or 631-object history mirror.
- Preserve every existing raw byte, accession identity, detailed record, compact record and all 20 `core14-mapping.json` entries.
- New records use `core14_cases: []` and an empty relevant excerpt; no inferred mapping or independent-witness promotion.
- Do not modify Reviewer A/B material for PR #54 or start B10-PR-D/E/F.
- Do not access or mutate Qdrant, official ingest or `local_kb_default`.
- Routine research verification uses focused/local tests plus hosted exact-head workflows; no major-version Runner run is required.

## Fixed 15-object register

| Accession ID | Family | Wikisource title | oldid | Revision timestamp |
|---|---|---:|---:|---|
| `zhws-yisizhan-root-r1965836` | yisizhan | 乙巳占 | 1965836 | 2020-09-27T08:07:35Z |
| `zhws-yisizhan-1-r1377475` | yisizhan | 乙巳占/1 | 1377475 | 2018-03-01T15:00:23Z |
| `zhws-yisizhan-3-r7904696` | yisizhan | 乙巳占/3 | 7904696 | 2026-06-28T01:40:45Z |
| `zhws-yisizhan-4-r1538289` | yisizhan | 乙巳占/4 | 1538289 | 2019-02-10T13:23:11Z |
| `zhws-yisizhan-6-r1715347` | yisizhan | 乙巳占/6 | 1715347 | 2019-08-09T19:44:36Z |
| `zhws-yisizhan-7-r1538297` | yisizhan | 乙巳占/7 | 1538297 | 2019-02-10T13:28:20Z |
| `zhws-yisizhan-9-r854566` | yisizhan | 乙巳占/9 | 854566 | 2017-04-16T03:55:11Z |
| `zhws-yisizhan-10-r1538300` | yisizhan | 乙巳占/10 | 1538300 | 2019-02-10T13:30:17Z |
| `zhws-hanshu-root-r7906813` | hanshu-tianwenzhi | 漢書 | 7906813 | 2026-07-05T13:28:29Z |
| `zhws-songshu-root-r2390963` | songshu-tianwenzhi | 宋書 | 2390963 | 2024-04-16T04:16:04Z |
| `zhws-jinshu-root-r2644704` | jinshu-tianwenzhi | 晉書 | 2644704 | 2026-01-27T03:11:20Z |
| `zhws-houhanji-skqs-root-r597585` | houhanji | 後漢紀 (四庫全書本) | 597585 | 2016-10-05T07:07:44Z |
| `zhws-houhanshu-root-r7902792` | houhanshu | 後漢書 | 7902792 | 2026-06-20T05:38:04Z |
| `zhws-houhanshu-101-r2043770` | houhanshu | 後漢書/卷101 | 2043770 | 2021-06-18T20:15:26Z |
| `zhws-houhanshu-102-r1484970` | houhanshu | 後漢書/卷102 | 1484970 | 2018-06-19T06:32:58Z |

---

## Task 1: Freeze the denominator and observe the TDD red state

**Files:**

- Create: `corpus/research_sources/related-wikisource/b10-r05-bounded-expansion.json`
- Modify: `apps/star-omen/tests/research_sources/test_source_inventory.py`
- Modify: `apps/star-omen/tests/research_sources/test_projector_roundtrip.py`
- Modify: `apps/star-omen/tests/research_sources/test_pilot_artifact.py`

- [x] Create a machine-readable register containing the base stable SHA, baseline manifest SHA-256, the exact 15 IDs/title/oldid/timestamp/family/raw-path tuples and the invariant expected counts.
- [x] Add tests requiring 31 accessions/raw files, seven families, exact family counts `11/2/2/5/4/2/5`, the exact 15 new IDs, empty Core14 scope for every new object and exactly 20 unchanged mapping IDs.
- [x] Snapshot the original 16 accession metadata identities and raw SHA-256/byte-count triples in the test/register so a later mutation fails closed.
- [x] Run the focused tests before data changes and record the expected failure at 16 rather than 31.

```bash
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q   tests/research_sources/test_source_inventory.py   tests/research_sources/test_projector_roundtrip.py   tests/research_sources/test_pilot_artifact.py
```

Expected: FAIL only on the new 31-object/15-ID requirements.

## Task 2: Capture the 15 immutable source objects and update Layer A

**Files:**

- Create: 15 `.wikitext` files beneath the six existing `p0/*/raw/` directories.
- Modify: six existing `p0/*/accessions.json` files and their collation notes when the denominator changes.
- Modify: `corpus/research_sources/related-wikisource/accession-manifest.json`.

- [x] Fetch each registered object from `https://zh.wikisource.org/w/index.php?title=<title>&oldid=<oldid>&action=raw` without normalization or silent fallback.
- [x] Verify the MediaWiki API reports the exact registered title, oldid and timestamp before accepting bytes.
- [x] Compute raw UTF-8 byte count and SHA-256; create one compact and one detailed record with matching shared fields.
- [x] Use `capture_status: complete`, `core14_cases: []`, an empty `relevant_excerpt`, and an explicit boundary-only locator/note. Do not claim whole-book evidence beyond the captured object.
- [x] Update family counts to yisizhan 11, shiji 2, hanshu 2, songshu 5, jinshu 4, houhanji 2 and houhanshu 5; update global totals from the actual bytes.
- [x] Re-run inventory tests and require all compact/detailed joins, raw file-set, SHA and byte-count gates to pass.

## Task 3: Rebuild and validate the reversible Layer-B projection

**Files:**

- Modify: `corpus/research_sources/related-wikisource/source-projection-pilot-v0.json`
- Modify: `apps/star-omen/tests/research_sources/test_source_graph_v0.py`
- Modify: `apps/star-omen/tests/research_sources/test_projector_roundtrip.py`
- Modify: `apps/star-omen/tests/research_sources/test_pilot_artifact.py`
- Modify: `docs/research/B10_R04_SOURCE_GRAPH_PILOT_REPORT.md`
- Create: `docs/research/B10_R05_BOUNDED_SOURCE_EXPANSION_REPORT.md`

- [x] Change only denominator expectations needed for 31 source objects; retain schema, node kinds, identity rules, evidence-link semantics and reverse-projector behavior.
- [x] Regenerate the deterministic artifact through `scripts/build_b10_r04_source_projection.py`; Git history and the R05 report preserve the R04 pilot hash and 16-object provenance.
- [x] Require 31 generated accession IDs, exactly 20 original mapping IDs, exact reverse projection, zero title-based merges, zero orphans, zero accepted independent-witness assertions and positive deferred assertions.
- [x] Prove the original 16 records/raw identities and the complete mapping document remain unchanged from the registered stable baseline.
- [x] Record old/new manifest and artifact SHA-256 values, counts and explicit NOT_RUN safety fields in the R05 report.

## Task 4: Replay all sources and complete local verification

**Files:**

- Modify: `docs/development/WORK_LOG.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: this plan.

- [x] Replay all 31 fixed-revision raw URLs and require exact SHA-256/byte counts; separately require the exact 15 registered revision timestamps.
- [ ] Run the deterministic builder check, focused research tests, contract/downstream gates, compile checks, governance checker and diff hygiene.

```bash
PYTHONPATH=apps/star-omen/src:packages/kb-contracts/python:packages/kb-text-core/python   python scripts/build_b10_r04_source_projection.py --repo-root . --check
cd apps/star-omen
PYTHONPATH=src:../../packages/kb-contracts/python:../../packages/kb-text-core/python pytest -q tests/research_sources
cd ../..
make contracts-test
make downstream-test
python scripts/check_development_governance.py
python -m compileall -q apps/star-omen/src/research_sources scripts/build_b10_r04_source_projection.py
git diff --check
```

- [x] Mark B10-R05 `VERIFYING`, record exact commands/counts/hashes and commit the intended implementation head.

## Task 5: Independent review and Draft PR

**Files:**

- Create: `docs/research/b10-r05-reviews/final-branch-review.md`
- Modify: `docs/development/WORK_LOG.md`, `TASKS.md`, `PROJECT_MEMORY.md` and this plan.

- [x] Independently recompute 31/31 raw identities, 31/31 compact-to-detailed joins, exact 15 target identity/timestamps, unchanged original 16 and unchanged 20 mappings.
- [x] Review graph closure, reverse projection, title-merge prevention, deferred authority, forbidden side effects and branch scope. Fix and repeat until Critical 0 / Important 0.
- [ ] Commit the immutable review record and governance-only closeout, then open a Draft PR targeting only `stable/kaiyuan-v2`.
- [ ] Verify the exact final PR head, changed paths, hosted required Actions and review threads. Add a hash-bound top-level review comment without another branch mutation.
- [ ] Keep the PR Draft and B10-R05 `VERIFYING` until the user authorizes integration.
