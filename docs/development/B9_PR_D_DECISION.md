# B9-PR-D Editorial Package and Stellarium Script Decision

## Status

```text
Task: B9-PR-D
Branch: codex/kaiyuan-b9-editorial-stellarium-v1
PR: #38
Base: stable/kaiyuan-v2 at 523c724add978bc4bb51fc07a716c6a852c95447
Successful implementation head before final docs: f4520ac706a07f309d063180fd7e7d42d7aac0ad
State: VERIFYING
```

## Accepted editorial boundary

1. B9-PR-D supports exactly one fixed Chinese `zh-CN` vertical template and exactly `80,000 ms`; it is not a general template engine.
2. The frozen `VideoPackage/v1` contract is not changed. B9-D adds a stricter internal `EditorialPackage/v1` that binds the video package to a deterministic one-shot-per-claim timeline.
3. Each claim has one claim class, stable ID, same-package typed references and a pending editorial review status.
4. The supported claim classes remain:

```text
astronomy_fact
classical_quote
historical_context
modern_interpretation
production_instruction
```

5. One astronomy claim requires exactly one accepted angular-distance/separation measurement. A verified star identity may use an explicit traditional name; verified membership must use membership-limited wording.
6. B9 supports zero or one historical-context asset. When present, the compiled claim explicitly states the source type and source title; multiple assets fail instead of being silently truncated.
7. B9 supports exactly one approved modern-interpretation asset. Its text and package disclosure must include `现代文化转译`.
8. `开口破局` / `開口破局` is allowed only in modern interpretation. It is rejected in historical context, classical quotation and production instruction.
9. Deterministic fate promises, fear language and coercive celestial claims are checked after NFKC normalization and removal of spacing/punctuation, so superficial formatting cannot bypass the gate.
10. `VideoPackage/v1.package_id` is derived from the event, assessment, template identity and the actual compiled claim classes/text/source references. Changing claim content cannot preserve the old package ID.

## Accepted classical-evidence boundary

A classical quotation is compiled only when all of the following hold:

- `RuleAssessment/v1.narration_eligibility == eligible`;
- the assessment has the same rule-set version as `EvidenceBundle/v1`;
- exactly one evidence-lineage entry has `narration_allowed=true`;
- that lineage belongs to the formally recommended rule;
- the matching assessment evidence reference is `citable`;
- assessment and lineage agree on evidence ID, locator and content hash;
- the approved quote asset SHA-256 equals the lineage content hash;
- the supplied quote-asset ID set exactly equals the narration-allowed classical-lineage ID set.

Blocked, candidate-only, ambiguous, missing or mismatched lineage produces no placeholder quotation and keeps `classical_status=omitted_no_allowed_lineage`. Supplying an unauthorized or extra quote asset fails explicitly; it is not silently dropped.

## Accepted asterism boundary

- Verified identity and verified membership must bind to the event target through the modern object ID or the reviewed template object/display mapping.
- An unrelated verified mapping fails closed; it cannot rename an arbitrary event target.
- Verified membership uses explicit member-relation language rather than identity wording.
- Ambiguous, region-only or unresolved mappings do not gain explicit traditional-star narration in this phase.

## Accepted shot-list boundary

`EditorialPackage/v1` enforces:

- unique shot IDs;
- exactly one shot for each claim;
- shot order equals claim order;
- shot claim class equals the referenced claim class;
- timeline begins at `0`, is continuous and ends at `80,000 ms`;
- each shot target has an allowlisted render-object mapping;
- `included_citable` has exactly one classical claim;
- `omitted_no_allowed_lineage` has no classical claim;
- disclosures are unique and modern interpretation includes its required disclosure.

Canonical editorial JSON is UTF-8, sorted-key, finite JSON with one trailing newline. Repeated generation from identical inputs is byte-identical.

## Accepted Stellarium boundary

1. Stellarium is a renderer only and does not become the scientific authority.
2. B9-PR-D generates a deterministic `.ssc` for the declared `26.x` API series but does not launch Stellarium, take screenshots or inspect visual output.
3. The only accepted command families are:

```text
core.clear
core.setGuiVisible
core.setDate
core.setTimeRate
core.setObserverLocation
core.selectObjectByName
core.wait
StelMovementMgr.setFlagTracking
StelMovementMgr.zoomTo
```

4. Absolute paths, traversal, include/eval, screenshot, shell/system execution, URLs, backslashes and control characters are rejected.
5. Script setup order, every shot command group and the final restore sequence are canonical and validated.
6. The script uses the event's UTC peak time and observer coordinates, the reviewed template observer label, and the editorial package's object map.
7. Parsed `core.wait()` duration must equal both `total_wait_ms` and the editorial package duration.
8. The script restores the B9-controlled renderer state with:

```text
StelMovementMgr.setFlagTracking(false);
core.setTimeRate(1.0);
core.setGuiVisible(true);
```

9. Script content, command inventory, version, wait metadata and SHA-256 are mutually validated. Repeated generation is byte-identical.

## TDD and review evidence

```text
Initial RED: editorial / stellarium modules absent
Implementation RED 1: 12 failed / 12 passed
Implementation RED 2: 4 failed / 20 passed
Implementation RED 3: 1 failed / 23 passed
Initial feature GREEN: 24 passed
Review RED 1: 10 failed / 24 passed
Review GREEN 1: 34 passed
Review RED 2: 4 failed / 34 passed
Pre-identity-review GREEN: 38 passed
Identity/orphan-quote review RED: 3 failed / 38 passed
Post-fix legacy-contract conflict: 1 failed / 40 passed
Final focused GREEN: 41 passed in 1.55s
Full downstream GREEN: 395 passed in 4.29s
```

Review hardening covered:

- assessment/lineage and rule-set mismatches;
- unrelated verified asterism mapping;
- duplicate shots, claim-class drift and classical-status drift;
- normalized prohibited-language bypasses;
- quote/lineage auditability;
- exact quote-asset-set validation and explicit rejection of unauthorized quotes;
- content-bound `VideoPackage` identity when claim text changes;
- script wait metadata, canonical order and renderer-state restoration;
- historical source disclosure;
- membership-limited wording;
- silent multi-history truncation;
- template observer-label propagation.

## Exact-head workflow evidence

Successful implementation head:

```text
f4520ac706a07f309d063180fd7e7d42d7aac0ad
```

```text
Development Governance: 30488226219 — success
B9 Editorial Stellarium: 30488226335 — success
Kaiyuan Stable Core: 30488226182 — success
Kaiyuan Upstream Runtime: 30488226257 — success
```

At that head the PR contained 17 expected files limited to the editorial/Stellarium implementation, fixed assets, tests, workflow and governance documents. Review threads and submitted reviews were both zero before final docs.

## Explicit exclusions

B9-PR-D does not run Stellarium GUI, capture screenshots, generate SRT, invoke FFmpeg, create audio/video, publish content, structure the whole book, mutate corpus/candidates/ingest/Qdrant/collections, access `local_kb_default`, or modify `main`.

## Follow-on boundary

B9-PR-E may consume the deterministic editorial package and `.ssc`, then add atomic package writing, review records, SRT/minimal preview command and hermetic E2E. It must not weaken claim lineage, reinterpret frozen v1 contracts, treat `.ssc` output as scientific evidence, silently discard unauthorized quote assets, or add automatic publishing.
