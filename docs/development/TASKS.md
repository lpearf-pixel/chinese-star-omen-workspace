# 开发任务台账

本文件维护当前活跃阶段和后续路线。B4–B8 历史台账位于 `docs/development/TASKS_B4_B8_ARCHIVE.md`。

## 状态定义

`BACKLOG`、`READY`、`IN_PROGRESS`、`BLOCKED`、`VERIFYING`、`DONE`、`CANCELLED`。

## 当前仓库事实

```text
Stable branch: stable/kaiyuan-v2
Last verified stable HEAD: d6f2f862d7cf45c1008925f6d4286aabb4e43077
Current feature branch: codex/kaiyuan-b9-ai-visual-review-v1
Current task: B9-G6-E3 exact-head verification
B9 overall: VERIFYING
B9-G6: BLOCKED after rejected first evidence review
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
- **Status:** `BLOCKED`
- **Goal:** on macOS run the exact `.ssc` and preview argv, validate actual preview media, inspect the result, capture at most 30 screenshots, and create canonical media-bound `LocalCapabilityEvidence/v1`
- **Runbook:** `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`
- **Required archive:** capability JSON、ffprobe JSON、preview.mp4、scene.ssc、preview command、package manifest、screenshot inventory and screenshots
- **Boundary:** synthetic CI is not real renderer evidence and does not authorize publication
- **Rejected evidence:** `b9-local-g6-evidence-20260730T040856Z.tar.gz`, archive SHA-256 `fc49031dc98083e46aad912b3cfaa43cea611ec80934c37352ba9691cf9eff52`
- **Reason:** archive integrity passed, but `july-21-event.json` and generated narration asserted `3.25°`; independent recomputation for the recorded 2026-07-21 11:00 UTC Shanghai observation was approximately `5.4°`. The fixture also used placeholder ephemeris provenance.

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
- **Status:** `VERIFYING`
- **Entry gate:** B9-G6-E2 merged and source-backed evidence regenerated.
- **Goal:** bind an externally produced AI visual assessment to exact preview and screenshot hashes, with `passed|rejected|needs_human_review`, confidence and itemized evidence.
- **Plan:** `docs/superpowers/plans/2026-07-30-kaiyuan-ai-visual-review.md`
- **Boundary:** AI cannot approve astronomy facts, classical evidence or a machine-rejected package.
- **Implementation commits:** `f941539`, `6ff8775`, `acdd98a`, `009daef`
- **Local verification:** focused assisted review `148 passed`; package review `80 passed`; contracts `6 passed`; text-core `22 passed`; downstream `475 passed`.
- **Remaining:** exact-head local gates, remote Draft PR workflows and merge.

### B9-G6-E4 — Lightweight human confirmation
- **Status:** `BACKLOG`
- **Entry gate:** B9-G6-E2 merged; E3 report available or explicitly `needs_human_review`.
- **Goal:** ask only three layperson checks after professional gates pass and bind the answer to exact review artifacts.
- **Plan:** `docs/superpowers/plans/2026-07-30-kaiyuan-light-human-confirmation.md`
- **Boundary:** no terminal `read`; no generic `y` approval; no approval control is shown after a hard rejection.

B9 remains `VERIFYING`; B10 cannot start until G6 evidence is accepted and final B9 closeout is merged.

## Governance

### GOV-T02 — Legacy PR #1/#7 disposition
- **Status:** `BACKLOG`
- **Boundary:** compare against stable v2 before closure; does not block G6

## B10 — Whole-book rule structuring
- **Status:** `BACKLOG`
- **Entry gate:** accepted B9-G6 evidence plus final B9 closeout

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
→ independently verify the resulting evidence archive
→ final B9 closeout
→ only then B10
```

Current prohibitions:

- no direct stable writes;
- no B10–B12 implementation;
- no official Qdrant or `local_kb_default` mutation;
- no automatic publishing or `final.mp4`;
- no claim that hosted CI is real Stellarium/FFmpeg evidence.
