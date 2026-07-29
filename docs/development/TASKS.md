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
Last verified stable HEAD: 8bc8d0c8f91f78e4a4faceb22a037b9c526596c0
Current feature branch: codex/kaiyuan-b9-scientific-provider-v1
Current PR: #34
Current task: B9-PR-B
Implementation status: VERIFYING
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
- **Final feature head:** `8bc3e4ae97780cd0f9f6f9c935508fd374684c4e`。
- **Exact-head workflows:** Governance `29889316084`、Stable Core `29889316073`、Upstream Runtime `29889316046` 均 success。
- **Evidence:** `docs/development/B9_PR_A_CLOSEOUT.md`。

### B9-PR-B — Scientific provider and asterism catalog

- **Status:** `VERIFYING`
- **Base:** `stable/kaiyuan-v2` at `8bc8d0c8f91f78e4a4faceb22a037b9c526596c0`。
- **Branch:** `codex/kaiyuan-b9-scientific-provider-v1`。
- **PR:** #34，draft，base only `stable/kaiyuan-v2`。
- **Delivered:**
  - versioned UTC/TT/TDB、coordinate-frame、observer and refraction conventions;
  - explicit local `.bsp` boundary with size/SHA-256 and file-identity revalidation;
  - offline Skyfield 1.51 provider using pinned `skyfield-data==7.0.0`;
  - deterministic body/fixed-star coordinates、moon phase、phase transitions、alt/az and angular separation;
  - path-free toolchain provenance;
  - versioned Chinese asterism catalog with exact ID/alias lookup and no nearest-star fallback;
  - canonical source snapshots and fixture manifests;
  - source-backed `HIP 65474 / Spica = 角宿一` identity;
  - deterministic `verified_identity|verified_membership|region_only|ambiguous|unresolved` narration boundaries;
  - dedicated B9 Scientific Provider workflow with retained logs.
- **Scientific source hashes:**
  - Stellarium canonical snapshot SHA-256 `d036a7f37e3c27ca1197d93739d922808e2a0d60e57b96b7692e7d60ca711229`；
  - Stellarium upstream Git blob SHA-1 `fe8761576dc6c5cd4a65e3551a81ead6122c895f`；
  - SIMBAD canonical snapshot SHA-256 `ecaa14864c3e94648d61a28929ef7e5d729b51d4c387ff2c57b40caf2d9d533d`。
- **User-side isolated validation:** Python 3.12.8、Skyfield 1.51、skyfield-data 7.0.0；`de421.bsp` 16,788,480 bytes，SHA-256 `a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc`。
- **TDD/review evidence:**
  - initial missing-module RED;
  - strict enum/alias review RED;
  - review boundary RED `18 failed / 22 passed`;
  - user-side stale-source-hash RED `15 failed / 304 passed`;
  - corrected focused exact-head gate `40 passed in 1.66s`;
  - corrected full downstream exact-head regression `319 passed in 3.75s`。
- **Successful evidence head:** `08f1f860637003e07ec0cb906ff85a47833afee4`。
- **Exact-head workflows at evidence head:**
  - Development Governance `30476222345` — success；
  - B9 Scientific Provider `30476222362` — success；
  - Kaiyuan Stable Core `30476222775` — success；
  - Kaiyuan Upstream Runtime `30476222618` — success。
- **Review:** zero review threads and zero submitted reviews at evidence head。
- **Decision:** `docs/development/B9_PR_B_DECISION.md`。
- **Start log:** `docs/development/B9_PR_B_START.md`。
- **Excluded:** KB retrieval、RuleAssessment adapter、classical evidence、omen judgment、editorial generation、Stellarium execution、FFmpeg/media、publishing、corpus/candidate/ingest/Qdrant and `local_kb_default` operations。
- **Remaining:** final docs-only exact-head workflows，diff/review audit，ready transition，squash merge，then docs-only closeout before B9-PR-C。

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

## B12 — 批量媒体与发布辅助
- **Status:** `BACKLOG`
- **Boundary:** 自动发布需要独立安全决策。

## 当前执行顺序

```text
B9-PR-B final docs-only exact-head workflows
→ independent diff/review-thread audit
→ mark PR #34 ready
→ squash merge to stable/kaiyuan-v2
→ docs-only closeout and stable HEAD recovery
→ only then B9-PR-C
```

当前不得：

- 在 stable 或旧 closeout 分支写实现；
- 提前启动 B9-PR-C、B10、B11 或 B12；
- 修改正式 Qdrant 或 `local_kb_default`；
- 接入检索、规则判断或媒体；
- 生成或发布视频；
- 将低置信星官映射升级为正式星名结论。
