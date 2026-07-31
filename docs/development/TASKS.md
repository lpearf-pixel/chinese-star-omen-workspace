# 开发任务台账

本文件维护当前活跃阶段和后续路线。B4–B8 历史台账位于 `docs/development/TASKS_B4_B8_ARCHIVE.md`。

## 状态定义

`BACKLOG`、`READY`、`IN_PROGRESS`、`BLOCKED`、`VERIFYING`、`DONE`、`CANCELLED`。

## 当前仓库事实

```text
Stable branch: stable/kaiyuan-v2
Last verified stable HEAD: 108e0d5fe42403e66b2f2c2a6e0c24585df955b8
Current feature branch: codex/kaiyuan-b10-passage-batches-v2
Current task: B10-PR-B passage inventory, source invalidation and resumable batches
B9 overall: DONE
B9-G6: DONE with accepted corrected archive
B10 overall: IN_PROGRESS
Release target: stable/kaiyuan-v2
Forbidden target: main
Protected collection: local_kb_default
```

实时恢复时必须重新核验以上事实。旧路线 PR #1、#7 仍开放，不得无证据关闭。

## 已完成稳定阶段

```text
B4–B8: DONE
B9 planning: DONE
#32/#33 B9-PR-A: DONE
#34/#35 B9-PR-B: DONE
#36/#37 B9-PR-C: DONE
#38/#39 B9-PR-D: DONE
#40/#41 B9-PR-E implementation and implementation closeout: DONE
#42 B9-G6-E1 preview-media hardening: MERGED
```

## B9

- **Overall status:** `VERIFYING`
- **Public contracts:** `AstronomyEvent/v1`、`RuleAssessment/v1`、`VideoPackage/v1`
- **Design:** `docs/superpowers/specs/2026-07-20-kaiyuan-evidence-video-pipeline-design.md`
- **Plan:** `docs/superpowers/plans/2026-07-20-kaiyuan-evidence-video-pipeline.md`

### B9-PR-A — Contract registry and compatibility
- **Status:** `DONE`
- **Evidence:** `docs/development/B9_PR_A_CLOSEOUT.md`

### B9-PR-B — Scientific provider and asterism catalog
- **Status:** `DONE`
- **Tests:** focused 40；full downstream 319
- **Evidence:** `docs/development/B9_PR_B_CLOSEOUT.md`

### B9-PR-C — RuleAssessment and evidence lineage
- **Status:** `DONE`
- **Tests:** focused 35；full downstream 354
- **Evidence:** `docs/development/B9_PR_C_CLOSEOUT.md`

### B9-PR-D — Editorial package and Stellarium script
- **Status:** `DONE`
- **Implementation:** #38 `e6cd46f87f16aef94074534aac09b03898ab9289`
- **Closeout:** #39 `d16e75d9eda153c13fcbcfc13449c49bb1a8af60`
- **Tests:** focused 41；full downstream 395
- **Evidence:** `docs/development/B9_PR_D_CLOSEOUT.md`

### B9-PR-E — Atomic package, review, preview and E2E
- **Status:** `DONE` for implementation; B9 local G6 remains
- **Implementation:** #40 `92e3c08371bb52651ea0fd5e4357fb9ce7dcd82f`
- **Implementation closeout:** #41 `41a613a1606cbbf8a77336fa01ea4c98236b57c7`
- **Tests:** focused 33；full downstream 428
- **Decision:** `docs/development/B9_PR_E_DECISION.md`
- **Runbook:** `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`
- **Boundary:** no TTS、`final.mp4`、batch media or publishing

### B9-G6-E1 — Preview media evidence hardening
- **Status:** `DONE`
- **Implementation PR:** #42，squash `b0a39ff4ec243aefb324287e1ab1b1a564fc38b6`
- **Closeout PR:** #43，merge `28f3b2a1ce5a9e324b6fc03060423bbacf1b917a`
- **Final feature head:** `88e66d8e5ec85db78f4fddecec2c4d7ffc6a9895`
- **Delivered:**
  - actual `preview.mp4` byte size and SHA-256;
  - 1080x1920 H.264、80,000±500 ms、one video、zero audio;
  - non-symlink bounded streaming hash and file-identity recheck;
  - strict caller-supplied ffprobe payload;
  - observed preview requires media evidence;
  - approved visual review requires media plus screenshots;
  - media-bound local G6 runbook and handoff archive.
- **Tests:** focused `48 passed in 1.42s`；full downstream `443 passed in 3.98s`
- **Exact-head workflows:**
  - Governance `30493748550` — success
  - Package Review Preview `30493748497` — success
  - Stable Core `30493748498` — success
  - Upstream Runtime `30493748522` — success
- **Review:** 8 expected files；0 review threads；0 submitted reviews
- **Decision:** `docs/development/B9_G6_E1_DECISION.md`
- **Closeout:** `docs/development/B9_G6_E1_CLOSEOUT.md`

### B9-G6 — Local/self-hosted renderer evidence
- **Status:** `DONE`
- **Goal:** on macOS run the exact `.ssc` and preview argv, validate actual preview media, inspect the result, capture at most 30 screenshots, and create canonical media-bound `LocalCapabilityEvidence/v1`
- **Runbook:** `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`
- **Required archive:** capability JSON、ffprobe JSON、preview.mp4、scene.ssc、preview command、package manifest、screenshot inventory and screenshots
- **Boundary:** synthetic CI is not real renderer evidence and does not authorize publication
- **Rejected evidence:** `b9-local-g6-evidence-20260730T040856Z.tar.gz`, archive SHA-256 `fc49031dc98083e46aad912b3cfaa43cea611ec80934c37352ba9691cf9eff52`
- **Reason:** archive integrity passed, but `july-21-event.json` and generated narration asserted `3.25°`; independent recomputation for the recorded 2026-07-21 11:00 UTC Shanghai observation was approximately `5.4°`. The fixture also used placeholder ephemeris provenance.
- **Accepted evidence:** `b9-local-g6-evidence-20260730T121805Z-corrected-v1.tar.gz`, archive SHA-256 `8a4af09210961fada5cb6e8ac1a3344d4055307bb7d8c48920c90f71c4020214`.
- **Acceptance:** 19 fixed safe members; no absolute paths or AppleDouble files; actual Stellarium `26.1.0`; FFmpeg `8.1.2`; 1080x1920 H.264 80-second preview; five byte-bound screenshots; renderer hard gate passed; all human confirmations true; final assisted review approved.

### B9-G6-E2 — Scientific provenance and machine hard gate
- **Status:** `DONE`
- **Goal:** replace the hand-authored July scientific assertion with verified offline provider output and make a deterministic hard gate reject any astronomy, lineage, media, screenshot or OCR inconsistency before approval is possible.
- **Design:** `docs/superpowers/specs/2026-07-30-kaiyuan-assisted-renderer-review-design.md`
- **Plan:** `docs/superpowers/plans/2026-07-30-kaiyuan-scientific-hard-gate.md`
- **Acceptance:** the rejected `3.25°` sample fails with a stable issue code; a provider-generated source-backed sample passes; hard rejection cannot be overridden by AI or human input.
- **Local implementation commits:** `69619b0`, `a91e91d`, `88bab18`, `2645fde`
- **Verification:** focused `130 passed`; contracts `6 passed`; text-core `22 passed`; downstream `457 passed`
- **Merged:** PR #44 into `stable/kaiyuan-v2` at `d6f2f862d7cf45c1008925f6d4286aabb4e43077`; all seven exact-head workflows passed.

### B9-G6-E3 — AI visual review report
- **Status:** `DONE`
- **Entry gate:** B9-G6-E2 merged and source-backed evidence regenerated.
- **Goal:** bind an externally produced AI visual assessment to exact preview and screenshot hashes, with `passed|rejected|needs_human_review`, confidence and itemized evidence.
- **Plan:** `docs/superpowers/plans/2026-07-30-kaiyuan-ai-visual-review.md`
- **Boundary:** AI cannot approve astronomy facts, classical evidence or a machine-rejected package.
- **Implementation commits:** `f941539`, `6ff8775`, `acdd98a`, `009daef`
- **Local verification:** focused assisted review `148 passed`; package review `80 passed`; contracts `6 passed`; text-core `22 passed`; downstream `475 passed`.
- **Merged:** PR #45 into `stable/kaiyuan-v2` at `f937c60c76f5e450279e05b3c04de67e296fa687`; all five exact-head workflows passed.

### B9-G6-E4 — Lightweight human confirmation
- **Status:** `DONE`
- **Entry gate:** B9-G6-E2 merged; E3 report available or explicitly `needs_human_review`.
- **Goal:** ask only three layperson checks after professional gates pass and bind the answer to exact review artifacts.
- **Plan:** `docs/superpowers/plans/2026-07-30-kaiyuan-light-human-confirmation.md`
- **Boundary:** no terminal `read`; no generic `y` approval; no approval control is shown after a hard rejection.
- **Implementation commits:** `80d8e1d`, `4bb6090`
- **Local verification:** focused assisted review `160 passed`; collector `3 passed` plus `bash -n`; contracts `6 passed`; text-core `22 passed`; downstream `487 passed`.
- **Merged:** PR #46 into `stable/kaiyuan-v2` at `939c5272a84a1bf3dd2e9c72037ea180f76e8adf`; all five exact-head workflows passed.
- **Completion evidence:** accepted corrected run `20260730T121805Z` contains the hash-bound AI report, all three confirmations and final `approved` resolver output.

### B9-G6-E5 — FFmpeg runtime preflight
- **Status:** `DONE`
- **Trigger:** the source-backed macOS package passed manifest verification but FFmpeg rejected `subtitles=subtitles.srt` at filtergraph execution.
- **Goal:** verify the selected FFmpeg/ffprobe toolchain with a real bounded subtitle smoke before the 80-second preview and expose one repeatable repository entrypoint.
- **Design:** `docs/superpowers/specs/2026-07-30-kaiyuan-ffmpeg-runtime-preflight-design.md`
- **Plan:** `docs/superpowers/plans/2026-07-30-kaiyuan-ffmpeg-runtime-preflight.md`
- **Boundary:** do not change `PreviewCommand/v1`, package hashes, B10–B12 scope, Qdrant, corpus or `local_kb_default`.
- **Acceptance:** explicit binary overrides, missing-feature and smoke-failure diagnostics, no-overwrite preview execution, focused/full gates and an updated macOS runbook.
- **Implementation commits:** `ac9ee58`, `ab7aaa5`, `d4f29ce`
- **Local verification:** runtime/collector/governance `15 passed`; B9 package-review plus runner `102 passed`; contracts `6 passed`; text-core `22 passed`; downstream `487 passed`.
- **Follow-up trigger:** the first source-backed preview reached the AI visual gate and was correctly rejected because the audience-facing historical subtitle exposed internal `source_type` and English `source_title` values.
- **Audience-copy follow-up:** internal source metadata is removed from the historical subtitle while the structured asset fields and `historical_source` reference remain intact; focused editorial and B9 review regression `170 passed`.
- **Merged:** PR #48 into `stable/kaiyuan-v2` at `c2be80c2adbf307178c353a6769ab98c170d1930`.

### B9-G6-E6 — Evidence handoff integrity
- **Status:** `DONE`
- **Trigger:** independently verified run `20260730T121805Z` has a valid canonical review/media/hash chain, but its handoff archive records Stellarium `26.2.0` while the bound overview shows `26.1`, includes five `/Users/...` screenshot inventory paths, and carries sixteen `._*` AppleDouble members.
- **Rejected archive:** `b9-local-g6-evidence-20260730T121805Z.tar.gz`, SHA-256 `0271e15b99151811123ff47f25e5254dec42703001e6bc8079344e6f66916918`.
- **Goal:** bind capability evidence to the actual `.app` version and create a fixed-member, relative-path, AppleDouble-free, deterministic no-overwrite archive.
- **Design:** `docs/superpowers/specs/2026-07-30-kaiyuan-b9-g6-handoff-integrity-design.md`
- **Plan:** `docs/superpowers/plans/2026-07-30-kaiyuan-b9-g6-handoff-integrity.md`
- **Boundary:** do not rerender or reinterpret approved review evidence; do not change corpus, Qdrant, `local_kb_default`, publishing authority, B10–B12, or `main`.
- **Acceptance:** actual Info.plist version must equal capability JSON; inventory paths are relative; archive contains no `._*` or unrelated members; existing output is never overwritten; focused/full gates and independent regenerated-archive review pass.
- **Local verification:** 10 handoff behaviors plus 10 preview/collector regressions passed through the same plain-assert functions; `compileall`, collector `bash -n`, CLI help and `git diff --check` passed.
- **Pressure test:** uploaded mismatch rejected without output; canonical capability version `26.1.0` produced 19 fixed members, five relative inventory entries and zero AppleDouble members.
- **Merged:** PR #49 into `stable/kaiyuan-v2` at `e5a5315fcea72ea878bf62968170d4f262fabc5d`; exact-head Development Governance `30566529753`, Kaiyuan Stable Core `30566529828` and Kaiyuan Upstream Runtime `30566529785` all succeeded.
- **Independent archive verification:** corrected archive SHA-256 `8a4af09210961fada5cb6e8ac1a3344d4055307bb7d8c48920c90f71c4020214` passed archive safety, privacy, fixed-member, stable schema, canonical binding, media, screenshot, OCR and visual checks.

### B9-FINAL-CLOSEOUT — Final B9 evidence and governance closeout
- **Status:** `DONE`
- **Base:** `stable/kaiyuan-v2` at `e5a5315fcea72ea878bf62968170d4f262fabc5d`
- **Goal:** record the accepted exact G6 archive, final B9 completion matrix, PR #49 exact-head evidence and unchanged safety boundaries in an independent docs-only PR.
- **Acceptance:** changed-file audit is docs-only; local docs/governance checks pass; the closeout PR targets only `stable/kaiyuan-v2`; exact-head required workflows and review pass; the PR is merged before B10 starts.
- **Boundary:** do not commit the local archive; do not change code, contracts, corpus, Qdrant, `local_kb_default`, `main`, media or publishing authority.
- **Closeout PR:** #50; initial exact head `a2f2c9c668f5a9b0da4ee13a424b9eea93fa1093`.
- **Initial exact-head workflows:** Development Governance `30598928710`, Kaiyuan Stable Core `30598928837` and Kaiyuan Upstream Runtime `30598928873` all succeeded.
- **Review:** four expected documentation files; no submitted reviews or review threads; mergeable.
- **Effective boundary:** B9 becomes `DONE` on stable only when PR #50 merges. The final status-only head must rerun all required workflows before merge.

B9 is complete in the PR #50 merge candidate. B10 cannot start until PR #50 is
merged and the resulting stable head is reverified.

## Governance

### GOV-T02 — Legacy PR #1/#7 disposition
- **Status:** `BACKLOG`
- **Boundary:** compare against stable v2 before closure; does not block G6

## B10 — Whole-book rule structuring
- **Status:** `IN_PROGRESS`
- **Entry gate:** satisfied by accepted B9-G6 evidence and merged PR #50 at `a10e33118c2e34f947a099492bb01e13a07a98a8`
- **Design:** `docs/superpowers/specs/2026-07-20-kaiyuan-whole-book-rule-structuring-design.md`
- **Plan:** `docs/superpowers/plans/2026-07-20-kaiyuan-whole-book-rule-structuring.md`
- **Charter:** `docs/research/KAIYUAN_RULE_PROGRAM_CHARTER.md`
- **Completion boundary:** all six whole-book denominators must reach terminal coverage; infrastructure or one release batch cannot mark B10 `DONE`.

### B10-T00 — Program charter and threshold governance
- **Status:** `DONE`
- **Base:** `stable/kaiyuan-v2` at `a10e33118c2e34f947a099492bb01e13a07a98a8`
- **Goal:** freeze the whole-book completion denominators, PR-A through PR-H sequence, resumable batch policy, calibration/threshold process and B11 input boundary before contract implementation.
- **Acceptance:** program charter, D-025 decision, task/memory/work-log state; citable false-positive gate fixed at `0`; post-pilot `threshold-freeze.json` required before full extraction; docs/governance gates and a docs-only PR targeting stable.
- **Boundary:** no rule contract implementation, corpus modification, candidate extraction, model call, Qdrant access, `local_kb_default` access or B11/B12 implementation.
- **Local verification:** charter acceptance scan, 5 governance unit tests, development governance checker, `compileall` and `git diff --check` passed on 2026-07-30; exact-head hosted gates remain required before merge.
- **PR:** #51, initial exact head `fb7fb012a98a7d6d75d37354da3b9ca73d743e76`.
- **Initial exact-head workflows:** Development Governance `30599473112`, Kaiyuan Stable Core `30599473165` and Kaiyuan Upstream Runtime `30599473127` all succeeded.
- **Final exact-head workflows:** Development Governance `30599537056`, Kaiyuan Stable Core `30599537037` and Kaiyuan Upstream Runtime `30599537036` all succeeded.
- **Merged:** PR #51 squash merged as `0df8c70551c1746d073a390e3fcd9371a5de8e5d`.

### B10-PR-A — OmenRule/v2, identity and annotation contract
- **Status:** `DONE`
- **Base:** `stable/kaiyuan-v2` at `0df8c70551c1746d073a390e3fcd9371a5de8e5d`.
- **Entry gate:** satisfied by merged B10-T00 and independently fetched exact stable commit.
- **Goal:** create strict `OmenRule/v2` and `RuleCandidate/v2` contracts, deterministic candidate identity, approval-only rule identity/version history, explicit v1 migration reporting, and a frozen annotation guide with reviewed cases.
- **Acceptance:** all ontology, identity lifecycle, split/merge/history, strict JSON, duplicate-ID, illegal-state, unknown-field, non-finite-number, v1 migration and annotation-case requirements in the B10 plan.
- **Boundary:** contracts and fixtures only; no passage inventory, full-book extraction, model call, review queue, Qdrant access, official ingest, B11/B12 implementation or corpus mutation.
- **Local verification checkpoint:** TDD RED observed for missing v2 modules; shared contracts `23 passed`; downstream `487 passed`; upstream `188 passed, 3 skipped`; final fresh rerun, governance and hosted exact-head gates remain.
- **PR:** #52, initial exact head `cbb2fc7c82e7b73404089bca0fd4ecae2915b422`.
- **Initial exact-head workflows:** Development Governance `30600436677`, Kaiyuan Stable Core `30600436719` and Kaiyuan Upstream Runtime `30600436650` all succeeded.
- **Review:** 18 expected files; zero submitted reviews and review threads; mergeable.
- **Final exact-head workflows:** Development Governance `30600525915`, Kaiyuan Stable Core `30600525882` and Kaiyuan Upstream Runtime `30600525861` all succeeded.
- **Merged:** PR #52 squash merged as `108e0d5fe42403e66b2f2c2a6e0c24585df955b8`.

### B10-PR-B — Passage inventory, source invalidation and resumable batches
- **Status:** `VERIFYING`
- **Base:** `stable/kaiyuan-v2` at `108e0d5fe42403e66b2f2c2a6e0c24585df955b8`.
- **Goal:** build deterministic primary passage inventory, explicit source-change invalidation and stable resumable batch/checkpoint contracts.
- **Acceptance:** existing locator/hash semantics; provenance-preserving duplicate handling; ambiguous anchor fail-closed; deterministic bytes independent of input order; batch size `100–500` with default `200`; stable batch identity; checkpoint tamper/concurrency/resume/idempotence/no-overwrite tests.
- **Boundary:** no full-book extraction, model call, review queue, Qdrant access, official ingest, B11/B12 implementation or corpus mutation.
- **Local verification checkpoint:** TDD RED observed for missing `rule_passages`; focused core `4 passed`; focused inventory/batch `8 passed`; contracts `23 passed`; text-core `26 passed`; downstream `495 passed`; upstream `188 passed, 3 skipped`; governance/schema/boundary checks passed; hosted gates remain.
- **PR:** #53, initial exact head `9de85036ef0ab1ed35477de69ce56e30a613f01e`.
- **Initial exact-head workflows:** Development Governance `30601232781`, Kaiyuan Stable Core `30601232820` and Kaiyuan Upstream Runtime `30601232778` all succeeded.
- **Review:** nine expected files; zero submitted reviews and review threads; mergeable. Final status-only exact-head gates remain.

### B10-PR-C — Golden sets, calibration pilot and threshold freeze
- **Status:** `BACKLOG`

### B10-PR-D — Full-book deterministic extraction
- **Status:** `BACKLOG`

### B10-PR-E — Optional model candidate adapter
- **Status:** `BACKLOG`
- **Boundary:** optional; disabled mode must remain a valid B10 completion path.

### B10-PR-F — Review queue, deduplication and conflicts
- **Status:** `BACKLOG`

### B10-PR-G — Full-book review waves and coverage
- **Status:** `BACKLOG`

### B10-PR-H — Rule release, offline verification and B11 gap report
- **Status:** `BACKLOG`

## B11 — Rule engine 2.0
- **Status:** `BACKLOG`

## B12 — Batch media and publishing assistance
- **Status:** `BACKLOG`
- **Boundary:** automatic publishing requires a separate safety decision

## Current sequence

```text
implement and merge B9-G6-E2 scientific hard gate
→ regenerate source-backed macOS G6 evidence
→ add B9-G6-E3 hash-bound AI visual report
→ add B9-G6-E4 lightweight human confirmation
→ harden FFmpeg runtime preflight and regenerate the preview
→ independently verify the resulting evidence archive
→ correct handoff version provenance and archive privacy/minimality
→ merge final B9 closeout
→ only then B10
```

Current prohibitions:

- no direct stable writes;
- no B10–B12 implementation;
- no official Qdrant or `local_kb_default` mutation;
- no automatic publishing or `final.mp4`;
- no claim that hosted CI is real Stellarium/FFmpeg evidence.
