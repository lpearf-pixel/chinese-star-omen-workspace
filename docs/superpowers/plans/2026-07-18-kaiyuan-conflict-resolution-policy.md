# Kaiyuan Conflict Resolution Policy v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute four deterministic conflict policies while preserving every match and distinguishing formal from provisional recommendations.

**Architecture:** A pure `conflict_resolution.py` module validates eligible rows, groups them, orders each group by policy, annotates selected/suppressed/manual rows, and returns a summary. `minimal_matcher.py` delegates only after B5-T01 matching and exposes the resulting trace through the existing report contract.

**Tech Stack:** Python 3.9/3.12, dataclasses/typed dictionaries using existing dict contracts, pytest.

## Global Constraints

- Base is `stable/kaiyuan-v2@e4e25ba39d43270b1d2ac54ae3057eb741161b38`.
- Target only `stable/kaiyuan-v2`; never target `main`.
- Never access or mutate `local_kb_default`.
- Do not modify corpus, CText, candidate, ingest, retrieval, Qdrant, B4 evidence, or B5-T01 condition semantics.
- Every production behavior begins with an observed failing test.

---

### Task 1: Define automatic conflict policies

**Files:**
- Create: `apps/star-omen/src/rule_engine/conflict_resolution.py`
- Create: `apps/star-omen/tests/test_conflict_resolution_policy_v2.py`

**Interfaces:**
- Consumes: `list[dict[str, Any]]` eligible match rows.
- Produces: `resolve_rule_conflicts(matches: list[dict[str, Any]]) -> ConflictResolutionResult` with annotated `matches`, `recommended_rule_id`, `provisional_recommended_rule_id`, `recommendation_status`, `conflict_detected`, `conflict_reasons`, and `conflict_trace`.

- [ ] Write failing tests for `highest_score`, `highest_priority`, and `prefer_primary_evidence`, including final `rule_id` ties.
- [ ] Run `cd apps/star-omen && pytest -q tests/test_conflict_resolution_policy_v2.py` and confirm import failure because the resolver does not exist.
- [ ] Implement input validation, grouping, the three order keys, selected/suppressed annotations, and compatibility reasons.
- [ ] Re-run the focused file and confirm automatic-policy tests pass.
- [ ] Commit test and minimal implementation.

### Task 2: Define manual review and invalid configuration behavior

**Files:**
- Modify: `apps/star-omen/tests/test_conflict_resolution_policy_v2.py`
- Modify: `apps/star-omen/src/rule_engine/conflict_resolution.py`

**Interfaces:**
- Consumes: the resolver from Task 1.
- Produces: explicit manual group trace and fail-closed configuration validation.

- [ ] Add failing tests proving multi-row `manual_review` clears formal selection, retains all rows, and provides only a provisional id.
- [ ] Add failing tests for mixed group policies, unknown policy, empty/duplicate ids, bool priority, non-finite score, and non-boolean evidence flag.
- [ ] Run focused tests and confirm failures identify missing manual/validation behavior.
- [ ] Implement manual resolution and deterministic `ValueError` paths without returning partial results.
- [ ] Run focused tests and confirm pass.
- [ ] Commit the second behavior slice.

### Task 3: Integrate resolver with matcher and report output

**Files:**
- Modify: `apps/star-omen/tests/test_rule_matcher.py`
- Modify: `apps/star-omen/src/rule_engine/minimal_matcher.py`
- Modify: `apps/star-omen/docs/rule-conflict-resolution.md`

**Interfaces:**
- Consumes: `resolve_rule_conflicts` result.
- Produces: existing matcher output plus `provisional_recommended_rule_id`, `recommendation_status`, `conflict_trace`, and per-row resolution fields.

- [ ] Add failing matcher tests for all automatic policies, manual withholding, suppression retention, trace propagation, and no-conflict compatibility.
- [ ] Run the focused matcher tests and confirm missing output/incorrect legacy selection failures.
- [ ] Replace inline conflict detection and global recommendation with the resolver call; map the selected row into existing top-level fields.
- [ ] Update the user-facing conflict policy document with exact ordering and manual semantics.
- [ ] Run `pytest -q tests/test_conflict_resolution_policy_v2.py tests/test_rule_matcher.py` and confirm pass.
- [ ] Commit integration.

### Task 4: Regression, governance, and release evidence

**Files:**
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/DECISIONS.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: this plan only to mark completed checklist items when evidence exists.

**Interfaces:**
- Consumes: all B5-T02 behavior and tests.
- Produces: auditable VERIFYING/CI/review/merge state.

- [ ] Run focused tests, then `make downstream-test`, `make contracts-test`, `make text-core-test`, and `make upstream-test`.
- [ ] Add D-012 with exact policy and recommendation semantics.
- [ ] Record RED/GREEN commands, results, branch, PR, and risks in `WORK_LOG.md`; move B5-T02 to `VERIFYING` before final gates.
- [ ] Push the branch and ensure the draft PR base is exactly `stable/kaiyuan-v2`.
- [ ] Run governance against the actual base/head and wait for every latest-head required workflow.
- [ ] Review changed files and threads; only then mark ready and squash merge.
- [ ] Record the actual merge commit from GitHub in the next feature branch before marking B5-T02 `DONE`.
