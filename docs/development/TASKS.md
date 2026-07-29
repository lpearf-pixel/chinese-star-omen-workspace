# 开发任务台账

本文件只维护当前活跃阶段和后续路线。B4–B8 的完整历史台账已归档到 `docs/development/TASKS_B4_B8_ARCHIVE.md`；详细执行证据以阶段日志、PR 和 CI 为准。

## 状态定义

| 状态 | 含义 |
|---|---|
| `BACKLOG` | 已记录，尚未排期 |
| `READY` | 需求与验收条件明确，可开始 |
| `IN_PROGRESS` | 正在实现 |
| `BLOCKED` | 受外部依赖、环境或信息阻塞 |
| `VERIFYING` | 产物完成，正在执行测试、CI 或 review |
| `DONE` | 验收证据、CI、提交/PR 均已记录 |
| `CANCELLED` | 明确取消并记录原因 |

## 当前仓库事实

```text
Stable branch: stable/kaiyuan-v2
Last verified stable HEAD: 41a613a1606cbbf8a77336fa01ea4c98236b57c7
Current feature branch: codex/kaiyuan-b9-preview-media-evidence-v1
Current task: B9-G6-E1 preview media evidence hardening
Implementation status: IN_PROGRESS
B9 overall status: VERIFYING
Release target: stable/kaiyuan-v2
Forbidden target: main
Protected legacy collection: local_kb_default
```

以上事实每次会话必须重新核验。当前开放旧路线 PR 仍包括 #1、#7。

## 已完成稳定阶段

```text
B4–B8: DONE
PLAN-T01 / B9-B10 planning: DONE
B9-PR-A implementation #32: 26b4ce14afbc0010357c0fd9bc21bc69aa025f70
B9-PR-A closeout #33: 8bc8d0c8f91f78e4a4faceb22a037b9c526596c0
B9-PR-B implementation #34: c72aa7630f58c5828b8343bcdd39c369efe1df76
B9-PR-B closeout #35: 48180f6239187b491e41d9f68be0a9aab8dde95d
B9-PR-C implementation #36: 38042b995e885101999c93c6698a9544f22a948b
B9-PR-C closeout #37: 523c724add978bc4bb51fc07a716c6a852c95447
B9-PR-D implementation #38: e6cd46f87f16aef94074534aac09b03898ab9289
B9-PR-D closeout #39: d16e75d9eda153c13fcbcfc13449c49bb1a8af60
B9-PR-E implementation #40: 92e3c08371bb52651ea0fd5e4357fb9ce7dcd82f
B9-PR-E implementation closeout #41: 41a613a1606cbbf8a77336fa01ea4c98236b57c7
```

## Governance

### GOV-T02 — 核验并处置旧开放 PR #1、#7
- **Status:** `BACKLOG`
- **Boundary:** 不得只因“看起来旧”而关闭；不阻塞 B9。

## B9 — 契约先行＋2026-07-21 垂直样片

- **Status:** `VERIFYING`
- **Public contracts:** `AstronomyEvent/v1`、`RuleAssessment/v1`、`VideoPackage/v1`。
- **Design:** `docs/superpowers/specs/2026-07-20-kaiyuan-evidence-video-pipeline-design.md`。
- **Plan:** `docs/superpowers/plans/2026-07-20-kaiyuan-evidence-video-pipeline.md`。

### B9-PR-A — Contract registry and compatibility
- **Status:** `DONE`
- **Evidence:** `docs/development/B9_PR_A_CLOSEOUT.md`。

### B9-PR-B — Scientific provider and asterism catalog
- **Status:** `DONE`
- **Tests:** focused 40 passed；full downstream 319 passed。
- **Evidence:** `docs/development/B9_PR_B_CLOSEOUT.md`。

### B9-PR-C — RuleAssessment and evidence lineage
- **Status:** `DONE`
- **Tests:** focused 35 passed；full downstream 354 passed。
- **Evidence:** `docs/development/B9_PR_C_CLOSEOUT.md`。

### B9-PR-D — Editorial package and Stellarium script
- **Status:** `DONE`
- **Implementation PR:** #38，squash `e6cd46f87f16aef94074534aac09b03898ab9289`。
- **Closeout PR:** #39，squash `d16e75d9eda153c13fcbcfc13449c49bb1a8af60`。
- **Tests:** focused 41 passed；full downstream 395 passed。
- **Evidence:** `docs/development/B9_PR_D_CLOSEOUT.md`。

### B9-PR-E — Atomic package, review, preview and E2E

- **Status:** `VERIFYING` — implementation merged；local G6 remains。
- **Implementation PR:** #40，squash `92e3c08371bb52651ea0fd5e4357fb9ce7dcd82f`。
- **Implementation closeout PR:** #41，squash `41a613a1606cbbf8a77336fa01ea4c98236b57c7`。
- **Tests:** focused `33 passed in 1.35s`；full downstream `428 passed in 4.51s`。
- **Delivered:** deterministic SRT、canonical manifest、atomic no-replace publication、four dimension-bound reviews、bounded shell-free preview argv、local capability evidence interface、blocked/citable hermetic E2E and runbook。
- **Decision:** `docs/development/B9_PR_E_DECISION.md`。
- **Runbook:** `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`。
- **Implementation closeout:** `docs/development/B9_PR_E_IMPLEMENTATION_CLOSEOUT.md`。

### B9-G6-E1 — Preview media evidence hardening

- **Status:** `IN_PROGRESS`
- **Base:** `stable/kaiyuan-v2` at `41a613a1606cbbf8a77336fa01ea4c98236b57c7`。
- **Branch:** `codex/kaiyuan-b9-preview-media-evidence-v1`。
- **Problem:** current `LocalCapabilityEvidence/v1` records preview observation and tool/command hashes but does not bind the actual `preview.mp4` bytes or ffprobe-visible properties。
- **Scope:**
  - add strict `PreviewMediaEvidence/v1`;
  - bind preview relative path、byte size、SHA-256、width、height、duration、video codec and audio stream count;
  - require observed preview to include media evidence;
  - require approved visual evidence to include preview media and screenshots;
  - add a bounded helper that hashes an actual local preview and validates caller-supplied ffprobe metadata;
  - update runbook and local evidence builder.
- **Acceptance:**
  - tests committed and RED observed before production change;
  - actual media hash changes when preview bytes change;
  - only `preview.mp4`, 1080x1920, H.264, approximately 80 seconds and zero audio streams are accepted;
  - non-finite/invalid metadata、path traversal、missing media and oversized input fail closed;
  - no subprocess or shell is introduced into the evidence model;
  - exact-head focused/full workflows pass.
- **Excluded:** generating media in hosted CI、arbitrary ffprobe/FFmpeg execution、`final.mp4`、publishing、TTS、Qdrant/corpus mutation。

### B9-G6 — Local/self-hosted renderer evidence

- **Status:** `BLOCKED` until B9-G6-E1 merges; then `READY`。
- **Goal:** execute the exact package `.ssc` and preview argv on macOS, inspect the visual result, capture at most 30 screenshots and produce media-bound `LocalCapabilityEvidence/v1`。
- **Runbook:** `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`。
- **Boundary:** local evidence authorizes neither automatic publication nor classical narration；synthetic CI reviews do not count as real publication approval。

B9 cannot be marked `DONE` and B10 cannot start until B9-G6 is reviewed and the final B9 closeout is merged.

## B10 — 《唐开元占经》全书规则结构化
- **Status:** `BACKLOG`
- **Entry gate:** B9-G6 evidence accepted and final B9 closeout merged。

## B11 — 规则执行器 2.0
- **Status:** `BACKLOG`

## B12 — 批量媒体与发布辅助
- **Status:** `BACKLOG`
- **Boundary:** 自动发布需要独立安全决策。

## 当前执行顺序

```text
B9-G6-E1 tests-first RED
→ preview media evidence implementation
→ focused/full review and merge
→ local/self-hosted macOS G6
→ final B9 closeout
→ only then B10
```

当前不得：

- 在 stable 直接写入；
- 提前启动 B10、B11 或 B12；
- 修改正式 Qdrant 或 `local_kb_default`；
- 自动发布、生成 `final.mp4` 或引入通用媒体编排；
- 将 hosted CI 冒充实际 Stellarium/FFmpeg G6 证据；
- 用“preview_observed=true”替代实际 preview media hash 和 ffprobe metadata。
