# Chinese Star Omen Workspace 全局记忆

> 本文件是跨会话恢复的全局事实与长期边界入口。它不替代 `TASKS.md`、`DECISIONS.md`、设计、计划或 `WORK_LOG.md`，但每次开始或恢复开发时必须先读，并用远端仓库事实更新过期内容。

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

恢复时必须重新读取远端 `stable/kaiyuan-v2`，不得因为本文件记录了 SHA 就假定它仍是最新值。

## 2. 当前阶段事实

### B8

```text
B8-T01: DONE
B8-T02: DONE
B8 closeout PR #29: merged
Stable closeout SHA: 6f00ff79fdaebb76f27f879abccc7c5a3fcf50e6
```

B8 已完成发布证据归档、离线复验和 hermetic 持续门禁。B8 没有遗留实现任务。

### 当前规划工作

```text
Planning branch: codex/kaiyuan-evidence-video-pipeline-v1
Planning PR: #30
PR base: stable/kaiyuan-v2
PR type: docs-only draft planning PR
Implementation status: NOT STARTED
```

PR #30 只能完善设计、计划、测试策略、任务路线和全局记忆。不得在该分支继续写 B9 功能代码。规划 PR 合并后，必须从新的 stable HEAD 创建独立实现分支。

### 其他开放 PR

截至 2026-07-20，远端仍存在早期开放 PR #1、#7。它们属于旧候选/`dev-test` 路线，不是 B9 稳定线实现任务。下一次仓库治理时应核验是否已被 stable v2 完全取代，并在有充分事实后标记 superseded/关闭；在关闭前不得宣称“仓库无开放 PR”。

## 3. 已批准总体路线：方案 C

```text
B9  契约先行＋2026-07-21 垂直样片
→ B10 《唐开元占经》全书规则结构化
→ B11 基于 B10 真实需求的规则执行器 2.0
→ B12 批量天象选题、通用媒体生产与发布辅助
```

### B9

冻结三个长期公共契约：

```text
AstronomyEvent/v1
RuleAssessment/v1
VideoPackage/v1
```

只完成一条可复验垂直样片：固定输入、星历、星官映射、古籍证据、规则评估、声明分类口播、Stellarium `.ssc`、SRT、审核记录和本地最小竖屏预览。

B9 不做全书结构化、自动配音、批量扫描、通用剪辑或自动发布。

### B10

建立 `OmenRule/v2`、标注手册、稳定 passage inventory、development/validation/sealed holdout 黄金集、确定性和可选模型辅助候选抽取、双阶段人工审核、去重、冲突、覆盖率统计及确定性规则发布包。

B10 的成果是规则知识资产和 B11 需求清单，不是完整自动推演。

### B11

只根据 B10 approved 规则中真实出现的需求扩展：复杂事件、时序、持续、留逆、组合天体、应期、历史回测等。不得在 B9/B10 阶段凭想象提前实现完整规则引擎。

### B12

在 B9 契约和 B10/B11 正式规则稳定后，才建设未来天象批量扫描、多模板媒体生产、配音、人工发布辅助和内容运营闭环。自动发布仍需独立安全决策。

## 4. 永久边界

- 《开元占经》v2 release 只进入 `stable/kaiyuan-v2`，不进入 `main`。
- `apps/local-kb-unified` 是正式 KB 唯一写入者。
- `apps/star-omen` 不执行正式 ingest，不直接修改正式 Qdrant。
- `local_kb_default` 不得在 v2 开发和测试中写、删、重建或迁移。
- raw corpus、`<pb:...>`、原字形和 `&KRxxxx;` 不静默改写。
- CText 仅用于人工或定点比对，不做批量抓取或自动覆盖。
- 最终引用必须验证 source、book、locator、page、paragraph、heading、anchor 和 hash。
- pending、rejected、stale、ambiguous、candidate-only 或 unverified 内容不是正式证据。
- transport/auth/timeout/contract/collection 错误不得转换为健康空结果。
- 模型只能生成候选，不得自动批准规则或古籍结论。
- Stellarium 是渲染器，不是现代天文学事实唯一来源。
- “开口破局”固定属于现代文化转译，不是《开元占经》原文。

## 5. B9 冻结边界

B9 实现开始后，以下 v1 语义不得原地修改：

```text
AstronomyEvent/v1
RuleAssessment/v1
VideoPackage/v1
```

破坏性变化必须创建新版本。实现中发现的新规则类别、复杂关系或媒体需求默认进入 B10–B12 backlog。只有 Critical 或 Important 缺陷允许修改 B9 scope。

B9 的 `preview.mp4` 可以无配音；`final.mp4`、TTS、批量选题和抖音上传不属于 B9 完成条件。

## 6. 测试总策略

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
- 科学黄金值不得由待测代码自行生成。
- 普通测试不得更新黄金文件。
- sealed holdout 不用于日常调 prompt、pattern 或阈值。
- citation、claim classification、review、source invalidation、conflict 和 release verifier 优先做 mutation testing，关键模块目标不低于 80%。

详细策略：`docs/development/B9_B10_TEST_STRATEGY.md`。

## 7. 关键设计与计划

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

## 8. 每次会话强制恢复顺序

1. 读取根目录 `AGENTS.md`。
2. 读取本文件 `docs/development/PROJECT_MEMORY.md`。
3. 查询远端 `stable/kaiyuan-v2` HEAD 和全部开放 PR，修正本文件中的过期事实。
4. 读取 `docs/development/DEVELOPMENT_MANUAL.md`。
5. 读取 `docs/development/TASKS.md`。
6. 读取 `docs/development/DECISIONS.md`。
7. 读取当前阶段设计和实施计划。
8. 读取 `docs/development/WORK_LOG.md` 最新相关记录。
9. 确认当前任务已经在 `TASKS.md` 标记为 `IN_PROGRESS`，才允许写代码。

## 9. 规划 PR #30 完成条件

PR #30 只有在以下条件满足后才可以从 Draft 进入 review：

- B9 已收敛为契约＋单条垂直样片；
- B10 有独立全书规则结构化设计与计划；
- B11/B12 的依赖边界明确但未过度设计；
- 分层测试和黄金数据政策写入仓库；
- 本全局记忆加入强制阅读顺序；
- PR 仍为 docs-only，无功能代码、schema 实现、媒体文件或 Qdrant 操作；
- Governance 门禁通过；
- 自检无 TBD、TODO、相互矛盾或未归属需求。

规划 PR 合并后必须重新读取 stable HEAD，再建立 B9 实现分支。不得直接在规划分支追加实现。

## 10. 当前下一动作

当前允许的下一动作仅限：

```text
完成 PR #30 文档自检和 governance
→ review/merge PR #30
→ 从新的 stable HEAD 建立 B9 实现分支
→ 在 TASKS.md 将 B9 第一个实现任务标记 IN_PROGRESS
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
