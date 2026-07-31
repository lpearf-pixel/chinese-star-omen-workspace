# B10-PR-C Calibration Implementation Plan

1. Register the exact PR-B merge and PR-C truth boundary.
2. Write failing tests for strict golden cases/manifests and sealed holdout.
3. Implement canonical calibration metrics and threshold-freeze contracts.
4. Add policy/runbook documentation for the human pilot handoff.
5. Add deterministic project-local anonymous reviewer slots so reviewers do
   not need external account IDs; keep two-person independence as a human
   evidence gate.
6. Run focused, full, governance and exact-head hosted gates.
7. Write failing tests for a strict real-inventory pilot selection and two
   content-identical, slot-specific, unlabelled worksheets.
8. Implement the minimum deterministic handoff builder with frozen coverage,
   source/hash/ambiguity validation and caller-selected no-overwrite
   publication. Do not infer strata, run an extractor/model, read holdout
   labels or commit generated source text.
9. Extend the runbook with the one-command local-corpus handoff and keep PR-C
   blocked until two different people return completed worksheets.

PR-D must not start until an approved freeze backed by reviewed pilot evidence
is committed and independently verified.
