# Core14 临时可用性分层

记录日期：2026-08-04。机器可读登记：
`corpus/research_sources/b10-core14/provisional-usability-stratification.json`。

本分层落实用户确认的操作口径，不产生新的 Reviewer A/B 标注，也不覆盖
B10-R02 或 B10-R06 的证据裁决。这里的“可用”仅表示可在明确披露
“待 Reviewer B 最终确认”的前提下用于内部研究；不等于双真人定稿、正式
规则批准或发布授权。

## 1. 可用但待 Reviewer B 最终确认（11）

```text
C02 C09 C11 C13 C14 C31 C41 C43 C44 C45 C47
```

统一操作状态：`provisional_usable_pending_reviewer_b`。

允许用途：

- 带来源定位的内部检索与研究摘引；
- 多文献映射、关系分析与异文对照；
- 原子规则拆分与可计算性研究；
- 明示“待 Reviewer B 最终确认”的内部研究报告。

使用条件：必须保留 passage/source locator、版本与哈希链；不得从整段
`eligible` 推导所有原子规则都已定稿；发现新边界、异文或主体歧义时，
立即移入补证流程而不是静默修正。

## 2. 隔离补证（3）

| 条目 | 证据状态 | 隔离原因 | 解除隔离的最低条件 |
|---|---|---|---|
| C03 | `needs_review` | 不同来源及“犯、乘、贯、食、吞”等关系须拆分；来源占应不同不能直接判为逻辑冲突 | Reviewer B 独立确认来源边界与原子拆分 |
| C24 | `ambiguous` | S8/S9 虽已拆开，但 `㑹客環守`、时长及形态异文仍无唯一校读 | 新版本证据或 Reviewer B 对保守拆分作独立裁决 |
| C33 | `needs_review` | 已排除上一节“留守”并补齐右边界，但新节拆分仍待独立人工确认 | Reviewer B 确认分节后重新评估引用资格 |

统一操作状态：`isolated_evidence_supplement`。三条当前不得进入普通内部
引用池、原子规则批量样本或映射基线；可继续做定向校勘、上下文补齐和
版本比对。

## 3. 对两组均生效的禁止项

截至本记录，Reviewer A 为
`USER_CONFIRMED_EVIDENCE_REVISED_READY_FOR_RETURN`，Reviewer B 为
`UNLABELLED_HUMAN_REVIEW_NOT_STARTED`。因此两组均不得用于：

- 满足或模拟第二名真人审核；
- 冻结 `threshold-freeze.json`；
- 正式规则发布、official ingest 或 official promotion；
- 解锁 PR #54 或启动 B10-PR-D/E/F；
- 写入 Qdrant、`local_kb_default` 或自动发布流程。

Reviewer B 返回后，只需对 A/B 分歧项做定向裁决；无分歧条目不因个别
争议自动推翻，但仍须经过 PR #54 冻结的完整双人门禁与批准记录验证。
