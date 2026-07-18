# 开发工作日志

按时间倒序记录实际开发批次、任务编号、改动、验证证据和遗留风险。任务只有在这里记录最新验证后才能在 `TASKS.md` 标记 `DONE`。

## 2026-07-18 — GOV-T01 / B4 continuation

### Scope

- 用户选择三层治理方案：长期手册、任务台账、工作记录，并增加决策记录和根目录入口。
- 所有后续任务必须先进入文件，开发前必须阅读手册。
- 继续 B4，不修改 `main`，目标仍为 `stable/kaiyuan-v2`。

### Changes

- 新增根目录 `AGENTS.md`，定义开发前强制阅读顺序和不可违反边界。
- 新增 `docs/development/DEVELOPMENT_MANUAL.md`。
- 新增 `docs/development/TASKS.md`，登记 GOV、B4、B5、B6 任务。
- 新增 `docs/development/DECISIONS.md`，记录 release、Qdrant、语料、CText、检索、sync 和 citation 决策。
- 正在新增 governance checker、单元测试和 PR gate。

### Current B4 diagnosis

最新 downstream CI 的明确失败根因：

1. `tests/test_cli_audit.py` 仍假设一个不存在的 `docs/a.md` 只要声明 `card_type=fenjuan` 就可以 `citable`。这与 B4 fail-closed 设计冲突。测试应改为真实 primary passage fixture，不应降低 resolver 验证。
2. 早期 candidate sync fixture 把 manifest hash 改成任意占位值，导致新本地 hash 验证把所有 item 正确标为 stale。fixture 应生成与 anchor 一致的 hash。
3. legacy `candidate_cards.sync_upstream_status` 测试仍 monkeypatch 已弃用的裸 `_retrieve_hits`，而新路径必须复用结构化 retriever。需要保留命令兼容但更新测试注入点。

### Verification evidence before governance batch

- PR: `#12 Harden Kaiyuan candidate sync and citable evidence`
- Base: `stable/kaiyuan-v2`
- Head before governance batch: `23f95fbfd020c039a6a08138df3e9acb4ff85256`
- Text-core Python 3.9/3.12 jobs: passing on the inspected run.
- Upstream unit, Qdrant incremental and retrieval-contract jobs: passing on the inspected run.
- Downstream: failing only on stale legacy expectations described above; no completion claim made.

### Remaining in this batch

- 完成 governance checker 和 CI。
- 修复 legacy audit fixture 而不放宽 citable 校验。
- 修复 candidate sync fixtures/compatibility tests。
- 接入 candidate roundtrip CI。
- 运行最新完整门禁并回写 head SHA 与结果。
