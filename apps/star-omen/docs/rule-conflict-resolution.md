# Rule Conflict Resolution (Sprint 5)

当一个事件命中多条规则时，所有非 `not_matched` 规则都保留在 `matches`。同一
`conflict_group` 必须声明一致的 `resolution_policy`；未知或混合策略明确失败。

支持的策略和确定性排序：

1. `highest_score`：score 降序、priority 升序、primary evidence 优先、rule id 升序。
2. `highest_priority`：priority 升序、score 降序、primary evidence 优先、rule id 升序。
3. `prefer_primary_evidence`：primary evidence 优先、score 降序、priority 升序、rule id 升序。
4. `manual_review`：多条候选时不输出正式推荐；按 highest-score 次序只提供 provisional id。

自动策略的非胜出规则不会被删除，而是标为 `suppressed=true` 并记录
`suppression_reason`。`conflict_trace` 保存候选原顺序、policy 排序、正式/临时选择和
被抑制规则。`recommended_rule_id` 仅表示正式推荐；人工复核时保持 null，避免把
`provisional_recommended_rule_id` 误当研究结论。
