# Chinese Star Omen Workspace 全局记忆

> 本文件是跨会话恢复的全局事实与长期边界入口。它不替代实时 GitHub、`TASKS.md`、`DECISIONS.md`、设计、计划或 `WORK_LOG.md`。每次开始或恢复开发时必须先读，并立即用远端事实修正过期内容。

## 1. 仓库与稳定基线

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Stable branch: stable/kaiyuan-v2
Last verified stable HEAD: 6f00ff79fdaebb76f27f879abccc7c5a3fcf50e6
Verified at: 2026-07-20
Forbidden release target: main
Protected legacy collection: local_kb_default
V2 collection: local_kb_kaiyuan_v2 or random ephemeral CI collection
```

恢复时必须重新读取远端 stable HEAD 和全部开放 PR，不得因为本文件记录了 SHA 就假定它仍为最新。

## 2. 当前阶段事实

### B8

```text
B8-T01: DONE
B8-T02: DONE
B8 closeout PR #29: merged
Stable closeout SHA: 6f00ff79fdaebb76f27f879abccc7c5a3fcf50e6
```

B8 已完成发布证据归档、离线复验和 hermetic 持续门禁，没有遗留实现任务。

### 当前规划工作

```text
Planning branch: codex/kaiyuan-evidence-video-pipeline-v1
Planning PR: #30
PR base: stable/kaiyuan-v2
PR type: docs-only draft planning PR
Implementation status: NOT STARTED
```

PR #30 只能完善设计、计划、测试策略、任务路线和全局记忆。不得在该分支写 B9 功能代码。规划 PR 合并后，必须从新的 remote stable HEAD 创建独立实现分支。

### 其他开放 PR

截至最后核验，远端仍存在早期开放 PR #1、#7。它们属于旧候选/`dev-test` 路线，不是 B9 稳定线实现任务。关闭前必须确认已被 stable v2 取代；在关闭前不得宣称“仓库无开放 PR”。

### 任务台账提醒

`TASKS.md` 的历史 B4/B8 顶部摘要仍需在规划 closeout/实现 Task 0 中刷新为当前稳定 HEAD 和 B9–B12 路线。该文档未刷新前，当前状态以实时 GitHub、本文件和 PR #30 设计/计划共同核验，不得直接依赖旧 header。

## 3. 已批准总体路线：方案 C

```text
B9  契约先行＋2026-07-21 垂直样片
→ B10 《唐开元占经》全书规则结构化
→ B11 基于 approved/citable 规则 gap 的执行器 2.0
→ B12 批量天象选题、通用媒体生产与发布辅助
```

### B9

冻结三个长期公共契约：

```text
AstronomyEvent/v1
RuleAssessment/v1
VideoPackage/v1
```

只完成一条可复验公开垂直样片：固定输入、星历、星官映射、古籍证据、规则评估、声明分类口播、Stellarium `.ssc`、SRT、审核记录和本地最小竖屏预览。

B9 不做全书结构化、自动配音、批量扫描、通用剪辑或自动发布。

### B10

建立 `OmenRule/v2`、candidate/rule identity、标注手册、稳定 passage inventory、development/validation/sealed holdout 黄金集、确定性和可选模型辅助候选抽取、可恢复审核队列、去重、冲突、全书覆盖率及确定性规则发布包。

B10 的成果是完整规则知识资产和正式 `engine-gap-report.json`，不是凭想象扩展完整推演器。

### B11

只根据 B10 approved/citable 规则中真实出现的频次、风险和测量需求扩展复杂事件、时序、持续、留逆、组合天体、应期和历史回测。Rejected、candidate-only 或未审核内容不得进入 B11 优先级。

### B12

在 B9 契约和 B10/B11 正式规则稳定后，才建设未来天象批量扫描、多模板媒体生产、配音、人工发布辅助和内容运营闭环。自动发布仍需独立安全决策。

## 4. B9 实施拓扑

B9 使用五个顺序实现 PR：

```text
B9-PR-A Contract registry and compatibility
→ B9-PR-B Scientific provider and asterism catalog
→ B9-PR-C RuleAssessment and evidence lineage
→ B9-PR-D Editorial package and Stellarium script
→ B9-PR-E Atomic package, review, preview and E2E
```

每个 PR 从前一 closeout 后的新 stable HEAD 开始。禁止以一个 PR 同时实现契约、星历、检索和媒体。

### B9 双轨验收

- 2026-07-21 是公开样片候选。若没有 citable 古籍规则，允许诚实产出 astronomy/history/modern-interpretation 版本，必须省略古籍占断。
- 独立 evidence-rich CI fixture 只用于验证 citable classical quote 正向路径，不是第二条公开视频，也不得冒充真实当日内容。

### B9 确定性边界

- canonical JSON、JSON Schema、registry、`.ssc`、SRT 和 manifests 必须 bit-for-bit deterministic；
- MP4 不要求跨 OS/FFmpeg 版本字节一致；媒体 hash 只绑定 exact toolchain manifest；
- 跨环境检查尺寸、时长、轨道/字幕清单和人工视觉结论。

## 5. B10 实施拓扑与完成分母

B10 适用 PR：

```text
B10-PR-A OmenRule/v2, identity and annotation
→ B10-PR-B Passage inventory and batch framework
→ B10-PR-C Golden sets and calibration pilot
→ B10-PR-D Full-book deterministic extraction
→ B10-PR-E Optional model adapter
→ B10-PR-F Review queue, dedup and conflict
→ B10-PR-G Full-book review waves and coverage
→ B10-PR-H Release, offline verification and engine gap
```

模型辅助默认 disabled，可跳过 B10-PR-E；禁用状态必须写入 manifest。

B10 只有满足以下全书分母才能 `DONE`：

1. 100% primary passages 进入 inventory；
2. 每个 passage 有 eligible/ineligible/ambiguous/needs_review 状态；
3. 每个 eligible passage 有 candidate 或 no-candidate reason；
4. 每个 candidate 进入 approved/rejected/deferred_with_reason 终态；
5. approved rules 全部通过 citable、去重/冲突和 source-change validation；
6. unresolved/ambiguous/deferred 保留在分母和报告中。

单批发布、基础设施完成或部分审核不能冒充“全书完成”。

## 6. 永久边界

- v2 release 只进入 `stable/kaiyuan-v2`，不进入 `main`。
- `apps/local-kb-unified` 是正式 KB 唯一写入者。
- `apps/star-omen` 不执行正式 ingest，不直接修改正式 Qdrant。
- `local_kb_default` 不得在 v2 开发和测试中写、删、重建或迁移。
- raw corpus、`<pb:...>`、原字形和 `&KRxxxx;` 不静默改写。
- CText 仅用于人工或定点比对，不做批量抓取或自动覆盖。
- 最终引用必须验证 source、book、locator、page、paragraph、heading、anchor 和 hash。
- pending、rejected、stale、ambiguous、candidate-only 或 unverified 内容不是正式证据。
- transport/auth/timeout/contract/collection 错误不得转换为健康空结果。
- 模型只能生成候选，不得自动批准规则、分配正式 rule ID 或形成古籍结论。
- Stellarium 是渲染器，不是现代天文学事实唯一来源。
- “开口破局”固定属于现代文化转译，不是《开元占经》原文。

## 7. 契约与变更控制

进入实现后，以下 v1 语义不得原地修改：

```text
AstronomyEvent/v1
RuleAssessment/v1
VideoPackage/v1
```

破坏性变化必须创建新版本。实现中发现的新规则类别、复杂关系或媒体需求默认进入 B10–B12 backlog。

只有以下类别可以修改当前 B9 scope：

- Critical：错误科学事实、错误古籍引用、越权写入、不可恢复产物；
- Important：契约兼容、确定性、审核门禁或安全边界被破坏。

普通增强不得扩大当前阶段。

## 8. 测试总策略

B9–B10 使用七层门禁：

```text
G0 Governance
G1 Contract
G2 Scientific
G3 Corpus/Retrieval
G4 Rule Quality
G5 Hermetic E2E
G6 Renderer
G7 Release
```

关键要求：

- 普通 PR 运行治理、契约、属性 smoke、科学黄金 smoke、检索负向黄金、规则 fixture、hermetic E2E 和 release verifier。
- Nightly 运行完整 property、科学黄金、全语料/validation、mutation 和长集成测试。
- Stellarium/FFmpeg 实际 GUI/视觉测试在本地或 self-hosted macOS 执行。
- 科学黄金值不得由待测代码或 Stellarium 自行生成。
- 普通测试不得更新黄金文件。
- sealed holdout 不用于日常调 prompt、pattern 或阈值。
- citation、claim lineage、review、source invalidation、conflict 和 release verifier 优先 mutation testing，关键模块目标不低于 80%。
- 长任务必须 checkpoint/resume、幂等、no-overwrite。

详细策略：`docs/development/B9_B10_TEST_STRATEGY.md`。

## 9. 关键文档

### 规划审查

```text
docs/development/B9_B10_PLAN_REVIEW.md
```

### B9

```text
docs/superpowers/specs/2026-07-20-kaiyuan-evidence-video-pipeline-design.md
docs/superpowers/plans/2026-07-20-kaiyuan-evidence-video-pipeline.md
```

### B10

```text
docs/superpowers/specs/2026-07-20-kaiyuan-whole-book-rule-structuring-design.md
docs/superpowers/plans/2026-07-20-kaiyuan-whole-book-rule-structuring.md
```

## 10. 每次会话强制恢复顺序

1. 读取根目录 `AGENTS.md`。
2. 读取本文件。
3. 查询远端 stable HEAD 和全部开放 PR，修正过期事实。
4. 读取 `DEVELOPMENT_MANUAL.md`。
5. 读取 `TASKS.md`，识别并修正旧 header。
6. 读取 `DECISIONS.md`。
7. 读取当前阶段设计、计划和 `B9_B10_PLAN_REVIEW.md`。
8. 读取 `WORK_LOG.md` 最新相关记录。
9. 只有当前实现任务在 `TASKS.md` 标记 `IN_PROGRESS` 后才允许写代码。

## 11. 规划 PR #30 完成条件

PR #30 只有以下条件满足后才可从 Draft 进入 review：

- B9 已收敛为契约＋单条垂直样片并拆为顺序小 PR；
- B10 有独立全书规则结构化计划、全书分母和可恢复批次；
- B11/B12 依赖边界明确但未过度设计；
- 分层测试、黄金数据、媒体确定性和模型数据治理写入仓库；
- 全局记忆加入强制阅读顺序；
- PR 仍为 docs-only，无功能代码、schema 实现、媒体文件或 Qdrant 操作；
- Governance/适用 docs-only workflows 通过；
- 自检无 TBD、TODO、范围矛盾或未归属需求。

规划 PR 合并后必须重新读取 stable HEAD，再建立 B9-PR-A 实现分支。不得直接在规划分支追加实现。

## 12. 当前下一动作

当前允许：

```text
完成 PR #30 文档自检和 review
→ 合并 PR #30
→ 从新的 stable HEAD 建立 B9-PR-A 分支
→ 刷新 TASKS.md 当前 header 并将首个实现任务标记 IN_PROGRESS
→ 才开始 TDD 实现
```

当前禁止：

```text
在 PR #30 写功能代码
启动 B10 实现
自动生成/发布视频
修改正式 Qdrant
把候选原文或现代转译升级为正式古籍结论
```