# Core14 Provisional Usability Stratification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the user-approved 11+3 Core14 operational split without converting Reviewer A assistance into final two-human approval.

**Architecture:** Add one deterministic JSON register as the machine-readable source of the provisional-use boundary and one research-facing Markdown explanation. Test the exact frozen denominator, disjointness, allowed statuses and fail-closed gates directly against the JSON. Keep Reviewer workbooks and the R02/R06 evidence decisions immutable.

**Tech Stack:** strict JSON, Markdown, Python standard-library validation, pytest, Git and the connected GitHub application.

## Global Constraints

- Target only Draft PR #64 and `stable/kaiyuan-v2`; never modify or target `main`.
- Reviewer A remains `USER_CONFIRMED_EVIDENCE_REVISED_READY_FOR_RETURN` and Reviewer B remains `UNLABELLED_HUMAN_REVIEW_NOT_STARTED`.
- The provisional-use set is exactly `C02,C09,C11,C13,C14,C31,C41,C43,C44,C45,C47`.
- The isolated evidence-supplement set is exactly `C03,C24,C33`.
- `provisional_usable_pending_reviewer_b` permits internal research use only; it is not final approval or authority for threshold freeze, release, ingest or promotion.
- Do not modify either Reviewer workbook, R02/R06 evidence decisions, raw corpus, runtime rules, formal KB, Qdrant, `local_kb_default`, B10-PR-D/E/F, B11/B12 or automatic publishing.

---

### Task 1: Define the machine-readable stratification contract

**Files:**
- Create: `scripts/tests/test_b10_core14_provisional_usability.py`
- Create: `corpus/research_sources/b10-core14/provisional-usability-stratification.json`

**Interfaces:**
- Consumes: the frozen Core14 case denominator and the completed R06 case dispositions.
- Produces: schema `b10-core14-provisional-usability/v1` with exactly two disjoint sets and explicit fail-closed governance gates.

- [x] **Step 1: Write the failing data-contract test**

Create a pytest test that loads the JSON register and asserts the exact 14-case denominator, the exact 11 and 3 case sets, unique/disjoint membership, the two allowed operational statuses, `reviewer_b_completed=false`, `two_distinct_humans_gate_passed=false`, and all threshold/release/ingest/promotion flags false.

- [x] **Step 2: Run the focused test and observe RED**

Run:

```bash
PYTHONPATH="$B10_PYTEST_DEPS" python -m pytest -q scripts/tests/test_b10_core14_provisional_usability.py
```

Expected: failure because `provisional-usability-stratification.json` does not exist.

- [x] **Step 3: Create the minimal strict JSON register**

Each of the 11 provisional rows uses `operational_status=provisional_usable_pending_reviewer_b`, `internal_research_use=true`, `final_human_approval=false`, and `reviewer_b_confirmation_required=true`. Each isolated row uses `operational_status=isolated_evidence_supplement`, `internal_research_use=false`, `citation_eligible=false`, and a case-specific reason matching the R06 record.

- [x] **Step 4: Rerun the focused test and observe GREEN**

Expected: `1 passed`.

### Task 2: Document the usage boundary and durable decision

**Files:**
- Create: `docs/research/core14-case-audits/provisional-usability-stratification.md`
- Modify: `docs/development/DECISIONS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`

**Interfaces:**
- Consumes: the tested JSON register.
- Produces: a researcher-facing usage matrix and durable governance rule separating provisional use from final release eligibility.

- [x] **Step 1: Add the 11+3 usage matrix**

State permitted internal uses for the 11 cases and explicit prohibitions for both sets. Record C03/C24/C33 as isolated with their existing `needs_review|ambiguous|needs_review` evidence states.

- [x] **Step 2: Append the decision without rewriting history**

Record that Reviewer-A-confirmed material may be used for internal mapping, retrieval and atomic-rule research while marked pending Reviewer B, but no such status satisfies the two-human gate or authorizes a canonical threshold freeze, formal rule release, ingest or promotion.

- [x] **Step 3: Refresh current project facts**

Record the live stable SHA, Draft PR #54/#64 state and B10-R07 `IN_PROGRESS` status without changing the frozen B10-PR-C blocker.

### Task 3: Verify and publish the provisional layer

**Files:**
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Consumes: the tested register, usage document and live GitHub facts.
- Produces: a verified Draft PR #64 update and a hash-bound PR #54 status note; no formal release artifact.

- [x] **Step 1: Move B10-R07 to `VERIFYING` and record local evidence**

Record the JSON and Markdown SHA-256 values, exact case counts and the unchanged human gate.

- [x] **Step 2: Run the full applicable verification set**

Run the focused test, governance unit tests, development-governance checker, strict JSON parse, `compileall`, `git diff --check`, frozen-workbook absence scan and a replay asserting `11+3=14` with zero overlap.

- [ ] **Step 3: Publish by fast-forwarding Draft PR #64 only**

Create a commit whose parent is the live PR #64 head, update `codex/kaiyuan-b10-core14-second-review-v1` without force, and update PR #64 metadata. Add one PR #54 comment binding the new register/report hashes while preserving its exact head and Draft/BLOCKED state.

- [ ] **Step 4: Re-read remote refs and close only B10-R07**

Confirm stable and PR #54 heads did not move, PR #64 contains the exact local tree, and both PRs remain Draft. Record the commit/comment references in `WORK_LOG.md`, mark B10-R07 `DONE`, and rerun the complete local validation before the final fast-forward closeout commit.
