# Kaiyuan Legacy PR Disposition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove whether legacy PR #1 and #7 are fully superseded by current stable v2, merge the evidence, close only the superseded PRs, and record their final state.

**Architecture:** A docs-only audit freezes live GitHub identities and classifies path plus semantic replacement. Closure is a separate reversible GitHub operation performed only after the audit merges. A final docs-only closeout binds the observed closed state.

**Tech Stack:** GitHub connector/API, Markdown, Git blob SHA, exact commit comparison.

## Global Constraints

- Target only `stable/kaiyuan-v2`; never `main`.
- Do not merge, rebase or cherry-pick either legacy branch.
- Any unresolved behavior/data obligation blocks closure.
- Do not modify PR #54 or substitute AI for Reviewer A/B.
- Do not access or mutate corpus, Qdrant, `local_kb_default`, official ingest, B10-PR-D/E/F, B11/B12 or publishing.

---

### Task 1: Freeze live identities and path matrices

**Files:**
- Create: `docs/development/GOV_T02_LEGACY_PR_DISPOSITION.md`
- Create: `docs/development/gov-t02-legacy-pr-matrix.json`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`

- [x] Record stable `5571ddb34311f1601c8e084efa133be99655cd5a`.
- [x] Record PR #1 base/head, 58 changed paths and diverged ancestry.
- [x] Record PR #7 base/head, 12 changed paths and diverged ancestry.
- [x] Compare every legacy path to stable by existence and blob SHA.
- [x] Persist all 70 rows with legacy/stable blobs, classification, responsibility and concrete stable implementation/test evidence.
- [x] Recompute exact/evolved/retired/unresolved counts from the persisted rows and require unresolved 0/70.
- [x] Require every missing path to be non-behavioral obsolete planning material.

### Task 2: Prove semantic supersession

**Files:**
- Create: `docs/superpowers/specs/2026-08-02-kaiyuan-legacy-pr-disposition-design.md`
- Modify: `docs/development/GOV_T02_LEGACY_PR_DISPOSITION.md`
- Modify: `docs/development/WORK_LOG.md`

- [x] Check all PR #1 candidate-contract, generation, sync, overlay, approval/import and test responsibilities on stable.
- [x] Check all PR #7 matching, ranking, provenance, audit, split, compare, packaging and test responsibilities on stable.
- [x] Verify comments, reviews and unresolved threads are empty for both PRs.
- [x] Mark both dispositions `superseded` with zero unresolved behavior/data rows.

### Task 3: Merge the audit evidence

**Files:**
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/WORK_LOG.md`

- [x] Open a Draft PR from the audit branch to `stable/kaiyuan-v2` (PR #61).
- [x] Verify exact-head changed paths, governance/stable/upstream Actions and independent review.
- [x] Squash merge the audit PR only after Critical 0 / Important 0 and all exact-head gates succeed (`08fb71ab1db7de509154214cca44693a5de4859c`).

### Task 4: Close the superseded legacy PRs

**Files:** none; GitHub PR metadata/comments only.

- [x] Add a hash-bound supersession comment to PR #1 (`5162877413`).
- [x] Close PR #1 without merging or deleting its branch.
- [x] Add a hash-bound supersession comment to PR #7 (`5162877570`).
- [x] Close PR #7 without merging or deleting its branch.
- [x] Re-read both PRs and require `state=closed`, `merged=false`.

### Task 5: Publish final closeout

**Files:**
- Create: `docs/development/GOV_T02_CLOSEOUT.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/WORK_LOG.md`

- [x] Record audit PR and merge SHA plus both legacy closure comments/states.
- [ ] Mark GOV-T02 `DONE` only on the final reviewed closeout head.
- [x] Verify open PRs contain #54 but not #1/#7.
- [ ] Run exact-head docs/governance gates and merge the final closeout PR.
