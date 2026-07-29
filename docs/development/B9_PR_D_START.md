# B9-PR-D Editorial Package and Stellarium Script Start

## 2026-07-30 — task started

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Stable branch: stable/kaiyuan-v2
Verified stable HEAD: 523c724add978bc4bb51fc07a716c6a852c95447
Feature branch: codex/kaiyuan-b9-editorial-stellarium-v1
Task: B9-PR-D Editorial package and Stellarium script
State: IN_PROGRESS
```

## Recovery verification

- stable equals `523c724add978bc4bb51fc07a716c6a852c95447`;
- open PRs are only legacy #1 and #7;
- B9-PR-A/B/C implementation and docs-only closeout are complete;
- B9-PR-E and B10+ remain `BACKLOG`.

## Fixed architecture

```text
AstronomyEvent/v1
+ RuleAssessment/v1
+ EvidenceBundle/v1
+ source-backed asterism resolution
+ fixed historical/modern assets
+ EditorialTemplate/v1
→ frozen VideoPackage/v1
→ EditorialPackage/v1 with continuous 80s shot list
→ deterministic StellariumScript/v1
```

## Claim boundaries

- `astronomy_fact` cites event measurements and, when named, verified asterism mapping;
- `classical_quote` requires a lineage entry with `narration_allowed=true`; caller-supplied exact text must hash to the lineage content hash;
- `historical_context` cites an explicit historical source asset and cannot impersonate a quotation;
- `modern_interpretation` requires the literal disclosure `现代文化转译`;
- `开口破局` is permitted only in `modern_interpretation`;
- `production_instruction` cites no research source;
- deterministic fate promises, coercive threats and celestial-causation claims fail closed.

## Stellarium boundary

The generated `.ssc` is ECMAScript text using a fixed allowlist from Stellarium 26.x public scripting APIs. It receives the event's UTC, WGS84 observer location and fixed modern object names. It contains no include, eval, filesystem path, screenshot, shell, network, arbitrary expression or caller-provided code.

Supported commands:

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

B9-PR-D validates script bytes only. Actual Stellarium launch, screenshots and visual inspection remain B9-PR-E/local self-hosted work.

## TDD order

```text
commit missing-module and claim/script fail-closed tests
→ observe RED
→ implement strict template/assets/editorial package
→ implement deterministic script and validator
→ focused GREEN
→ review regressions and full downstream
→ exact-head workflows and independent review
```

## Explicit exclusions

No GUI execution, screenshots, SRT, FFmpeg, audio/video, publishing, full-book rule structuring, corpus/candidate/ingest/Qdrant mutation or `local_kb_default` access.
