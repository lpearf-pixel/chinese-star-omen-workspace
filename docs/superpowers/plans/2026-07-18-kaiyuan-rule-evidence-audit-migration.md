# Kaiyuan Rule Evidence Audit and Migration v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax.

**Goal:** Build a fail-closed bulk rule-evidence audit that proposes and atomically writes only uniquely verified citable migrations.

**Architecture:** A pure migration planner parses primary sources via `kb-text-core`, classifies each rule, validates every proposed patch through the B4 resolver, and optionally writes a separate output file. CLI wiring remains a thin adapter.

**Tech Stack:** Python 3.9/3.12, pytest, `kb-text-core`, existing evidence resolver.

## Global Constraints

- Target only `stable/kaiyuan-v2` through PR.
- Never mutate raw corpus, input rule files, `main`, `local_kb_default`, candidate state, ingest, retrieval, or Qdrant.
- Only unique exact raw/normalized passage matches may be migrated.

### Task 1: Planner contract and RED

**Files:** create `apps/star-omen/src/rule_engine/rule_evidence_migration.py`; create `apps/star-omen/tests/test_rule_evidence_migration_v2.py`.

- [ ] Write failing tests for all seven statuses and deterministic counts.
- [ ] Run focused tests and observe missing-module RED.
- [ ] Implement source loading, rule validation, exact matching and proposal construction.
- [ ] Validate each proposal with `resolve_evidence` and run focused GREEN.

### Task 2: Safe apply and CLI

**Files:** modify planner/test; modify `apps/star-omen/src/cli.py`; add CLI tests.

- [ ] Write failing tests for separate output, input alias refusal, atomic replace and source byte preservation.
- [ ] Implement plan serialization and safe apply.
- [ ] Add `audit-rule-evidence-migration` adapter without changing existing audit behavior.
- [ ] Run focused CLI and planner tests.

### Task 3: Repository fixture migration and regression

**Files:** add a generated migrated rules fixture only if current legacy reference is uniquely provable; update audit documentation and work log.

- [ ] Run the planner against repository primary sources.
- [ ] Keep ambiguous/unresolved items candidate-only; do not hand-author citable fields.
- [ ] Run downstream, contracts, text-core, upstream and governance gates.
- [ ] Move task to VERIFYING, record exact evidence, review, ready and squash merge.
