# B4 Candidate Sync、可引用证据与黄金评测运行手册

本手册适用于 `stable/kaiyuan-v2` 发布线的 B4 能力。执行前必须先阅读根目录 `AGENTS.md` 和 `docs/development/DEVELOPMENT_MANUAL.md`。

## 1. 安全边界

```text
Release base: stable/kaiyuan-v2
Forbidden merge target: main
Protected legacy collection: local_kb_default
V2 collection: local_kb_kaiyuan_v2
CI collection: random ephemeral collection
```

禁止：

- 下游执行正式 ingest；
- 下游直接写 Qdrant；
- 测试删除、重建或写入 `local_kb_default`；
- pending/rejected/stale candidate 进入正式 evidence；
- 网络错误被转换为 `hits=[]` 或 `sync_status=pending`；
- 自动抓取 CText 或自动改写 raw corpus。

## 2. Candidate 标准流程

```text
1. downstream generate
2. copy to upstream incoming
3. upstream validate
4. manual review
5. change review_status to approved or rejected
6. upstream promote approved
7. upstream ingest into v2 collection
8. downstream sync status
9. verify official retrieval and citable primary source
```

### 2.1 生成候选卡

从 workspace 根目录：

```bash
make generate-candidate
```

等价命令：

```bash
cd apps/star-omen
python -m src.cli generate-candidate-card \
  --query "荧惑守心" \
  --book-id kaiyuan_zhanjing \
  --out-dir data/generated_candidates/extract_cards/kaiyuan_zhanjing
```

输出必须保持：

```text
evidence_level=candidate
source_namespace=downstream_generated
review_status=pending
sync_status=pending
```

生成失败或上游 meta 不可用时，可以离线完成原文抽取，但必须在 candidate 中明确记录 meta unavailable，不能伪造成功版本。

### 2.2 复制到上游 incoming

```bash
mkdir -p apps/local-kb-unified/incoming/downstream_candidates/codex-ready
rsync -av \
  apps/star-omen/data/generated_candidates/extract_cards/kaiyuan_zhanjing/ \
  apps/local-kb-unified/incoming/downstream_candidates/codex-ready/
```

`incoming/downstream_candidates` 永远不是正式 ingest source。

### 2.3 校验

```bash
make validate-candidates
```

校验失败时不要手工绕过。修复 candidate frontmatter、manifest、stable ID、anchor 或 hash 后重新执行。

### 2.4 人工审核

只允许显式设置：

```yaml
review_status: approved
```

或：

```yaml
review_status: rejected
```

不得由生成器自动批准。

### 2.5 Promote

```bash
make promote-candidates
```

只有 approved candidate 会被复制到上游 `data/generated`。Promote 后应为：

```text
evidence_level=primary
source_namespace=official
generated_status=promoted
review_status=approved
```

Promote 不自动执行 ingest。

### 2.6 Ingest

确认环境默认 collection 为 v2：

```bash
export KB_SEARCH_DEFAULT_COLLECTION=local_kb_kaiyuan_v2
```

然后执行上游 ingest。任何命令输出如果显示目标为 `local_kb_default`，立即停止。

增量行为：

```text
unchanged hash → skip
new passage → insert
changed passage → upsert
removed v2-managed passage → delete stale
```

空语料、embedding 失败或 upsert 失败时不得执行 stale delete，也不得发布新的成功 manifest。

### 2.7 Sync

```bash
make sync
```

成功报告：

```text
schema_version=candidate-sync-report/v2
run_status=ok
updated={merged,needs_review,pending,stale}
error=null
```

运行错误：

```text
run_status=error
error.code=authentication_failed|upstream_unavailable|timeout|contract_error|collection_not_found|invalid_response
```

运行错误时所有 candidate manifest 和原 `sync_status` 必须保持不变。

## 3. Sync 状态解释

| 状态 | 含义 | 后续动作 |
|---|---|---|
| `pending` | 上游健康查询成功，但没有正式同一候选 | 审核、promote、ingest 后再 sync |
| `merged` | 正式 extract card 与 candidate content hash 一致 | 保留 provenance，可退出 overlay |
| `needs_review` | 上游有同主题正式卡，但 hash/anchor 不一致 | 人工比对版本与校勘记录 |
| `stale` | 本地 candidate card、source、anchor 或 hash 已漂移 | 重新生成或人工修复，不得直接 promote |

网络错误不是上述任何状态。

## 4. 可引用证据校验

命令：

```bash
cd apps/star-omen
python -m src.cli resolve-evidence \
  --rule path/to/rule.json \
  --kb-root path/to/sources \
  --strict
```

只有以下全部通过才能得到 `status=citable`：

```text
path
card_type
book
locator
page
paragraph
heading
anchor
hash
```

失败状态：

| 状态 | 含义 |
|---|---|
| `candidate_only` | 非 primary，或 primary 引用字段尚不完整 |
| `missing_source` | 文件不存在或不可读 |
| `source_outside_root` | 路径逃逸 KB root |
| `book_mismatch` | book id 与源路径不一致 |
| `card_type_mismatch` | 声明类型与路径类型不一致 |
| `locator_mismatch` | canonical locator 不一致 |
| `page_mismatch` | 页码不存在或不属于 locator |
| `paragraph_mismatch` | 段落索引不存在或锚点多义 |
| `heading_mismatch` | 标题层级不一致 |
| `anchor_mismatch` | 原文或规范化锚点无法定位 |
| `hash_mismatch` | 声明 hash 与 anchor/passage 不一致 |

不要通过删除 page、anchor 或 hash 字段把 mismatch 降级为“可引用”。旧最小引用可以继续加载，但只能是 candidate-only，直到补齐字段。

## 5. 规则证据审计

```bash
cd apps/star-omen
python -m src.cli audit-rules \
  --rules-path data/processed/corpus/sample_rules.json \
  --kb-root data/sources
```

报告应包含：

```text
total_rules
citable
candidate_only
missing_evidence
status_counts
details[].candidate_reason
details[].trace.checks
```

修复顺序：

1. `missing_evidence`
2. `missing_source` / `source_outside_root`
3. book/locator/page/paragraph/heading mismatch
4. anchor/hash mismatch
5. candidate-only primary fields

## 6. 黄金检索评测

```bash
cd apps/star-omen
python -m src.cli eval-corpus \
  --eval-path eval/corpus_eval_cases.yaml \
  --collection local_kb_kaiyuan_v2
```

核心指标：

```text
stage1_pool_match
stage2_pool_match
official_primary_used
fallback_used
source_locator_match
page_marker_match
heading_match
citable_fields_present
pollution_detected
failure_reasons
pass
```

正式 primary 必需的 case 不得依赖 filesystem fallback。`prompt_asset`、`nav`、`qa_example` 或 pending candidate 出现在 evidence 输出中必须失败。

## 7. CText 定点比对

```bash
python scripts/audit_kaiyuan_spot_checks.py \
  --config corpus/kaiyuan_zhanjing/ctext_spot_checks.json \
  --corpus-root apps/local-kb-unified/data/sources/古籍/唐開元占經 \
  --strict \
  --out /tmp/kaiyuan-ctext-spot-check-report.json
```

报告必须显示：

```text
network_accessed=false
local_raw_preserved=true
all_matched=true
```

允许状态：

```text
exact_raw
exact_normalized
```

其他状态进入人工审计：

```text
mismatch
missing_source
missing_page
invalid
```

CText 定点比对只验证人工记录的片段，不访问网络、不批量抓取、不自动修正文献。

## 8. CI 门禁

B4 合并前必须确认最新 head 的以下 workflow 全绿：

```text
Development Governance
Kaiyuan Stable Core
Kaiyuan Upstream Runtime
```

其中至少包含：

```text
governance checker unit tests
contracts tests
text-core Python 3.9
text-core Python 3.12
downstream tests
CText strict spot checks
upstream tests
Docker Compose validation
secret and machine-path scan
Qdrant incremental integration
Qdrant retrieval contract integration
candidate roundtrip integration
```

不得引用旧 commit 的绿色结果作为最新 head 的验收证据。

## 9. Candidate roundtrip 故障排查

专用测试覆盖：

```text
generate
→ approve
→ promote
→ collect desired corpus
→ incremental ingest to ephemeral Qdrant
→ structured retrieve official extract card
→ downstream sync merged
→ timeout preserves manifest bytes
→ linked primary resolves citable
```

失败时按顺序检查：

1. `APP_CONFIG_PATH` 是否指向 `apps/star-omen/config/config.yaml`；
2. Qdrant health；
3. random collection 是否创建；
4. candidate frontmatter 与 manifest hash；
5. promote 输出目录；
6. desired item 是否带 `review_status=approved`；
7. structured retrieval 是否使用 `extract_card`；
8. citable primary 是否带 page/paragraph/heading/anchor/hash。

CI 会上传 `candidate-roundtrip.log`，先阅读完整 traceback，再修复根因。

## 10. 回滚

B4 不迁移或覆盖 `local_kb_default`。回滚步骤：

1. 将服务默认 collection 切回原先值；
2. 保留 `local_kb_kaiyuan_v2` 供调查，不立即删除；
3. 回滚 `stable/kaiyuan-v2` 的 B4 squash commit；
4. 恢复上一个成功 corpus manifest；
5. 重新运行 health/meta/retrieval smoke；
6. 在 `WORK_LOG.md` 记录原因、受影响版本和恢复证据。

## 11. 发布完成定义

B4 可发布必须同时满足：

- PR base 为 `stable/kaiyuan-v2`；
- PR 不修改 `main`；
- 所有任务在 `TASKS.md` 为 `DONE`；
- 最新 head 全部 required CI 通过；
- `WORK_LOG.md` 记录 commit、workflow run 和测试结果；
- PR 不触碰 `local_kb_default`；
- raw corpus 未被静默改写；
- CText 定点比对报告通过；
- PR review 完成并 squash 合入稳定分支。
