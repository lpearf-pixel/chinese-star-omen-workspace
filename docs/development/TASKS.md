# 开发任务台账

本文件维护当前活跃阶段和后续路线。B4–B8 历史台账位于 `docs/development/TASKS_B4_B8_ARCHIVE.md`。

## 状态定义

`BACKLOG`、`READY`、`IN_PROGRESS`、`BLOCKED`、`VERIFYING`、`DONE`、`CANCELLED`。

## 当前仓库事实

```text
Stable branch: stable/kaiyuan-v2
Last verified stable HEAD: 99c0a85c1f944add8d013aedbae830fe022b7c3b
Current feature branch: codex/kaiyuan-evidence-feedback-loop-skeleton-v1
Current task: VFL-T01-D1 remote-delivery reconciliation VERIFYING; VFL-T01
local S0 DONE; B10-PR-C remains BLOCKED on Reviewer B
Open PRs: #54 only; Draft and human-review blocked
B9 overall: DONE
B9-G6: DONE with accepted corrected archive
B10 overall: IN_PROGRESS
Release target: stable/kaiyuan-v2
Forbidden target: main
Protected collection: local_kb_default
```

实时恢复时必须重新核验以上事实。旧路线 PR #1、#7 已在合并证据审计后以 `closed / merged=false` 处置；分支与历史保留，禁止重新合并或 cherry-pick。

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

- **Overall status:** `DONE`
- **Public contracts:** `AstronomyEvent/v1`、`RuleAssessment/v1`、`VideoPackage/v1`
- **Design:** `docs/superpowers/specs/2026-07-20-kaiyuan-evidence-video-pipeline-design.md`
- **Plan:** `docs/superpowers/plans/2026-07-20-kaiyuan-evidence-video-pipeline.md`

### ASTRO-R01 — Twenty-eight mansion catalog and external-media audit foundation
- **Status:** `DONE` (approved phases 1–5; later expansion remains unclaimed)
- **Base:** `stable/kaiyuan-v2` at `c2e8fcabb04354fd14d0c72b3b6020a47e63a583`.
- **Branch:** `codex/kaiyuan-28-mansions-external-audit-v1`.
- **Goal:** use 毕宿 as the first complete gold sample for source-bound member stars,
  defining-star mansion regions and objective relation measurements; then reuse
  the same contracts for all twenty-eight mansions, navigation cards and an
  external broadcaster/video claim-audit resource layer.
- **Phase 1 acceptance:** preserve the existing 角宿一/Spica identity; bind the
  eight 毕宿 members and the following 觜宿 defining star to pinned Stellarium
  and Hipparcos records; calculate mansion-region membership separately from
  nearest-member angular separation; treat an unqualified `临毕` as
  `ambiguous_relation`; expose no `犯/入/守/留` conclusion without the required
  distance, transition, velocity or duration evidence.
- **Later phases:** add all 28 defining stars and regions; add source-backed
  member/line data and uncertainty states for every mansion; enrich the 28
  navigation cards; create `ExternalMediaSource/v1`, `ExternalClaim/v1`,
  `EvidenceLink/v1` and `ExternalAudit/v1`, starting with 祖山觀's 23-item
  collection and nine priority audits.
- **Boundary:** research/scientific candidate infrastructure only. No Reviewer
  A/B substitution, PR #54 or #64 mutation, threshold freeze, formal rule
  promotion, source-corpus rewrite, official ingest, Qdrant access,
  `local_kb_default` mutation, automatic weather inference, B11/B12 release or
  `main` operation.
- **Phase 1 implementation heads:** `b9e34b3` catalog; `ea98308` pure region
  evaluator; `ec5db76` provider binding; `a776dda` navigation binding.
- **Phase 1 verification:** asterism baseline `13 passed`; catalog GREEN
  `16 passed`; pure evaluator suite `28 passed`; astronomy/asterism focused
  `58 passed`; navigation/science focused `60 passed`; downstream `613 passed`.
- **Phase 1 publication:** Draft PR #65, remote head
  `09d4ec9781e874ef0bc346a7e48d8072541158cf`; locally reviewed and remote trees
  both equal `56f0d51c98694d1b5685e6220f8945106a41f824`.
- **Phase 2 acceptance:** add the exact 28 defining-star denominator, require
  sequence `1..28`, close every eastern boundary to the next western boundary
  including 軫宿 → 角宿, and expose region-only assessment without treating a
  partial defining-star shell as complete nearest-member coverage.
- **Phase 2 implementation heads:** `9e350d9` closed catalog cycle; `adb2396`
  region-only/member-proximity split; `04bfd4b` offline provider binding.
- **Phase 2 verification checkpoint:** exact denominator `36 entries / 28
  asterisms / 28 lunar_mansions`; catalog/source/fixture suite `32 passed`;
  pure region suite `18 passed`; focused astronomy/asterism/navigation suite
  `73 passed`; governance unit tests `21 passed`; development-governance scope
  `26 files / 15 code files`; full downstream `626 passed`; compileall,
  canonical-hash, diff and forbidden-path checks passed. One final replay is
  required after the evidence commit.
- **Phase 2 publication:** Draft PR #65 remote head
  `19c076ddbff60b29a7d22443dbbb9bad0c11a527`; locally reviewed and remote
  trees both equal `c796215b89e0cdc214e4f3943e365c1ec6bfae72`. Runner was
  `NOT RUN`; no merge was attempted.
- **Phase 3 acceptance:** bind the pinned Stellarium fixed-name and line records
  for all 28 mansion asterisms to Hipparcos I/239 J1991.25 coordinates; preserve
  157 base members, five cross-asterism related endpoints and 57 line segments
  without nearest-star inference. Exact complete definitions may expose member
  proximity; the three status-2 翼宿 identities remain `ambiguous`, so 翼宿
  remains region-only for relation assessment. 附耳, 钺, 长沙, 左辖 and 右辖
  remain related objects rather than extra mansion members.
- **Phase 3 implementation heads:** `d7140af` source snapshots and fixture;
  `97fa9f3` catalog memberships and completeness validation; `7a8548b`
  complete-member proximity and provider preflight.
- **Phase 3 verification checkpoint:** exact denominator `162 entries / 28
  asterisms / 28 lunar_mansions`, with `157 members / 5 related endpoints / 57
  line segments`; completeness `26 complete / 1 complete_gold_sample / 1
  ambiguous`; source suite `6 passed`; asterism suite `43 passed`; focused
  astronomy/asterism/navigation suite `80 passed`; governance unit tests `21
  passed`; development-governance scope `31 files / 18 code files`; full
  downstream `633 passed`; compileall, 14 canonical source/fixture hashes, diff
  and forbidden-path checks passed. One final replay is required after the
  evidence commit.
- **Phase 3 publication:** Draft PR #65 remote head
  `dbfa9d26e90cf8f1e31bc8b0fecdbb1129344474`; locally reviewed and remote
  trees both equal `a40c8eb6290b92ee06e1653922d82e6293cbcb27`. Runner was
  `NOT RUN`; no merge was attempted.
- **Phase 4 acceptance:** bind every one of the 28 `lunar_mansion_card` files to
  its exact catalog definition and mansion region; require overview order to
  equal sequence 1–28; make simplified/traditional title aliases resolve to the
  same card; expose completeness, members, related endpoints, ambiguous member
  IDs, lines, boundaries, provenance and source refs without adding unreviewed
  classical quotations or omen conclusions.
- **Phase 4 implementation heads:** `f196507` all-card RED gate; `0303dd8`
  generated catalog bindings and modern-mapping sections.
- **Phase 4 verification checkpoint:** RED was `1 failed / 1 passed` and listed
  all 27 cards missing a status block. GREEN focused navigation/science was `80
  passed`. The exact card projection is `28 cards / 6 explicit alias variants /
  157 members / 5 related endpoints / 3 ambiguous members / 57 line segments`;
  28/28 classical body suffixes were byte-identical after the bounded modern
  section. Pre-closeout head `86eb156` passed governance `21`, development
  governance `59 files / 18 code files`, focused `80`, canonical hash tests `8`,
  downstream `633`, compileall, diff, clean-worktree and forbidden-path scans.
  The evidence commit requires one exact-head replay before publication.
- **Phase 4 publication:** Draft PR #65 remote head
  `b7232ef3c6595c8d209255e2a4550a1d7b63f04a`; locally reviewed and remote
  trees both equal `535ea6e62df4aff6ebb72d9fe4e14f45c338d228`. Its parent is Phase 3
  `dbfa9d2`; the ref update was a non-force fast-forward. Runner was `NOT RUN`;
  no merge was attempted.
- **Phase 5 acceptance:** add strict `ExternalMediaSource/v1`,
  `ExternalClaim/v1`, `EvidenceLink/v1` and `ExternalAudit/v1` contracts plus a
  cross-reference bundle validator, committed JSON Schemas and canonical
  fixtures. Exact creator/work locators and captured hashes are mandatory;
  missing source bytes must remain `source_missing`, never inferred from search
  snippets or same-name accounts.
- **Phase 5 source gate:** opened on 2026-08-12 by the user-supplied direct
  creator and work short links. They resolve to 祖山觀（無用之人）🌓, Douyin
  number `35031221639`, UID `2129076815950670`, stable `sec_uid`
  `MS4wLjABAAAAAzgxglR-dz-mRK53rZNuTqMwh1HktiIHLXa-3ZSVXCH4zDH0xjcWCN8BKyQ3plyK`,
  and collection `7664842437629921326`. The approved denominator is frozen as
  collection episodes 1–23; the live collection's growth to 40 is source drift,
  not permission to expand this phase.
- **Phase 5 contract implementation heads:** `275ec71` four strict public models;
  `2f5a6c4` fail-closed bundle/cross-reference semantics; `3c315a6` committed
  schemas, registry entries and canonical synthetic fixtures.
- **Phase 5 verification checkpoint:** Task 1 RED was an import failure, then
  model GREEN `18` and existing-contract regression `59`; bundle suite GREEN
  `30`; registered contract/external-media suite GREEN `94`. Pre-closeout head
  passed governance `21`, development governance `78 files / 31 code files`,
  focused science/navigation/contracts/external-media `174`, downstream `668`
  and compileall. Exact evidence-head replay and Draft publication remain.
- **Phase 5 real-source implementation:** `f242112` opened the source gate;
  `0f5e47a` added the exact 23-item inventory, nine candidate audit bundles and
  canonical real-asset manifest; `af085bd` fixed the direct-work timestamp to
  exact UTC; `3159828` pinned all 23 inventory tuples and cross-bound the WMO
  context snapshot to the gold audit. Episode 22/work `7669807398794598565`
  remains `ambiguous`; missing classical source is `source_missing` and no
  weather-system equivalence is inferred.
- **Phase 5 real-source verification:** independent review found no Critical or
  asset mismatch; all Important findings were fixed. Pre-publication exact head
  `3159828`, tree `0a37058a`, passed governance `21`, development governance
  `91 files / 32 code files`, focused `179`, canonical source/fixture `13`, full
  downstream `673`, compileall, diff, stable-ancestor, clean-worktree and
  forbidden-path gates.
- **Phase 5 publication checkpoint:** locally reviewed tree `2acb2a5b` was
  published as remote commit `3c7c38c1` by a non-force fast-forward. Readback
  confirmed Draft PR #65 remained open, draft and unmerged on the unchanged
  stable base. The final evidence-only head requires the same exact-head replay
  and non-force readback; Runner remains unauthorized and no merge is attempted.
- **Current work:** none inside the approved phases 1–5. Any later creator or
  corpus expansion must be separately registered and planned before mutation.
- **Design:** `docs/superpowers/specs/2026-08-12-kaiyuan-28-mansions-external-audit-design.md`.
- **Phase 1 plan:** `docs/superpowers/plans/2026-08-12-kaiyuan-bi-mansion-gold-sample.md`.
- **Phase 2 plan:** `docs/superpowers/plans/2026-08-12-kaiyuan-28-mansion-region-cycle.md`.
- **Phase 3 plan:** `docs/superpowers/plans/2026-08-12-kaiyuan-28-mansion-membership-lines.md`.
- **Phase 4 plan:** `docs/superpowers/plans/2026-08-12-kaiyuan-28-mansion-navigation-status.md`.
- **Phase 5 plan:** `docs/superpowers/plans/2026-08-12-external-media-audit-contracts.md`.

### DOC-R01 — Durable new-Work handoff

- **Status:** `DONE`.
- **Goal:** add a compact root `agent.md` with stable global instructions and a
  root `summary.md` with the latest verified project handoff, then make both
  part of the mandatory new-Work read order.
- **Allowed scope:** `AGENTS.md`, `agent.md`, `summary.md`,
  `docs/development/DEVELOPMENT_MANUAL.md`, task/work-log state and the existing
  Draft PR #65 description/head.
- **Prohibited:** product code, raw corpus, Reviewer A/B artifacts, Qdrant,
  `local_kb_default`, workflows, PR #54/#64, Runner, stable merge and `main`.
- **Acceptance:** a new Work can recover repository roles, safety boundaries,
  current milestones, exact verification commands and next-action protocol
  without relying on chat history; volatile facts are explicitly marked for
  live revalidation.
- **Delivery:** handoff content checkpoint remote commit `2774a727e4fcd87804fbd3f441ac1fff34762b1a`,
  tree `d3a7df3f071dc2553472adcc4d386eedad20e3fd`; published by non-force
  fast-forward to Draft PR #65. Final closeout remains documentation-only.

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
- **Status:** `DONE`
- **Audit branch:** `docs/kaiyuan-gov-t02-legacy-pr-disposition-v1`
- **Closeout branch:** `docs/kaiyuan-gov-t02-closeout-v1`
- **Design:** `docs/superpowers/specs/2026-08-02-kaiyuan-legacy-pr-disposition-design.md`
- **Plan:** `docs/superpowers/plans/2026-08-02-kaiyuan-legacy-pr-disposition.md`
- **Audit:** `docs/development/GOV_T02_LEGACY_PR_DISPOSITION.md`
- **Row matrix:** `docs/development/gov-t02-legacy-pr-matrix.json` (70 rows; Git blob `9d61ed3daf5d1318e7c4e8d71d96afa7032fd952`)
- **Audit merge:** PR #61, reviewed head `cd99ed2a1a94e0b698530bf63e2d4269ba23acfa`, squash `08fb71ab1db7de509154214cca44693a5de4859c`.
- **Closure evidence:** PR #1 head `0eaeffac6d875ce6834e2a5632708ba8933bf812` closed without merge at 2026-08-03T06:05:15Z after comment `5162877413`; PR #7 head `3cc654b92514223d069b56162c874b5a1a65e060` closed without merge at 2026-08-03T06:05:16Z after comment `5162877570`.
- **Result:** all 70 legacy paths classified, unresolved count 0; #1/#7 are absent from the open PR set. PR #62 final head `82b464049f1ca39557696016dddab3cdcfc2762c` passed Development Governance `30789542306`, Kaiyuan Stable Core `30789542258`, Kaiyuan Upstream Runtime `30789542404` and independent review Critical 0 / Important 0 / Minor 0 / Ready YES.
- **Closeout merge:** PR #62 squash merged only to `stable/kaiyuan-v2` as `96b41a4524d36c7ffb2f1e2ec66ca4aed1565962`; immediately after that merge the open PR set contained only human-blocked #54. Later governance PRs do not change this historical result.
- **Boundary:** do not reopen, merge or cherry-pick either legacy branch; no behavior, corpus, candidate, Qdrant, `local_kb_default`, PR #54, B10-PR-D/E/F, B11/B12 or `main` change.
### GOV-T03 — Local-first verification and major-version Runner gate
- **Status:** `DONE`
- **Goal:** make local verification the default for routine work and reserve one final unified Runner validation for the exact major-version candidate immediately before merging into `stable/kaiyuan-v2`.
- **Acceptance:** root `AGENTS.md`, the long-lived development manual and B9–B10 test strategy define the same policy; missing Runner evidence is recorded as `NOT RUN`/`BLOCKED`, never passed; `gh` is explicitly optional when the GitHub App or API provides an equivalent auditable operation.
- **Boundary:** documentation/governance only; no workflow, product code, corpus, Qdrant, `local_kb_default`, PR #54 implementation, `main`, or stable ref mutation.
- **PR and review:** PR #55; independent review found zero Critical, Important or Minor findings after the B9–B10 strategy reconciliation.

### GOV-T04 — Major-version unified Runner workflow migration
- **Status:** `DONE`; effective on stable at `c2e8fcabb04354fd14d0c72b3b6020a47e63a583`
- **Branch:** `codex/kaiyuan-gov-t04-unified-runner-v1`
- **Design:** `docs/superpowers/specs/2026-08-02-kaiyuan-major-version-runner-workflow-design.md`
- **Goal:** replace transitional per-PR automatic Runner triggers with one explicit exact-head major-version stable merge gate while retaining independently scheduled nightly and task-specific real-environment evidence.
- **Acceptance:** ordinary PR and branch-push events trigger none of the migrated Runner workflows; the release operator launches one documented unified validation by pushing a lightweight `kaiyuan-runner/v2/<exact-sha>` tag; the raw remote tag object, tag suffix, event SHA, commit object, checkout HEAD and current stable ancestry must agree; all eight reusable workflows must succeed; the final result JSON and SHA-256 sidecar are candidate/base/ref/run bound and fail closed; the live stable HEAD must still equal artifact `base_sha` immediately before merge.
- **Verification checkpoint:** pilot head `ca7f05691fbb2a5ee9c1232950f8ad914f4b107f` passed unified run `30800888691`; artifact ZIP SHA-256 `43ef662ce403904019d0c428b634e7aca82d178a84ac02db81f701c436069812` and result JSON SHA-256 `f706719312d22a400a94e15375b493286ae74143d9abefa2198295dceef811fd` were independently verified with all nine results `success`. Final review found four Important gaps; their tag-object, topology, stable-drift and governance-state fixes are included in the closeout candidate. That new exact head still requires one successful unified run, live-base equality and expected-head merge before this `DONE` becomes effective.
- **Boundary:** workflow/governance only; nightly remains an independent future task because no scheduled workflow exists on the audited baseline; real-device, scientific, corpus, human, migration, security and production evidence remain independently governed. No product, schema, corpus, Qdrant, `local_kb_default`, PR #54 implementation, B10-PR-D/E/F, B11/B12, publishing or `main` change.

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
- **Status:** `DONE`
- **Base:** `stable/kaiyuan-v2` at `108e0d5fe42403e66b2f2c2a6e0c24585df955b8`.
- **Goal:** build deterministic primary passage inventory, explicit source-change invalidation and stable resumable batch/checkpoint contracts.
- **Acceptance:** existing locator/hash semantics; provenance-preserving duplicate handling; ambiguous anchor fail-closed; deterministic bytes independent of input order; batch size `100–500` with default `200`; stable batch identity; checkpoint tamper/concurrency/resume/idempotence/no-overwrite tests.
- **Boundary:** no full-book extraction, model call, review queue, Qdrant access, official ingest, B11/B12 implementation or corpus mutation.
- **Local verification checkpoint:** TDD RED observed for missing `rule_passages`; focused core `4 passed`; focused inventory/batch `8 passed`; contracts `23 passed`; text-core `26 passed`; downstream `495 passed`; upstream `188 passed, 3 skipped`; governance/schema/boundary checks passed.
- **PR:** #53, initial exact head `9de85036ef0ab1ed35477de69ce56e30a613f01e`.
- **Initial exact-head workflows:** Development Governance `30601232781`, Kaiyuan Stable Core `30601232820` and Kaiyuan Upstream Runtime `30601232778` all succeeded.
- **Review:** nine expected files; zero submitted reviews and review threads; mergeable.
- **Final head and merge:** final head `3059748`; Development Governance `30601310046`, Kaiyuan Stable Core `30601310041` and Kaiyuan Upstream Runtime `30601310051` succeeded under the pre-GOV-T03 policy; PR #53 squash merged as `7ed60487a9a77e93578f14e27e35dc7612dcc054`.

### B10-PR-C — Golden sets, calibration pilot and threshold freeze
- **Status:** `BLOCKED`
- **Blocking evidence:** Draft PR #54 requires two different people to independently complete Reviewer A and Reviewer B worksheets. AI, blank worksheets and anonymous slot creation do not satisfy this gate.
- **Exit gate:** reviewed pilot fixtures and an approved canonical `threshold-freeze.json`; only then may B10-PR-D start.

### B10-R01 — C24 source accession and parallel-text pilot
- **Status:** `DONE`
- **Locator:** `卷38 / KR3g0018_WYG_038-13b`.
- **Goal:** preserve a revision-bound public source snapshot, record every cited
  ancient source, separate observation from emendation hypotheses, and compare
  the repeated Jupiter/Mars/Saturn formula before any C24 citation decision.
- **Acceptance:** source bytes and hashes are recorded; Wikisource revision and
  Kanripo commit/blob identities are pinned; sections eight and nine are split;
  `客環守` alternatives remain explicit; a staged multi-text mapping plan has
  entry/exit gates and does not pre-empt the later schema decision.
- **Boundary:** research support only; no human-review substitution, threshold
  freeze, full-book extraction, model approval, official ingest, Qdrant access,
  `local_kb_default` mutation, source-text normalization, B11/B12, or `main`.

### B10-R02 — Core14 source audit and mapping preparation
- **Status:** `DONE`
- **Cases:** `C02`, `C03`, `C09`, `C11`, `C13`, `C14`, `C24`,
  `C31`, `C33`, `C41`, `C43`, `C44`, `C45`, `C47`.
- **Goal:** extend each frozen passage to source-section boundaries, preserve
  revision-bound public carriers, register quoted ancient works, compare
  parallel formulae, propose atomic splits, and separate formal-candidate value
  from current citation eligibility.
- **Acceptance:** all fourteen cases have source identities, boundary findings,
  ancient-source registers, atomic-rule proposals, unresolved readings and
  explicit recommendations; a cross-case report records consistent
  computability and threshold semantics; archived public excerpts are
  hash-bound and the deliverables pass an independent review.
- **Boundary:** AI research pre-review only; no substitution for Reviewer A/B,
  no threshold freeze, no official ingest or evidence promotion, no Qdrant or
  `local_kb_default` mutation, no silent source normalization, no B11/B12 and
  no `main`.

### B10-R06 — Core14 disputed-case second evidence review
- **Status:** `DONE`
- **Cases:** `C03`, `C24`, `C33`, `C47`.
- **Goal:** preserve the completed Reviewer A workbook while adding an
  append-only second-round evidence decision for the four disputed cases,
  including exact source locators, section boundaries, variants, atomic-rule
  consequences and a minimal independent handoff for Reviewer B.
- **Acceptance:** each case has a source-bound delta decision; C03 distinguishes
  source variation from logical contradiction; C24 keeps the section split and
  unresolved `客環守`/duration/shape readings; C33 excludes the preceding
  `留守` clause and recovers the complete right boundary; C47 carries no
  `duplicate` label without a concrete `duplicate_of`; structured evidence and
  the human-readable report pass deterministic validation; PR #54 receives a
  hash-bound review-status comment without changing its head.
- **Boundary:** evidence and review metadata only; do not modify the frozen
  Reviewer A/B workbook bytes, original R02 audit artifacts, runtime code, main
  rules, main data, thresholds, Qdrant, `local_kb_default`, B10-PR-D/E/F,
  B11/B12, automatic publishing or `main`. Reviewer B remains an independent
  different human and is not completed or simulated by this task.

### B10-R07 — Core14 provisional usability stratification
- **Status:** `DONE`
- **Cases:** provisional-use set `C02`, `C09`, `C11`, `C13`, `C14`, `C31`,
  `C41`, `C43`, `C44`, `C45`, `C47`; isolated evidence-supplement set `C03`,
  `C24`, `C33`.
- **Goal:** record the user-approved operational split between cases that may
  support internal research while awaiting Reviewer B and cases that must stay
  isolated for additional evidence, without changing any formal review label.
- **Acceptance:** a deterministic machine-readable register contains exactly
  the frozen Core14 denominator split 11+3 with no overlap; every provisional
  case remains explicitly pending Reviewer B; every isolated case remains
  non-citable; all threshold-freeze, release, ingest and promotion gates remain
  false; the same boundary is documented for researchers and bound to Draft
  PR #64/PR #54 metadata.
- **Boundary:** do not modify Reviewer A/B workbook bytes, R02/R06 decisions,
  raw corpus, runtime rules, thresholds, formal KB, Qdrant,
  `local_kb_default`, B10-PR-D/E/F, B11/B12, automatic publishing or `main`.

### B10-R08 — PR #64 stable-integration reconciliation
- **Status:** `DONE`
- **Historical reconciliation state:** Draft PR #64 head
  `35c2a77c7da3b964555a6bb1e41ec8a23d35ec55` is four commits ahead of its
  original base `c2e8fcabb04354fd14d0c72b3b6020a47e63a583`; after ASTRO-R01 merged,
  live `stable/kaiyuan-v2` is
  `c9d490392233b7432f5a0136dcd213613abe05a7` and GitHub reports the PR as
  one commit behind and not mergeable.
- **Goal:** replay the frozen R06/R07 evidence on the new stable baseline,
  preserve both sides of governance and handoff history, and restore Draft PR
  #64 to an auditable mergeable state without changing any research decision.
- **Allowed scope:** the existing 12 PR #64 evidence, report, plan, test and
  governance paths plus the stable handoff files needed to record exact
  integration state.
- **Prohibited:** Reviewer workbook changes, new case labels, threshold freeze,
  B10-PR-D/E/F, official ingest or promotion, Qdrant, `local_kb_default`, raw
  corpus normalization, automatic publishing, `main`, or stable merge.
- **Done:** the branch contains the new stable ancestor; R06/R07 artifacts and
  hashes remain byte-identical; the 11+3 denominator and every false gate are
  preserved; conflicts are resolved with no dropped ASTRO-R01/DOC-R01 state;
  focused, governance, contract, text-core, downstream and upstream checks pass;
  Draft PR #64 is updated and read back as open, Draft and mergeable.
- **Verify:** run the Core14 focused test, governance unit/checker, contracts,
  text-core, full downstream and upstream suites, strict JSON/hash replay,
  `compileall`, `git diff --check`, forbidden-path scan and remote tree readback.
- **Delivery:** non-force fast-forward update of the existing PR #64 branch;
  keep the PR Draft and do not merge it or modify `stable/kaiyuan-v2`/`main`.
- **Remote integration result:** GitHub App merge commit
  `2384533291b1163738fb06f6984a348f78ecc558`, tree
  `d7149bd569b3840733ef7aacd0663396d112e322`; PR #64 read back open, Draft,
  mergeable, ahead 5/behind 0 with exact stable merge base and 13 expected paths.
- **Later repository state:** PR #64 was merged on 2026-08-14; its stable merge
  result is `99c0a85c1f944add8d013aedbae830fe022b7c3b`. This does not change PR #54,
  Reviewer B or any threshold-freeze gate.


### B10-R03 — Related Wikisource source localization
- **Status:** `DONE` (P0)
- **Base:** `stable/kaiyuan-v2` at `6cffa1e4adf428f068149a31e7f2572dce4a2069`.
- **Branch:** `codex/kaiyuan-b10-related-wikisource-localization-v1`.
- **Execution plan:** `docs/superpowers/plans/2026-08-01-b10-related-wikisource-localization.md`.
- **Goal:** localize the related ancient works that have identifiable Wikisource
  texts with the same provenance treatment as 《唐開元占經》: permanent
  revisions, original text, volume/section locators, hashes, accession manifests,
  collation notes and GitHub auditability.
- **Plan:** `docs/research/B10_RELATED_WIKISOURCE_LOCALIZATION_PLAN.md`.
- **Priority:** P0 starts with 《乙巳占》, 《史記·天官書》,
  《漢書·天文志》, 《宋書·天文志》, 《晉書·天文志》,
  袁宏《後漢紀》 and 《後漢書》 because they directly affect Core14
  boundary or variant decisions. Exact known scopes include C03, C09, C11,
  C13, C14, C41, C43, C45 and C47; accession review may add only evidence-backed
  scope, never inferred associations.
- **Acceptance:** each localized object has an oldid-bound source snapshot,
  replayable URL, access date, SHA-256, version-family identity and explicit
  mapping scope; lost works or carrier-only quotations are recorded as excerpts
  and are never fabricated as complete standalone books.
- **Delivered:** 7 work families, 16 fixed-revision source objects, 645,044 raw UTF-8 bytes and 20 reversible mappings for 9 Core14 cases.
- **Draft PR:** #57 targets only `stable/kaiyuan-v2`; remote readback passed and targeted final re-review is approved at `48d7b0f796041931f25c44c9595f25264709096d` with Critical 0 / Important 0 / Minor 0.
- **Follow-up:** whole-book expansion and formal multi-text structure discussion remain `BACKLOG`; P0 does not claim whole-book completion.
- **Boundary:** P0 research sources only; no production schema freeze, official ingest, Reviewer A/B change, Qdrant access or `local_kb_default` access.

### B10-R04 — Reversible multi-text source model and natural-boundary expansion policy
- **Status:** `DONE`
- **Base:** `stable/kaiyuan-v2` at `090f1b95d1c0b798077162408cea3d3bedd975a5`.
- **Branch:** `codex/kaiyuan-b10-multitext-source-model-v1`.
- **Merged:** PR #58 squash merged as `1a30070d3517d07097fbffe3a8ed43a9a0144c5f` after the exact reviewed head passed all three required Actions.
- **Delivered:** immutable 16-object Layer A, rebuildable Work–TextVersion–Carrier–SourceObject Layer B, 20/20 reversible Core14 evidence links, 46 nodes, 39 bibliographic edges, 80 research assertions and an audit-bound pilot artifact.
- **Verification:** Task 1–4 local suite `166 passed`; exact-head Development Governance, Kaiyuan Stable Core and Kaiyuan Upstream Runtime all succeeded; final independent review Critical 0 / Important 0 / Minor 0 / Ready YES.
- **Boundary:** no production multi-text schema, rule/candidate identity change, independent-witness promotion, Reviewer A/B substitution, official ingest, Qdrant access, `local_kb_default` access, B11/B12 or `main`.

### B10-R05 — Bounded 15-accession source expansion
- **Status:** `DONE`
- **Base:** `stable/kaiyuan-v2` at `1a30070d3517d07097fbffe3a8ed43a9a0144c5f`.
- **Branch:** `codex/kaiyuan-b10-r05-bounded-source-expansion-v1`.
- **Goal:** add exactly 15 fixed-revision Wikisource accession/raw objects to the existing seven-family research package, rebuild the reversible projection against 31 source objects, and prove that all 20 Core14 mappings and the original 16 objects remain unchanged.
- **Fixed denominator:** 《乙巳占》 root plus volumes 1, 3, 4, 6, 7, 9 and 10 (8); 《漢書》 root (1); 《宋書》 root (1); 《晉書》 root (1); 袁宏《後漢紀》（四庫全書本） root (1); 《後漢書》 root plus volumes 101 and 102 (3). Total 15.
- **Acceptance:** exact ID/title/oldid register; 31 compact/detailed joins; 31 raw SHA-256 and byte counts; family counts 11/2/2/5/4/2/5; existing 16 metadata/raw identities unchanged; mapping document still exactly 20; zero new Core14 case claims; deterministic projection/check; no title merge, orphan or accepted independent-witness claim.
- **Plan:** `docs/superpowers/plans/2026-08-02-kaiyuan-b10-r05-bounded-source-expansion.md`.
- **Reviewed implementation head:** `46a360e96980b2d48fb2faba6b1876a93a93e27c`.
- **Final PR head:** `b084b10216f2be8ea2854768528e209d4c069c77`.
- **Merged:** PR #59 squash merged as `bcb72c9c922a8d87319cc88aec7a772016a1cf27`.
- **Exact-head workflows:** Development Governance `30784883162`, Kaiyuan Stable Core `30784883137`, Kaiyuan Upstream Runtime `30784883149`; all succeeded.
- **Delivered:** 15 new fixed revisions; 31 accessions/raw objects; 1,050,322 raw bytes; 76 graph nodes, 69 edges, 155 research assertions and the unchanged 20 evidence links; current artifact 233,498 bytes, SHA-256 `583b00a9d160d7374453ef4ec552acc05fa8faf9841a87978a0183d1bc595468`.
- **Verification:** 31/31 network raw replay; 15/15 target title/oldid/timestamp; inventory `62 passed`; combined focused suite `98 passed`; builder `--check`, compileall and remote artifact readback passed; branch review Critical 0 / Important 0 / Minor 0; all three final exact-head hosted Actions succeeded as recorded above.
- **Boundary:** no 631-object provider-history mirror, no inferred mapping, no Reviewer A/B change, no B10-PR-D/E/F start, no production schema freeze, official ingest, Qdrant or `local_kb_default` access.

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

## VFL — Evidence-to-video feedback loop

### VFL-T01 — Offline control-plane skeleton
- **Status:** `DONE` for the local S0 implementation/review scope; exact feature
  branch delivery is complete, while PR/integration/rendering/publication remain
  unclaimed
- **Base:** `stable/kaiyuan-v2` at
  `99c0a85c1f944add8d013aedbae830fe022b7c3b`.
- **Branch:** `codex/kaiyuan-evidence-feedback-loop-skeleton-v1`.
- **Goal:** connect an already audited external-media bundle, caller-supplied
  read-only local evidence probes, deterministic comparison, non-applying
  improvement candidates, a B9-bound production request, manual publication
  handoff and optional caller-supplied outcome in one offline auditable run.
- **Pilot:** 祖山觀 episode 22 / work `7669807398794598565`.
- **Design:**
  `docs/superpowers/specs/2026-08-29-kaiyuan-evidence-feedback-loop-skeleton-design.md`.
- **Plan:**
  `docs/superpowers/plans/2026-08-29-kaiyuan-evidence-feedback-loop-skeleton.md`.
- **Implemented Tasks 1–5:** strict non-authorizing lifecycle contracts;
  defensive external-audit/local-probe comparison; deterministic bounded
  improvement and safe B9 request planning; semantic-closure-checked atomic
  package assembly; and the canonical episode 22 fixture plus offline CLI.
  Final task heads are `72ca961`、`dba073b`、`6e87823`、`07f4d97` and
  `a951680` respectively.
- **Task 5 hardening:** after the initial CLI commit `663cc26`, fix
  `b190614` preserved literal shell metacharacters and embedded quotes across
  the Make recipe boundary. Fix `a951680` then prevented GNU Make function
  expansion and command-line override of the private transport aliases. Both
  rounds use real Make/CLI regressions; no Python production or fixture bytes
  changed in either round.
- **Final-review fixes:** the whole-branch review of `59af182` found exactly
  two Important findings and no Critical or Minor finding. FR-01 allowed
  modern-authority/retrieval-only evidence to authorize a decisive local
  result; FR-02 allowed an outcome metric ID to collide with a run metric ID.
  Commit `21e6904` fixes both in contract-owned validators across exactly four
  code/test paths. The same reviewer approved the scoped fixes with zero
  remaining findings after exhaustive/adversarial matrices.
- **Acceptance:** the episode 22 pilot is deterministic; external audit status
  and modern-context-only limits are preserved; every candidate records
  `apply_allowed=false`; the production request forbids absent classical quotes
  and storm-equivalence claims; publication remains manually blocked; invalid
  input, broken references and output collisions fail without partial output.
- **Verification:** TDD RED/GREEN evidence; feedback-loop focused tests;
  external-media and B9 package/review regression; full downstream tests;
  strict JSON, compileall, governance, diff and forbidden-path checks; independent
  review with no unresolved Critical or Important finding.
- **Local verification candidate:** final-review focused `58 passed`; complete
  feedback-loop `86 passed`; related external-media/B9/package regression
  `112 passed`; complete supported downstream `759 passed`; compileall exit
  `0`; governance unit `21 passed`; development governance passed.
  Two fresh canonical CLI runs produced the same eight relative members and
  run ID
  `feedback-run:vfl:e2fb1a2d98be3ea09b2c885f68832530741772afc588a40c9005c3761dcef6e0`;
  manifest SHA-256 is
  `00b96fd7dec1ad90da94af29bea90860b85b6712ad336c7bb7d345e412a8ebc4`
  and the canonical member-path/hash list SHA-256 is
  `fcacc7ac898f2a082147209b2cee28ae3144a450e59f974dd73f62bd0dada315`.
  An occupied-output replay exited `1`, preserved the complete tree and left
  zero staging residue.
- **Renewed whole-branch review:** exact candidate
  `33657fae698970a9d820870ab180c3712e9f295a`, tree
  `8bcce81842e6130d0328b525168f8b46c9955d7e`, contains `15 commits / 25
  changed paths / 15 code files` from stable and was approved with
  `0 Critical / 0 Important / 0 Minor`. FR-01 and FR-02 remain recorded as
  closed findings rather than erased history.
- **Residual:** the implementation code head is
  `21e69048b7277023458ee5217acec85d259eebb8` with tree
  `c869c1f3f81a5cdedf92ec026054b22e8e9bb958`. Local S0 is complete and Runner
  is `NOT RUN`. The 2026-08-30 local closeout was initially unpushed; on
  2026-08-31 exact closeout `f36b146`, tree `fe4babc`, was non-force pushed to
  the same feature branch. It still has no PR; no stable merge, render, upload
  or publication was performed.
- **Boundary:** additive offline research/control plane only. No live scraping,
  transcript/OCR reconstruction, model training, corpus/rule/threshold mutation,
  official ingest, Qdrant or `local_kb_default` access, account credentials,
  rendering/upload side effect, Reviewer A/B substitution, PR #54 mutation,
  B10-PR-D/E/F start, B11/B12 release or `main` operation.

### VFL-T01-D1 — Remote delivery state reconciliation

- **Status:** `VERIFYING`.
- **Base:** completed VFL-T01 local closeout
  `f36b146ddb08809b6b23a8db5e5fc94393165a21`, tree
  `fe4babc7c34328a4b18f22bbea998882ae38b2dc`.
- **Branch:** `codex/kaiyuan-evidence-feedback-loop-skeleton-v1`.
- **Goal:** replace the historical pre-push wording with exact, read-back
  remote delivery evidence while preserving VFL-T01's completed local S0
  implementation/review result and every D-031 authority boundary.
- **Allowed scope:** `docs/development/TASKS.md`, `DECISIONS.md`,
  `PROJECT_MEMORY.md`, `WORK_LOG.md`, root `summary.md` and a bounded execution
  status note in the existing VFL plan.
- **Prohibited:** product/test code, S1 or later VFL adapters, PR #54, Reviewer
  state, B10-PR-D/E/F, B11/B12, raw corpus, Qdrant, `local_kb_default`, media
  rendering/upload/publication, PR creation/merge, direct stable writes,
  `main`, force push or Runner dispatch.
- **Done:** all durable state agrees that the feature branch was non-force
  pushed at exact head `f36b146`; remote `stable/kaiyuan-v2` remains
  `99c0a85`; no PR, merge, render, upload or publication is claimed; docs and
  governance checks pass on the final documentation head.
- **Verify:** governance unit discovery; development-governance comparison to
  `99c0a85`; full downstream regression; `compileall`; `git diff --check`;
  exact changed-path/content scans; clean status after commit; remote branch,
  stable and `main` ref readback.
- **Delivery:** one documentation-only commit on the existing feature branch,
  followed by a non-force fast-forward push and exact remote readback. Keep
  Runner `NOT RUN`; do not create or modify a PR.

## B12 — Batch media and publishing assistance
- **Status:** `BACKLOG`
- **Boundary:** automatic publishing requires a separate safety decision

## Current sequence

```text
B10-R05 merged and recorded DONE
→ ASTRO-R01 phases 1–5 and DOC-R01 merged to stable at c9d490392233b7432f5a0136dcd213613abe05a7
→ B10-R06 evidence publication remains DONE on Draft PR #64
→ B10-R07 records 11 cases as provisional internal-use pending Reviewer B and isolates C03/C24/C33 for evidence supplementation
→ B10-R08 reconciles Draft PR #64 with the new stable baseline without changing those decisions
→ wait for a different human to independently complete Reviewer B across all 14 cases
→ validate the real reviewed fixtures and approval record; any frozen-gate failure remains BLOCKED
→ PR-C may publish canonical threshold-freeze.json only after every frozen gate passes
→ B10-PR-D/E/F remain unauthorized and BACKLOG until their entry gates pass and each task is separately recorded IN_PROGRESS
→ B10-PR-G/H and B11 remain BACKLOG behind the accepted B10 sequence
↳ VFL-T01 local S0 is DONE against frozen B9/external-audit interfaces
→ VFL-T01 remains at a manual handoff and may emit proposals only; any later adapter/stage requires separate authorization and it does not start or release B12
```

Current prohibitions:

- no direct stable writes;
- no B10-PR-D/E/F start before PR #54 satisfies the human-review and threshold-freeze gates;
- no AI substitution for Reviewer A/B;
- no official Qdrant or `local_kb_default` mutation;
- no automatic publishing or `final.mp4`;
- no automatic application of a VFL improvement or learning proposal;
- no claim that hosted CI replaces human, corpus, scientific or real-device evidence.
