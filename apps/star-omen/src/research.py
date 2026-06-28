from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from src.models import CaseReport, CelestialHistoricalCorrelation, HistoricalEvent
from src.rule_engine.minimal_matcher import match_event_to_rules

DATE_PRECISIONS = {"day", "month", "year", "range", "unknown"}
CALENDAR_SYSTEMS = {"gregorian", "julian", "chinese_lunisolar", "unknown"}
RELATION_TYPES = {"within_rule_window", "same_record", "later_interpretation", "manual_hypothesis", "rejected"}
CONFIDENCES = {"high", "medium", "low"}
STATUSES = {"draft", "reviewed", "published", "rejected"}
EVIDENCE_STATUSES = {"primary_citable", "candidate_only", "missing"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _json_files(root: Path, name: str) -> list[Path]:
    folder = root / name
    if not folder.exists():
        return []
    return sorted(folder.glob("*.json"))


def _model_validate(model_cls: Any, data: dict[str, Any]) -> Any:
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)
    return model_cls.parse_obj(data)


def _load_collection(root: Path, name: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    rows: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for path in _json_files(root, name):
        try:
            obj = load_json(path)
        except Exception as exc:  # pragma: no cover - defensive CLI reporting
            errors.append(f"{path}: invalid json: {exc}")
            continue
        obj_id = obj.get("id") if isinstance(obj, dict) else None
        if not obj_id:
            errors.append(f"{path}: missing id")
            continue
        if path.stem != str(obj_id):
            errors.append(f"{path}: id {obj_id!r} must match filename stem {path.stem!r}")
        rows[str(obj_id)] = {**obj, "_path": str(path)}
    return rows, errors


def _load_rules(rules_path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    try:
        rules = load_json(rules_path)
    except Exception as exc:
        return {}, [f"{rules_path}: invalid rules json: {exc}"]
    if not isinstance(rules, list):
        return {}, [f"{rules_path}: rules file must be a JSON array"]
    return {str(rule.get("id")): rule for rule in rules if isinstance(rule, dict) and rule.get("id")}, []


def validate_research_data(research_root: Path = Path("data/research"), rules_path: Path = Path("data/processed/corpus/sample_rules.json")) -> dict[str, Any]:
    celestial, errors = _load_collection(research_root, "celestial_events")
    historical, hist_errors = _load_collection(research_root, "historical_events")
    correlations, corr_errors = _load_collection(research_root, "correlations")
    rules, rule_errors = _load_rules(rules_path)
    errors.extend(hist_errors)
    errors.extend(corr_errors)
    errors.extend(rule_errors)
    warnings: list[str] = []

    for event_id, event in celestial.items():
        for key in ["body", "event_type", "target_asterism"]:
            if not event.get(key):
                errors.append(f"celestial_event {event_id}: missing required field {key}")

    for event_id, event in historical.items():
        try:
            _model_validate(HistoricalEvent, {k: v for k, v in event.items() if k != "_path"})
        except Exception as exc:
            errors.append(f"historical_event {event_id}: invalid HistoricalEvent: {exc}")
        for key in ["title", "summary", "source_refs"]:
            if not event.get(key):
                errors.append(f"historical_event {event_id}: missing required field {key}")
        for idx, ref in enumerate(event.get("source_refs") or []):
            if not isinstance(ref, dict) or not (ref.get("title") or ref.get("citation")):
                errors.append(f"historical_event {event_id}: source_refs[{idx}] must include title or citation")
        parsed_start = _parse_date(event.get("date_start"))
        if event.get("date_start") and parsed_start is None:
            msg = f"historical_event {event_id}: date_start {event.get('date_start')!r} is not parseable"
            if event.get("date_precision") == "day":
                errors.append(msg)
            else:
                warnings.append(msg)
        if event.get("date_precision") not in DATE_PRECISIONS:
            errors.append(f"historical_event {event_id}: invalid date_precision {event.get('date_precision')!r}")
        if event.get("calendar_system") not in CALENDAR_SYSTEMS:
            errors.append(f"historical_event {event_id}: invalid calendar_system {event.get('calendar_system')!r}")
        if event.get("date_precision") in {"month", "year", "range", "unknown"}:
            warnings.append(f"historical_event {event_id}: date_precision={event.get('date_precision')} may be insufficient for exact time_delta_days")

    for corr_id, corr in correlations.items():
        try:
            _model_validate(CelestialHistoricalCorrelation, {k: v for k, v in corr.items() if k != "_path"})
        except Exception as exc:
            errors.append(f"correlation {corr_id}: invalid CelestialHistoricalCorrelation: {exc}")
        for key in ["confidence", "status", "relation_type", "evidence_status"]:
            if not corr.get(key):
                errors.append(f"correlation {corr_id}: missing required field {key}")
        celestial_id = str(corr.get("celestial_event_id") or "")
        historical_id = str(corr.get("historical_event_id") or "")
        if celestial_id not in celestial:
            errors.append(f"correlation {corr_id}: missing celestial_event_id {celestial_id!r}")
        if historical_id not in historical:
            errors.append(f"correlation {corr_id}: missing historical_event_id {historical_id!r}")
        for rule_id in corr.get("matched_rule_ids") or []:
            if rule_id not in rules:
                errors.append(f"correlation {corr_id}: matched_rule_id {rule_id!r} not found in {rules_path}")
        if corr.get("relation_type") not in RELATION_TYPES:
            errors.append(f"correlation {corr_id}: invalid relation_type {corr.get('relation_type')!r}")
        if corr.get("confidence") not in CONFIDENCES:
            errors.append(f"correlation {corr_id}: invalid confidence {corr.get('confidence')!r}")
        if corr.get("status") not in STATUSES:
            errors.append(f"correlation {corr_id}: invalid status {corr.get('status')!r}")
        if corr.get("evidence_status") not in EVIDENCE_STATUSES:
            errors.append(f"correlation {corr_id}: invalid evidence_status {corr.get('evidence_status')!r}")
        if corr.get("time_delta_days") is None:
            warnings.append(f"correlation {corr_id}: time_delta_days is null; report will state date/window limitations")

    return {
        "ok": not errors,
        "celestial_events_count": len(celestial),
        "historical_events_count": len(historical),
        "correlations_count": len(correlations),
        "errors": errors,
        "warnings": warnings,
    }


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _event_date(celestial_event: dict[str, Any]) -> date | None:
    return _parse_date(celestial_event.get("date_start") or celestial_event.get("datetime_utc"))


def _historical_date(historical_event: dict[str, Any]) -> date | None:
    if historical_event.get("date_precision") != "day":
        return None
    return _parse_date(historical_event.get("date_start"))


def _parse_time_window_days(value: str | None) -> tuple[int | None, int | None]:
    if not value:
        return None, None
    m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*d\s*$", value)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def _computed_evidence_status(match: dict[str, Any]) -> str:
    if match.get("primary_evidence_found") is True:
        return "primary_citable"
    evidence_summary = match.get("evidence_summary") if isinstance(match.get("evidence_summary"), dict) else {}
    if match.get("candidate_only") is True or evidence_summary.get("status") == "candidate_only":
        return "candidate_only"
    return "missing"


def _rule_subset(rules: dict[str, dict[str, Any]], ids: list[str]) -> list[dict[str, Any]]:
    return [rules[rule_id] for rule_id in ids if rule_id in rules]


def _find_correlation(research_root: Path, correlation_id: str | None, correlation_file: Path | None) -> dict[str, Any]:
    if correlation_file:
        return load_json(correlation_file)
    if not correlation_id:
        raise ValueError("provide --correlation-id or --correlation-file")
    path = research_root / "correlations" / f"{correlation_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"correlation not found: {path}")
    return load_json(path)


def build_case_report(
    *,
    correlation_id: str | None = None,
    correlation_file: Path | None = None,
    research_root: Path = Path("data/research"),
    rules_path: Path = Path("data/processed/corpus/sample_rules.json"),
    out_dir: Path = Path("data/research/case_reports"),
) -> dict[str, Any]:
    correlation = _find_correlation(research_root, correlation_id, correlation_file)
    celestial = load_json(research_root / "celestial_events" / f"{correlation['celestial_event_id']}.json")
    historical = load_json(research_root / "historical_events" / f"{correlation['historical_event_id']}.json")
    rules_by_id, errors = _load_rules(rules_path)
    if errors:
        raise ValueError("; ".join(errors))
    rules = list(rules_by_id.values())
    match = match_event_to_rules(event=celestial, rules=rules)
    matched_rule_ids = correlation.get("matched_rule_ids") or match.get("matched_rule_ids") or []
    matched_rules = _rule_subset(rules_by_id, matched_rule_ids)

    limitations = list(correlation.get("caveats") or [])
    c_date = _event_date(celestial)
    h_date = _historical_date(historical)
    computed_delta = (h_date - c_date).days if c_date and h_date else None
    if computed_delta is None:
        limitations.append("日期精度不足或缺少可解析日期，time_delta_days 记为 null，不能做精确应期判断。")
    time_delta_days = correlation.get("time_delta_days") if correlation.get("time_delta_days") is not None else computed_delta

    window_min, window_max = _parse_time_window_days((matched_rules[0] if matched_rules else {}).get("time_window") or match.get("time_window"))
    within_window = None
    if time_delta_days is not None and window_min is not None and window_max is not None:
        within_window = window_min <= int(time_delta_days) <= window_max
    elif matched_rules:
        limitations.append("规则 time_window 或日期精度不足，无法自动判定是否落在应期窗口内。")

    computed_status = _computed_evidence_status(match)
    evidence_status = correlation.get("evidence_status") or computed_status
    if evidence_status == "candidate_only":
        limitations.append("evidence_status=candidate_only：只能作为候选线索，不可作为最终事实证据。")
    if evidence_status == "missing":
        limitations.append("evidence_status=missing：当前缺少可引用古籍证据。")
    if evidence_status != computed_status:
        limitations.append(f"人工记录的 evidence_status={evidence_status} 与机器估计 {computed_status} 不一致，需复核。")

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report_id = correlation["id"]
    title = f"{celestial.get('title') or celestial.get('id')} ↔ {historical.get('title') or historical.get('id')}"
    case_report = {
        "id": report_id,
        "title": title,
        "celestial_event": celestial,
        "historical_events": [historical],
        "correlations": [correlation],
        "matched_rules": matched_rules,
        "evidence_summary": match.get("evidence_summary", {}),
        "machine_assessment": {
            "match_rule": match,
            "computed_evidence_status": computed_status,
            "time_delta_days": time_delta_days,
            "time_window": (matched_rules[0] if matched_rules else {}).get("time_window") or match.get("time_window"),
            "within_rule_window": within_window,
        },
        "human_assessment": {
            "relation_type": correlation.get("relation_type"),
            "confidence": correlation.get("confidence"),
            "status": correlation.get("status"),
            "notes": correlation.get("notes"),
            "caveats": correlation.get("caveats") or [],
        },
        "conclusion": _conclusion(evidence_status, within_window, correlation),
        "limitations": _dedupe(limitations),
        "generated_at": generated_at,
        "report_version": "case-report/v1",
        "source_paths": {
            "correlation": str(research_root / "correlations" / f"{correlation['id']}.json"),
            "celestial_event": str(research_root / "celestial_events" / f"{correlation['celestial_event_id']}.json"),
            "historical_event": str(research_root / "historical_events" / f"{correlation['historical_event_id']}.json"),
            "rules": str(rules_path),
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{report_id}.md"
    json_path = out_dir / f"{report_id}.report.json"
    _model_validate(CaseReport, case_report)
    md_path.write_text(render_case_markdown(case_report), encoding="utf-8")
    write_json(json_path, case_report)
    return {"ok": True, "report_path": str(md_path), "json_report_path": str(json_path), "case_report": case_report}


def _dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        if item and item not in out:
            out.append(item)
    return out


def _conclusion(evidence_status: str, within_window: bool | None, correlation: dict[str, Any]) -> str:
    window_text = "落在应期窗口内" if within_window is True else "未能确认落在应期窗口内" if within_window is False else "应期窗口待判定"
    return (
        f"该案例记录为{correlation.get('relation_type')}类型的研究性关联，{window_text}。"
        f"证据状态为 {evidence_status}，人工置信度为 {correlation.get('confidence')}，状态为 {correlation.get('status')}。"
        "本报告仅记录研究性对应关系，不作因果证明。"
    )


def render_case_markdown(report: dict[str, Any]) -> str:
    celestial = report["celestial_event"]
    historical = report["historical_events"][0]
    corr = report["correlations"][0]
    machine = report["machine_assessment"]
    human = report["human_assessment"]
    evidence_status = corr.get("evidence_status")
    rules = report.get("matched_rules") or []
    rule_lines = "\n".join(f"- `{r.get('id')}`：{r.get('source_text')}；time_window={r.get('time_window')}；severity={r.get('severity')}" for r in rules) or "- 待补匹配规则"
    limitations = "\n".join(f"- {x}" for x in report.get("limitations", [])) or "- 暂无"
    candidate_warning = "\n> **注意：candidate_only 只能作为候选线索，不可作为最终事实证据。**\n" if evidence_status == "candidate_only" else ""
    return f"""# {report['title']}

## 机器可读元数据

- case_id: `{report['id']}`
- correlation_id: `{corr.get('id')}`
- report_version: `{report['report_version']}`
- generated_at: `{report['generated_at']}`
- evidence_status: `{evidence_status}`
- confidence: `{human.get('confidence')}`
- status: `{human.get('status')}`

## 天象事件摘要

- id: `{celestial.get('id')}`
- title: {celestial.get('title') or celestial.get('id')}
- datetime_utc/date_start: {celestial.get('datetime_utc') or celestial.get('date_start')}
- body/event_type/target: {celestial.get('body')} / {celestial.get('event_type')} / {celestial.get('target_asterism')}
- summary: {celestial.get('summary') or celestial.get('notes') or '待补'}

## 匹配规则摘要

{rule_lines}

## 古籍证据状态

- evidence_status: `{evidence_status}`
- machine_computed_evidence_status: `{machine.get('computed_evidence_status')}`
- evidence_summary: `{json.dumps(report.get('evidence_summary', {}), ensure_ascii=False)}`
{candidate_warning}
## 历史事件摘要

- id: `{historical.get('id')}`
- title: {historical.get('title')}
- date_start/date_end: {historical.get('date_start')} / {historical.get('date_end')}
- date_precision: `{historical.get('date_precision')}`
- calendar_system: `{historical.get('calendar_system')}`
- source_date_text: {historical.get('source_date_text') or '待补'}
- dynasty/reign_period/location: {historical.get('dynasty')} / {historical.get('reign_period')} / {historical.get('location')}
- summary: {historical.get('summary')}

## 时间窗口判断

- time_delta_days: `{machine.get('time_delta_days')}`
- time_window: `{machine.get('time_window')}`
- within_rule_window: `{machine.get('within_rule_window')}`

## 人工研究判断

- relation_type: `{human.get('relation_type')}`
- confidence: `{human.get('confidence')}`
- status: `{human.get('status')}`
- notes: {human.get('notes') or '待补'}

## 关联结论

{report.get('conclusion')}

## 置信度

人工置信度为 `{human.get('confidence')}`。该字段由研究者维护，不由系统完全自动判定。

## 限制与待补证据

{limitations}

## 原始 JSON 摘要或引用路径

```json
{json.dumps(report.get('source_paths', {}), ensure_ascii=False, indent=2)}
```
"""


def build_research_index(research_root: Path = Path("data/research")) -> dict[str, Any]:
    celestial, _ = _load_collection(research_root, "celestial_events")
    historical, _ = _load_collection(research_root, "historical_events")
    correlations, _ = _load_collection(research_root, "correlations")
    indexes: list[dict[str, Any]] = []
    for corr_id, corr in sorted(correlations.items()):
        cel = celestial.get(str(corr.get("celestial_event_id")), {})
        hist = historical.get(str(corr.get("historical_event_id")), {})
        report_path = research_root / "case_reports" / f"{corr_id}.md"
        json_path = research_root / "case_reports" / f"{corr_id}.report.json"
        indexes.append({
            "case_id": corr_id,
            "correlation_id": corr_id,
            "title": f"{cel.get('title') or cel.get('id')} ↔ {hist.get('title') or hist.get('id')}",
            "celestial_event_id": corr.get("celestial_event_id"),
            "celestial_event_title": cel.get("title") or cel.get("id"),
            "celestial_event_date_start": cel.get("date_start") or cel.get("datetime_utc"),
            "historical_event_id": corr.get("historical_event_id"),
            "historical_event_title": hist.get("title") or hist.get("id"),
            "historical_event_date_start": hist.get("date_start"),
            "dynasty": hist.get("dynasty"),
            "rule_ids": corr.get("matched_rule_ids") or [],
            "evidence_status": corr.get("evidence_status"),
            "confidence": corr.get("confidence"),
            "status": corr.get("status"),
            "relation_type": corr.get("relation_type"),
            "time_delta_days": corr.get("time_delta_days"),
            "date_precision": hist.get("date_precision"),
            "report_path": str(report_path),
            "json_report_path": str(json_path),
            "updated_at": corr.get("updated_at") or corr.get("created_at"),
        })
    out = {"schema_version": "research-case-index/v1", "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "items": indexes}
    write_json(research_root / "indexes" / "case_index.json", out)
    return out
