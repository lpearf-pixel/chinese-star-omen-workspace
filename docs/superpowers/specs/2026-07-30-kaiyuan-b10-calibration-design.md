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
- Reviewers do not need a GitHub account, email address, employee number or
  pre-existing identifier. The project deterministically issues exactly two
  pseudonymous reviewer slot IDs from the pilot ID. Slot IDs are audit keys,
  not proof of personhood: two different people must still complete the two
  worksheets independently, and slot creation alone never counts as review.
- A freeze is `approved` only with passing validation metrics, zero citable
  false positives and a non-placeholder human approval record. Otherwise it is
  `needs_human_approval` and cannot unlock PR-D.
- Existing contract examples are test inputs, not pilot evidence.
- Pilot handoff uses a separate strict selection contract. A human prepares the
  passage IDs and stratum metadata against a real passage inventory; the
  builder validates source identity, unique/non-ambiguous passages and the
  frozen category/relation/computability/risk coverage. It does not infer
  strata or labels.
- The builder emits exactly two canonical worksheets, one per issued anonymous
  slot. The case content and ordering are identical while the reviewer ID is
  slot-specific. Annotation fields remain absent and
  `human_review_completed=false`; worksheet creation is not review evidence.
- Worksheets may contain the selected raw passage snapshots required by a
  human reviewer, but are caller-selected local outputs and are never committed
  as repository fixtures. Holdout cases and sealed labels are not accepted by
  the handoff builder.

## Acceptance

Strict unknown-field rejection, finite bounded metrics, split disjointness,
manifest/hash binding, ordinary holdout denial, release-gate holdout access,
deterministic canonical bytes, tamper rejection, atomic no-overwrite and
threshold floors all have tests. Anonymous reviewer slot IDs must be stable,
distinct, namespace-confined and rejected when supplied outside their pilot.
Pilot selection/worksheet contracts must reject incomplete coverage, inventory
drift, unknown or ambiguous passage IDs, duplicate cases, cross-slot content
drift, prefilled annotations, holdout selection and output overwrite.
