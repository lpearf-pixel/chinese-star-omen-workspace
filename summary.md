# Chinese Star Omen Workspace — 项目交接总结

**快照日期：** 2026-08-13

**仓库：** `lpearf-pixel/chinese-star-omen-workspace`

**稳定发布线：** `stable/kaiyuan-v2`

**禁止目标：** `main`

**受保护 collection：** `local_kb_default`

> 本文件用于新 Work 快速理解项目，不替代实时 GitHub。开始工作必须重新
> 核验 stable HEAD、开放 PR、分支 HEAD、工作区和最新任务台账。

## 1. 最近实时核验状态

2026-08-13 读取 GitHub 后确认：

- `stable/kaiyuan-v2`：`c2e8fcabb04354fd14d0c72b3b6020a47e63a583`。
- 开放 PR 只有 #54、#64、#65，三者均为 Draft、未合并。
- PR #54：B10 calibration safety，仍被两名不同真人 Reviewer A/B 门禁
  阻塞；不得启动依赖 threshold freeze 的后续正式阶段。
- PR #64：Core14 第二轮证据与 11+3 临时研究分层，保持独立 Draft；
  Reviewer B 尚未开始，不能把临时可用性当作正式人工批准。
- PR #65：ASTRO-R01，base 为 `stable/kaiyuan-v2`，已完成批准的 Phase
  1–5，保持 Draft、未合并、Runner `NOT RUN`。

PR #65 在本次交接文档任务开始前的远端头为
`4cb97a16a67102068b5dc7302758cfd2892a23a0`，树为
`e5aee521e1e69d02a0ac1a81bfd8eb8fe3f0d204`。本文件提交后该 HEAD 会变化，
因此新 Work 必须读取 PR 实时 head，而不能继续使用这个父级检查点。

本交接资料的内容检查点已发布为远端提交
`2774a727e4fcd87804fbd3f441ac1fff34762b1a`，树
`d3a7df3f071dc2553472adcc4d386eedad20e3fd`。后续状态收尾提交会继续改变
PR head，但 `agent.md`/`summary.md` 的该内容树已经过治理和结构检查。

## 2. 项目架构

```text
apps/local-kb-unified  官方 KB、Qdrant ingest、检索 API、candidate promotion
apps/star-omen         下游只读检索、候选、规则、天文、星官与视频研究
packages/kb-contracts  上下游共享契约和 manifest
packages/kb-text-core  原文定位、offset、anchor、hash、passage 的唯一语义
corpus/                不可静默改写的《开元占经》原始语料与审计资料
docs/development/      跨会话状态、任务、决策、工作日志
```

正式 ingest 只能由 `apps/local-kb-unified` 执行。`apps/star-omen` 可以产生
candidate artifact，但不得直接写 Qdrant 或把候选提升为 official evidence。

## 3. 已完成主线

### B4–B8

已完成检索、证据、发布观测/归档等基础阶段。详细历史已移入
`docs/development/TASKS_B4_B8_ARCHIVE.md`，不要仅凭旧聊天恢复分支。

### B9

B9 总体 `DONE`。已经完成：

- `AstronomyEvent/v1`、`RuleAssessment/v1`、`VideoPackage/v1` 公共契约；
- source-bound 科学/星官模型、规则 lineage、编辑/package/review/preview；
- 三层 G6 门禁：机器硬检查 → hash-bound AI 视觉检查 → 三项真人体验确认；
- 真实 macOS 证据 run `20260730T121805Z` 的修正归档已接受。

接受的修正归档 SHA-256：
`8a4af09210961fada5cb6e8ac1a3344d4055307bb7d8c48920c90f71c4020214`。
早期错误归档继续保持 rejected，不得重新解释为通过。

### B10

B10 整体仍 `IN_PROGRESS`：

- T00、PR-A、PR-B 与 R01–R07 已完成各自批准范围；
- PR #54 / B10-PR-C 仍因两名独立真人审核缺失而 `BLOCKED`；
- Reviewer A 的修订资料可返回，Reviewer B 必须由另一名真人独立完成；
- C03/C24/C33 属 `isolated_evidence_supplement`，只能定向补证/校勘；
- 11 条 `provisional_usable_pending_reviewer_b` 只允许明示待 B 确认的内部
  检索、多文映射和研究，不能进入正式规则、official ingest 或阈值冻结；
- B10-PR-D/E/F 与 B11/B12 未获当前任务授权。

## 4. ASTRO-R01：二十八宿与外部媒体审计

批准设计：
`docs/superpowers/specs/2026-08-12-kaiyuan-28-mansions-external-audit-design.md`。

Phase 1–5 已完成：

1. 毕宿金样本、星官 catalog 和纯月宿区域 evaluator。
2. 28 个 defining stars 与闭合月宿区域 cycle。
3. 全二十八宿成员/连线来源绑定和 completeness 状态。
4. 28 张导航卡的科学状态投影与繁简别名校验。
5. 外部媒体契约、祖山觀 23 条清单和 9 份候选审计。

冻结科学投影：

- 28 mansion cards；
- 157 个基础成员；
- 5 个 related endpoints；
- 3 个 ambiguous members；
- 57 条 line segments；
- completeness 为 `26 complete / 1 complete_gold_sample / 1 ambiguous`。

关键语义：传统星官成员、月宿区域和最近成员距离是三个不同问题；
`in_mansion_region` 不能自动推出 `临/犯/入/守/留`。翼宿三项 status-2
身份继续 ambiguous；附耳、钺、长沙、左辖、右辖是 related object，不是额外
月宿成员。

Phase 6（其他创作者的有界扩展）未登记为当前活动任务。开始前必须新建设计/
计划和任务，不得顺手扩展来源范围。

## 5. 祖山觀真实来源集

用户提供的两个抖音短链解析为同一创作者与合集：

- 创作者：`祖山觀（無用之人）🌓`
- 抖音号：`35031221639`
- UID：`2129076815950670`
- 合集：`7664842437629921326`，`8月必看天象值得期待`
- 批准 denominator：episode 1–23
- 捕获时合集 live total：40；24–40 只记录为 source drift

来源集包含 23 个唯一 work：17 个 note、6 个 video。每条锁定 episode、
work ID、media kind、canonical URL、UTC 发布时间和 captured-description
SHA-256。没有导入 transcript、OCR、图片内容或无法定位的古典引文。

9 个 priority episodes：`1,2,3,7,9,11,16,20,22`。

Episode 22 / work `7669807398794598565` 是完整金样本：

- `毕宿天象的烈风` → `historical_correspondence` / `source_missing`
- `能不能对应海上风暴？` → `modern_inference` / `ambiguous`
- WMO tropical-cyclone 定义 → `modern_authority` / `context_only`
- overall → `ambiguous`

WMO 快照的 reference ID、URL 与 SHA-256 已交叉绑定。它只说明现代热带
气旋定义，不能证明“烈风”等同海上风暴、台风或热带气旋。

资产位置：

- `apps/star-omen/data/video_pipeline/external_media/祖山觀/source-set-v1.json`
- `apps/star-omen/data/video_pipeline/external_media/祖山觀/audits/`
- `apps/star-omen/data/video_pipeline/external_media/祖山觀/evidence/`
- `tests/fixtures/external-media/祖山觀/manifest.json`

## 6. 最近 ASTRO-R01 验证证据

最终实现/closeout 父级树通过：

- governance unit：21 passed；
- development governance：91 changed files / 32 code files；
- navigation/asterism/astronomy/contracts/external-media：179 passed；
- canonical source/fixture：13 passed；
- full downstream：673 passed；
- compileall、diff、stable ancestry、clean worktree、forbidden-path scan：通过；
- independent review：无 Critical/asset mismatch；两项 Important 已修复；
- Runner：`NOT RUN`；PR #65 保持 Draft、unmerged。

审查修复包括：逐条锁定 23 个 episode/work/type/time/URL/description-hash
tuple，以及把 WMO evidence_ref_id/URL/SHA 与 canonical snapshot 交叉绑定。

## 7. 当前不可做事项

- 不修改、合并或重定向到 `main`。
- 不直接 push `stable/kaiyuan-v2`。
- 不写/删/重建 `local_kb_default`，不由下游执行 official ingest。
- 不静默改原始古籍，不用模型代替 Reviewer A/B。
- 不把外部视频或现代气象材料升级为古典证据/规则权威。
- 不改 PR #54/#64 来完成 ASTRO-R01 或文档交接。
- 不自动启动 B10-PR-D、B11、B12 或 ASTRO-R01 Phase 6。
- 不为普通 Draft/文档提交运行 Runner；只有 exact major-version stable
  merge candidate 才运行一次统一 Runner。

## 8. 新 Work 的推荐接管步骤

```text
1. 读 AGENTS.md → agent.md → summary.md → PROJECT_MEMORY.md
2. 实时核验 stable HEAD、全部开放 PR、当前 branch/HEAD/tree/dirty state
3. 读 DEVELOPMENT_MANUAL、TASKS、DECISIONS、相关设计/计划、最新 WORK_LOG
4. 修正过期事实并登记新任务；没有 IN_PROGRESS 任务不得实现
5. 明确 scope/forbidden/done/verify/delivery
6. TDD 实现，focused → related regression → 适用完整门禁
7. 独立审查，修复 Critical/Important
8. WORK_LOG 记录 exact-head 证据，非强制发布 Draft，读回远端状态
```

用户偏好常规问题无需反复确认：选择推荐的可逆方案，持续诊断、修复、测试
到计划完成；只有权限、付费、不可逆动作、保护分支或重大方向变化才暂停。
