# 《唐开元占经》规则标注手册 v1

## 1. 状态与用途

```text
guide_version: kaiyuan-rule-annotation/v1
contract: omen-rule/v2 + rule-candidate/v2
status: frozen for B10-PR-A contract fixtures
```

本手册定义 passage 到候选规则的人工标注语义。它不是自动抽取 pattern，
也不授权候选成为正式规则。正式规则仍须通过稳定 passage、citable
evidence、初审、独立复核和必要裁决。

原文、`<pb:...>`、原字形与实体不可改写。校勘、释义和现代标识只进入
派生字段。

## 2. 标注单位

### 2.1 一段一规则

一个完整条件组只指向一个占应时，建立一个候选。并列同义词、同一对象
的别名或对同一结果的补充说明，不单独拆分。

### 2.2 一段拆多规则

出现以下任一情况时拆分：

- 不同 trigger 分别对应不同 effect；
- 同一 trigger 的多个 effect 有独立条件或应期；
- 连续枚举的对象可独立成立，且原文为每项给出不同占应；
- 上位规则与明确特例同时出现。

所有拆分候选保留同一 passage ID 和各自 raw span。不能通过复制整段而
丢失每条规则的精确 span。

### 2.3 多段合一规则

只有在多个 passage 明确共同构成一个条件或互为不可缺少的释义时合并。
候选按稳定顺序记录全部 passage ID 和 raw span，不选一个“代表段落”
替代其余证据。

同文重复、全文与分卷重复不属于多段合一；它们先保留 provenance，
后续由去重阶段决定。

## 3. 主语、枚举与引文

### 3.1 省略主语

只在同一 heading 或紧邻上文明确给出唯一主语时补全。补全值进入
`actors`，原文 span 不补字，并在 `editorial_notes` 记录来源。若存在
两个合理主语，保留 `uncertainty` 并进入 `needs_review`。

### 3.2 连续枚举

共享主语和占应、只替换同类 target 的枚举可保留为一条规则，target
按原文顺序记录。每项占应不同则拆分。省略的后续谓语不能凭常识补写。

### 3.3 引用他书与异文

- 引文必须绑定实际包含引文的 passage；
- 引用来源名称写入 tradition/provenance，不伪造外部 locator；
- 异文同时保留，不选择“较合理”版本覆盖原文；
- 异文改变 trigger/effect 时建立 conflict 或 ambiguity；
- 缺字、脱文或无法可靠断句时进入 `needs_review`，不得生成 formal rule。

## 4. 天象类别与关系词

`body_or_actor` 至少覆盖：

- 日、月；
- 五星；
- 二十八宿及星官；
- 客星、彗星、流星；
- 日食、月食；
- 云、气及其他明确天象主体。

`relation` 与 `relation_terms` 保存原词。常见关系包括：

```text
犯 入 守 离 掩 合 聚 凌 乘 留 逆 顺 出 见 伏
```

现代归一名称可用于稳定比较，但不得删除原词。关系语义不确定时保留
原词并标记 uncertainty，不强行映射到角距或拓扑运算。

## 5. Trigger 和条件

`trigger` 至少记录：

- `body_or_actor`；
- `event_type`；
- `target_object_or_region`；
- `relation_terms`；
- `required_measurements`；
- `sequence_conditions`；
- `visibility_conditions`。

空间、时间和观测性质分别标注。色、大小、芒角、动摇、明暗等进入
`observational_properties`，不混入 effect。

原文没有数值阈值时不得补造。可以记录所需测量，但 computability 必须
说明为何只能部分计算或不能计算。

## 6. Effect

每条候选至少记录：

- effect domain；
- subject scope；
- polarity；
- severity；
- 原文占应描述；
- 明示应期；
- 必要的历史语境。

标准 effect domain：

```text
politics leadership military agriculture climate economy
public_health ritual border general_omen other
```

没有明示应期时 `time_window=null`，不能从后世案例反推。吉凶不明使用
`unknown`，不可用现代价值判断补全。

## 7. Computability

```text
computable
partially_computable
not_computable
unknown
```

- `computable`：trigger 和条件可由定义明确的观测量判断；
- `partially_computable`：部分条件可计算，但阈值、语义或上下文不完整；
- `not_computable`：核心条件是政治、象征或无法操作化的描述；
- `unknown`：当前材料不足以分类。

后三类必须写结构化原因。`not_computable` 是正式研究结论，不是抽取失败。

## 8. 例外、上位规则与冲突

- 例外写入 `exceptions`，不删除一般规则；
- 上位规则和特例分别保留，由后续 resolution policy 处理；
- 相同 trigger、不同 effect 不自动合并；
- 不同传统或异文冲突进入 conflict group；
- unresolved conflict 使用 `manual_adjudication` 或 `unresolved`；
- suppressed、rejected、merged、split 全部保留 identity 和 history。

## 9. Evidence

正式 `OmenRule/v2` 的每项 evidence 必须为 `citable`，并完整包含：

```text
passage_id
kb_book_id
source_locator
page_marker
heading_path
paragraph_index
raw_start/raw_end
raw_content_hash
normalized_content_hash
source_fingerprint
quote
```

locator、page、heading、paragraph、anchor/span 或 hash 任一不成立时，
候选可以保留，但不能创建 formal rule。citable false positive 容许值
固定为 `0`。

## 10. Identity 与历史

`candidate_id` 绑定 extractor identity、排序后的 passage IDs、raw spans
和 proposal hash。任何绑定输入变化产生新 candidate ID。

模型、pattern 或人工草稿只能创建 candidate。`rule_id` 仅在人工批准时
分配。批准后的语义变化产生递增 `rule_version`，保留每个历史版本的
content hash、reviewer、时间和原因，不覆盖旧记录。

merge、split、reject、defer 和 approve 都必须成为有单调 sequence 的
history event。终态必须与最后事件一致。

## 11. 审核状态

候选允许：

```text
needs_review deferred_with_reason rejected merged split approved
```

正式规则只接受 `approved` review。初审、独立复核和裁决流程由后续
B10-PR-F 实现；PR-A 只冻结契约字段，不提前实现队列。

## 12. 冻结案例

`tests/fixtures/rules/v2/annotation-cases/` 包含手工逐项核对的规范案例：

1. 单段单规则；
2. 单段拆多规则；
3. 多段合一规则；
4. heading 补全省略主语；
5. 异文/缺字进入 needs review；
6. 不可计算规则仍可保留。

`manifest.json` 绑定每个文件 SHA-256。普通测试只读验证，禁止自动更新
案例或 manifest。任何变更须在独立评审中同时更新 guide version、理由、
before/after 和 manifest hash。
