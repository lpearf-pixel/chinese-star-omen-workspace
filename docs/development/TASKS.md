# 开发任务台账

本文件是所有当前和后续开发任务的唯一状态台账。聊天、PR 评论和临时笔记不能替代本文件。

## 状态定义

| 状态 | 含义 |
|---|---|
| `BACKLOG` | 已记录，尚未排期 |
| `READY` | 需求与验收条件明确，可开始 |
| `IN_PROGRESS` | 正在实现 |
| `BLOCKED` | 受外部依赖、环境或信息阻塞 |
| `VERIFYING` | 实现完成，正在执行测试、CI 或 review |
| `DONE` | 验收证据、CI、提交/PR 已记录 |
| `CANCELLED` | 明确取消并记录原因 |

## 当前发布线

```text
Stable base: stable/kaiyuan-v2
Current feature: codex/kaiyuan-rule-semantics-v2
Current PR: #13
Release target: stable/kaiyuan-v2
Forbidden target: main
Protected legacy collection: local_kb_default
V2 collection: local_kb_kaiyuan_v2 or ephemeral CI collection
```

## 最新稳定基线

```text
B4 PR: #12
B4 merged stable commit: 8bca22a93c8124d350cf61bbc71b37c36a4af0b8
B4 final feature head: 6a1939b763c697f94fe0e04d53d1d56250bfc528
Development Governance run: 29624628445 — success
Kaiyuan Stable Core run: 29624628452 — success
Kaiyuan Upstream Runtime run: 29624628436 — success
```

B4 已 squash 合入 `stable/kaiyuan-v2`。`main` 和 `local_kb_default` 未参与 B4 release。B5 从上述稳定提交建立独立 feature branch。

## Governance

### GOV-T01 — 建立强制开发手册、任务台账、工作日志和决策记录

- **Status:** `DONE`
- **Scope:** `AGENTS.md`, `docs/development/*`, governance checker and CI.
- **Acceptance:**
  - 开发前阅读顺序写入根目录入口文件；
  - 长期边界和测试要求写入开发手册；
  - 所有任务拥有稳定编号与状态；
  - 代码 PR 必须更新 `TASKS.md` 或 `WORK_LOG.md`；
  - governance checker 有独立单元测试；
  - CI 对 `stable/kaiyuan-v2` PR 生效。
- **Evidence:** Development Governance run `29624628445` 通过。

## B4 — Candidate sync、可引用证据与黄金评测

设计：`docs/superpowers/specs/2026-07-17-kaiyuan-citable-sync-and-golden-eval-design.md`

计划：`docs/superpowers/plans/2026-07-17-kaiyuan-citable-sync-and-golden-eval.md`

运行手册：`docs/development/B4_RELEASE_RUNBOOK.md`

### B4-T01 — Shared sync error contract

- **Status:** `DONE`
- **Evidence:** shared contract tests and final B4 gates passed.

### B4-T02 — Structured downstream transport errors

- **Status:** `DONE`
- **Evidence:** transport taxonomy and full downstream regression passed.

### B4-T03 — Atomic candidate sync

- **Status:** `DONE`
- **Evidence:** atomic sync tests, workspace regression and candidate roundtrip passed.

### B4-T04 — Strong citable evidence resolver

- **Status:** `DONE`
- **Evidence:** resolver, CLI, matcher and roundtrip citable checks passed.

### B4-T05 — Rule audit and strict CLI reporting

- **Status:** `DONE`
- **Evidence:** strict CLI, status-aware audit and rule evidence regression passed.

### B4-T06 — Golden retrieval evaluation v2

- **Status:** `DONE`
- **Evidence:** golden evaluator tests and downstream regression passed.

### B4-T07 — Promotion/ingest/retrieve/sync roundtrip

- **Status:** `DONE`
- **Evidence:** candidate-roundtrip job passed with ephemeral Qdrant and did not access `local_kb_default`.

### B4-T08 — Targeted CText spot-check audit

- **Status:** `DONE`
- **Source:** Chinese Text Project Wiki《開元占經》，用户确认本项目可二次开发；文本未经校订。
- **Evidence:** strict local spot-check gate passed without network access or raw-corpus rewrite.

### B4-R01 — Pre-merge sync/transport integrity review

- **Status:** `DONE`
- **Evidence:** canonical book-scoped sync, card integrity, locator-aware merge and generic 404 hardening passed final gates.

### B4-T09 — Documentation and release gates

- **Status:** `DONE`
- **Evidence:**
  - PR #12 final head `6a1939b...` passed all three required workflows；
  - PR was marked ready and squash merged as `8bca22a9...` into `stable/kaiyuan-v2`；
  - `main` was not targeted；
  - tests used v2/ephemeral collections and did not write `local_kb_default`。

## B5 — 规则引擎语义收口

### B5-T01 — 三值条件与 `insufficient_data`

- **Status:** `VERIFYING`
- **Goal:** 缺失的角距、持续时间、可见性等必要输入必须成为 `unknown`，不能自动当作通过。
- **Scope:** `conditions.py`, `minimal_matcher.py`, `match_result.py`, focused tests, design/plan and user-facing reports.
- **Acceptance:**
  - 条件状态使用 `pass | fail | unknown`；未配置的可选条件不进入分母；
  - `body`, `event_type`, `target` 等核心身份条件失败时为 `not_matched`；
  - rule `trigger.body` 与 `trigger.event_type` 必须是非空字符串，配置错误需明确失败；
  - 已提供且不满足的非核心条件为 `partial_match`；
  - 没有已知失败、但至少一个必要条件为 `unknown` 时为 `insufficient_data`；
  - 全部适用条件通过且 primary evidence 可引用时为 `matched`；
  - 全部适用条件通过但只有候选/缺失证据时为 `candidate_only`；
  - `trigger_ratio` 只把 `pass` 计入分子，`unknown` 进入适用条件分母，未配置条件不进入分母；
  - 输出新增 `condition_states`、`unknown_conditions`、`failed_conditions`、`trigger_ratio`，保留 `missing_conditions` 兼容字段；
  - 数值缺失、空字符串、非有限数和类型错误都归为 `unknown`，不得抛出未分类异常；
  - 非有限数的 condition trace 必须可用严格 JSON 序列化，不得输出裸 `NaN`/`Infinity`；
  - visibility required 且字段缺失为 `unknown`，显式 false 为 `fail`，`visibility_required=false` 时条件不适用；
  - rule 未配置 target 时 target 不适用且不进入分母；
  - 非法 numeric threshold 或非法 `visibility_required` 配置需明确失败，不能变成 event-level unknown；
  - scoring 不得给 unknown 条件通过分；
  - 旧 matched/candidate/not_matched 行为在数据完整时保持兼容；
  - focused tests、downstream regression 和治理门禁通过。
- **Implementation evidence:** `da007704c7b11a0ed90241f57a4e02062f57a191` 的 Governance `29625394299`、Stable Core `29625394306`、Upstream Runtime `29625394314` 全部成功；等待当前文档状态 head 的 final gates。

### B5-T02 — 冲突组 resolution policy

- **Status:** `READY`
- **Goal:** 实际执行 `resolution_policy`, `conflict_group`, `rule_priority`，而非只报告冲突存在。
- **Start condition:** B5-T01 合入稳定分支或作为同一 B5 PR 的下一独立、已验证任务。

### B5-T03 — 规则证据批量审计与迁移

- **Status:** `BACKLOG`
- **Goal:** 把 legacy primary 引用补齐 locator/page/anchor/hash；保留无法补齐项为 candidate-only。

## B6 — 性能、可观察性与发布

### B6-T01 — Filesystem primary passage cache

- **Status:** `BACKLOG`
- **Goal:** 基于 path/mtime/hash 的只读 passage index，避免每次查询全量解析所有 Markdown。

### B6-T02 — 检索与同步可观察性

- **Status:** `BACKLOG`
- **Goal:** 记录 stage latency、pool size、fallback reason、sync run error、corpus version 和 collection。

### B6-T03 — Stable release runbook and rollback drill

- **Status:** `BACKLOG`
- **Goal:** 验证 `local_kb_kaiyuan_v2` 切换、回滚、manifest 对账和旧 collection 保护。

## 当前执行顺序

```text
B5-T01 final-head full gates
→ PR #13 ready/review/squash to stable/kaiyuan-v2
→ B5-T02
→ B5-T03
→ B6
```
