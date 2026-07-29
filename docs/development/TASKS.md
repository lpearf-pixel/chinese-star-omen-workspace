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
Last verified stable HEAD before closeout: e6cd46f87f16aef94074534aac09b03898ab9289
Current closeout branch: codex/kaiyuan-b9-editorial-closeout-v1
Current task: B9-PR-D closeout
Implementation status: B9-PR-D DONE; B9-PR-E READY after closeout merge
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
- **Final feature head:** `2e0b4713c158a321de645d74808316852fc20177`。
- **Tests:** focused `41 passed in 1.55s`；full downstream `395 passed in 4.29s`。
- **Exact-head workflows:** Governance `30488433312`、Editorial/Stellarium `30488434202`、Stable Core `30488433382`、Upstream Runtime `30488433542` 均 success。
- **Review:** 17 expected files；0 review threads；0 submitted reviews。
- **Delivered:** strict 80-second claim compiler、content-bound package identity、exact quote-lineage set validation、one-shot-per-claim timeline、deterministic safe Stellarium 26.x `.ssc`。
- **Boundary:** no GUI、screenshots、SRT、FFmpeg、audio/video、publishing、corpus/candidate/ingest/Qdrant/collection or `local_kb_default` mutation。
- **Decision:** `docs/development/B9_PR_D_DECISION.md`。
- **Closeout:** `docs/development/B9_PR_D_CLOSEOUT.md`。

### B9-PR-E — Atomic package, review, preview and E2E
- **Status:** `READY`
- **Entry gate:** B9-PR-D docs-only closeout merged；重新核验远端 stable HEAD 与开放 PR；从新 stable 建独立 feature branch。
- **Scope:** atomic no-overwrite package writing、review records、deterministic SRT、bounded FFmpeg preview argv、hermetic vertical E2E、local/self-hosted Stellarium/preview evidence interface。
- **Excluded:** TTS、final.mp4、batch generation、automatic publishing、full-book rule structuring、formal Qdrant mutation。

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
B9-PR-D docs-only closeout workflows/review/merge
→ re-read remote stable HEAD and open PRs
→ create B9-PR-E branch from exact stable
→ mark B9-PR-E IN_PROGRESS
→ tests-first RED
→ atomic package/review/SRT/preview/E2E implementation
```

当前不得：

- 在 stable 或 closeout 分支写 B9-PR-E 实现；
- 提前启动 B10、B11 或 B12；
- 修改正式 Qdrant 或 `local_kb_default`；
- 自动发布或生成 `final.mp4`；
- 弱化 claim、evidence、quote-set、package-ID 或 `.ssc` 安全边界。
