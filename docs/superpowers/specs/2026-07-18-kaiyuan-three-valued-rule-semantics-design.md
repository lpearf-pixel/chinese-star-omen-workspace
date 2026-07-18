# Kaiyuan Three-Valued Rule Semantics v2 Design

## Goal

Make rule matching distinguish a condition that passed, a condition that failed, and a condition that could not be evaluated because required event data is missing or invalid. Missing angular distance, duration, or visibility must never be treated as a successful trigger.

## Release boundary

- Base branch: `stable/kaiyuan-v2`.
- Feature branch: `codex/kaiyuan-rule-semantics-v2`.
- Target only `stable/kaiyuan-v2`; never target `main`.
- Do not modify ingest, Qdrant collections, raw corpus, candidate workflow, or CText records in this task.
- Preserve B4 fail-closed evidence semantics.

## Current problem

The current matcher uses expressions equivalent to:

```python
angular_ok = True if threshold is None or angular_value is None else ...
duration_ok = True if threshold is None or duration_value is None else ...
```

A rule can therefore be reported as fully triggered when the event did not supply data required by configured thresholds. This conflates:

```text
condition satisfied
condition not configured
condition cannot be evaluated
```

Visibility is handled differently: a required but missing flag becomes false. The engine has no single condition model, no `unknown_conditions`, and no `insufficient_data` result.

## Considered approaches

### A. Treat every missing value as `fail`

This is conservative but semantically inaccurate. A missing observation is not evidence that a threshold was violated, and it makes incomplete historical records indistinguishable from measured negative results.

### B. Three-valued applicable conditions — selected

Each configured condition returns:

```text
pass
fail
unknown
```

Unconfigured conditions are not applicable and are omitted from aggregation. Known failures and unknown inputs produce different match statuses and traces.

This is selected because it is fail-closed without fabricating negative evidence and is auditable in research reports.

### C. Omit missing values from scoring

This preserves old match rates but hides missing evidence and can still produce a full match from only a subset of required conditions. It is rejected.

## Condition model

Add a focused rule-engine module, for example:

```text
src/rule_engine/conditions.py
```

It owns:

```python
class ConditionState(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class ConditionEvaluation:
    name: str
    state: ConditionState
    required: bool
    expected: object
    actual: object
    reason: str
```

The public serialized form is a mapping keyed by condition name. The engine does not serialize an internal `not_applicable` state; an unconfigured condition is simply absent from `condition_states` and the trigger-ratio denominator.

## Applicable conditions

### Core identity conditions

Always evaluate:

```text
body
event_type
```

Evaluate `target` only when the rule supplies a target. A missing rule target is unconstrained and not applicable.

Core conditions use `pass` or `fail`; malformed/missing event identity values are failures because the event does not identify the rule's required phenomenon.

### Numeric threshold conditions

Evaluate only when the threshold configuration contains the relevant requirement:

```text
angular_distance <= angular_distance_threshold_deg
duration_days >= min_duration_days
```

State rules:

```text
valid finite numeric value and threshold satisfied  -> pass
valid finite numeric value and threshold violated   -> fail
missing, null, empty, bool, nonnumeric, NaN, infinity -> unknown
```

Boolean values are not accepted as numbers even though Python treats `bool` as a subclass of `int`.

### Visibility

Evaluate only when `visibility_required=true`:

```text
is_visible is true  -> pass
is_visible is false -> fail
missing/malformed   -> unknown
```

If visibility is not required, it is not applicable and does not affect the ratio.

## Aggregation and match status

Aggregate in this order:

1. If any core identity condition fails: `not_matched`.
2. Otherwise, if any applicable non-core condition fails: `partial_match`.
3. Otherwise, if any applicable condition is unknown: `insufficient_data`.
4. Otherwise, if all applicable conditions pass and evidence is citable: `matched`.
5. Otherwise, if all applicable conditions pass but final evidence is unavailable: `candidate_only`.

A known threshold violation takes precedence over an additional unknown value because the rule is already known not to be fully satisfied. Unknown is used only when the available data has no known failure but cannot establish a full trigger.

## Trigger ratio and scoring

For applicable conditions:

```text
trigger_ratio = pass_count / (pass_count + fail_count + unknown_count)
```

Consequences:

- `unknown` never contributes to the numerator.
- unconfigured conditions do not inflate or dilute the score.
- complete passing data remains compatible with existing scores.
- incomplete data receives a lower score and `insufficient_data` status.

The existing evidence bonus remains unchanged in B5-T01. Conflict-resolution scoring is handled separately in B5-T02.

## Output contract

Additive fields on each rule match and on the selected result:

```json
{
  "condition_states": {
    "body": {
      "state": "pass",
      "required": true,
      "expected": "Mars",
      "actual": "Mars",
      "reason": "exact_match"
    },
    "angular_distance": {
      "state": "unknown",
      "required": true,
      "expected": {"max_deg": 1.0},
      "actual": null,
      "reason": "missing_value"
    }
  },
  "unknown_conditions": ["angular_distance"],
  "failed_conditions": [],
  "missing_conditions": ["angular_distance"],
  "trigger_ratio": 0.75
}
```

Compatibility:

- Keep `missing_conditions`; it becomes the ordered union of failed and unknown conditions.
- Keep `trigger_match_reason`; enrich it but do not remove old keys.
- Keep existing statuses and add `insufficient_data`.
- Keep `candidate_only` boolean; it is true for every non-citable result, including `insufficient_data`, unless a later contract explicitly replaces it.

## Error handling

Condition evaluation must not raise for malformed optional measurement data. It returns `unknown` with a precise reason such as:

```text
missing_value
empty_value
invalid_numeric
non_finite_numeric
invalid_visibility
```

Programming/configuration errors such as an invalid configured threshold should fail validation or raise a clear configuration error rather than silently becoming event-level unknown. B5-T01 will at minimum reject a nonnumeric threshold with a deterministic error in tests.

## Rule ranking behavior

B5-T01 preserves current priority/score sorting to limit scope. `insufficient_data` rows remain visible in `matches`, but a fully matched or candidate-only row with equivalent priority and a higher score naturally ranks above them.

Actual `resolution_policy` execution and group conflict resolution are deferred to B5-T02.

## Testing

Focused tests must cover:

- complete angular/duration/visibility data passes;
- missing angular distance -> unknown and `insufficient_data`;
- invalid/NaN/infinite numeric values -> unknown;
- measured angular or duration failure -> `partial_match`;
- required visibility missing -> unknown;
- required visibility false -> fail;
- unconfigured optional conditions are absent and do not affect ratio;
- core body/event/target mismatch -> `not_matched`;
- all conditions pass + citable evidence -> `matched`;
- all conditions pass + non-citable evidence -> `candidate_only`;
- unknown is never counted as pass;
- old complete-data fixtures remain compatible;
- serialized `RuleMatchResult` contains the additive fields.

Run focused tests first, then the complete downstream and repository gates required by the development manual.

## Completion criteria

B5-T01 is complete when:

- the task ledger and work log are current;
- the selected three-valued model is implemented once in a focused module;
- matcher and result serialization use it;
- all focused and downstream tests pass;
- latest-head governance, stable-core, and applicable upstream regression gates are green;
- the PR targets only `stable/kaiyuan-v2`.
