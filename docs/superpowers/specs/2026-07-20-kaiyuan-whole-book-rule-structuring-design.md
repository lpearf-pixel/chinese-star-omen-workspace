# B10 《唐开元占经》全书规则结构化设计

## 1. 目标

B10 将已经完整保存并可定位检索的《唐开元占经》原文，转换为可审核、可版本化、可回链、可统计覆盖率的规则知识资产。B10 的首要目标不是提高自动推演能力，而是建立可靠的规则语料生产线和质量基线，为 B11 规则执行器 2.0 提供真实需求。

B10 完成后应能够回答：

- 全书有多少可识别占候 passage；
- 已生成多少候选规则；
- 已审核、可引用、可计算和不可计算的规则各有多少；
- 哪些卷、天体、星官、动作词仍缺覆盖；
- 哪些规则重复、冲突、存在异文或需要人工解释；
- 每条正式规则来自哪一卷、哪一页、哪一段原文；
- 本次规则发布包是否可离线复验。

## 2. 非目标

B10 不实现：

- 完整天象计算与复杂时序执行；
- 以模型输出自动批准正式规则；
- 自动改写 raw corpus；
- 用一个统一阈值强行计算所有古籍动作；
- 自动给个人命运下结论；
- 批量视频生产；
- 将不可计算或语义不明的古文静默丢弃。

复杂事件执行、应期计算和历史回测进入 B11；视频批量化进入 B12。

## 3. `OmenRule/v2` 本体

B10 先冻结版本化规则本体。核心字段：

```text
schema_version
rule_id
rule_version
rule_status
source_passage_ids
tradition
trigger
actors
relation
spatial_conditions
temporal_conditions
observational_properties
effect
effect_domain
severity
time_window
exceptions
conflict_group
rule_priority
resolution_policy
computability
uncertainty
editorial_notes
review
provenance
```

### 3.1 触发结构

```text
body_or_actor
event_type
target_object_or_region
relation_terms
required_measurements
sequence_conditions
visibility_conditions
```

### 3.2 占应结构

```text
effect_domain
subject_scope
polarity
severity
stated_time_window
historical_context
```

### 3.3 可计算性

```text
computable
partially_computable
not_computable
unknown
```

`not_computable` 是正式研究结论，不是失败。规则仍需保存原文、语义、原因和审核状态。

## 4. 稳定原文单元

每个候选和正式规则绑定一个或多个稳定 passage：

```text
kb_book_id
source_locator
page_marker
heading_path
paragraph_index
raw_start
raw_end
raw_content_hash
normalized_content_hash
source_fingerprint
```

passage ID 使用现有 `kb-text-core` 定位语义和稳定 hash，不另写解析器。原文变化时，受影响规则必须标记 `source_changed` 并重新审核，不能静默继续为 citable。

## 5. 标注规范

B10 在批量抽取前先完成标注手册。手册至少定义：

- 一段原文何时算一条、两条或多条规则；
- “若……则……”、省略主语、连续枚举和引用他书如何处理；
- 日、月、五星、二十八宿、客星、彗星、流星、日月食、云气等类别；
- 犯、入、守、离、掩、合、聚、凌、乘、留、逆、顺、出、见、伏等动作；
- 色、大小、芒角、动摇、明暗等观测性质；
- 占应对象、领域、吉凶、严重度和应期；
- 异文、缺字、语义不明和不可计算如何标记；
- 重复规则、上位规则、特例规则和冲突规则如何区分。

标注结果必须保留原文片段和结构化解释，不能只保留最终字段。

## 6. 黄金集与数据分层

建立三个互不混淆的数据集：

```text
development set
validation set
sealed holdout set
```

- development 用于设计抽取器和标注规范；
- validation 用于任务验收和回归；
- sealed holdout 仅在阶段发布前开启，不用于调 prompt、规则或阈值。

黄金集应覆盖不同卷、不同天体、不同关系词、简单和复杂语句、可计算与不可计算规则、重复和冲突案例。

## 7. 候选抽取

支持两类抽取器：

### 7.1 确定性抽取器

使用标题、句式、动作词、条件词和占应词生成高精度候选。所有匹配保留 raw offsets 和 pattern version。

### 7.2 模型辅助抽取器

模型只能生成候选。每次输出必须记录：

```text
model_provider
model_name
model_version
prompt_version
prompt_hash
input_passage_id
input_hash
raw_model_output
parsed_candidate
created_at
```

解析失败、模型不可用或输出不一致不能产生正式规则。模型不得读取或写入正式 Qdrant，也不得批准候选。

## 8. 人工审核

正式规则至少经过两阶段审核：

```text
initial_review
→ independent_recheck
→ adjudication_if_needed
```

同一审核者执行时应采用时间隔离复核，避免把第一次判断当作独立复核。记录审核人、时间、版本、修改字段和理由。

多人审核时统计一致率；主要类别和关键字段目标 Cohen’s κ 不低于 0.80。未达到时优先修订标注手册，而非强行增加自动规则。

## 9. 去重、合并与冲突

分别处理：

- 全文与分卷的同源重复；
- 同一规则在不同卷重复；
- 同义但文字不同；
- 上位规则与特例；
- 相同触发、不同占应；
- 不同传统或引文来源冲突；
- 一段原文拆为多规则；
- 多段原文支持同一规则。

系统不得自动删除被抑制规则。每个合并、别名或冲突组保留完整 provenance 和人工决定。

## 10. 覆盖率与质量指标

B10 用自动指标替代主观“完成百分比”。每次评测至少输出：

```text
total_primary_passages
eligible_omen_passages
candidate_rules
reviewed_rules
approved_rules
citable_rules
computable_rules
partially_computable_rules
not_computable_rules
ambiguous_rules
missing_evidence_rules
conflict_groups
duplicate_groups
coverage_by_volume
coverage_by_body
coverage_by_event_type
coverage_by_relation_term
coverage_by_effect_domain
review_rejection_rate
inter_annotator_agreement
```

每个指标说明分母和计算方法。不得把“未识别 passage”从分母静默排除以提高覆盖率。

## 11. 规则发布包

每次正式发布生成内容受限、确定性、可离线复验的发布包：

```text
rule-release-manifest.json
rules.jsonl
passage-bindings.jsonl
coverage-report.json
evaluation-report.json
source-fingerprint.json
migration-report.json
review-summary.json
```

发布包复用 B7/B8 原则：

- canonical bytes 和成员 hash；
- caller-selected no-overwrite 输出；
- 失败不产生部分包；
- 可离线重跑 schema、引用和评测验证；
- 不包含 secret、机器绝对路径或未授权模型原始数据；
- 分类和归档不自动删除旧规则发布包。

## 12. 测试策略

### 12.1 Contract

- `OmenRule/v2` 严格 schema；
- v1 加载兼容；
- v1→v2 迁移不静默改变含义；
- unknown fields、重复 ID、非法状态和非有限值 fail-closed。

### 12.2 Passage binding

- source/locator/page/paragraph/heading/anchor/hash 全链验证；
- source 改变触发重新审核；
- 多处相同 anchor 不得自动唯一绑定。

### 12.3 Extraction quality

- development 和 validation 分离；
- 报告 precision、recall、F1；
- 关键高风险类别优先控制 false positive；
- sealed holdout 只在发布门禁使用。

### 12.4 Annotation quality

- 标注手册 fixture；
- 双阶段审核状态机；
- 一致率统计；
- 审核历史不可覆盖。

### 12.5 Dedup/conflict

- 确定性聚类；
- tie-break 稳定；
- suppressed rule 保留；
- 不同传统不能静默合并。

### 12.6 Mutation testing

优先覆盖：

- evidence eligibility；
- approval state；
- source-change invalidation；
- conflict resolution；
- release verifier。

关键模块 mutation score 目标不低于 80%。

## 13. 与 B9/B11/B12 的接口

- B9 只消费 `RuleAssessment/v1`，不直接消费 `OmenRule/v2` 内部字段。
- B10 输出真实规则类型和可计算性统计。
- B11 根据 B10 的 approved 规则需求扩展事件检测、时序、组合关系和回测。
- B12 只从已审核规则和稳定内容契约生成批量视频候选。

## 14. 变更控制

1. `OmenRule/v2` 语义冻结后，破坏性变化使用新版本。
2. 标注手册版本与规则发布版本绑定。
3. 黄金集更新必须显式批准，保留 before/after 和理由。
4. sealed holdout 不得用于日常调参。
5. 模型、prompt 或抽取 pattern 变化必须触发 validation 回归。
6. 新规则类别先进入 backlog，不在进行中的任务中顺便扩展。

## 15. 完成标准

B10 完成需要：

- `OmenRule/v2`、标注规范和版本政策冻结；
- 稳定 passage 单元和 source-change 失效机制可用；
- development/validation/holdout 黄金集建立；
- 确定性和可选模型辅助候选抽取可审计；
- 双阶段审核、去重、冲突和覆盖率统计完成；
- 至少一批跨类别正式规则发布包通过离线复验；
- 覆盖率由实际指标报告，不再使用主观百分比；
- B11 获得真实、按优先级排序的执行器需求清单。