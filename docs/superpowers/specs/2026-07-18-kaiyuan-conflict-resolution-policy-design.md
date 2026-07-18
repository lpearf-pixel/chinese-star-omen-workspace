# Kaiyuan Conflict Resolution Policy v2 Design

## Goal

Execute rule conflict metadata instead of merely reporting that a conflict exists. The resolver must preserve every eligible match for audit while producing a deterministic recommendation, or explicitly withholding one for manual review.

## Scope and safety boundary

- Base: `stable/kaiyuan-v2@e4e25ba39d43270b1d2ac54ae3057eb741161b38`.
- Branch: `codex/kaiyuan-conflict-resolution-v2`.
- Target only `stable/kaiyuan-v2`; never target `main`.
- Do not modify raw corpus, CText records, candidate flow, ingest, retrieval, Qdrant schemas, or `local_kb_default`.
- Preserve B4 fail-closed citable evidence and B5-T01 three-valued conditions.

## Considered approaches

### Inline resolution in `minimal_matcher.py`

This has the smallest file count but mixes condition evaluation, evidence resolution, ranking, policy validation, suppression, and reporting. It makes policy-focused tests difficult and increases regression risk.

### Focused pure resolver module — selected

Add `src/rule_engine/conflict_resolution.py`. It consumes serialized match rows and returns resolved rows plus a summary. The matcher remains responsible for producing matches and adapts the resolver result into its existing response.

This provides a small deterministic boundary, direct unit tests, and no dependency on storage or external services.

### Extensible strategy registry/classes

A class per policy would support third-party policies but adds lifecycle and registration complexity that the four fixed policies do not require. It is deferred until a real extension need exists.

## Eligibility and grouping

- `not_matched` rows are excluded before conflict resolution, as today.
- Rows with a non-empty `conflict_group` are grouped by that exact string.
- Rows without a group remain independent candidates and are never suppressed by another ungrouped row.
- A one-row group is resolved without conflict, but its policy is still validated.
- All rows remain in `matches`; resolution adds metadata and does not delete evidence.

Every eligible row must have a unique, non-empty string `rule_id`. `rule_priority` must be an integer but not a boolean. `match_score` must be finite numeric. `primary_evidence_found` must be boolean. Invalid inputs fail with `ValueError`; they are configuration/contract errors, not event-level unknowns.

## Policy consistency

Supported policies are:

```text
highest_score
highest_priority
prefer_primary_evidence
manual_review
```

Missing policy defaults to `highest_score` for compatibility. Every row in the same group must declare the same normalized policy. Unknown policy or a mixed-policy group raises `ValueError` naming the group and policies. No partial resolution result is returned.

## Deterministic ordering

All orderings end with ascending `rule_id` as the stable tie-breaker.

```text
highest_score:
  match_score descending
  rule_priority ascending
  primary_evidence_found true first
  rule_id ascending

highest_priority:
  rule_priority ascending
  match_score descending
  primary_evidence_found true first
  rule_id ascending

prefer_primary_evidence:
  primary_evidence_found true first
  match_score descending
  rule_priority ascending
  rule_id ascending
```

For `manual_review`, the same order as `highest_score` identifies a provisional candidate only. It never becomes the group's resolved winner.

## Recommendation semantics

For an automatically resolved group:

- the first ordered row is `selected`;
- other group rows are `suppressed`;
- suppressed rows remain in `matches` with `suppressed=true`, `resolution_status=suppressed`, and `suppression_reason` referencing the selected rule and policy.

For `manual_review` with more than one row:

- every row is `resolution_status=manual_review` and `suppressed=false`;
- the group has no `selected_rule_id`;
- `provisional_rule_id` records the deterministic highest-score candidate;
- the group contributes no candidate to the final recommendation.

A one-row `manual_review` group has no actual conflict and is selected normally; manual review only withholds a recommendation when alternatives exist.

The top-level `recommended_rule_id` is selected from automatically resolved group winners and ungrouped rows using the legacy global order: priority ascending, score descending, evidence true first, rule id ascending. `provisional_recommended_rule_id` is populated only when no final recommendation exists and unresolved manual groups have a provisional candidate. This makes provisional status impossible to mistake for a formal recommendation.

## Output contract

Existing fields remain. Add:

```json
{
  "recommended_rule_id": null,
  "provisional_recommended_rule_id": "rule_a",
  "recommendation_status": "manual_review",
  "conflict_trace": [
    {
      "conflict_group": "mars_guarding_xin",
      "resolution_policy": "manual_review",
      "candidate_rule_ids": ["rule_a", "rule_b"],
      "ordered_rule_ids": ["rule_a", "rule_b"],
      "selected_rule_id": null,
      "provisional_rule_id": "rule_a",
      "suppressed_rule_ids": [],
      "status": "manual_review"
    }
  ]
}
```

`recommendation_status` is `selected`, `manual_review`, or `not_matched`. `conflict_detected` is true only for groups containing more than one row. `conflict_reasons` remains as a compatibility summary derived from the trace.

## Testing

Focused tests cover all four policies, every tie-break stage, mixed/unknown policy failure, invalid identifiers and ranking inputs, one-row groups, ungrouped compatibility, manual withholding, provisional semantics, suppression retention, and top-level report propagation. Full downstream and repository gates must remain green.

## Completion criteria

- Task, decision, plan, work log, PR and exact-head CI evidence are current.
- Policy logic is isolated and deterministic.
- Full `matches` remains auditable.
- Manual review cannot silently become a formal recommendation.
- No protected corpus, collection, candidate, ingest, or retrieval behavior changes.
