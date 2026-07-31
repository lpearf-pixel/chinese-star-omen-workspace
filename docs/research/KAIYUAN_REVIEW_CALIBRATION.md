# B10 规则审核校准与阈值冻结

## Pilot handoff

项目已为 `pilot:kaiyuan-b10-pr-c-v1` 生成两个匿名席位：

```text
reviewer_a = reviewer:anon:a3ed615d9706befdec85569f
reviewer_b = reviewer:anon:c6d751fedc80e326e652a5ef
```

它们记录在 `eval/rules/v2/manifests/reviewer-slots.json`。审核者不需要
GitHub、邮箱或任何现成账号；把 A、B 工作表分别交给两位不同的真人即可。
席位 ID 只是审计键，不证明已经审核，也不能由同一人同时填写两席。

1. 两名人工审核者分别使用项目分配的 A/B 匿名席位，按
   `kaiyuan-rule-annotation/v1` 独立标注分层样本。
2. 保存每项 expected/predicted formal-candidate、citation eligibility、
   disagreement 和 category；不删除困难项。
3. development 用于修订手册，validation 用于冻结判断；日常校准不得
   打开 holdout labels。
4. 报告必须保留 TP/FP/FN/TN、case 总数、分类分母、precision、recall、
   agreement 和 citable false-positive 计数。
5. formal-candidate precision 下限不得低于 `0.90`，citable false
   positive 必须为 `0`。

## Freeze authority

缺少 reviewed fixtures、passing validation report、真实批准人或 decision
reference 时，生成物只能是 `needs_human_approval`。只有 `approved`
canonical `threshold-freeze.json` 可解除 PR-D 阻塞。

生成匿名席位不会改变以上状态，也不得写成 `human_review_completed=true`。

冻结后任何阈值变化必须独立决策，保存 before/after、development、
validation、sealed holdout 影响和既有候选失效范围；不得覆盖旧报告。

## Real-corpus worksheet preparation

仓库不保存全书原文，以下命令必须在持有 `_kb-ingest/docs` 的本机执行。
生成物包含原文片段，只能保存在调用方选择的本地目录，不得提交 Git。

先从真实原始字节生成 inventory：

```bash
cd /实际路径/chinese-star-omen-workspace

export KAIYUAN_KB_ROOT="/实际路径/_kb-ingest/docs"
export KAIYUAN_PILOT_ROOT="${TMPDIR:-/tmp}/kaiyuan-b10-pilot"
mkdir -p "$KAIYUAN_PILOT_ROOT"

PYTHONPATH="apps/star-omen:packages/kb-text-core/python:packages/kb-contracts/python" \
python3 -m src.rule_structuring.pilot_handoff inventory \
  --kb-root "$KAIYUAN_KB_ROOT" \
  --out "$KAIYUAN_PILOT_ROOT/passage-inventory.json"
```

人工从 inventory 选择真实 passage，并将选择保存为
`$KAIYUAN_PILOT_ROOT/pilot-selection.json`。选择文件必须使用
`pilot-selection/v1`，绑定 inventory 的 exact `source_fingerprint`，case
按 `case_id` 排序且 passage 不重复。每个 case 明确填写：

```text
case_id
passage_id
split = development | validation
celestial_categories
relation_terms
sentence_complexity = simple | compound | cross_passage
computability = computable | partially_computable | not_computable
evidence_risk = low | medium | high
special_case_tags = ambiguous | duplicate | conflict
```

整体选择必须覆盖黄金集政策中的九类天象、八个关系词、全部复杂度、
可计算性、风险、三种困难项、两个 split 和至少两个卷。工具不会从原文
猜这些标签，也不会接受 holdout、source-ambiguous passage、未知 passage
或已漂移 inventory。

选择复核后，一条命令生成两份内容相同、席位独立且完全未标注的工作表：

```bash
PYTHONPATH="apps/star-omen:packages/kb-text-core/python:packages/kb-contracts/python" \
python3 -m src.rule_structuring.pilot_handoff worksheets \
  --kb-root "$KAIYUAN_KB_ROOT" \
  --selection "$KAIYUAN_PILOT_ROOT/pilot-selection.json" \
  --reviewer-slots "eval/rules/v2/manifests/reviewer-slots.json" \
  --out-dir "$KAIYUAN_PILOT_ROOT/worksheets"
```

输出为 `reviewer_a.json` 与 `reviewer_b.json`。两者绑定同一
`shared_content_sha256`，但各自绑定不同匿名 reviewer ID；所有
`expected_label` 均为 `null`，`human_review_completed=false`。工具拒绝
覆盖既有输出。生成工作表仍不构成人工审核或阈值批准。
