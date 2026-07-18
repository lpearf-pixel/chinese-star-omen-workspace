# 开发工作日志

按时间倒序记录实际开发批次、任务编号、改动、验证证据和遗留风险。任务只有在这里记录最新验证后才能在 `TASKS.md` 标记 `DONE`。

## 2026-07-18 — B4-R01 pre-merge integrity review verified

### Verified head

```text
767e107d7ccaf34a6dbfc7881dd2860ca0bd1369
```

### Workflow evidence

```text
Development Governance
run 29624529981
conclusion: success

Kaiyuan Stable Core
run 29624530036
conclusion: success

Kaiyuan Upstream Runtime
run 29624529987
conclusion: success
```

### Review findings and fixes

1. **真实 CLI sync 绕过 canonical book filter**
   - Finding: `candidate_cards.sync_upstream_status()` 为每个 item 调用 legacy helper，新建 retriever 且未传 `kb_book_id`。
   - Fix: 真实入口只创建一个结构化 `KBSearchRetriever`，直接交给 `sync_candidate_manifests()`；official lookup 统一传 `filters={"kb_book_id": book_id}`、`structured_recall` 和 `extract_card`。
   - Test: legacy CLI sync test 改为拦截 canonical `retrieve()`，验证 filter/stage/card pool。

2. **Candidate card 完整性字段可缺失**
   - Finding: manifest 有 anchor/hash 时，card frontmatter 缺少对应字段仍可能通过本地校验。
   - Fix: card 的 `anchor_text` 和 `content_hash` 都成为本地 current 的必要字段；缺失时标为 `stale`，不访问上游。

3. **相同引文跨卷误合并风险**
   - Finding: official hit 只要 content hash 相同就会标记 `merged`，没有验证 source locator。
   - Fix: `merged` 现在要求 content hash 与 canonical source locator 同时一致；有正式卡但 locator 缺失或不一致时为 `needs_review`。

4. **Generic 404 被误报为 collection missing**
   - Finding: 任意 HTTP 404 都被分类为 `collection_not_found`，旧服务缺少 `/v1/meta` 时会产生错误诊断。
   - Fix: 只有上游显式返回 `COLLECTION_NOT_FOUND` 才使用该错误码；generic 404 为非重试 `contract_error`。

### Gate coverage

- governance checker；
- Python 3.9/3.12 text core；
- shared contracts；
- strict CText spot checks；
- full downstream regression including new sync/transport tests；
- upstream unit and compose/security checks；
- Qdrant incremental and retrieval-contract integration；
- candidate promote/ingest/retrieve/sync/citation roundtrip。

### Status

- B4-R01: `DONE`
- B4-T09: remains `VERIFYING` until the documentation status commit receives a fresh final-head gate.
- No change to `main` or `local_kb_default`.

## 2026-07-18 — GOV-T01 / B4-T01–T08 verified

### Verified head

```text
6152acc6bd9e3dbb07af97b10df42577ff87af54
```

### Workflow evidence

```text
Development Governance
run 29623960771
conclusion: success

Kaiyuan Stable Core
run 29623960806
conclusion: success

Kaiyuan Upstream Runtime
run 29623960814
conclusion: success
```

### Gates covered

- governance checker unit tests and task/work-log PR policy；
- shared contracts；
- text-core Python 3.9 and Python 3.12；
- strict local CText spot checks；
- downstream full regression；
- upstream unit tests；
- Docker Compose validation；
- machine-local path and secret artifact scan；
- Qdrant incremental reconciliation；
- Qdrant retrieval contract；
- candidate generate/approve/promote/ingest/retrieve/sync/citation roundtrip。

### Root-cause fixes in this batch

1. **Legacy audit expectation**
   - Failure: an absent `docs/a.md` was expected to be citable merely because it declared `card_type=fenjuan`.
   - Fix: build a real `KR3g0018_031` passage fixture with locator, page, heading, paragraph, anchor and raw hash.
   - Safety: resolver fail-closed requirements were preserved; no assertion was weakened.

2. **Canonical book filter and limit compatibility**
   - Failure: old CLI tests expected `filters.book_id`; v2 wire contract requires `kb_book_id`.
   - Fix: tests now require canonical `kb_book_id`; retrieval client accepts transitional `limit` while using `top_k` internally.

3. **CText Mars-heart spot check**
   - Failure: the manually recorded excerpt omitted the character `來` before `三月`, so strict comparison correctly reported mismatch.
   - Fix: corrected the reference record to `其來三月彗星如房后百二十日名山崩熒惑守心`.
   - Safety: local raw corpus was not changed.

4. **Candidate roundtrip configuration**
   - Failure: the integration job ran from workspace root while the downstream config lives at `apps/star-omen/config/config.yaml`.
   - Fix: test explicitly sets `APP_CONFIG_PATH` to the repository config.

5. **Structured-card indexing cardinality**
   - Failure: the roundtrip assumed one Qdrant point per Markdown candidate, but heading-based structured indexing correctly emitted several retrieval records from one approved card.
   - Fix: validate shared official approval/provenance and matching candidate hash across one or more records; do not force an artificial one-point invariant.

### Delivered governance and operations documentation

- `AGENTS.md`
- `docs/development/DEVELOPMENT_MANUAL.md`
- `docs/development/TASKS.md`
- `docs/development/WORK_LOG.md`
- `docs/development/DECISIONS.md`
- `docs/development/B4_RELEASE_RUNBOOK.md`
- `scripts/check_development_governance.py`
- `.github/workflows/development-governance.yml`

### Status after verification

- GOV-T01: `DONE`
- B4-T01 through B4-T08: `DONE`
- B4-T09: `VERIFYING`
- B5-T01: `READY` after B4 merge

### Remaining release work

- Run all required workflows on the final documentation/status head.
- Update PR #12 body with final evidence.
- Mark PR ready only when the latest head is green.
- Squash merge only into `stable/kaiyuan-v2`.
- Confirm `main` and `local_kb_default` were not modified.

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
- 新增 governance checker、单元测试和 PR gate。

### Current B4 diagnosis

最初 downstream CI 的明确失败根因：

1. `tests/test_cli_audit.py` 仍假设一个不存在的 `docs/a.md` 只要声明 `card_type=fenjuan` 就可以 `citable`。这与 B4 fail-closed 设计冲突。
2. 早期 candidate sync fixture 把 manifest hash 改成任意占位值，导致新本地 hash 验证把所有 item 正确标为 stale。
3. legacy `candidate_cards.sync_upstream_status` 测试仍依赖旧裸请求 seam，需要保持命令兼容但统一到结构化 retriever。

### Verification evidence before governance batch

- PR: `#12 Harden Kaiyuan candidate sync and citable evidence`
- Base: `stable/kaiyuan-v2`
- Head before governance batch: `23f95fbfd020c039a6a08138df3e9acb4ff85256`
- Text-core Python 3.9/3.12 jobs: passing on the inspected run.
- Upstream unit, Qdrant incremental and retrieval-contract jobs: passing on the inspected run.
- Downstream: failing on stale legacy expectations; no completion claim was made at that point.
