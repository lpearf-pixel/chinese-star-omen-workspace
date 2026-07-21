# B9–B10 实施前计划审查

## 1. 审查结论

本次审查只修改规划文档，不进入功能开发。方案 C 保持不变：

```text
B9 契约先行＋2026-07-21 垂直样片
→ B10 全书规则结构化
→ B11 由 approved rules 驱动的规则执行器 2.0
→ B12 批量媒体与发布辅助
```

原计划总体方向正确，但存在会导致实现期持续修改的风险：单个 PR 范围过大、公开样片可能没有可引用古籍规则、媒体字节确定性定义不准确、B10 全书目标与单批完成条件矛盾、人工审核无法断点恢复、模型辅助“可选”与完成条件冲突。

这些问题已写回 B9/B10 实施计划。

## 2. 已固化的 B9 优化

1. B9 拆成五个顺序实现 PR，不允许一个大型 PR 同时做契约、科学计算、检索和媒体。
2. 增加 JSON Schema registry，Python model、schema、registry 和 canonical fixture 必须一致。
3. 每个口播 claim 增加稳定 `claim_id`、唯一类型、source refs 和 review status，形成声明级 lineage。
4. 增加固定 toolchain manifest，记录 Python、Skyfield、星历、timescale、Stellarium 和 FFmpeg 版本/hash。
5. 科学黄金值必须来自独立参考源；至少一类事件执行 differential check。
6. 2026-07-21 采用双轨验收：
   - 公开包允许在无 citable 规则时诚实降为 astronomy/history 版本；
   - 独立 evidence-rich CI fixture 覆盖 classical quote 正向路径。
7. 明确结构化资产 bit-for-bit deterministic；MP4 只在相同 toolchain 下绑定 hash，不要求跨 OS/FFmpeg 版本字节一致。
8. 增加 subprocess timeout、路径限制、截图数量和结构化包大小预算。
9. B9 scope 只有 Critical/Important 缺陷可以修改；普通增强进入 B10–B12 backlog。

## 3. 已固化的 B10 优化

1. 明确全书完成分母，不能以“至少一批规则发布”冒充全书完成。
2. `candidate_id` 与 `rule_id` 分离；rule ID 只在人工批准后分配，approved rule 修改必须新版本。
3. B10 拆成基础设施、校准试点、全书抽取、审核波次和发布五阶段，共八个适用 PR。
4. 全书任务使用稳定 batch ID、checkpoint/resume、幂等和 no-overwrite。
5. pilot 使用跨卷、跨天体、跨关系词、跨复杂度分层抽样，不用连续前几卷替代代表性样本。
6. pilot 后输出 `threshold-freeze.json`；后续阈值变化必须独立决策和 before/after 报告。
7. 确定性候选正式精度目标不低于 0.90；citable evidence false positive 固定为 0。
8. 模型辅助默认 disabled，不是 B10 完成前提；启用时增加外部 provider 数据治理。
9. 增加 append-only review queue、claim/lease、超时归还、并发冲突和断点恢复。
10. 所有 candidate 必须进入 approved、rejected 或 deferred_with_reason 终态；困难项不能因跳过而消失。
11. 发布包新增 `release-diff.json` 和 `engine-gap-report.json`，B11 只消费 approved/citable 规则的 gap。

## 4. 尚未固定为常量、但已固定选择流程的项目

以下内容依赖实施环境或权威数据，当前不应凭空锁死具体值：

- 2026-07-21 公开样片的最终观测地点；
- 具体星历文件逻辑名和版本；
- 独立科学黄金来源及其许可/引用方式；
- 本地 macOS 的 Stellarium/FFmpeg 实际版本和能力；
- B10 审核者名单、可用工时和最终 wave 容量；
- 模型辅助是否启用及 provider。

它们均有 preflight、manifest、审核或决策门禁。缺少这些事实时任务保持 BLOCKED/insufficient_data，不允许猜测。

## 5. 防止后续持续修改的规则

- 规划 PR #30 不承载实现。
- B9/B10 每个实现 PR 只承担一个可独立 review 的交付物。
- v1/v2 公共契约进入实现后只增版本，不原地重解释。
- 黄金更新使用独立 PR 和显式批准命令。
- 新功能默认进入 backlog，禁止“顺便实现”。
- 每个 PR 开始前核验 stable HEAD、开放 PR 和前置 closeout。
- 每个 PR 完成时记录 exact head、测试、fixture/toolchain、review、workflow run 和 squash SHA。

## 6. 当前状态

```text
Implementation: NOT STARTED
Planning PR: #30
Planning branch: codex/kaiyuan-evidence-video-pipeline-v1
Stable base used by PR: 6f00ff79fdaebb76f27f879abccc7c5a3fcf50e6
```

远端事实必须在下一次会话重新核验。