# B9-PR-E Start — Atomic Package, Review, Preview and E2E

## Verified repository facts

```text
Verified at: 2026-07-30
Stable branch: stable/kaiyuan-v2
Exact base: d16e75d9eda153c13fcbcfc13449c49bb1a8af60
Feature branch: codex/kaiyuan-b9-package-review-preview-v1
Release target: stable/kaiyuan-v2
Forbidden target: main
Open legacy PRs: #1, #7
```

B9-PR-D implementation PR #38 and docs-only closeout PR #39 are merged. This branch was created from the closeout squash and contains no inherited unmerged implementation.

## Scope

B9-PR-E is the final B9 implementation slice. It may add only:

- deterministic SRT from the reviewed claim/shot timeline;
- canonical package-member manifest and hash inventory;
- atomic same-filesystem no-overwrite publication;
- four independent review dimensions: astronomy, classical evidence, editorial, render;
- bounded FFmpeg preview argv construction without shell execution;
- optional local/self-hosted capability evidence records;
- hermetic July 21 blocked-classical and evidence-rich citable E2E fixtures.

## Frozen inputs and reused boundaries

B9-PR-E consumes without reinterpreting:

```text
AstronomyEvent/v1
RuleAssessment/v1
VideoPackage/v1
EvidenceBundle/v1
EditorialPackage/v1
StellariumScript/v1
```

It must preserve:

- content-bound package and claim identities;
- exact quote-asset-set equality with narration-allowed lineage;
- candidate/ambiguous/missing evidence never becoming classical narration;
- deterministic `.ssc` and its fixed command allowlist;
- Stellarium as renderer only;
- no official ingest or Qdrant writes.

## Resource and path limits

```text
Structured package maximum: 10 MiB, excluding optional media
Preview resolution: 1080x1920
Preview timeout: 120 seconds
Preview audio: optional/absent for B9
Completed output overwrite: forbidden
Symlink/traversal/absolute member paths: forbidden
```

All package members are validated in staging before publication. Publication must use same-filesystem atomic no-overwrite semantics and must leave no completed or partial output on failure.

## TDD protocol

1. Commit governance/start evidence before production code.
2. Commit tests for missing `package`, `review`, `subtitle` and `preview` modules.
3. Observe exact-head RED in the dedicated focused workflow.
4. Implement the minimum deterministic pure builders first.
5. Add filesystem publication only after pure validation is green.
6. Inject tampering, traversal, race, timeout, capability and review failures.
7. Run focused, full downstream, upstream/runtime and governance gates.
8. Keep the PR draft until independent review and final exact-head workflows pass.

## Explicit exclusions

No TTS, voice cloning, `final.mp4`, batch generation, arbitrary FFmpeg filters, shell execution, automatic publishing, whole-book structuring, corpus/candidate/ingest/Qdrant/collection mutation, `local_kb_default` access or `main` change.
