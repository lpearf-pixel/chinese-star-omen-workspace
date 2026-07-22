# Chinese Star Omen Workspace 全局记忆

> 本文件是跨会话恢复的全局事实与长期边界入口。它不替代实时 GitHub、`TASKS.md`、`DECISIONS.md`、设计、计划或工作日志。每次开始或恢复开发时必须先读，并立即用远端事实修正过期内容。

## 1. 仓库与稳定基线

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Stable branch: stable/kaiyuan-v2
Last verified stable HEAD: 017601e74f32f50fea9faeb663b72eb8cfe3b93c
Verified at: 2026-07-22
Planning PR #30: merged
Planning PR final head: d31a69f89aabba2b360d31b7af2b7ac6b88fd30d
Planning squash merge: 017601e74f32f50fea9faeb663b72eb8cfe3b93c
Implementation status: NOT STARTED
Forbidden release target: main
Protected legacy collection: local_kb_default
V2 collection: local_kb_kaiyuan_v2 or random ephemeral CI collection
```

恢复时必须重新读取远端 stable HEAD 和全部开放 PR。不得因为本文件记录了 SHA 就假定它仍为最新。

## 2. 当前阶段事实

### 已完成

```text
B4: DONE
B5: DONE
B6: DONE
B7: DONE
B8-T01: DONE
B8-T02: DONE
B8 closeout PR #29: merged
B9/B10 planning PR #30: merged
```

B8 已完成发布证据归档、离线复验和 hermetic 持续门禁。PR #30 已完成方案 C、B9/B10 计划硬化、测试策略、活跃任务台账和全局记忆建设。

### 当前 closeout

```text
Closeout branch: codex/kaiyuan-b9-b10-plan-closeout
Closeout type: docs-only state update
Implementation status: NOT STARTED
```

Closeout 只记录 PR #30 的 exact-head workflows、合并 SHA、稳定 HEAD 和下一阶段边界。不得在 closeout 分支写功能代码。

### 其他开放 PR

截至最后核验，远端仍存在早期开放 PR #1、#7。它们属于旧候选/`dev-test` 路线，不是 B9 稳定线实现任务。关闭前必须确认已被 stable v2 取代；在关闭前不得宣称仓库无开放 PR。

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

单批发布、基础设施完成或部分审核不能冒充全书完成。

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

```text
docs/development/B9_B10_PLAN_REVIEW.md
docs/development/B9_B10_TEST_STRATEGY.md
docs/superpowers/specs/2026-07-20-kaiyuan-evidence-video-pipeline-design.md
docs/superpowers/plans/2026-07-20-kaiyuan-evidence-video-pipeline.md
docs/superpowers/specs/2026-07-20-kaiyuan-whole-book-rule-structuring-design.md
docs/superpowers/plans/2026-07-20-kaiyuan-whole-book-rule-structuring.md
```

## 10. 每次会话强制恢复顺序

1. 读取根目录 `AGENTS.md`。
2. 读取本文件。
3. 查询远端 stable HEAD 和全部开放 PR，修正过期事实。
4. 读取 `DEVELOPMENT_MANUAL.md`。
5. 读取 `TASKS.md`。
6. 读取 `DECISIONS.md`。
7. 读取当前阶段设计、计划和 `B9_B10_PLAN_REVIEW.md`。
8. 读取 `WORK_LOG.md` 最新相关记录。
9. 只有当前实现任务在 `TASKS.md` 标记 `IN_PROGRESS` 后才允许写代码。

## 11. 当前下一动作

当前只允许完成规划 closeout：

```text
核验 closeout exact-head workflows
→ review/merge closeout PR
→ 重新读取 stable HEAD 与开放 PR
→ 保持 B9-PR-A 为 BACKLOG
```

用户此前要求“先计划，不要开发”。因此 closeout 后不得自动创建 B9 实现分支、不得把 B9-PR-A 标为 `IN_PROGRESS`，直到用户明确授权进入开发。

当前禁止：

```text
在规划或 closeout 分支写功能代码
启动 B9/B10/B11/B12 实现
自动生成或发布视频
修改正式 Qdrant
把候选原文或现代转译升级为正式古籍结论
```
