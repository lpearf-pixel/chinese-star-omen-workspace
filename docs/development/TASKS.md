# 开发任务台账

本文件只维护当前活跃阶段和后续路线。B4–B8 的完整历史台账已原样归档到 `docs/development/TASKS_B4_B8_ARCHIVE.md`；详细执行证据继续以 `WORK_LOG.md`、PR 和 CI 为准。

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
Last verified stable HEAD: 017601e74f32f50fea9faeb663b72eb8cfe3b93c
Planning PR #30: merged
Planning PR final head: d31a69f89aabba2b360d31b7af2b7ac6b88fd30d
Planning squash merge: 017601e74f32f50fea9faeb663b72eb8cfe3b93c
Current closeout branch: codex/kaiyuan-b9-b10-plan-closeout
Implementation status: NOT STARTED
Release target: stable/kaiyuan-v2
Forbidden target: main
Protected legacy collection: local_kb_default
V2 collection: local_kb_kaiyuan_v2 or random ephemeral CI collection
```

以上远端事实每次会话必须重新核验。当前开放 PR 还包括旧路线 #1、#7，不能宣称仓库无开放 PR。

## 已完成稳定阶段

```text
B4: DONE
B5: DONE
B6: DONE
B7: DONE
B8-T01: DONE
B8-T02: DONE
B8 closeout PR #29: merged
B9/B10 planning PR #30: merged
```

完整 B4–B8 任务明细：`docs/development/TASKS_B4_B8_ARCHIVE.md`。

## 当前规划任务

### PLAN-T01 — B9/B10 方案 C、计划硬化与全局记忆

- **Status:** `VERIFYING`
- **Planning PR:** #30，已 squash 合入 `stable/kaiyuan-v2`。
- **Final head:** `d31a69f89aabba2b360d31b7af2b7ac6b88fd30d`。
- **Exact-head workflows:**
  - Development Governance `29809558357` — success；
  - Kaiyuan Stable Core `29809558424` — success；
  - Kaiyuan Upstream Runtime `29809558491` — success。
- **Squash merge:** `017601e74f32f50fea9faeb663b72eb8cfe3b93c`。
- **Closeout branch:** `codex/kaiyuan-b9-b10-plan-closeout`。
- **Goal:** 冻结“B9 契约＋垂直样片 → B10 全书规则结构化 → B11 执行器 2.0 → B12 批量媒体”的路线，并补齐测试、记忆、范围和完成定义。
- **Acceptance:**
  - B9 拆为五个顺序实现 PR；
  - B10 拆为基础设施、试点、全书抽取、审核波次和发布；
  - 全书完成分母明确；
  - JSON Schema registry、claim lineage、toolchain provenance、双轨样片验收明确；
  - batch/checkpoint/review queue/model governance/engine-gap 明确；
  - 七层测试、黄金文件和媒体确定性边界明确；
  - PR #30 保持 docs-only，无功能代码、schema 实现、媒体或 Qdrant 操作；
  - closeout PR exact-head workflows 和合并证据记录后转 `DONE`。
- **Plan review:** `docs/development/B9_B10_PLAN_REVIEW.md`。

### GOV-T02 — 核验并处置旧开放 PR #1、#7

- **Status:** `BACKLOG`
- **Goal:** 逐项比较旧 PR 与 stable v2，确认是否完全 superseded；有充分证据后添加说明并关闭。
- **Boundary:** 不得只因“看起来旧”而关闭；不影响 B9 规划 closeout。

## B9 — 契约先行＋2026-07-21 垂直样片

- **Status:** `BACKLOG`
- **Entry gate:** PLAN-T01 closeout 合并；重新读取新 stable HEAD；用户明确授权进入实现；建立独立 B9-PR-A 分支。
- **Public contracts:** `AstronomyEvent/v1`、`RuleAssessment/v1`、`VideoPackage/v1`。
- **Design:** `docs/superpowers/specs/2026-07-20-kaiyuan-evidence-video-pipeline-design.md`。
- **Plan:** `docs/superpowers/plans/2026-07-20-kaiyuan-evidence-video-pipeline.md`。

### B9-PR-A — Contract registry and compatibility
- **Status:** `BACKLOG`

### B9-PR-B — Scientific provider and asterism catalog
- **Status:** `BACKLOG`

### B9-PR-C — RuleAssessment and evidence lineage
- **Status:** `BACKLOG`

### B9-PR-D — Editorial package and Stellarium script
- **Status:** `BACKLOG`

### B9-PR-E — Atomic package, review, preview and E2E
- **Status:** `BACKLOG`

B9 不做全书结构化、TTS、批量扫描、通用剪辑或自动发布。

## B10 — 《唐开元占经》全书规则结构化

- **Status:** `BACKLOG`
- **Entry gate:** B9 closeout 后的新 stable HEAD 和稳定 `RuleAssessment/v1`。
- **Design:** `docs/superpowers/specs/2026-07-20-kaiyuan-whole-book-rule-structuring-design.md`。
- **Plan:** `docs/superpowers/plans/2026-07-20-kaiyuan-whole-book-rule-structuring.md`。

### B10-PR-A — OmenRule/v2, identity and annotation
- **Status:** `BACKLOG`

### B10-PR-B — Passage inventory and resumable batch framework
- **Status:** `BACKLOG`

### B10-PR-C — Golden sets and calibration pilot
- **Status:** `BACKLOG`

### B10-PR-D — Full-book deterministic extraction
- **Status:** `BACKLOG`

### B10-PR-E — Optional model candidate adapter
- **Status:** `BACKLOG`
- **Note:** 可跳过；默认 disabled，不是 B10 完成前提。

### B10-PR-F — Review queue, deduplication and conflict workflow
- **Status:** `BACKLOG`

### B10-PR-G — Full-book review waves and coverage
- **Status:** `BACKLOG`

### B10-PR-H — Rule release, offline verification and engine-gap report
- **Status:** `BACKLOG`

B10 只有满足全书 inventory、eligibility、candidate/no-reason、候选终态和 approved-rule 验证分母后才能 DONE，单批发布不能冒充全书完成。

## B11 — 规则执行器 2.0

- **Status:** `BACKLOG`
- **Entry gate:** B10 正式 `engine-gap-report.json`；只统计 approved/citable 规则。
- **Scope:** 根据真实频次和风险补复杂事件、时序、持续、留逆、组合天体、应期和历史回测。

## B12 — 批量媒体与发布辅助

- **Status:** `BACKLOG`
- **Entry gate:** B9 契约稳定，B10/B11 正式规则和执行能力可用。
- **Scope:** 未来天象扫描、多模板媒体、配音、人工发布辅助和运营闭环。
- **Boundary:** 自动发布需要独立安全决策。

## 当前执行顺序

```text
PLAN-T01 closeout exact-head docs workflows and review
→ review/merge closeout PR
→ re-read remote stable HEAD and open PRs
→ keep B9-PR-A BACKLOG
```

用户此前要求“先计划，不要开发”。因此 closeout 完成后不得自动建立 B9 实现分支，也不得将 B9-PR-A 标记为 `IN_PROGRESS`，直到用户明确授权。

当前不得：

- 在规划或 closeout 分支写功能代码；
- 提前启动 B9/B10/B11/B12；
- 修改正式 Qdrant 或 `local_kb_default`；
- 生成或发布视频；
- 将候选原文或现代转译升级为正式古籍结论。
