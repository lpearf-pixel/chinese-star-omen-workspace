# 开发工作日志

按时间倒序记录实际开发批次、任务编号、改动、验证证据和遗留风险。任务只有在这里记录最新验证后才能在 `TASKS.md` 标记 `DONE`。

## 2026-07-18 — B6-T02 implementation verifying

### TDD evidence

```text
RED 1: ModuleNotFoundError: src.observability
GREEN 1: helper contract 16 passed

RED 2: retrieval modules had no monotonic timing seam or observability envelope
GREEN 2: official/fallback/error two-stage tests 7 passed

RED 3: candidate_sync had no monotonic seam or returned observability
GREEN 3: candidate sync v1/v2 20 passed

RED 4: nested NaN/Infinity remained in an observability error copy
GREEN focused: observability/retrieval/transport/sync 47 passed
```

### Implementation

- Added additive `kb-observability/v1` envelopes with monotonic, finite, non-negative latency.
- Official retrieval records requested/raw/returned pools, collection, optional upstream latency and corpus version.
- Two-stage retrieval records ordered structured, official-primary, and filesystem fallback stages plus explicit fallback reason.
- Official errors still raise `KBSearchError`; safe trace is attached only under `details.observability`, and errors never trigger fallback.
- Candidate sync reports total latency, collection/corpus provenance, checked/lookups/hits and structured `run_error`; failed manifests remain byte-identical and latency is not persisted into manifests.
- Nested non-finite values are converted to null only in the copied trace, preserving caller/error inputs.

### Local verification

```text
focused: 47 passed
contracts: 6 passed
text-core: 22 passed
downstream: 217 passed
upstream: 49 passed, 3 skipped
```

B6-T02 is `VERIFYING`, not `DONE`. Draft PR #17 targets only `stable/kaiyuan-v2`. Remaining: publish, exact-head governance and three workflows, independent review, review-fix RED/GREEN if needed, ready and squash merge. No corpus, candidate content, ingest, Qdrant, collection, `main`, or `local_kb_default` change.

### Independent review fixes

Review reported no Critical, two Important, and one Minor issue. Four new/updated assertions reproduced all failures:

- top-level two-stage collection ignored effective response collection;
- conflicting stage collection/corpus versions were silently guessed;
- sync telemetry duplicated upstream message/details containing simulated secret/raw content;
- injected non-official hit providers increased `official_hit_count`.

Fixes now promote collection/corpus provenance only on official-stage consensus, expose deterministic `provenance_conflicts`, allowlist sync telemetry errors to code/status/retryable, and count official hits only on the official retriever path. The authoritative top-level sync error and atomic manifest behavior remain unchanged. Fresh focused/full gates and a new exact-head CI run are required.

## 2026-07-18 — B6-T02 observability design and plan

- Inventory confirmed upstream retrieve already returns some `latency_ms`, collection, and optional corpus metadata, but downstream two-stage results have no uniform stage trace and candidate sync reports expose errors without timing/count provenance.
- Selected an additive `kb-observability/v1` envelope using client monotonic timing. Upstream timing is retained separately and invalid/missing values become null.
- Retrieval errors still raise; sync errors remain run-level reports and preserve all manifest bytes. No error becomes healthy empty results or candidate status.
- Design: `docs/superpowers/specs/2026-07-18-kaiyuan-retrieval-sync-observability-design.md`.
- Plan: `docs/superpowers/plans/2026-07-18-kaiyuan-retrieval-sync-observability.md`.
- Decision: D-015.
- No implementation claim. Next exact action: create draft PR, add observability helper tests, observe import RED, then implement only the pure helper.

## 2026-07-18 — B6-T01 merged; B6-T02 started

```text
PR: #16
Final head: 9a395ac8bacb1ab0464b584a8e9ef31f5f5d42cb
Development Governance: 29644669300 — success
Kaiyuan Stable Core: 29644669317 — success
Kaiyuan Upstream Runtime: 29644669313 — success
Squash merge: 0632c0a87515b4b6d33ea2476630d62e2b3321d7
```

GitHub returned `merged=true`, and `refs/heads/stable/kaiyuan-v2` independently resolved to the same squash SHA. PR #16 targeted only `stable/kaiyuan-v2`; no corpus, candidate, ingest, Qdrant, collection, `main`, or `local_kb_default` change.

B6-T02 started from the actual merge SHA on `codex/kaiyuan-retrieval-observability-v2`. Task moved to `IN_PROGRESS` before design. Next action: inventory retrieval/sync result schemas and error boundaries, then define additive JSON-safe observability fields for stage latency, pool size, fallback reason, sync run error, corpus version, and collection.

## 2026-07-18 — B6-T01 implementation verifying

### TDD evidence

```text
RED 1: test_primary_passage_cache_v2.py collection failed with
ModuleNotFoundError: src.connectors.primary_passage_cache
GREEN 1: 9 passed

RED 2: scanner integration failed because primary_file_scanner had no
primary_passage_cache injection point
GREEN 2: cache + filesystem retrieval 16 passed

RED 3: resolver and migration integration failed because both modules had no
primary_passage_cache injection point
GREEN 3: cache + retrieval + resolver + migration 37 passed
```

### Implementation

- Added a bounded, thread-safe process-local LRU of immutable strict-UTF-8 source snapshots and `kb-text-core` passages.
- Each load reads and hashes exact bytes; a content change invalidates parsing even when mtime and byte length are preserved.
- Missing, invalid UTF-8, or unstable sources never return a stale snapshot. Parser errors propagate.
- Filesystem fallback, citable resolver, and rule-evidence migration reuse snapshots. Resolver still performs every B4 validation on every call; migration fingerprint keeps its exact raw-byte algorithm.
- Draft PR #16 targets only `stable/kaiyuan-v2`.

### Local verification

```text
PATH=/tmp/kaiyuan-b5/bin:$PATH make contracts-test
6 passed

PATH=/tmp/kaiyuan-b5/bin:$PATH make text-core-test
22 passed

PATH=/tmp/kaiyuan-b5/bin:$PATH make downstream-test
195 passed

PATH=/tmp/kaiyuan-b5/bin:$PATH make upstream-test
49 passed, 3 skipped
```

B6-T01 is `VERIFYING`, not `DONE`. Remaining: publish implementation, run governance and all three exact-head GitHub workflows, independent review, fix any Critical/Important finding with RED tests, then ready/squash merge. No raw corpus, candidate, ingest, Qdrant, collection, `main`, or `local_kb_default` change.

### Independent review fix

Review found one Important issue and no Critical issues: `KaiyuanPassage` is frozen but its `heading_path` was a mutable list, so returning the cached parser object allowed a consumer to poison later resolver/migration loads without changing source bytes.

```text
RED: cached heading_path was ['唐開元占經', '熒惑占'] rather than an immutable tuple
GREEN focused: 38 passed
GREEN downstream: 196 passed
GREEN contracts: 6 passed
GREEN text-core: 22 passed
GREEN upstream: 49 passed, 3 skipped
```

The cache now defensively converts every cached passage heading path to a tuple. The regression attempts mutation and proves a later unchanged-byte load remains source-derived. Publishing this fix creates a new head and requires all exact-head CI again.

## 2026-07-18 — B6-T01 design and implementation plan

- Hot paths confirmed in `primary_file_scanner`, `evidence_resolver`, and rule-evidence migration: unchanged primary Markdown was decoded and/or parsed repeatedly.
- Selected a bounded process-local cache of exact-byte source snapshots and immutable `kb-text-core` passages. Each load hashes strict UTF-8 bytes, so preserved mtime/size cannot hide content changes.
- Design: `docs/superpowers/specs/2026-07-18-kaiyuan-primary-passage-cache-design.md`.
- Plan: `docs/superpowers/plans/2026-07-18-kaiyuan-primary-passage-cache.md`.
- Decision: D-014.
- No implementation or completion claim yet. Next exact action: create draft PR, add `tests/test_primary_passage_cache_v2.py`, run focused pytest, and record the expected RED before implementing the cache module.

## 2026-07-18 — B5-T03 merged; B6-T01 started

```text
PR: #15
Final head: dcea5ac9b58cb9621307104b18ea49c4caa2f10b
Governance: 29640418519 — success
Stable Core: 29640418556 — success
Upstream Runtime: 29640418531 — success
Squash merge: 6dd0910a2d6b825904ae8e0dcc7d3f1a75557775
```

B5-T03 merged only to `stable/kaiyuan-v2`. Repository audit kept the legacy primary reference ambiguous and created no migrated evidence or raw-corpus change.

B6-T01 started on `codex/kaiyuan-primary-passage-cache-v2`. Task moved to `IN_PROGRESS` before design. Next action: inventory filesystem parse hot paths and define path/mtime/hash invalidation semantics.

## 2026-07-18 — B5-T03 evidence migration implementation verifying

### TDD and implementation

```text
RED: ModuleNotFoundError: src.rule_engine.rule_evidence_migration
focused GREEN: 4 passed
CLI/audit related: 7 passed
```

- Added a read-only bulk planner using `kb-text-core` primary passages.
- Only a unique exact raw/normalized match can become `migratable`.
- Every proposal is revalidated by the B4 resolver as `citable`.
- Apply writes a separate atomic output and refuses input overwrite.
- Added Typer and argparse `audit-rule-evidence-migration` command.

### Repository audit

```text
source_fingerprint: sha256:f2e01f0cb17d77f9aa441d7e1481ebdae7ad9f340bd1bf7b9c2dd2b0a12ccbdc
total_rules: 4
ambiguous: 1
missing_evidence: 3
migratable: 0
```

The legacy `荧惑守心` anchor occurs in multiple primary passages and remains ambiguous/candidate-only. No migrated fixture or source change was created.

### Local gates

```text
contracts: 6 passed
text-core: 22 passed
downstream: 181 passed
upstream: 49 passed, 3 skipped
```

B5-T03 is `VERIFYING`, not `DONE`. Draft PR #15 targets `stable/kaiyuan-v2`. Remaining work is exact-head CI, independent review, ready and squash merge. No `main`, raw corpus, candidate, ingest, retrieval, Qdrant, or `local_kb_default` change.

### Independent review fixes

Review found one Critical and three Important issues. New tests first reproduced three failures, then fixes:

- apply now binds every plan detail to current index/rule id/before evidence, verifies source fingerprint, rejects duplicate/out-of-range indices, and re-runs the resolver before any write;
- plan/apply output must differ from input and remain outside `kb_root`; plan output is atomic too;
- malformed evidence is `invalid_rule`, while only absent evidence is `missing_evidence`;
- missing/empty primary `kb_root` fails clearly instead of returning healthy unresolved;
- restored candidate-generation CLI message to its original command.

Post-review verification: focused 6 passed; downstream 183 passed; contracts 6 passed; text-core 22 passed; upstream 49 passed, 3 skipped. A new exact-head CI run is required after publishing these fixes.

## 2026-07-18 — B5-T02 merged; B5-T03 started

### B5-T02 final evidence

```text
PR: #14
Final feature head: 05cdf6271b73284e943e357df754292ebc31ade1
Development Governance: 29631008326 — success
Kaiyuan Stable Core: 29631008308 — success
Kaiyuan Upstream Runtime: 29631008338 — success
Squash merge commit: 57da1a8b9afb994b3f3ef0ac1714d14fd4a3d37b
Base: stable/kaiyuan-v2
```

GitHub returned `merged=true` for the expected head after independent review fixes and fresh final-head gates. PR #14 did not target `main` and did not change corpus, candidate, ingest, retrieval, Qdrant schema, or `local_kb_default`.

### B5-T03 start

- Branch: `codex/kaiyuan-rule-evidence-migration-v2` from the actual B5-T02 stable merge commit.
- Task moved to `IN_PROGRESS` before design or implementation.
- Next: inventory legacy rule evidence states, define fail-closed audit/migration design, write implementation plan, and open a draft PR to `stable/kaiyuan-v2` before behavior changes.

## 2026-07-18 — B5-T01 merged; B5-T02 started

### B5-T01 merge evidence

```text
PR: #13
Final feature head: 5e4ef05a3e4c4bfa02334676ef877f1bf1eccc8d
Development Governance: 29625533123 — success
Kaiyuan Stable Core: 29625533107 — success
Kaiyuan Upstream Runtime: 29625533117 — success
Squash merge commit: e4e25ba39d43270b1d2ac54ae3057eb741161b38
Base: stable/kaiyuan-v2
```

GitHub returned `merged=true` for the expected feature head. PR #13 did not target `main`; its changed-file audit contained only rule engine, related tests, and development/spec/plan documents. It did not change raw corpus, candidate flow, ingest, retrieval, Qdrant schema, or `local_kb_default`.

### B5-T02 start

- Branch: `codex/kaiyuan-conflict-resolution-v2` from the actual merged stable commit above.
- Task moved to `IN_PROGRESS` before behavior implementation.
- Selected design: a pure conflict resolver module with deterministic policy keys, explicit manual-review withholding, retained suppressed rows, and group trace.
- Design: `docs/superpowers/specs/2026-07-18-kaiyuan-conflict-resolution-policy-design.md`.
- Plan: `docs/superpowers/plans/2026-07-18-kaiyuan-conflict-resolution-policy.md`.
- Decision: D-012.
- Remaining risk: no B5-T02 behavior has been implemented or verified yet; TDD RED is the next gate.

## 2026-07-18 — B5-T02 conflict resolution implementation verifying

### TDD evidence

```text
RED 1:
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python /tmp/kaiyuan-b5/bin/pytest -q tests/test_conflict_resolution_policy_v2.py
result: collection error, ModuleNotFoundError: src.rule_engine.conflict_resolution

GREEN 1:
same command
result: 14 passed

RED 2:
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python /tmp/kaiyuan-b5/bin/pytest -q tests/test_rule_matcher.py
result: 2 failed, 4 passed
failures: recommendation_status absent; manual_review still returned a formal recommended_rule_id

GREEN 2:
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python /tmp/kaiyuan-b5/bin/pytest -q tests/test_conflict_resolution_policy_v2.py tests/test_rule_matcher.py
result: 20 passed

RED 3 (compatibility self-review):
minimal legacy row without explicit score/priority/evidence raised KeyError: rule_priority

GREEN 3:
normalized compatible defaults onto the copied row before ordering
focused result: 21 passed
```

### Implementation

- Added pure `resolve_rule_conflicts()` with fail-closed row validation.
- Executed `highest_score`, `highest_priority`, `prefer_primary_evidence`, and `manual_review`.
- Added stable rule-id tie-breaking, group-policy consistency checks, suppression metadata, formal/provisional recommendation separation, and group trace.
- Replaced the matcher's report-only conflict block with resolver output while preserving all eligible rows.

### Local regression evidence

```text
downstream: 174 passed
contracts: 6 passed
text-core: 22 passed
upstream: 49 passed, 3 skipped
```

The initial upstream collection failure was environmental: the fresh isolated venv lacked declared upstream dependencies (`qdrant_client`, `requests`, `fastapi`). Installing both repository requirements files resolved collection without code or assertion changes.

### Pre-merge review fixes

Independent review found three Important issues. Each received an observed failing regression test before the fix:

1. `minimal_matcher` coerced `rule_priority` with `int()`, allowing bool/string/float configuration to bypass resolver validation. The matcher now passes the raw value and the resolver alone validates it.
2. The resolver stripped `conflict_group`, incorrectly merging distinct exact strings such as `group-a` and ` group-a`. It now only uses whitespace to recognize an empty group and otherwise preserves the exact string.
3. The matcher attached all conflict reasons to every grouped row. It now maps each multi-row trace to only that exact group, so singleton groups and their top-level recommendation remain clean.

Review-fix RED: 3 failed. Review-fix GREEN: focused 24 passed; downstream 177 passed; contracts 6 passed; text-core 22 passed; upstream 49 passed, 3 skipped.

### Status

- Task is `VERIFYING`, not `DONE`.
- Draft PR: #14, base `stable/kaiyuan-v2`.
- Previous verified implementation head: `fbc114b6ec7841918f8ca041cd6372d429e3fce6`; its three workflows passed before review fixes.
- Changed-file audit is limited to rule engine, focused tests, conflict documentation, task/decision/work log, design and plan. Review threads: 0.
- Remaining: publish review fixes and require fresh final-head workflows; after they pass, re-check threads/diff, mark ready and squash merge.
- No corpus, CText, candidate, ingest, retrieval, Qdrant schema, `main`, or `local_kb_default` change.

## 2026-07-18 — B5-T01 three-valued rule semantics implementation verified

### Scope

- 把规则条件从隐式布尔值升级为 `pass | fail | unknown`。
- 缺失角距、持续时间和必需可见性不再自动视为通过。
- 新增 `insufficient_data`，不改变 B4 citable evidence、candidate、语料或 Qdrant 行为。

### TDD RED evidence

```text
Initial failing-test head: c85e32d704b5bfb42ac75c52aa77e720da259141
Kaiyuan Stable Core run: 29624857624
Observed failure: ModuleNotFoundError: src.rule_engine.conditions
```

新测试先定义了 condition contract、numeric/visibility unknown 语义、聚合状态和输出字段；在实现模块不存在时 downstream job 明确失败。

第二轮回归发现两个旧 fixture 仍编码“缺失测量不影响完整匹配”的旧语义：

```text
Intermediate head: f452aee538bc7c2b07c7a82c377c396328c6c43e
Result: 2 failed, 149 passed
```

根因与处理：

1. page mismatch 规则事件没有 angle/duration。证据仍保持 `page_mismatch`，但 trigger 正确改为 `insufficient_data`。
2. `structured_only_demo` 缺少 angle/duration/visibility。旧 `candidate_only/partial` 期望改为 `insufficient_data`，并断言 unknown condition 列表。

没有降低 B4 evidence mismatch 断言。

### Implementation

- 新增 `src/rule_engine/conditions.py`：
  - `ConditionState`；
  - `ConditionEvaluation`；
  - exact、max numeric、min numeric、required visibility evaluator；
  - missing/empty/bool/nonnumeric/NaN/infinity 的明确 unknown reason；
  - invalid configured threshold 的 deterministic ValueError；
  - 非有限 actual 转为严格 JSON-safe 字符串。
- 扩展 `RuleMatchResult`：
  - `condition_states`；
  - `unknown_conditions`；
  - `failed_conditions`；
  - `trigger_ratio`。
- 重构 `minimal_matcher.py`：
  - 核心 identity fail → `not_matched`；
  - 已知非核心 fail → `partial_match`；
  - 无已知 fail 但存在 unknown → `insufficient_data`；
  - 全部适用条件 pass 后依据 B4 citable evidence 判定 `matched` 或 `candidate_only`；
  - 未配置 target/visibility/threshold 不进入条件集合与分母；
  - unknown 进入分母但不进入 pass 分子；
  - rule trigger body/event_type 必须是非空字符串；
  - malformed related asterism data 不产生未分类异常。

### Implementation verification

```text
Verified implementation head: da007704c7b11a0ed90241f57a4e02062f57a191

Development Governance
run 29625394299
conclusion: success

Kaiyuan Stable Core
run 29625394306
conclusion: success

Kaiyuan Upstream Runtime
run 29625394314
conclusion: success
```

覆盖：

- focused three-valued condition tests；
- strict JSON-safe condition trace；
- invalid trigger/threshold/visibility configuration；
- optional target and `visibility_required=false` omission；
- full downstream regression；
- Python 3.9/3.12 text-core；
- shared contracts；
- strict CText spot checks；
- upstream unit and safety gates；
- Qdrant incremental/retrieval contract；
- B4 candidate roundtrip regression。

### Review status

- D-011 已记录三值聚合决策。
- B5-T01 进入 `VERIFYING`。
- PR #13 仍为 draft。
- 本日志和任务状态提交后必须重新运行 final-head 门禁，才能标记 ready 或合并。
- `main`、raw corpus、candidate flow、Qdrant schema 和 `local_kb_default` 未修改。

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
   - Finding: `candidate_cards.sync_upstream_status()` 为每个 item 调用 legacy helper，新建 retriever且未传 `kb_book_id`。
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
