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
Current feature: codex/kaiyuan-citable-sync-v2
Current PR: #12
Release target: stable/kaiyuan-v2
Forbidden target: main
Protected legacy collection: local_kb_default
V2 collection: local_kb_kaiyuan_v2 or ephemeral CI collection
```

## 最新验证基线

```text
Verified head: 6152acc6bd9e3dbb07af97b10df42577ff87af54
Development Governance run: 29623960771 — success
Kaiyuan Stable Core run: 29623960806 — success
Kaiyuan Upstream Runtime run: 29623960814 — success
```

该 head 已包含开发治理、严格 CText 定点比对、下游全回归、上游单元测试、Qdrant 增量、Qdrant 检索契约和 candidate roundtrip。后续文档状态更新会再次触发最终门禁；不得以该历史 head 代替最终 merge head。

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
- **Evidence:** `Development Governance` run `29623960771` 通过；详情见 `WORK_LOG.md`。

## B4 — Candidate sync、可引用证据与黄金评测

设计：`docs/superpowers/specs/2026-07-17-kaiyuan-citable-sync-and-golden-eval-design.md`

计划：`docs/superpowers/plans/2026-07-17-kaiyuan-citable-sync-and-golden-eval.md`

运行手册：`docs/development/B4_RELEASE_RUNBOOK.md`

### B4-T01 — Shared sync error contract

- **Status:** `DONE`
- **Scope:** 共享错误码、run status、序列化与 retryable 语义。
- **Acceptance:**
  - 支持 `authentication_failed`, `upstream_unavailable`, `timeout`, `contract_error`, `collection_not_found`, `invalid_response`；
  - 上下游引用同一契约；
  - contracts test 通过。
- **Evidence:** shared contract tests 在 Stable Core 和 workspace regression 中通过。

### B4-T02 — Structured downstream transport errors

- **Status:** `DONE`
- **Scope:** `KBSearchError` 结构化错误和 HTTP/transport 分类。
- **Acceptance:**
  - 401/403、404、408/timeout、422、429/5xx、连接错误、invalid JSON/shape 均有明确分类；
  - 旧字符串异常使用方式保持兼容；
  - 不再将错误转换为空命中。
- **Evidence:** transport taxonomy tests 和下游全回归在 run `29623960806`/`29623960814` 通过。

### B4-T03 — Atomic candidate sync

- **Status:** `DONE`
- **Scope:** 全 manifest 内存规划、run-level error、原子替换与旧入口兼容。
- **Acceptance:**
  - 健康无命中为 `pending`；
  - 相同正式 hash 为 `merged`；
  - 正式卡存在但 hash 不同为 `needs_review`；
  - 本地 source/anchor/hash 漂移为 `stale`；
  - 任一上游错误时所有 manifest byte-for-byte 不变；
  - 多 item 中途失败不产生部分写入；
  - `sync-upstream-status` CLI 使用新执行器。
- **Evidence:** atomic sync unit tests、workspace regression 和 candidate roundtrip 均通过。

### B4-T04 — Strong citable evidence resolver

- **Status:** `DONE`
- **Scope:** source、book、locator、page、paragraph、heading、anchor、hash 的 passage-backed 校验。
- **Acceptance:**
  - 只有完整验证结果可为 `citable`；
  - 缺源、越界、错书、错 locator/page/paragraph/heading/anchor/hash 返回精确状态；
  - `is_citable_evidence` 对 v2 只接受 `status=citable`；
  - legacy 最小引用保持可加载但默认 `candidate_only`；
  - resolver 返回 checks 和 matched passage trace。
- **Evidence:** legacy audit fixture 已改为真实 passage；resolver、rule matcher 和 roundtrip citable checks 通过。

### B4-T05 — Rule audit and strict CLI reporting

- **Status:** `DONE`
- **Scope:** `resolve-evidence --strict`、`audit-rules`、规则引擎证据状态。
- **Acceptance:**
  - strict 模式报告精确失败状态；
  - audit 按全部验证状态计数并输出 trace；
  - mismatch 状态永不设置 primary evidence；
  - 旧命令名保持兼容。
- **Evidence:** CLI evidence audit、legacy CLI audit 和 rule matcher 回归在下游套件通过。

### B4-T06 — Golden retrieval evaluation v2

- **Status:** `DONE`
- **Scope:** 两阶段池、正式 primary、fallback policy、locator/page/heading/citable fields 和污染检测。
- **Acceptance:**
  - 每个 case 输出 pool、official primary、fallback、locator、page、heading、citable 和 pollution 指标；
  - “荧惑守心”“月犯心宿”等有明确卷页标题预期；
  - pending candidate、prompt/nav/example 污染导致失败；
  - 兼容旧 eval case 字段。
- **Evidence:** golden retrieval evaluator tests 与下游回归通过。

### B4-T07 — Promotion/ingest/retrieve/sync roundtrip

- **Status:** `DONE`
- **Scope:** 临时 Qdrant 端到端 candidate 工作流。
- **Acceptance:**
  - generate → approve → promote → desired corpus → ingest → structured retrieve → sync merged；
  - pending candidate 排除；
  - 模拟 timeout 后 manifest 不变；
  - linked primary passage 通过 citable 校验；
  - 使用 deterministic fake embedding 和随机 ephemeral collection；
  - 专用 CI job 通过。
- **Evidence:** `candidate-roundtrip` job 在 `Kaiyuan Upstream Runtime` run `29623960814` 通过；未访问 `local_kb_default`。

### B4-T08 — Targeted CText spot-check audit

- **Status:** `DONE`
- **Scope:** 无网络定点片段比对和来源记录。
- **Acceptance:**
  - 只读取人工记录的 CText 片段；
  - 报告 `exact_raw`, `exact_normalized`, `mismatch`, `missing_source`, `missing_page`, `invalid`；
  - 明确 `network_accessed=false`, `automatic_bulk_download=false`, `local_raw_preserved=true`；
  - strict audit 在正式 121 卷目录运行；
  - 结果写入 release 文档，不修改 raw corpus。
- **Source:** Chinese Text Project Wiki《開元占經》，用户确认本项目可二次开发；文本未经校订。
- **Evidence:** strict spot-check 在 Stable Core run `29623960806` 通过。

### B4-T09 — Documentation and release gates

- **Status:** `VERIFYING`
- **Scope:** runbook、PR 状态、全部 CI 和稳定分支合并。
- **Acceptance:**
  - 同步错误、原子性、citation statuses、修复流程、黄金指标、CText policy 文档完整；
  - contracts、text-core 3.9/3.12、upstream、downstream、Qdrant incremental、retrieval contract、candidate roundtrip、spot-check、governance 全绿；
  - PR 从 draft 转为 ready；
  - squash 只合入 `stable/kaiyuan-v2`；
  - `main` 和 `local_kb_default` 无变化。
- **Current state:** 运行手册和治理文件已完成；等待本次状态/日志提交后的最终 head 门禁，再更新 PR 并合入稳定分支。

## B5 — 规则引擎语义收口

### B5-T01 — 三值阈值判断

- **Status:** `READY`
- **Goal:** 角距、持续时间、可见性缺失时使用 `unknown`，不得自动视为通过。
- **Expected statuses:** `not_matched`, `insufficient_data`, `partial_match`, `candidate_only`, `matched`。
- **Start condition:** B4 PR #12 合入 `stable/kaiyuan-v2` 后，从稳定分支建立新 feature branch。

### B5-T02 — 冲突组 resolution policy

- **Status:** `BACKLOG`
- **Goal:** 实际执行 `resolution_policy`, `conflict_group`, `rule_priority`，而非只报告冲突存在。

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
B4-T09 最终 head 全门禁
→ PR #12 ready/review/squash 到 stable/kaiyuan-v2
→ 从稳定分支开始 B5-T01
→ B5-T02
→ B5-T03
→ B6
```
