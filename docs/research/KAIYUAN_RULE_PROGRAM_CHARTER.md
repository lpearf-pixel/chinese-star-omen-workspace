# 《唐开元占经》全书规则结构化项目章程

## 1. 授权范围

B10 将既有可定位 primary passage 转换为候选、审核和正式发布规则资产。
它建立规则语料生产线，不在本阶段实现复杂天象执行、个人命运判断、
批量视频或自动发布。

本章程约束 B10-PR-A 至 B10-PR-H。任何阶段不得改写 raw corpus，不得
读写、删除、重建或迁移 `local_kb_default`。模型只能生成候选。

## 2. 全书完成分母

B10 只有在以下六项同时满足时才能标记 `DONE`：

1. `100%` primary passages 进入稳定、可复验的 inventory。
2. 每个 passage 获得 `eligible | ineligible | ambiguous | needs_review`
   eligibility 状态。
3. 每个 eligible passage 至少产生候选规则，或保存结构化
   `no_candidate_reason`。
4. 每个候选进入 `approved | rejected | deferred_with_reason` 审核终态。
5. 每个 approved rule 通过 citable evidence、source-change、
   去重/冲突和 release validation。
6. unresolved、ambiguous、deferred 和失败项继续保留在分母、backlog
   与 coverage 报告中。

基础设施完成、某一卷完成或一批规则发布均不能替代上述全书分母。
报告不得通过排除未识别或困难 passage 提高覆盖率。

## 3. 独立 PR 顺序

```text
B10-PR-A  OmenRule/v2, candidate/rule identity and annotation contract
→ B10-PR-B Passage inventory, source invalidation and resumable batches
→ B10-PR-C Golden sets, calibration pilot and threshold freeze
→ B10-PR-D Full-book deterministic extraction
→ B10-PR-E Optional model candidate adapter
→ B10-PR-F Review queue, deduplication and conflict workflow
→ B10-PR-G Full-book review waves and coverage
→ B10-PR-H Rule release, offline verification and engine-gap report
```

每个适用阶段从前一 closeout 后的新 `stable/kaiyuan-v2` 建分支，独立
测试、review、merge 和 closeout。模型辅助未启用时可跳过 PR-E，但
release manifest 必须记录 `model_extraction=disabled`。

## 4. 身份与不可变历史

- candidate identity 绑定 extractor、source passage IDs、raw spans 和
  candidate payload hash。
- 正式 `rule_id` 只能在人工批准时分配，模型不得指定。
- approved rule 的语义修改产生新 `rule_version`，不得覆盖旧版本。
- merge、split、reject、defer、adjudication 和 source change 保留全部
  candidate IDs、review history 和理由。
- raw corpus、passage source bytes 和既有发布包保持不可变；校勘与解释
  只存在于派生层。

## 5. Pilot 与阈值冻结

### 5.1 Pilot 前

Pilot 前指标只用于设计和估算，不是可在失败后移动的 release threshold。
确定性抽取器进入正式候选路径的 precision 候选目标为 `>= 0.90`。
citable evidence false-positive gate 从本章程起固定为 `0`。

### 5.2 Pilot 后

B10-PR-C 必须生成 canonical `threshold-freeze.json`，至少记录：

```text
schema_version
freeze_id
created_at
source_release_head
annotation_guide_version
development_manifest_sha256
validation_manifest_sha256
sealed_holdout_manifest_sha256
extractor_version
pattern_version
review_policy_version
formal_candidate_precision_min
formal_candidate_recall_min
category_thresholds
review_agreement_min
citable_false_positive_max
approved_by
decision_reference
```

`citable_false_positive_max` 必须为 `0`。threshold freeze 未通过前不得
启动全书抽取。

### 5.3 冻结后变更

任何 extractor、review、agreement 或 release threshold 变化必须进入
独立决策和 PR，保存：

- before/after；
- 变更原因；
- development、validation 和 sealed holdout 影响；
- false-positive 分类；
- 人工批准记录；
- 对既有 candidate、review wave 和 release 的失效范围。

不得在失败批次中临时调阈值并覆盖原结果。

## 6. 批次与恢复政策

长任务必须满足：

- batch ID 由任务类型、输入 passage/candidate 集合、source fingerprint、
  policy/tool version 和参数的 canonical hash 稳定生成；
- checkpoint 绑定 batch ID、输入 hash、已完成项、失败项、deferred 项、
  输出 hash 和单调序号；
- resume 先验证 checkpoint schema、identity、hash 和状态机；
- 相同输入重复执行幂等，不生成重复候选或重复 review decision；
- 输出由调用方指定并 no-overwrite；并发同 batch 只能有一个有效发布者；
- checkpoint mismatch、source change、损坏、并发冲突和部分失败明确
  fail-closed；
- 中断不得静默从头覆盖旧结果，困难项不得因重试或跳过而消失；
- failed/deferred 项持续进入 coverage 分母和 remaining backlog。

默认 batch 为 200 passages；B10-PR-B 可在 `100–500` 范围配置，但参数
必须进入 batch identity。

## 7. 数据集与审核治理

development、validation 和 sealed holdout 三个 split 不得混用。
sealed holdout expected labels 不参与日常 prompt、pattern 或阈值调整。
黄金集更新必须显式批准并保留 before/after。

正式规则至少经过 initial review、independent recheck，以及有分歧时的
adjudication。同一审核者复核必须记录时间隔离。审核历史 append-only，
任何字段修改必须保存修改前后、理由、审核身份和时间。

关键类别与字段的 Cohen's kappa 候选目标为 `>= 0.80`；最终门槛由
`threshold-freeze.json` 固定。未达标时优先修订标注手册并重新校准，
不得通过跳过分歧项提高指标。

## 8. 模型边界

模型适配默认 `disabled`。若后续显式启用：

- 只发送 policy allowlist 字段；
- 记录 provider、model、prompt/input hash 和原始响应治理策略；
- invalid、timeout、拒答或不一致输出不能产生正式规则；
- 模型不能 approve、分配正式 rule ID、promote、ingest 或写 Qdrant；
- 模型结果与确定性抽取结果分开评测；
- provider、model 或 prompt 变化必须重跑 validation。

禁用模型不会阻止 B10 完成。

## 9. B11 输入边界

B11 只能消费 B10-PR-H 正式发布包中的 `engine-gap-report.json`。进入
频次和优先级计算的规则必须同时为 approved、citable、未因 source
change 失效，并完成去重/冲突处理。

未审核候选、rejected、deferred、ambiguous、missing evidence 或模型
原始输出不得驱动 B11 实现。

## 10. 阶段报告

每个阶段至少记录：

- stable base、feature head、PR 和 squash SHA；
- 输入 manifest、source fingerprint 和工具/policy 版本；
- focused、regression、governance 和 exact-head CI；
- changed-file、review 和 unresolved-thread 审计；
- 已完成分母、remaining backlog、failed/deferred 项；
- 对下一阶段的 entry gate 和仍然有效的禁止边界。

所有覆盖率必须公开分母和算法。B10 最终 closeout 还必须记录人工审核
工作量、remaining deferred 风险和 B11 gap report identity。
