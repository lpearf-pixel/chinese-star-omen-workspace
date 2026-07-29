# 开发任务台账

本文件只维护当前活跃阶段和后续路线。B4–B8 的完整历史台账已原样归档到 `docs/development/TASKS_B4_B8_ARCHIVE.md`；详细执行证据继续以阶段日志、PR 和 CI 为准。

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
Last verified stable HEAD: 523c724add978bc4bb51fc07a716c6a852c95447
Current feature branch: codex/kaiyuan-b9-editorial-stellarium-v1
Current task: B9-PR-D
Implementation status: IN_PROGRESS
Release target: stable/kaiyuan-v2
Forbidden target: main
Protected legacy collection: local_kb_default
```

以上事实每次会话必须重新核验。当前开放旧路线 PR 仍包括 #1、#7。

### 稳定分支治理事件

2026-07-22 曾误用 contents API 在 stable 新增并立即删除临时 `README.tmp`。净文件差异为空，但历史保留两个直接提交。不得改写历史；后续实现只通过 feature branch 和 PR。

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

- **Status:** `IN_PROGRESS`
- **Base:** `stable/kaiyuan-v2` at `523c724add978bc4bb51fc07a716c6a852c95447`。
- **Branch:** `codex/kaiyuan-b9-editorial-stellarium-v1`。
- **Scope:**
  - strict fixed `EditorialTemplate/v1` for one 80-second Chinese vertical slice;
  - claim compiler into frozen `VideoPackage/v1`;
  - claim/source cross-validation against `AstronomyEvent/v1`、`RuleAssessment/v1`、`EvidenceBundle/v1` and asterism resolution;
  - `classical_quote` only from lineage with `narration_allowed=true` and matching quote SHA-256;
  - “开口破局” only as disclosed `modern_interpretation`;
  - prohibited deterministic-fate and fear-language gate;
  - deterministic continuous shot list and editorial package;
  - capability-gated deterministic Stellarium `.ssc` generation;
  - allowlisted commands, safe object names, UTC/location/object consistency and no paths/includes/eval/arbitrary script;
  - one fixed example input, modern interpretation asset and template;
  - focused CI with retained logs and package-level consistency tests.
- **Stellarium boundary:** script generation targets the documented 26.x scripting API and uses only `core.clear`、`core.setGuiVisible`、`core.setDate`、`core.setTimeRate`、`core.setObserverLocation`、`core.selectObjectByName`、`core.wait`、`StelMovementMgr.setFlagTracking`、`StelMovementMgr.zoomTo`。No GUI execution or screenshot in this PR。
- **Acceptance:**
  - tests committed and RED observed before production modules;
  - every spoken claim has exactly one class, stable ID and valid same-package refs;
  - astronomy claims reference existing event measurements/verified mapping;
  - classical claims are omitted when lineage is blocked/missing/ambiguous;
  - quote text hash must match citable lineage content hash;
  - modern interpretation includes explicit disclosure and cannot be reclassified;
  - prohibited promises/threats fail closed;
  - shot timeline starts at 0, is continuous, ends at exactly 80,000 ms and uses only compiled claim IDs;
  - repeated package and `.ssc` generation is byte-identical;
  - `.ssc` time/location/object match the event and fixed object map;
  - missing commands or unsupported Stellarium capability is blocked;
  - no absolute path, path traversal, include/eval/shell/screenshot command;
  - focused/full exact-head workflows and independent review pass;
  - no Qdrant、ingest、corpus、candidate、media or publishing operation.
- **Start log:** `docs/development/B9_PR_D_START.md`。
- **Excluded:** Stellarium GUI execution、screenshots、SRT、FFmpeg、audio/video、publishing、full-book rule structuring。

### B9-PR-E — Atomic package, review, preview and E2E
- **Status:** `BACKLOG`

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
B9-PR-D tests-first RED
→ minimal editorial package and claim compiler
→ deterministic Stellarium script
→ focused/full regressions
→ independent review and exact-head workflows
→ squash merge and docs-only closeout
→ only then B9-PR-E
```

当前不得：

- 在 stable 或旧 closeout 分支写实现；
- 提前启动 B9-PR-E、B10、B11 或 B12；
- 修改正式 Qdrant 或 `local_kb_default`；
- 运行 Stellarium GUI、截图或生成音视频；
- 将 blocked lineage 升级为 classical quotation。
