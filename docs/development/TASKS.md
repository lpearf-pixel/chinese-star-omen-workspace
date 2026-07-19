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
Current feature: codex/kaiyuan-ephemeral-release-gate-v2
Current PR: pending (B8-T02 draft PR will target stable/kaiyuan-v2)
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

- **Status:** `DONE`
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

- **Status:** `DONE`
- **Goal:** 实际执行 `resolution_policy`, `conflict_group`, `rule_priority`，而非只报告冲突存在。
- **Base evidence:** B5-T01 PR #13 squash merged to `stable/kaiyuan-v2` as `e4e25ba39d43270b1d2ac54ae3057eb741161b38`.
- **Branch:** `codex/kaiyuan-conflict-resolution-v2`.
- **Acceptance:**
  - 执行 `highest_score`, `highest_priority`, `prefer_primary_evidence`, `manual_review`；
  - 每种 policy 使用确定性排序和稳定 `rule_id` tie-breaker；
  - 同组 policy 不一致、未知 policy、空/重复 rule id 明确失败；
  - `manual_review` 不产生该组正式 recommendation，但保留 provisional recommendation；
  - suppressed rule 保留在完整 `matches`，并携带 suppression trace；
  - 输出 group-level conflict trace 和用户可见 summary；
  - 无冲突和默认 `highest_score` 的旧行为保持兼容。

### B5-T03 — 规则证据批量审计与迁移

- **Status:** `DONE`
- **Goal:** 把 legacy primary 引用补齐 locator/page/anchor/hash；保留无法补齐项为 candidate-only。
- **Base evidence:** B5-T02 PR #14 squash merged as `57da1a8b9afb994b3f3ef0ac1714d14fd4a3d37b`.
- **Branch:** `codex/kaiyuan-rule-evidence-migration-v2`.
- **Current result:** 1 `ambiguous`, 3 `missing_evidence`, 0 `migratable`; no silent promotion.

## B6 — 性能、可观察性与发布

### B6-T01 — Filesystem primary passage cache

- **Status:** `DONE`
- **Base evidence:** B5-T03 PR #15 squash merged as `6dd0910a2d6b825904ae8e0dcc7d3f1a75557775`.
- **Branch:** `codex/kaiyuan-primary-passage-cache-v2`.
- **Goal:** 基于 path/mtime/hash 的只读 passage index，避免每次查询全量解析所有 Markdown。
- **Design:** `docs/superpowers/specs/2026-07-18-kaiyuan-primary-passage-cache-design.md`.
- **Plan:** `docs/superpowers/plans/2026-07-18-kaiyuan-primary-passage-cache.md`.
- **Acceptance:** exact-byte hash invalidation; bounded thread-safe LRU; no stale-on-error result; scanner/resolver/migration reuse; unchanged retrieval/citation semantics; full gates and independent review.
- **Merge evidence:** PR #16 final head `9a395ac8bacb1ab0464b584a8e9ef31f5f5d42cb` squash merged to `stable/kaiyuan-v2` as `0632c0a87515b4b6d33ea2476630d62e2b3321d7`.

### B6-T02 — 检索与同步可观察性

- **Status:** `DONE`
- **Goal:** 记录 stage latency、pool size、fallback reason、sync run error、corpus version 和 collection。
- **Base evidence:** B6-T01 PR #16 squash merged as `0632c0a87515b4b6d33ea2476630d62e2b3321d7`.
- **Branch:** `codex/kaiyuan-retrieval-observability-v2`.
- **Design:** `docs/superpowers/specs/2026-07-18-kaiyuan-retrieval-sync-observability-design.md`.
- **Plan:** `docs/superpowers/plans/2026-07-18-kaiyuan-retrieval-sync-observability.md`.
- **Acceptance:** additive strict-JSON trace; client stage/total latency; requested/raw/returned pools; fallback reason; collection/corpus provenance; structured sync run error; unchanged exception and atomic manifest semantics; full gates and independent review.
- **Merge evidence:** PR #17 final head `534723d0828c8f438900e203d96e981daf77218d` squash merged to `stable/kaiyuan-v2` as `af3f80d8b415f98825a0516fbbce7890e134a90c`.

### B6-T03 — Stable release runbook and rollback drill

- **Status:** `DONE`
- **Goal:** 验证 `local_kb_kaiyuan_v2` 切换、回滚、manifest 对账和旧 collection 保护。
- **Base evidence:** B6-T02 PR #17 squash merged as `af3f80d8b415f98825a0516fbbce7890e134a90c`.
- **Branch:** `codex/kaiyuan-stable-release-rollback-v2`.
- **Design:** `docs/superpowers/specs/2026-07-18-kaiyuan-stable-release-rollback-design.md`.
- **Plan:** `docs/superpowers/plans/2026-07-18-kaiyuan-stable-release-rollback.md`.
- **PR:** #18, base `stable/kaiyuan-v2`.
- **Merge evidence:** final head `4f403682d8d39860b383d9483446704d82a85029`; Governance `29647775680`, Stable Core `29647775679`, Upstream Runtime `29647775710` all succeeded; squash merged as `1378f2790b52c5f08ddf235223fcf128928fc911`.
- **Acceptance:** pure non-mutating three-phase verifier; exact release/rollback manifest reconciliation; healthy structured and primary smoke; exact prior-routing restoration; invariant `local_kb_default` fingerprint; explicit failed report/exit semantics; synthetic CI drill; operator runbook; full gates and independent review.

## 当前执行顺序

```text
B5-T01 final-head full gates
→ PR #13 ready/review/squash to stable/kaiyuan-v2
→ B5-T02
→ B5-T03
→ B6
→ B7-T01
→ B7-T02
→ B7-T03
→ B8-T01
```

## B7 — 发布观测自动化

### B7-T01 — Read-only release observation capture

- **Status:** `DONE`
- **Base evidence:** B6-T03 closeout PR #19 squash merged as `627b3dc086966fec0c527500e4a7e5fac6a8f987`.
- **Branch:** `codex/kaiyuan-release-observation-capture-v2`.
- **Goal:** 从 KB Search 与 Qdrant 的只读接口采集 B6 release-drill phase observation，减少人工拼装 artifact 的遗漏与伪造风险。
- **Acceptance:** no routing or Qdrant mutation; explicit transport/auth/timeout/contract errors; exact health/meta/stage/pool/collection provenance; protected collection fingerprint from allowlisted metadata only; no secret/raw body/source content in output; atomic caller-selected output; output validates through the existing B6 verifier; focused/full gates and independent review.
- **Design:** `docs/superpowers/specs/2026-07-18-kaiyuan-release-observation-capture-design.md`.
- **Plan:** `docs/superpowers/plans/2026-07-18-kaiyuan-release-observation-capture.md`.
- **Merge evidence:** PR #20 final head `57f43bcc1778b2e79926ca625a08ac4f4de49016`; squash merge `eef5f2c2afd64312bedf7c33cc07fe7ca6f5f41f` to `stable/kaiyuan-v2`; exact-head workflows Governance `29666701659`, Stable Core `29666701666`, Upstream Runtime `29666701658` all succeeded.

### B7-T02 — Fail-closed release artifact assembly

- **Status:** `DONE`
- **Base evidence:** B7-T01 closeout PR #21 squash merged to `stable/kaiyuan-v2` as `549143c396d1566096e26797161d8d9b25ccf2dd`.
- **Branch:** `codex/kaiyuan-release-artifact-assembly-v2`.
- **Goal:** 将三份独立 B7 phase observation 与已批准 release manifest 组装为现有 B6 verifier 的严格输入，消除人工复制 schema、phase 和 manifest identity 的风险。
- **Acceptance:** strict unique-key/finite JSON; exact observation schema and phase_name-to-slot binding; safe RFC3339 capture ordering; exact allowlisted manifest identity; in-memory B6 validation before output; atomic caller-selected no-overwrite output; validation/input failures create no artifact; no network, routing, ingest, corpus, candidate or Qdrant mutation; full gates and independent review.
- **Design:** `docs/superpowers/specs/2026-07-18-kaiyuan-release-artifact-assembly-design.md`.
- **Plan:** `docs/superpowers/plans/2026-07-18-kaiyuan-release-artifact-assembly.md`.
- **Merge evidence:** PR #22 final head `23168954f809f046dedee7d1ce107be8dd0332d4`; exact-head workflows Governance `29670048368`, Stable Core `29670048362`, Upstream Runtime `29670048361` all succeeded; squash merged to `stable/kaiyuan-v2` as `4abd11d5f5c30991656cbf525f9f3be0ff3fbf38`.

### B7-T03 — Sealed release evidence bundle and offline verification

- **Status:** `DONE`
- **Base evidence:** B7-T02 closeout PR #23 squash merged to `stable/kaiyuan-v2` as `d3aaea12f0a033703e91ee1f715441761444d563`.
- **Branch:** `codex/kaiyuan-release-evidence-bundle-v2`.
- **Goal:** 将已验证的三阶段 release artifact、批准 manifest identity 与验证结果封装为可搬运、可离线复验、内容受限且防篡改的单文件发布证据包。
- **Acceptance:** exact ZIP member inventory and byte hashes/sizes; strict versioned bundle manifest; release head/tool/schema provenance; offline no-extraction fail-closed verifier reruns B7-T02 assembly and B6 validation; deterministic bytes; atomic caller-selected no-overwrite file creation; no raw corpus, hit, snippet, source path, secret, network, routing, ingest, Qdrant or collection mutation; focused/full gates and independent review.
- **Design:** `docs/superpowers/specs/2026-07-18-kaiyuan-release-evidence-bundle-design.md`.
- **Plan:** `docs/superpowers/plans/2026-07-18-kaiyuan-release-evidence-bundle.md`.
- **Merge evidence:** PR #24 final head `71cc8d9e299154d877b7600d2e042c4541312339`; exact-head workflows Governance `29672619531`, Stable Core `29672619536`, Upstream Runtime `29672619530` all succeeded; squash merged to `stable/kaiyuan-v2` as `bf56df0a1f396d1e2db40f72c6b52e809dd7ab9c`.

## B8 — 发布证据归档与持续门禁

### B8-T01 — Verified evidence archive index and retention classification

- **Status:** `DONE`
- **Base evidence:** B7-T03 closeout PR #25 squash merged to `stable/kaiyuan-v2` as `dfefb73daf001af051a50a461c63a4e7ab308fe8`.
- **Branch:** `codex/kaiyuan-release-evidence-archive-v2`.
- **Goal:** 对多份 B7-T03 证据包离线复验后生成确定性归档索引，并根据显式策略标记保留或可转冷归档，不自动移动或删除任何证据。
- **Acceptance:** every indexed bundle passes exact-byte and semantic B7-T03 verification; strict versioned index; unique bundle hash and safe logical name; deterministic ordering; explicit `keep_latest` plus pinned hashes; `retain|cold_archive_eligible` classification with reasons; atomic caller-selected no-overwrite index; no path/content/secret leakage; no network, deletion, routing, ingest, Qdrant or collection mutation; full gates and independent review.
- **Design:** `docs/superpowers/specs/2026-07-18-kaiyuan-release-evidence-archive-design.md`.
- **Plan:** `docs/superpowers/plans/2026-07-18-kaiyuan-release-evidence-archive.md`.
- **Merge evidence:** PR #26 final head `d58e7ff91adf54a35b9d9d49c54a3a2fa5a12ad0`; exact-head workflows Governance `29673734249`, Stable Core `29673734284`, Upstream Runtime `29673734259` all succeeded; squash merged to `stable/kaiyuan-v2` as `c6af74a5875d3df55e56bbea251ede63b56c427c`.

### B8-T02 — Hermetic end-to-end release evidence gate

- **Status:** `VERIFYING`
- **Base evidence:** B8-T01 closeout PR #27 squash merged to `stable/kaiyuan-v2` as `bae59e0b636588c5600916ce992c642746f002da`.
- **Branch:** `codex/kaiyuan-ephemeral-release-gate-v2`.
- **Goal:** 在 hermetic CI 中串联只读 observation capture、artifact assembly、sealed bundle creation 与 offline verification，持续证明跨组件发布证据契约兼容。
- **Acceptance:** deterministic three-phase capture through read-only fakes; real B7-T02/B7-T03 pure APIs; exact passed validation and verified bundle summary; explicit call audit proving no create/upsert/delete/routing/ingest operation; random safe ephemeral prior collection; no live service access and no create, write or delete of `local_kb_default`; its required invariant fingerprint is supplied only by a hermetic fake inspection; failure injection remains fail-closed; no production-release claim; focused/full gates and independent review.
- **Design:** `docs/superpowers/specs/2026-07-18-kaiyuan-ephemeral-release-gate-design.md`.
- **Plan:** `docs/superpowers/plans/2026-07-18-kaiyuan-ephemeral-release-gate.md`.
