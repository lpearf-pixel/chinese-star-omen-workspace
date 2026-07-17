# Kaiyuan Corpus Hardening v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the post-PR-#6 corpus, locator, heading and audit hardening delta onto the new `stable/kaiyuan-v2` release line without touching `main` or importing the Qdrant runtime.

**Architecture:** `stable/kaiyuan-v2` is the release base. A short-lived `codex/kaiyuan-corpus-hardening-v2` branch receives only the hardening delta already developed after PR #6. The shared `packages/kb-text-core` remains the single parser/matcher source used by corpus audits and downstream filesystem fallback.

**Tech Stack:** Python 3.12, pytest, GitHub Actions, Markdown corpus files, GitHub pull requests.

## Global Constraints

- Never merge this release line into `main`.
- Target branch is `stable/kaiyuan-v2`.
- Preserve raw corpus text and all `&KRxxxx;` entities.
- Do not import Qdrant/Docker runtime in this plan.
- Write canonical `kb_book_id`; read `book_id` only as a compatibility alias.
- Do not commit `.env`, secrets, data volumes, models or absolute local paths.

---

### Task 1: Establish release policy and approved design

**Files:**
- Create: `docs/superpowers/specs/2026-07-17-kaiyuan-stable-release-and-hardening-design.md`
- Create: `docs/superpowers/plans/2026-07-17-kaiyuan-corpus-hardening-v2.md`

**Interfaces:**
- Consumes: user decision that release work must not target `main`.
- Produces: stable branch policy and scoped A.1 plan.

- [x] **Step 1: Create `stable/kaiyuan-v2` from current `dev-test`.**
- [x] **Step 2: Create `codex/kaiyuan-corpus-hardening-v2` from the stable branch.**
- [x] **Step 3: Commit the approved design and plan.**

### Task 2: Port strict corpus and locator primitives

**Files:**
- Create: `corpus/kaiyuan_zhanjing/baseline.json`
- Create: `packages/kb-text-core/pyproject.toml`
- Modify: `packages/kb-text-core/python/kb_text_core/__init__.py`
- Modify: `packages/kb-text-core/python/kb_text_core/anchors.py`
- Modify: `packages/kb-text-core/python/kb_text_core/matching.py`
- Modify: `packages/kb-text-core/python/kb_text_core/parser.py`
- Modify: `packages/kb-text-core/python/kb_text_core/ranking.py`
- Create: `scripts/audit_kaiyuan_baseline.py`
- Modify: `scripts/audit_kaiyuan_corpus.py`
- Create: `scripts/compare_kaiyuan_volumes.py`
- Modify: `scripts/split_kaiyuan_fulltext.py`

**Interfaces:**
- Consumes: current PR #6 `kb_text_core` public functions.
- Produces: strict corpus audit, canonical page-to-volume locator helpers, nested heading extraction and deterministic baseline verification.

- [ ] **Step 1: Add failing tests for nested ancient headings, heading-only classification, canonical fulltext locator and page-volume mismatch detection.**

Run:

```bash
PYTHONPATH=packages/kb-text-core/python pytest -q \
  packages/kb-text-core/tests/test_text_core.py \
  packages/kb-text-core/tests/test_text_core_strict.py
```

Expected before implementation: failures in the new strict cases.

- [ ] **Step 2: Port the reviewed post-PR-#6 implementation from `codex/kaiyuan-corpus-retrieval-v2`.**

The port must preserve these signatures:

```python
def build_anchor_context(text: str, start: int, end: int, *, window: int = 160) -> AnchorContext: ...
def find_match_spans(text: str, query: str, *, variants: list[str] | None = None, allow_loose: bool = True, loose_window: int = 400) -> list[MatchSpan]: ...
def audit_kaiyuan_corpus(fulltext_path: Path, volumes_dir: Path) -> dict[str, Any]: ...
def dedupe_primary_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]: ...
```

- [ ] **Step 3: Run text-core tests.**

Expected: all text-core tests pass.

- [ ] **Step 4: Commit the parser/audit hardening as one reviewable unit.**

Commit message:

```text
feat: harden Kaiyuan corpus audit and locator parsing
```

### Task 3: Port downstream filesystem fallback hardening

**Files:**
- Modify: `apps/star-omen/src/connectors/primary_file_scanner.py`
- Modify: `Makefile`
- Modify: `docs/kaiyuan-corpus-retrieval-v2.md`

**Interfaces:**
- Consumes: `kb_text_core` matching, heading, locator and ranking helpers.
- Produces: canonical `source_locator`, chapter-oriented `matched_headings`, complete scan-before-limit and correctly classified exact/related primary hits.

- [ ] **Step 1: Add failing downstream regression tests.**

Required assertions:

```python
assert hit["source_locator"] == "KR3g0018_031"
assert hit["heading_path"][-1] == "熒惑犯心五"
assert stats["matched_headings"] == ["熒惑犯心五"]
assert heading_only_hit not in stage2_exact
```

- [ ] **Step 2: Port the scanner hardening.**

The scanner must:

```text
scan all eligible files
→ build all match clusters
→ canonicalize locator and volume
→ rank and deduplicate
→ truncate to limit
```

It must never return early from the filesystem loop.

- [ ] **Step 3: Run focused downstream tests.**

```bash
cd apps/star-omen
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
pytest -q tests/test_kaiyuan_retrieval_v2.py tests/test_candidate_sync_v1.py
```

Expected: PASS.

- [ ] **Step 4: Commit downstream hardening.**

Commit message:

```text
feat: harden Kaiyuan fallback provenance and headings
```

### Task 4: Verify the immutable real corpus baseline

**Files:**
- Verify: `apps/local-kb-unified/data/sources/古籍/唐開元占經/唐開元占經-全文合併版.md`
- Verify: `apps/local-kb-unified/data/sources/古籍/唐開元占經/分卷/KR3g0018_000.md` through `KR3g0018_120.md`
- Verify: `corpus/kaiyuan_zhanjing/baseline.json`

**Interfaces:**
- Consumes: strict audit CLI and immutable corpus.
- Produces: release gate that fails on corpus drift, missing volumes, invalid markers or changed raw hash.

- [ ] **Step 1: Run strict corpus audit.**

```bash
make audit-kaiyuan-corpus
```

Expected:

```text
ok=true
section_count=121
volume_file_count=121
page_marker_count=3435
missing_sections=[]
missing_volume_files=[]
different_volumes=[]
page_marker_volume_mismatches=[]
```

- [ ] **Step 2: Run immutable baseline audit.**

```bash
make audit-kaiyuan-baseline
```

Expected: exit code 0 and all recorded counts/hashes match.

- [ ] **Step 3: Commit any generated deterministic report only if the repository policy explicitly tracks it.**

No timestamp-only artifacts are committed.

### Task 5: Full verification and pull request

**Files:**
- Verify: `.github/workflows/kaiyuan-pr-a.yml`
- Verify: all files changed in Tasks 1–4.

**Interfaces:**
- Consumes: completed A.1 branch.
- Produces: reviewable PR into `stable/kaiyuan-v2`.

- [ ] **Step 1: Run all local-equivalent test targets.**

```bash
make contracts-test
make text-core-test
make downstream-test
```

Expected: all pass.

- [ ] **Step 2: Verify no forbidden files or paths are present.**

```bash
git diff --name-only stable/kaiyuan-v2...HEAD | \
  grep -E '(^|/)(\.env|qdrant_storage|postgres_data|ollama_data|models)(/|$)|/Users/'
```

Expected: no output.

- [ ] **Step 3: Open PR to `stable/kaiyuan-v2`.**

Title:

```text
Harden Kaiyuan corpus provenance and primary fallback
```

- [ ] **Step 4: Wait for Python 3.12 CI and inspect failures before merge.**

- [ ] **Step 5: Merge only after all gates pass.**

After A.1 merges, start a separate B1 plan and branch for the real upstream runtime import.
