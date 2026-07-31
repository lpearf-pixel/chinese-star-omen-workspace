# B10-PR-C Calibration Design

## Scope

Provide strict, canonical contracts for golden cases, split manifests,
calibration observations/reports and threshold freezes. Ordinary APIs must
never reveal sealed-holdout expected labels. All outputs are caller-selected,
atomic and no-overwrite.

## Decisions

- Development and validation cases may carry reviewed expected labels.
- Holdout public fixtures carry only stratum and source identity. Expected
  labels live in a separate sealed asset and require an explicit release-gate
  API.
- Metrics are computed from immutable reviewed observations, not inferred from
  prose. Precision, recall, agreement and citable false positives retain their
  integer denominators.
- A freeze is `approved` only with passing validation metrics, zero citable
  false positives and a non-placeholder human approval record. Otherwise it is
  `needs_human_approval` and cannot unlock PR-D.
- Existing contract examples are test inputs, not pilot evidence.

## Acceptance

Strict unknown-field rejection, finite bounded metrics, split disjointness,
manifest/hash binding, ordinary holdout denial, release-gate holdout access,
deterministic canonical bytes, tamper rejection, atomic no-overwrite and
threshold floors all have tests.
