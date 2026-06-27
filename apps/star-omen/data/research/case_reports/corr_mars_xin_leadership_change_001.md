# 荧惑守心研究样例天象 ↔ 中枢权力变动样例历史事件

## 机器可读元数据

- case_id: `corr_mars_xin_leadership_change_001`
- correlation_id: `corr_mars_xin_leadership_change_001`
- report_version: `case-report/v1`
- generated_at: `2026-06-27T15:08:13.464595Z`
- evidence_status: `candidate_only`
- confidence: `low`
- status: `draft`

## 天象事件摘要

- id: `mars_guarding_xin_001`
- title: 荧惑守心研究样例天象
- datetime_utc/date_start: 2026-03-11T12:00:00Z
- body/event_type/target: mars / guarding / xin_xiu
- summary: 用于研究案例报告流程的最小样例天象。

## 匹配规则摘要

- `rule_mars_guarding_xin_001`：荧惑守心；time_window=0-90d；severity=high

## 古籍证据状态

- evidence_status: `candidate_only`
- machine_computed_evidence_status: `primary_citable`
- evidence_summary: `{"status": "citable", "card_type": "fenjuan", "source_locator": "卷十二/荧惑占/第三段", "anchor_text": "荧惑守心"}`

> **注意：candidate_only 只能作为候选线索，不可作为最终事实证据。**

## 历史事件摘要

- id: `hist_sample_leadership_change_001`
- title: 中枢权力变动样例历史事件
- date_start/date_end: 2026-04-15 / None
- date_precision: `day`
- calendar_system: `gregorian`
- source_date_text: 样例日期，待补真实史料
- dynasty/reign_period/location: sample / None / sample capital
- summary: 用于演示天象—规则—证据—历史事件—报告链路的中性样例。

## 时间窗口判断

- time_delta_days: `35`
- time_window: `0-90d`
- within_rule_window: `True`

## 人工研究判断

- relation_type: `within_rule_window`
- confidence: `low`
- status: `draft`
- notes: 研究性关联样例，不表达因果证明。

## 关联结论

该案例记录为within_rule_window类型的研究性关联，落在应期窗口内。证据状态为 candidate_only，人工置信度为 low，状态为 draft。本报告仅记录研究性对应关系，不作因果证明。

## 置信度

人工置信度为 `low`。该字段由研究者维护，不由系统完全自动判定。

## 限制与待补证据

- 样例 correlation，仅用于验证报告链路。
- 历史 source_refs 为 placeholder，待补真实史料。
- evidence_status=candidate_only：只能作为候选线索，不可作为最终事实证据。
- 人工记录的 evidence_status=candidate_only 与机器估计 primary_citable 不一致，需复核。

## 原始 JSON 摘要或引用路径

```json
{
  "correlation": "data/research/correlations/corr_mars_xin_leadership_change_001.json",
  "celestial_event": "data/research/celestial_events/mars_guarding_xin_001.json",
  "historical_event": "data/research/historical_events/hist_sample_leadership_change_001.json",
  "rules": "data/processed/corpus/sample_rules.json"
}
```
