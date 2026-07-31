# B10 规则审核校准与阈值冻结

## Pilot handoff

1. 两名人工审核者按 `kaiyuan-rule-annotation/v1` 独立标注分层样本。
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

冻结后任何阈值变化必须独立决策，保存 before/after、development、
validation、sealed holdout 影响和既有候选失效范围；不得覆盖旧报告。
