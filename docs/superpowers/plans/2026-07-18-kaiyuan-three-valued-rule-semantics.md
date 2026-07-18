# Kaiyuan Three-Valued Rule Semantics v2 Implementation Plan

> Required workflow: read `AGENTS.md` and the development manual, update the task ledger, use TDD, debug root causes, and record fresh verification before completion.

**Goal:** Replace implicit “missing means pass” rule checks with auditable `pass | fail | unknown` condition evaluations and add `insufficient_data` without changing Qdrant, corpus, candidate, or B4 evidence behavior.

**Base:** `stable/kaiyuan-v2@8bca22a93c8124d350cf61bbc71b37c36a4af0b8`

**Branch:** `codex/kaiyuan-rule-semantics-v2`

**Design:** `docs/superpowers/specs/2026-07-18-kaiyuan-three-valued-rule-semantics-design.md`

**Task:** `B5-T01` in `docs/development/TASKS.md`

## Constraints

- Never target `main`.
- Never access or mutate `local_kb_default`.
- Do not change raw corpus, CText records, ingest, retrieval, or candidate sync.
- Preserve B4 `citable` semantics.
- Do not implement conflict resolution in this task; that is B5-T02.
- Missing or malformed event measurements must not raise and must not pass.
- Invalid threshold configuration must fail clearly.

---

## Task 1: Define the condition contract with failing tests

**Files:**
- Create: `apps/star-omen/src/rule_engine/conditions.py`
- Create: `apps/star-omen/tests/test_rule_condition_states_v2.py`

- [ ] Write tests for `ConditionState.PASS`, `FAIL`, `UNKNOWN` serialization.
- [ ] Write tests for finite numeric max/min evaluation.
- [ ] Write tests for missing, empty, bool, nonnumeric, NaN and infinity becoming `unknown`.
- [ ] Write tests for required visibility true/false/missing/malformed.
- [ ] Write tests proving unconfigured conditions are omitted rather than treated as pass.
- [ ] Confirm RED because the module does not exist.
- [ ] Implement the smallest `ConditionEvaluation` and evaluator helpers.
- [ ] Run the focused test file.

## Task 2: Extend the match-result contract

**Files:**
- Modify: `apps/star-omen/src/rule_engine/match_result.py`
- Extend: `apps/star-omen/tests/test_rule_condition_states_v2.py`

- [ ] Add failing serialization tests for `condition_states`, `unknown_conditions`, `failed_conditions`, and `trigger_ratio`.
- [ ] Preserve existing constructor fields and serialized keys.
- [ ] Add the fields with safe defaults only where compatibility requires them.
- [ ] Run focused tests.

## Task 3: Replace boolean trigger evaluation in the matcher

**Files:**
- Modify: `apps/star-omen/src/rule_engine/minimal_matcher.py`
- Create/modify: matcher tests under `apps/star-omen/tests/`

- [ ] Add failing test: missing angular distance with configured threshold -> `insufficient_data`.
- [ ] Add failing test: missing duration -> `insufficient_data`.
- [ ] Add failing test: required visibility missing -> `insufficient_data`.
- [ ] Add failing test: explicit threshold violation -> `partial_match`.
- [ ] Add failing test: core body/event/target mismatch -> `not_matched`.
- [ ] Add failing test: all applicable conditions pass + citable -> `matched`.
- [ ] Add failing test: all applicable conditions pass + non-citable -> `candidate_only`.
- [ ] Add failing test: unknown and known failure together -> `partial_match`.
- [ ] Implement applicable-condition construction and ordered aggregation.
- [ ] Compute `trigger_ratio = pass / applicable` with unknown in the denominator.
- [ ] Populate additive condition fields and compatibility `missing_conditions`.
- [ ] Run focused matcher tests.

## Task 4: Validate threshold configuration deterministically

**Files:**
- Modify if needed: `apps/star-omen/src/rule_engine/thresholds.py`
- Extend condition/matcher tests.

- [ ] Add failing test for a nonnumeric configured angular or duration threshold.
- [ ] Decide and document the exact exception type/message.
- [ ] Reject invalid configuration rather than classifying it as event-level unknown.
- [ ] Preserve YAML and fallback loader compatibility.
- [ ] Run threshold and matcher tests.

## Task 5: Update downstream reports and compatibility tests

**Files:**
- Modify only as required: CLI/research report adapters that serialize matcher output.
- Update existing rule-engine tests whose expectations encoded “missing means pass”.
- Add focused report tests if output is transformed.

- [ ] Confirm `condition_states`, `unknown_conditions`, and `trigger_ratio` reach CLI/report JSON.
- [ ] Preserve old keys and complete-data behavior.
- [ ] Ensure `primary_evidence_found` still depends only on B4 `status=citable`.
- [ ] Ensure `candidate_only` remains true for non-citable/insufficient results.
- [ ] Run full downstream tests and fix only root causes.

## Task 6: Documentation, decision record, and CI

**Files:**
- Modify: `docs/development/DECISIONS.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`
- Update this plan status.

- [ ] Record the selected three-valued aggregation decision.
- [ ] Move B5-T01 to `VERIFYING` before final gates.
- [ ] Open a draft PR to `stable/kaiyuan-v2`.
- [ ] Run governance, stable-core, downstream, and applicable upstream regression gates on the latest head.
- [ ] Review the diff for accidental changes to corpus/Qdrant/candidate behavior.
- [ ] Record workflow run IDs and exact head SHA.
- [ ] Mark B5-T01 `DONE` only after successful merge evidence; otherwise keep `VERIFYING`.
- [ ] Squash merge only into `stable/kaiyuan-v2`.

## Verification commands

Focused examples:

```bash
cd apps/star-omen
pytest -q tests/test_rule_condition_states_v2.py
pytest -q tests -k 'rule and (condition or matcher)'
```

Repository gates:

```bash
make contracts-test
make text-core-test
make downstream-test
make upstream-test
python scripts/check_development_governance.py --base <base> --head <head>
```

CI is the authoritative cross-environment evidence. Do not claim completion from an older green commit after changing documentation or code.
