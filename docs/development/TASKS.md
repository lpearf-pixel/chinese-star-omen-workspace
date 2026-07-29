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
Current PR: #38
Current task: B9-PR-D
Implementation status: VERIFYING
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

- **Status:** `VERIFYING`
- **Base:** `stable/kaiyuan-v2` at `523c724add978bc4bb51fc07a716c6a852c95447`。
- **Branch:** `codex/kaiyuan-b9-editorial-stellarium-v1`。
- **PR:** #38，draft，base only `stable/kaiyuan-v2`。
- **Delivered:**
  - fixed strict `EditorialTemplate/v1` for one 80-second `zh-CN` vertical slice;
  - deterministic claim compiler into frozen `VideoPackage/v1`;
  - stricter internal `EditorialPackage/v1` with one-shot-per-claim and continuous timeline invariants;
  - astronomy/source/mapping cross-validation against `AstronomyEvent/v1`、`RuleAssessment/v1`、`EvidenceBundle/v1` and asterism resolution;
  - citable classical quotation only from the formally recommended、narration-allowed lineage with matching locator/hash/text SHA-256;
  - exact quote-asset-set validation：unauthorized、extra or blocked-lineage quote input fails explicitly rather than being silently dropped;
  - content-bound `VideoPackage/v1.package_id` derived from actual claim classes、text and source references;
  - explicit historical source type/title disclosure and fail-closed single-history limit;
  - verified identity wording and verified-membership-limited wording;
  - “开口破局” only as disclosed `modern_interpretation`;
  - NFKC/spacing/punctuation-resistant deterministic-fate、fear and coercion language gate;
  - deterministic 80,000 ms shot list and canonical UTF-8 JSON;
  - capability-gated deterministic Stellarium 26.x `.ssc`;
  - canonical setup/shot/restore command order、wait-duration binding、safe object names、reviewed observer label、UTC/location/object consistency;
  - renderer-state restoration for tracking、time rate and GUI;
  - fixed July 21 input、modern interpretation asset、template and dedicated CI with retained logs.
- **Classical-evidence boundary:** assessment and evidence bundle must agree on event、assessment、rule-set、formal recommendation、evidence ID、locator and hash；blocked/candidate/ambiguous/missing lineage never produces a classical placeholder；supplied quote IDs must exactly equal allowed lineage IDs。
- **Asterism boundary:** verified mapping must bind to the event target；verified membership says it is a reviewed member relationship rather than asserting identity；unrelated or unresolved mappings cannot rename the event。
- **Editorial boundary:** zero or one historical asset、exactly one modern asset、zero or one allowed classical lineage；every claim has exactly one shot and the timeline starts at 0 and ends at 80,000 ms；changing claim content changes package identity。
- **Stellarium boundary:** only the fixed allowlist is accepted；no path、traversal、include/eval、URL、screenshot、shell or arbitrary command；script generation does not launch Stellarium or take screenshots。
- **TDD/review evidence:**
  - initial RED: `editorial` / `stellarium` modules absent；
  - implementation RED 1: `12 failed / 12 passed`；
  - implementation RED 2: `4 failed / 20 passed`；
  - implementation RED 3: `1 failed / 23 passed`；
  - initial feature GREEN: `24 passed`；
  - review RED 1: `10 failed / 24 passed`；
  - review GREEN 1: `34 passed`；
  - review RED 2: `4 failed / 34 passed`；
  - pre-identity-review GREEN: `38 passed`；
  - identity/orphan-quote review RED: `3 failed / 38 passed`；
  - post-fix legacy-contract conflict: `1 failed / 40 passed`；
  - final focused GREEN: `41 passed in 1.55s`；
  - full downstream GREEN: `395 passed in 4.29s`。
- **Successful implementation head before final docs:** `f4520ac706a07f309d063180fd7e7d42d7aac0ad`。
- **Exact-head workflows at implementation head:**
  - Development Governance `30488226219` — success；
  - B9 Editorial Stellarium `30488226335` — success；
  - Kaiyuan Stable Core `30488226182` — success；
  - Kaiyuan Upstream Runtime `30488226257` — success。
- **Review:** 17 expected changed files before final docs；zero review threads；zero submitted reviews。
- **Decision:** `docs/development/B9_PR_D_DECISION.md`。
- **Start log:** `docs/development/B9_PR_D_START.md`。
- **Excluded:** Stellarium GUI execution、screenshots、SRT、FFmpeg、audio/video、publishing、full-book rule structuring、corpus/candidate/ingest/Qdrant/`local_kb_default` mutation。
- **Remaining:** final docs-only exact-head workflows，diff/review audit，ready transition，squash merge，then docs-only closeout before B9-PR-E。

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
B9-PR-D final docs-only exact-head workflows
→ independent diff/review-thread audit
→ mark PR #38 ready
→ squash merge to stable/kaiyuan-v2
→ docs-only closeout and stable HEAD recovery
→ only then B9-PR-E
```

当前不得：

- 在 stable 或旧 closeout 分支写实现；
- 提前启动 B9-PR-E、B10、B11 或 B12；
- 修改正式 Qdrant 或 `local_kb_default`；
- 运行 Stellarium GUI、截图或生成音视频；
- 将 blocked lineage 升级为 classical quotation；
- 静默忽略未经 lineage 授权的 quote asset。
