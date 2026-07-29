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
Last verified stable HEAD: 48180f6239187b491e41d9f68be0a9aab8dde95d
Current feature branch: codex/kaiyuan-b9-rule-assessment-lineage-v1
Current task: B9-PR-C
Implementation status: IN_PROGRESS
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
B9-PR-A: DONE
B9-PR-A implementation PR #32: 26b4ce14afbc0010357c0fd9bc21bc69aa025f70
B9-PR-A closeout PR #33: 8bc8d0c8f91f78e4a4faceb22a037b9c526596c0
B9-PR-B implementation PR #34: c72aa7630f58c5828b8343bcdd39c369efe1df76
B9-PR-B closeout PR #35: 48180f6239187b491e41d9f68be0a9aab8dde95d
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

- **Status:** `IN_PROGRESS`
- **Base:** `stable/kaiyuan-v2` at `48180f6239187b491e41d9f68be0a9aab8dde95d`。
- **Branch:** `codex/kaiyuan-b9-rule-assessment-lineage-v1`。
- **Scope:**
  - deterministic `AstronomyEvent/v1` → legacy matcher input projection;
  - existing matcher/evidence resolver → frozen `RuleAssessment/v1` projection;
  - optional fail-closed two-stage retrieval only for unresolved rule evidence;
  - exact-primary hydration only after unique exact hit and full resolver validation;
  - content-free `EvidenceBundle/v1` with rule/evidence/claim-class lineage;
  - formal versus provisional recommendation and narration eligibility;
  - deterministic IDs, fixtures, negative-golden and integration tests.
- **Evidence projection:**
  - `citable` remains citable only with locator and normalized SHA-256;
  - overlay/structured fallback remains `candidate_only`;
  - multiple exact passages or conflicting source metadata becomes `ambiguous`;
  - missing source/evidence becomes `missing_evidence`;
  - transport/auth/timeout/contract errors propagate and never become healthy empty results.
- **Formal recommendation:** only an internally selected rule with `match_status=matched` and citable evidence may populate `recommended_rule_id` or become narration eligible. Candidate-only/insufficient/partial/manual-review results remain blocked and may expose only provisional identity.
- **Start log:** `docs/development/B9_PR_C_START.md`。
- **Acceptance:**
  - task and failing tests committed before production modules;
  - public output contains only frozen contract fields, not matcher internals;
  - event ID, rule IDs, conditions, conflicts and evidence links fail closed on malformed input;
  - official structured recall → official primary → filesystem fallback order is preserved by the existing retriever;
  - candidate overlay is never considered citable;
  - unique exact primary candidate must pass source/locator/page/paragraph/heading/anchor/hash resolver checks before hydration;
  - evidence bundle is content-free, canonical and deterministically hashable;
  - evidence-rich regression enables classical narration only for a citable selected rule;
  - 2026-07-21 no-rule path remains honest and blocked for classical narration;
  - focused/full exact-head workflows and independent review pass;
  - no corpus/candidate/ingest/Qdrant/`local_kb_default` mutation and no media generation.
- **Excluded:** editorial text generation、Stellarium script、SRT/FFmpeg/media、full-book rule structuring、Qdrant mutation。

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

## B12 — 批量媒体与发布辅助
- **Status:** `BACKLOG`
- **Boundary:** 自动发布需要独立安全决策。

## 当前执行顺序

```text
B9-PR-C governance start
→ tests-first RED
→ minimal event/matcher/evidence projection
→ retrieval hydration and evidence bundle
→ focused/full regressions
→ independent review and exact-head workflows
→ squash merge and docs-only closeout
→ only then B9-PR-D
```

当前不得：

- 在 stable 或旧 closeout 分支写实现；
- 提前启动 B9-PR-D、B10、B11 或 B12；
- 修改正式 Qdrant 或 `local_kb_default`；
- 生成或发布视频；
- 将 candidate、ambiguous、missing 或 unverified evidence 升级为正式古籍口播。
