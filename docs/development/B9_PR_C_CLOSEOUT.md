# B9-PR-C RuleAssessment and Evidence Lineage Closeout

## 2026-07-30 — implementation merged

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Release branch: stable/kaiyuan-v2
Feature branch: codex/kaiyuan-b9-rule-assessment-lineage-v1
PR: #36
Base before merge: 48180f6239187b491e41d9f68be0a9aab8dde95d
Final feature head: c218ce6d364d12964dff17b50d5f7605593d0fd1
Development Governance: 30481026839 — success
B9 RuleAssessment Lineage: 30481027508 — success
Kaiyuan Stable Core: 30481026842 — success
Kaiyuan Upstream Runtime: 30481027262 — success
Squash merge: 38042b995e885101999c93c6698a9544f22a948b
```

## Delivered

- explicit `AstronomyEvent/v1` to existing matcher projection;
- two-pass orchestration that identifies candidates before external retrieval;
- external hydration only for `candidate_only` rows;
- existing matcher/resolver projection into frozen `RuleAssessment/v1`;
- formal and provisional recommendation separation;
- exact-primary hydration with primary-candidate membership, status and provenance validation;
- content-free canonical `EvidenceBundle/v1` lineage;
- serialized build results exclude matcher diagnostics and source text;
- evidence-rich positive fixture and July 21 honest blocked-classical fixture;
- dedicated RuleAssessment CI with retained focused logs.

## Final evidence

```text
Focused exact-head: 35 passed in 1.19s
Full downstream exact-head: 354 passed in 3.37s
Changed files: 22 expected adapter/lineage/test/fixture/governance files
Review threads: 0
Submitted reviews: 0
```

## TDD and independent review history

```text
Initial RED: 3 missing-module collection errors
Fixture GREEN: 22 passed
Review RED 1: 5 failed / 22 passed
Review GREEN 1: 31 passed
Review RED 2: 3 failed / 28 passed
Review GREEN 2: 31 passed
Final review RED: 4 failed / 31 passed
Final GREEN: 35 passed
```

Review fixes covered:

1. no retrieval for core non-matching rules;
2. no retrieval for partial or insufficient-data rows;
3. matcher diagnostics excluded from serialized results;
4. all rule IDs and rule-set versions validated before external effects;
5. non-exact and explicit candidate-only hits blocked;
6. exact hit must belong to primary candidates;
7. exact hit requires exactly one official/fallback provenance route;
8. candidate ordering may change after evidence score upgrades without changing candidate identity set.

## Safety boundary

No editorial copy, Stellarium script, subtitle, audio, video, publishing, full-book rule extraction, corpus/candidate/ingest/Qdrant/collection mutation or `local_kb_default` access occurred in B9-PR-C.

## Follow-on

B9-PR-D must start from the closeout merge's new stable HEAD and consume only frozen `AstronomyEvent/v1`, `RuleAssessment/v1` and `EvidenceBundle/v1`. A `classical_quote` claim may be generated only when the matching lineage entry has `narration_allowed=true`.
