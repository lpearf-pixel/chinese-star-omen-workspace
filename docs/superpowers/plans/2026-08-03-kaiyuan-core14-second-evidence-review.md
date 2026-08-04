# Core14 Disputed-Case Second Evidence Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an append-only, source-bound second evidence decision for C03, C24, C33 and C47, then bind that evidence to PR #54 without substituting for Reviewer B.

**Architecture:** Keep the completed R02 audit and Reviewer workbooks immutable. Add one structured JSON delta register and one readable adjudication report; both refer to fixed source identities and state only what changed after the first review. Validate case coverage, status boundaries, source references and forbidden-scope absence before publishing metadata to PR #54.

**Tech Stack:** Markdown, strict JSON, Python standard library validation, Git and the connected GitHub application.

## Global Constraints

- Target only `stable/kaiyuan-v2`; never target or modify `main`.
- Preserve raw corpus bytes, page markers, original glyphs and prior R02 audit artifacts.
- Do not modify Reviewer A or Reviewer B workbook bytes in the repository task.
- Reviewer B must remain a different independent human; AI research is not human-review evidence.
- Do not freeze thresholds, start B10-PR-D/E/F, ingest, access Qdrant, access `local_kb_default`, or modify runtime code, main rules or main data.
- PR #54 may receive review metadata, but its implementation head must not change in this task.

---

### Task 1: Freeze Scope and Source Identities

**Files:**
- Modify: `docs/development/TASKS.md`
- Create: `docs/superpowers/plans/2026-08-03-kaiyuan-core14-second-evidence-review.md`
- Read: `corpus/research_sources/b10-core14/wikisource-revision-register.json`
- Read: `corpus/research_sources/b10-core14/audit-early.json`
- Read: `corpus/research_sources/b10-core14/audit-middle.json`
- Read: `corpus/research_sources/b10-core14/audit-late.json`

**Interfaces:**
- Consumes: R02 frozen case IDs, locators, source revisions and first-review decisions.
- Produces: task scope and immutable input set for the delta review.

- [x] **Step 1: Mark B10-R06 `IN_PROGRESS` with the four exact case IDs and exclusions**

Record `C03`, `C24`, `C33`, `C47` and the evidence-only boundary in `TASKS.md` before creating evidence artifacts.

- [x] **Step 2: Verify pinned source coverage**

Run:

```bash
python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path('corpus/research_sources/b10-core14/wikisource-revision-register.json').read_text())
found = {case for row in data['volumes'] for case in row['cases']}
required = {'C03', 'C24', 'C33', 'C47'}
assert required <= found, sorted(required - found)
print('PINNED_SOURCE_COVERAGE_OK', ','.join(sorted(required)))
PY
```

Expected: `PINNED_SOURCE_COVERAGE_OK C03,C24,C33,C47`.

### Task 2: Build the Append-Only Delta Decision

**Files:**
- Create: `corpus/research_sources/b10-core14/disputed-case-second-review.json`
- Create: `docs/research/core14-case-audits/disputed-case-second-review.md`
- Create: `docs/research/core14-case-audits/reviewer-b-disputed-case-source-pack.md`

**Interfaces:**
- Consumes: pinned source revisions, the R02 audits and direct source-context comparisons.
- Produces: exactly four delta decisions with `reviewer_b_required=true` where final human adjudication remains outstanding.

- [x] **Step 1: Recheck exact local source context and fixed public revisions**

For each case, record the carrier volume/page marker, fixed Wikisource revision, Kanripo identity, left/right boundary, parallel-text evidence and unresolved readings. Do not normalize or overwrite source strings.

- [x] **Step 2: Write the four decisions**

Use these evidence-constrained states:

```text
C03 = needs_review; not a terminal logical conflict; split by source and relation
C24 = ambiguous; split S8/S9; 客環守 and duration/shape variants unresolved
C33 = needs_review; preceding 留守 clause excluded; right boundary incomplete
C47 = eligible; no duplicate tag without a concrete duplicate_of identifier
```

- [x] **Step 3: Separate formal-candidate value from current citation eligibility**

Keep all four as research/formal candidates where applicable, but retain `citation_eligible=false` for C03, C24 and C33 pending the stated evidence or Reviewer B decision. C47 may remain citation-eligible with its recorded textual-variant disclosure.

- [x] **Step 4: Create a neutral Reviewer B source pack**

List only frozen locators, source strings, fixed revision links and neutral
questions. Do not expose Reviewer A selections or the second-review
recommendations in that file.

### Task 3: Validate Evidence and Frozen Boundaries

**Files:**
- Modify: `docs/development/WORK_LOG.md`
- Modify: `docs/development/TASKS.md`

**Interfaces:**
- Consumes: the two Task 2 artifacts.
- Produces: deterministic validation evidence and `VERIFYING` state; it does not produce human approval.

- [x] **Step 1: Validate strict JSON and case/status invariants**

Run a Python standard-library check requiring exactly four unique cases, allowed statuses, exact source references, `duplicate_of=null` for C47, and `reviewer_b_completed=false` globally.

- [x] **Step 2: Run governance and forbidden-path checks**

Run:

```bash
B10_PYTEST_DEPS="$(mktemp -d /tmp/kaiyuan-pytest-deps-XXXXXX)"
python -m pip install --disable-pip-version-check --target "$B10_PYTEST_DEPS" 'pytest==8.3.5'
PYTHONPATH="$B10_PYTEST_DEPS" python -m pytest -q scripts/tests/test_check_development_governance.py
python scripts/check_development_governance.py --base stable/kaiyuan-v2 --head HEAD
git diff --check stable/kaiyuan-v2...HEAD
```

Expected: five governance tests pass, the governance checker passes and `git diff --check` is silent.

- [x] **Step 3: Record hashes and move B10-R06 to `VERIFYING`**

Record SHA-256 for the JSON and report, exact base/head, validation commands, and the unchanged blocker: Reviewer B is not started.

### Task 4: Publish Review Metadata Without Changing PR #54 Head

**Files:**
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: `docs/development/TASKS.md`

**Interfaces:**
- Consumes: validated Task 2 artifact hashes and exact Git branch head.
- Produces: a research-support pull request plus a hash-bound PR #54 status comment.

- [ ] **Step 1: Commit and publish the evidence-support branch**

Push `codex/kaiyuan-b10-core14-second-review-v1` and open a Draft PR targeting only `stable/kaiyuan-v2`.

- [ ] **Step 2: Add one PR #54 comment**

The comment must name the support PR/head, both artifact hashes, all four case dispositions, Reviewer A completed, Reviewer B not started, and state that PR #54 remains Draft/BLOCKED and PR-D/E/F remain forbidden.

- [ ] **Step 3: Re-read live refs and PR states**

Confirm `stable/kaiyuan-v2`, PR #54 head, the support PR head, review threads and open-PR set. Any drift is recorded; no merge is performed in this task.

- [ ] **Step 4: Mark B10-R06 `DONE` only after GitHub evidence exists**

Record the support PR URL/number and PR #54 comment ID in `WORK_LOG.md`, then mark only B10-R06 `DONE`. B10-PR-C remains `BLOCKED` until a different human returns Reviewer B and the canonical threshold-freeze gate passes.
