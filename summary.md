# Chinese Star Omen Workspace — 项目交接总结

**快照日期：** 2026-09-03

**仓库：** `lpearf-pixel/chinese-star-omen-workspace`

**稳定发布线：** `stable/kaiyuan-v2`

**禁止目标：** `main`

**受保护 collection：** `local_kb_default`

> 本文件用于新 Work 快速理解项目，不替代实时 GitHub。开始工作必须重新
> 核验 stable HEAD、开放 PR、分支 HEAD、工作区和最新任务台账。

## 1. 最近实时核验状态

2026-09-03 重新读取 GitHub 后确认：

- `stable/kaiyuan-v2`：`99c0a85c1f944add8d013aedbae830fe022b7c3b`。
- VFL 功能分支 `codex/kaiyuan-evidence-feedback-loop-skeleton-v1` 已通过
  非强制新分支推送包含已审查 closeout
  `f36b146ddb08809b6b23a8db5e5fc94393165a21`，tree
  `fe4babc7c34328a4b18f22bbea998882ae38b2dc`；随后交付状态校准检查点
  `857a7a02c26d0cdf6d6d484345b4ded577ec232c`，tree
  `7f9f7d1c7eb2c363b205c2242cd2445992ddb6e9`，也已非强制推送并读回一致。
- VFL-T02 stacked 分支
  `codex/kaiyuan-feedback-loop-readonly-adapters-v1` 已交付 Task 1–5 实现
  `4d902efef46a122e9a19128cba4c7d75eee67b14`，tree
  `7bac6c9359d6c503307851d8ea55d3eb86142b41`；公开 fetch 与本地 tree
  回读一致。S1 当前为 `VERIFYING`；完整本地门禁与 fresh
  whole-branch review 仍未完成，尚未宣称 `DONE`。
- 开放 PR 只有 #54；它仍为 Draft、未合并。
- PR #54：B10 calibration safety，仍被两名不同真人 Reviewer A/B 门禁
  阻塞；不得启动依赖 threshold freeze 的后续正式阶段。
- PR #64：Core14 第二轮证据与 11+3 临时研究分层已于 2026-08-14
  合并；stable 合并提交为
  `99c0a85c1f944add8d013aedbae830fe022b7c3b`。Reviewer B 仍未完成，
  不能把临时可用性或 PR 合并当作正式双真人批准。
- PR #65：ASTRO-R01 批准的 Phase 1–5 已于 2026-08-13 squash merge，
  stable 合并提交为 `c9d490392233b7432f5a0136dcd213613abe05a7`。

PR #65 的最终远端 head 为
`c76a229ed4dc00217b973f2407c0adbb95624601`；合并前验证绑定树
`ad9dac014ae0e62a93d471ff0d467d047f073449`。该历史只证明 ASTRO-R01
交付，不能替代后续任务的实时 ref 核验。

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

### VFL-T01

VFL-T01 的本地 S0 implementation/review scope 当前为 `DONE`。Tasks 1–5 已实现用户此前批准的
“先搭完整系统骨架、再逐模块优化”方向：把既有外部媒体审计、调用方提供的
只读本地证据探针、确定性比较、不可自动应用的改进候选、B9 视频生产请求、
人工发布交接和可选结果反馈连接为一个离线控制平面。

S0 只运行祖山觀 episode 22 金样本，不抓取直播数据、不重建 transcript/OCR，
不训练模型、不改语料/规则/Qdrant、不渲染或上传视频，也不解锁 B12。所有
改进和学习输出都固定为 proposal，必须在所属模块的新任务中独立批准。

Tasks 1–4 分别冻结严格生命周期契约、实现防御性比较、生成确定性非应用提案/
B9 请求，并复用 B9 原子发布原语完成语义闭包校验。Task 5 增加真实 episode 22
fixture 与离线 CLI；其后 `b190614` 修复 shell 路径字节边界，`a951680` 再阻止
GNU Make function 展开和内部 alias 覆盖。`59af182` 的首次 whole-branch review
随后发现恰好两个 Important（`0 Critical / 0 Minor`）：FR-01 允许非权威 modern/
retrieval evidence 产生决定性结果，FR-02 允许 outcome/run metric ID 冲突。

`21e6904` 在 contract owner 内修复两项不变量，且只改一份 contract production
文件和三份针对性测试。相同 final reviewer 以 exhaustive/adversarial matrices
完成 scoped re-review，结论为两项修复均 `APPROVED`、remaining findings `0`。
当前实现代码 head/tree 为
`21e69048b7277023458ee5217acec85d259eebb8` /
`c869c1f3f81a5cdedf92ec026054b22e8e9bb958`。

当前本地验证为 focused `58 passed`、feedback-loop `86 passed`、related
`112 passed`、完整 downstream `759 passed`、治理 unit `21 passed`，compileall
与 development governance 通过。两次 fresh CLI 运行产生同一八成员 run
`feedback-run:vfl:e2fb1a2d98be3ea09b2c885f68832530741772afc588a40c9005c3761dcef6e0`；
manifest SHA-256 为
`00b96fd7dec1ad90da94af29bea90860b85b6712ad336c7bb7d345e412a8ebc4`。
占用输出重跑非零退出且整树不变、无 staging 残留。Renewed whole-branch review
批准 exact candidate `33657fae698970a9d820870ab180c3712e9f295a` / tree
`8bcce81842e6130d0328b525168f8b46c9955d7e`，覆盖 `15 commits / 25 paths /
15 code files`，结论为 `0 Critical / 0 Important / 0 Minor`；FR-01/FR-02
保留为已关闭 findings。

2026-08-30 本地 closeout 时 Runner 为 `NOT RUN`，feature branch 尚未 push
且没有 PR；这是当时的历史事实。2026-08-31 随后的远端交付只把已审查的
exact closeout `f36b146` 非强制推送到同名功能分支。当前仍无 VFL PR、merge、
render、upload 或 publication；stable 与 PR #54 未变，Runner 仍为 `NOT RUN`。
该远端分支交付不扩大本地 S0 的 `DONE` 范围；任何后续 VFL stage 仍须独立授权。

### VFL-T02

VFL-T02 已在独立 stacked 分支完成 Task 1–5 实现交付，并进入
`VERIFYING`。批准的 Solution A 只消费既有 episode 22
审计、显式两查询计划和 caller-supplied local-source snapshot，通过字面
loopback、proxy-free、redirect-free 的现有两阶段 KB 客户端检索，并用同一
snapshot bytes 重新完成 citable passage 验证。它不抓取平台、不调用模型、
不改 corpus/Qdrant/rule，也不访问 `local_kb_default`。

部署中的 `/v1/retrieve` 没有 corpus version，且 official hit 只有截断
`snippet` 而不是 resolver anchor。S1 不伪造这两个字段：它通过同一 pinned
transport 在调用前后校验 `/v1/meta`：完整 meta session hash 只用于内存漂移
检测，持久 identity 只绑定排除 `meta_status` 与全部 `run_stats` 的 semantic
provenance hash，因此 latency 不会改变 probe/run identity；
`snippet` 永不作 anchor，只有 raw offsets 唯一匹配 caller snapshot passage 且
locator/page/paragraph/heading/hash 全部一致时，才从 frozen bytes 在内存中还原。

S1 输出不具有语义判定权：所有成功 probes 固定 `unresolved`，所有 reference
固定 `citable_passage/context_only`。只有完整批次和 snapshot postflight 成功
后才调用不变的 S0 atomic package builder；任何 typed failure 都不得留下部分
probe、package 或 staging 输出。

仓库内 episode 22 query plan 明确是 `hermetic_test`/ephemeral fixture，public
CLI 会在凭据或网络前拒绝它。真实 smoke 只接受另行审核、与当前 meta 和 caller
snapshot 精确一致的 `reviewed_live` plan；缺少任一前提均记录 `BLOCKED`。

书面设计已获用户批准，两个独立规格审查均为
`0 Critical / 0 Important`。六任务 TDD 计划已冻结：strict local inputs、
source snapshot/byte-loader seams、safe transport/pre-fallback validation、
citable projection/complete batch、episode 22 CLI/E2E、完整验证/独立审查/
治理收口。每项任务完成后独立提交、非强制推送并远端 tree 回读。

真实 local-KB smoke 只有在匹配 snapshot 与 literal-loopback service 同时可用
时运行；缺失则准确记为 `BLOCKED`，不冒充通过。该环境证据不妨碍 hermetic
S1 结束，但继续阻止 S2 使用真实 S1 输出。B10 Reviewer B 仍放在正式规则路径
末端，由不同真人独立完成；它不阻塞 VFL-T02，也不能被 S1 审查替代。

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
- Runner：`NOT RUN`；PR #65 已按任务级本地优先政策合入 stable。

审查修复包括：逐条锁定 23 个 episode/work/type/time/URL/description-hash
tuple，以及把 WMO evidence_ref_id/URL/SHA 与 canonical snapshot 交叉绑定。

## 7. 当前不可做事项

- 不修改、合并或重定向到 `main`。
- 不直接 push `stable/kaiyuan-v2`。
- 不写/删/重建 `local_kb_default`，不由下游执行 official ingest。
- 不静默改原始古籍，不用模型代替 Reviewer A/B。
- 不把外部视频或现代气象材料升级为古典证据/规则权威。
- 不改 PR #54 来完成 VFL-T01、ASTRO-R01 或文档交接。
- 不自动启动 B10-PR-D、B11、B12 或 ASTRO-R01 Phase 6；VFL-T01 仅是
  已单独授权的离线接口骨架，不构成这些阶段的启动或发布。
- 不自动应用 VFL 候选/提案，不自动渲染、上传或发布。
- VFL-T02 不访问 `local_kb_default`，不把检索命中解释成语义支持或反驳，
  不绕过 caller snapshot 或 literal-loopback 边界。
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
