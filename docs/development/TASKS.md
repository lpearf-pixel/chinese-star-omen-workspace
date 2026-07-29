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
Last verified stable HEAD: d16e75d9eda153c13fcbcfc13449c49bb1a8af60
Current feature branch: codex/kaiyuan-b9-package-review-preview-v1
Current task: B9-PR-E
Implementation status: IN_PROGRESS
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
```

## Governance

### GOV-T02 — 核验并处置旧开放 PR #1、#7

- **Status:** `BACKLOG`
- **Boundary:** 不得只因“看起来旧”而关闭；不阻塞 B9。

## B9 — 契约先行＋2026-07-21 垂直样片

- **Status:** `IN_PROGRESS`
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

- **Status:** `IN_PROGRESS`
- **Base:** `stable/kaiyuan-v2` at `d16e75d9eda153c13fcbcfc13449c49bb1a8af60`。
- **Branch:** `codex/kaiyuan-b9-package-review-preview-v1`。
- **Scope:**
  - deterministic SRT derived from the frozen claim/shot timeline;
  - atomic same-filesystem no-overwrite package publication;
  - canonical manifest and hash inventory for structured assets, `.ssc`, SRT and optional preview metadata;
  - independent review records for astronomy、classical evidence、editorial and render dimensions;
  - bounded FFmpeg preview argv construction without shell execution;
  - hermetic end-to-end assembly for the July 21 blocked-classical path and evidence-rich citable path;
  - local/self-hosted capability evidence interface for actual Stellarium/preview verification.
- **Acceptance:**
  - tests are committed and RED observed before production modules;
  - staging validates every member before an atomic publish and refuses overwrite/races;
  - package paths are relative, confined, normalized and free of symlink/traversal ambiguity;
  - structured package size is bounded to 10 MiB excluding optional media;
  - SRT cues are monotonic, non-overlapping, cover the editorial timeline and are byte-deterministic;
  - review dimensions remain independent and classical publishability is blocked by candidate/ambiguous/missing/tampered evidence;
  - preview command is an argv list only, fixed at 1080x1920, bounded to 120 seconds, with no shell or arbitrary filters/paths;
  - `preview.mp4` is optional and toolchain-bound; `final.mp4` is forbidden;
  - hermetic E2E performs no network, GUI, Qdrant or official ingest operation;
  - repeated structured generation is byte-identical and tampering fails before publication;
  - focused/full exact-head workflows and independent review pass.
- **Excluded:** TTS、voice cloning、`final.mp4`、batch generation、general media orchestration、automatic publishing、full-book rule structuring、formal Qdrant mutation。
- **Start log:** `docs/development/B9_PR_E_START.md`。

B9 不做全书结构化、TTS、批量扫描、通用剪辑或自动发布。

## B10 — 《唐开元占经》全书规则结构化
- **Status:** `BACKLOG`
- **Entry gate:** B9 closeout 后的新 stable HEAD。

## B11 — 规则执行器 2.0
- **Status:** `BACKLOG`

## B12 — 批量媒体与发布辅助
- **Status:** `BACKLOG`
- **Boundary:** 自动发布需要独立安全决策。

## 当前执行顺序

```text
B9-PR-E governance start
→ tests-first RED
→ deterministic SRT and canonical member inventory
→ atomic package writer and review gate
→ bounded preview argv and capability evidence
→ hermetic blocked/citable E2E
→ independent review and exact-head workflows
→ squash merge and B9 closeout
```

当前不得：

- 在 stable 或旧 closeout 分支写实现；
- 提前启动 B10、B11 或 B12；
- 修改正式 Qdrant 或 `local_kb_default`；
- 自动发布、生成 `final.mp4` 或引入通用媒体编排；
- 弱化 claim、evidence、quote-set、package-ID、`.ssc`、atomic/no-overwrite 或 review 安全边界。
