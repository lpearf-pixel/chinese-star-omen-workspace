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
Last verified stable HEAD before closeout: 38042b995e885101999c93c6698a9544f22a948b
Current closeout branch: codex/kaiyuan-b9-rule-assessment-closeout-v1
Current task: B9-PR-C closeout
Implementation status: B9-PR-C DONE; B9-PR-D READY after closeout merge
Release target: stable/kaiyuan-v2
Forbidden target: main
Protected legacy collection: local_kb_default
V2 collection: local_kb_kaiyuan_v2 or random ephemeral CI collection
```

以上事实每次会话必须重新核验。当前开放旧路线 PR 仍包括 #1、#7。

### 稳定分支治理事件

2026-07-22 在建立 B9-PR-A 分支时误用 contents API，曾直接在 stable 新增临时 `README.tmp`；随即停止实现并删除该文件。净文件差异为空，但 stable 历史保留两个直接提交。不得改写历史掩盖该事件；后续所有实现只通过 feature branch 和 PR。

## 已完成稳定阶段

```text
B4: DONE
B5: DONE
B6: DONE
B7: DONE
B8-T01: DONE
B8-T02: DONE
PLAN-T01 / B9-B10 planning: DONE
B9-PR-A implementation PR #32: 26b4ce14afbc0010357c0fd9bc21bc69aa025f70
B9-PR-A closeout PR #33: 8bc8d0c8f91f78e4a4faceb22a037b9c526596c0
B9-PR-B implementation PR #34: c72aa7630f58c5828b8343bcdd39c369efe1df76
B9-PR-B closeout PR #35: 48180f6239187b491e41d9f68be0a9aab8dde95d
B9-PR-C implementation PR #36: 38042b995e885101999c93c6698a9544f22a948b
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
- **Implementation PR:** #32，squash `26b4ce14afbc0010357c0fd9bc21bc69aa025f70`。
- **Closeout PR:** #33，squash `8bc8d0c8f91f78e4a4faceb22a037b9c526596c0`。
- **Evidence:** `docs/development/B9_PR_A_CLOSEOUT.md`。

### B9-PR-B — Scientific provider and asterism catalog

- **Status:** `DONE`
- **Implementation PR:** #34，squash `c72aa7630f58c5828b8343bcdd39c369efe1df76`。
- **Closeout PR:** #35，squash `48180f6239187b491e41d9f68be0a9aab8dde95d`。
- **Tests:** focused 40 passed；full downstream 319 passed。
- **Evidence:** `docs/development/B9_PR_B_CLOSEOUT.md`。

### B9-PR-C — RuleAssessment and evidence lineage

- **Status:** `DONE`
- **Base:** `stable/kaiyuan-v2` at `48180f6239187b491e41d9f68be0a9aab8dde95d`。
- **Implementation PR:** #36，squash `38042b995e885101999c93c6698a9544f22a948b`。
- **Final feature head:** `c218ce6d364d12964dff17b50d5f7605593d0fd1`。
- **Exact-head workflows:**
  - Development Governance `30481026839` — success；
  - B9 RuleAssessment Lineage `30481027508` — success；
  - Kaiyuan Stable Core `30481026842` — success；
  - Kaiyuan Upstream Runtime `30481027262` — success。
- **Tests:** focused `35 passed in 1.19s`；full downstream `354 passed in 3.37s`。
- **Review:** 22 expected files；zero review threads；zero submitted reviews。
- **Delivered:** explicit event projection、candidate-first two-pass matcher orchestration、candidate-only evidence hydration、frozen RuleAssessment projection、formal/provisional recommendation separation、content-free EvidenceBundle lineage、dual positive/blocked fixtures and dedicated CI。
- **Fail-closed boundary:** non-match/partial/insufficient/already-citable rows do not retrieve；exact hit must belong to primary candidates and have exactly one official/fallback route；overlay/non-exact/candidate/multi-hit/resolver mismatch cannot become citable。
- **Decision:** `docs/development/B9_PR_C_DECISION.md`。
- **Start log:** `docs/development/B9_PR_C_START.md`。
- **Closeout:** `docs/development/B9_PR_C_CLOSEOUT.md`。
- **Excluded:** editorial、Stellarium、SRT/FFmpeg/media、full-book structuring、corpus/candidate/ingest/Qdrant/`local_kb_default` mutation。

### B9-PR-D — Editorial package and Stellarium script

- **Status:** `READY`
- **Entry gate:** B9-PR-C docs-only closeout merged；重新核验 remote stable HEAD 与开放 PR；从新 stable 建独立 feature branch。
- **Scope:** claim compiler、claim-level source validation、editorial package、deterministic Stellarium `.ssc` generation and package-level consistency tests。
- **Classical boundary:** `classical_quote` 只能来自 `EvidenceBundle/v1` 中 `narration_allowed=true` 的 lineage；其余古籍相关输出必须省略或标为 blocked。
- **Excluded:** Stellarium GUI execution、screenshots、SRT、FFmpeg、audio/video、publishing and full-book rule structuring。

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

## B12 — 批量媒体与发布辅助
- **Status:** `BACKLOG`
- **Boundary:** 自动发布需要独立安全决策。

## 当前执行顺序

```text
B9-PR-C docs-only closeout workflows/review/merge
→ re-read remote stable HEAD and open PRs
→ create B9-PR-D branch from exact stable
→ mark B9-PR-D IN_PROGRESS
→ tests-first RED
→ minimal claim compiler/editorial package/Stellarium script implementation
```

当前不得：

- 在 stable 或 closeout 分支写 B9-PR-D 实现；
- 提前启动 B9-PR-E、B10、B11 或 B12；
- 修改正式 Qdrant 或 `local_kb_default`；
- 运行 Stellarium GUI 或生成视频；
- 将 blocked lineage 升级为 classical quotation。
