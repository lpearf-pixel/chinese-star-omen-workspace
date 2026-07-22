# 开发任务台账

本文件只维护当前活跃阶段和后续路线。B4–B8 的完整历史台账已原样归档到 `docs/development/TASKS_B4_B8_ARCHIVE.md`；详细执行证据继续以 `WORK_LOG.md`、阶段日志、PR 和 CI 为准。

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
Last verified stable HEAD before closeout: 26b4ce14afbc0010357c0fd9bc21bc69aa025f70
Current closeout branch: codex/kaiyuan-b9-contract-registry-closeout-v1
Current task: B9-PR-A closeout
Implementation status: B9-PR-A DONE; B9-PR-B READY after closeout merge
Release target: stable/kaiyuan-v2
Forbidden target: main
Protected legacy collection: local_kb_default
V2 collection: local_kb_kaiyuan_v2 or random ephemeral CI collection
```

以上事实每次会话必须重新核验。当前开放旧路线 PR 仍包括 #1、#7。

### 稳定分支治理事件

2026-07-22 在建立 B9-PR-A 分支时误用 contents API，曾直接在 stable 新增临时 `README.tmp`；随即停止实现并删除该文件。`cd630c44...` 与修复后 stable 的净文件差异为空，但 stable 历史多出两个直接提交。不得改写 stable 历史掩盖该事件；后续所有实现只通过 feature branch 和 PR。

## 已完成稳定阶段

```text
B4: DONE
B5: DONE
B6: DONE
B7: DONE
B8-T01: DONE
B8-T02: DONE
PLAN-T01 / B9-B10 planning: DONE
Planning PR #30: merged as 017601e74f32f50fea9faeb663b72eb8cfe3b93c
Planning closeout PR #31: merged as cd630c44a16ade295626e62dcee8e27ee99c8f3a
B9-PR-A implementation PR #32: merged as 26b4ce14afbc0010357c0fd9bc21bc69aa025f70
```

完整 B4–B8 任务明细：`docs/development/TASKS_B4_B8_ARCHIVE.md`。

## Governance

### GOV-T02 — 核验并处置旧开放 PR #1、#7

- **Status:** `BACKLOG`
- **Goal:** 逐项比较旧 PR 与 stable v2，确认是否完全 superseded；有充分证据后添加说明并关闭。
- **Boundary:** 不得只因“看起来旧”而关闭；不阻塞 B9。

## B9 — 契约先行＋2026-07-21 垂直样片

- **Status:** `IN_PROGRESS`
- **Public contracts:** `AstronomyEvent/v1`、`RuleAssessment/v1`、`VideoPackage/v1`。
- **Design:** `docs/superpowers/specs/2026-07-20-kaiyuan-evidence-video-pipeline-design.md`。
- **Plan:** `docs/superpowers/plans/2026-07-20-kaiyuan-evidence-video-pipeline.md`。

### B9-PR-A — Contract registry and compatibility

- **Status:** `DONE`
- **Base:** `stable/kaiyuan-v2` at `d63bfd458764bf7999ff20b4c367f53c0b4f31fe`.
- **Branch:** `codex/kaiyuan-b9-contract-registry-v1`.
- **PR:** #32，squash merged。
- **Final feature head:** `8bc3e4ae97780cd0f9f6f9c935508fd374684c4e`。
- **Exact-head workflows:**
  - Development Governance `29889316084` — success；
  - Kaiyuan Stable Core `29889316073` — success；
  - Kaiyuan Upstream Runtime `29889316046` — success。
- **Squash merge:** `26b4ce14afbc0010357c0fd9bc21bc69aa025f70`。
- **Review:** zero review threads and zero submitted reviews at final head。
- **Delivered:**
  - strict Pydantic v1 public contracts;
  - Draft 2020-12 JSON Schema snapshots and registry;
  - canonical JSON bytes and three canonical fixtures;
  - fixture file hash → manifest hash → registry binding;
  - strict ASCII IDs, UTC, finite numbers, formal recommendation and same-package references;
  - recursive additive-optional compatibility checks including nested `$defs`;
  - focused, property, fixture, Pydantic/JSON Schema negative and review regression tests.
- **TDD:** initial missing-module RED; two-review-regression RED; eleven-validation-gap RED; JSON Schema key-space RED; local focused GREEN `26 passed`。
- **Decision:** `docs/development/B9_PR_A_DECISION.md`。
- **Start log:** `docs/development/B9_PR_A_START.md`。
- **Closeout:** `docs/development/B9_PR_A_CLOSEOUT.md`。
- **Boundary:** no Skyfield calculation, asterism catalog, retrieval, rule adapter, corpus/candidate/ingest/Qdrant, Stellarium, FFmpeg or media change。

### B9-PR-B — Scientific provider and asterism catalog

- **Status:** `READY`
- **Entry gate:** B9-PR-A docs-only closeout merged；重新核验 remote stable HEAD 与开放 PR；从新 stable 建独立 feature branch。
- **Scope:** scientific conventions、fixed ephemeris provider boundary、toolchain provenance、versioned Chinese asterism catalog and scientific/asterism fixtures。
- **Excluded:** retrieval integration、RuleAssessment adapter、editorial、Stellarium execution、FFmpeg/media。

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

## B12 — 批量媒体与发布辅助

- **Status:** `BACKLOG`
- **Entry gate:** B9 契约稳定，B10/B11 正式规则和执行能力可用。
- **Boundary:** 自动发布需要独立安全决策。

## 当前执行顺序

```text
B9-PR-A docs-only closeout workflows/review/merge
→ re-read remote stable HEAD and open PRs
→ create B9-PR-B branch from exact stable
→ mark B9-PR-B IN_PROGRESS
→ tests-first RED
→ minimal scientific/catalog implementation
```

当前不得：

- 在 stable 或 closeout 分支写 B9-PR-B 实现；
- 提前启动 B9-PR-C、B10、B11 或 B12；
- 修改正式 Qdrant 或 `local_kb_default`；
- 生成或发布视频；
- 将候选原文或现代转译升级为正式古籍结论。
