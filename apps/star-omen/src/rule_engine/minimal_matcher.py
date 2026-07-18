from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.connectors.evidence_resolver import resolve_evidence
from src.connectors.kb_contract import is_citable_evidence
from src.rule_engine.conditions import (
    ConditionEvaluation,
    ConditionState,
    evaluate_exact,
    evaluate_max_numeric,
    evaluate_min_numeric,
    evaluate_required_visibility,
)
from src.rule_engine.match_result import RuleMatchResult
from src.rule_engine.scoring import compute_match_score
from src.rule_engine.thresholds import load_event_thresholds

CORE_CONDITIONS = {"body", "event_type", "target"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _target_match(trigger_target: str | None, event: dict[str, Any]) -> bool:
    if not trigger_target:
        return True
    target_asterism = str(event.get("target_asterism") or "")
    related = [str(value) for value in (event.get("related_asterisms") or [])]
    notes = str(event.get("notes") or "")

    if trigger_target == "multi_planet":
        return len(related) >= 5 or "五星" in notes
    return trigger_target == target_asterism or trigger_target in related


def _target_actual(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_asterism": event.get("target_asterism"),
        "related_asterisms": list(event.get("related_asterisms") or []),
    }


def _rule_thresholds(
    all_thresholds: dict[str, Any],
    event_type: str,
) -> dict[str, Any]:
    configured = all_thresholds.get(event_type, {})
    if configured is None:
        return {}
    if not isinstance(configured, dict):
        raise ValueError(
            f"event threshold configuration for {event_type!r} must be a mapping"
        )
    return configured


def _build_condition_evaluations(
    *,
    event: dict[str, Any],
    trigger_body: str,
    trigger_event_type: str,
    trigger_target: Any,
    event_thresholds: dict[str, Any],
) -> list[ConditionEvaluation]:
    event_body = str(event.get("body") or "")
    event_type = str(event.get("event_type") or "")
    evaluations = [
        evaluate_exact("body", event_body, expected=trigger_body),
        evaluate_exact("event_type", event_type, expected=trigger_event_type),
    ]

    if trigger_target is not None and str(trigger_target) != "":
        expected_target = str(trigger_target)
        evaluations.append(
            evaluate_exact(
                "target",
                _target_actual(event),
                expected=expected_target,
                passed=_target_match(expected_target, event),
                pass_reason="target_match",
                fail_reason="target_mismatch",
            )
        )

    if "angular_distance_threshold_deg" in event_thresholds:
        evaluations.append(
            evaluate_max_numeric(
                "angular_distance",
                event.get("angular_distance_deg"),
                threshold=event_thresholds.get("angular_distance_threshold_deg"),
                expected_key="max_deg",
            )
        )

    if "min_duration_days" in event_thresholds:
        evaluations.append(
            evaluate_min_numeric(
                "duration",
                event.get("duration_days"),
                threshold=event_thresholds.get("min_duration_days"),
                expected_key="min_days",
            )
        )

    if "visibility_required" in event_thresholds:
        visibility_required = event_thresholds.get("visibility_required")
        if not isinstance(visibility_required, bool):
            raise ValueError("visibility_required must be a boolean")
        if visibility_required:
            evaluations.append(evaluate_required_visibility(event.get("visibility")))

    return evaluations


def _aggregate_status(
    evaluations: list[ConditionEvaluation],
    *,
    primary_evidence_found: bool,
) -> str:
    if any(
        evaluation.name in CORE_CONDITIONS
        and evaluation.state is ConditionState.FAIL
        for evaluation in evaluations
    ):
        return "not_matched"
    if any(
        evaluation.name not in CORE_CONDITIONS
        and evaluation.state is ConditionState.FAIL
        for evaluation in evaluations
    ):
        return "partial_match"
    if any(
        evaluation.state is ConditionState.UNKNOWN for evaluation in evaluations
    ):
        return "insufficient_data"
    return "matched" if primary_evidence_found else "candidate_only"


def match_event_to_rules(
    *,
    event: dict[str, Any],
    rules: list[dict[str, Any]],
    kb_root: str | Path | None = None,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    thresholds = load_event_thresholds()
    if not isinstance(thresholds, dict):
        raise ValueError("event threshold configuration must be a mapping")

    for rule in rules:
        trigger = rule.get("trigger") or {}
        if not isinstance(trigger, dict):
            raise ValueError("rule trigger must be a mapping")
        trigger_body = str(trigger.get("body") or "")
        trigger_event_type = str(trigger.get("event_type") or "")
        trigger_target = trigger.get("target")
        event_thresholds = _rule_thresholds(thresholds, trigger_event_type)

        evaluations = _build_condition_evaluations(
            event=event,
            trigger_body=trigger_body,
            trigger_event_type=trigger_event_type,
            trigger_target=trigger_target,
            event_thresholds=event_thresholds,
        )
        condition_states = {
            evaluation.name: evaluation.to_dict() for evaluation in evaluations
        }
        failed_conditions = [
            evaluation.name
            for evaluation in evaluations
            if evaluation.state is ConditionState.FAIL
        ]
        unknown_conditions = [
            evaluation.name
            for evaluation in evaluations
            if evaluation.state is ConditionState.UNKNOWN
        ]
        missing_conditions = [
            evaluation.name
            for evaluation in evaluations
            if evaluation.state is not ConditionState.PASS
        ]
        pass_count = sum(
            1 for evaluation in evaluations if evaluation.state is ConditionState.PASS
        )
        trigger_ratio = pass_count / len(evaluations) if evaluations else 0.0

        evidence_obj = rule.get("evidence")
        resolved_evidence = (
            resolve_evidence(evidence_obj, kb_root=kb_root)
            if isinstance(evidence_obj, dict)
            else None
        )
        evidence_status = (resolved_evidence or {}).get("status", "missing")
        primary_evidence_found = bool(
            resolved_evidence and is_citable_evidence(resolved_evidence)
        )
        used_structured_fallback = evidence_status == "candidate_only"
        match_status = _aggregate_status(
            evaluations,
            primary_evidence_found=primary_evidence_found,
        )

        match_score = compute_match_score(
            trigger_ratio=trigger_ratio,
            primary_evidence_found=primary_evidence_found,
            used_structured_fallback=used_structured_fallback,
        )
        trace = (
            resolved_evidence.get("trace")
            if isinstance(resolved_evidence, dict)
            and isinstance(resolved_evidence.get("trace"), dict)
            else {}
        )

        result = RuleMatchResult(
            rule_id=rule.get("id"),
            match_status=match_status,
            match_score=match_score,
            trigger_match_reason={
                "body": f"{event.get('body')} == {trigger_body}",
                "event_type": (
                    f"{event.get('event_type')} == {trigger_event_type}"
                ),
                "target": trigger_target,
            },
            missing_conditions=missing_conditions,
            conflicting_conditions=[],
            thresholds_used=event_thresholds,
            effect_domain=rule.get("effect_domain", []),
            severity=rule.get("severity"),
            time_window=rule.get("time_window"),
            evidence_summary={
                "status": evidence_status,
                "candidate_reason": (resolved_evidence or {}).get(
                    "candidate_reason"
                ),
                "card_type": (resolved_evidence or {}).get("card_type"),
                "source_locator": (resolved_evidence or {}).get(
                    "source_locator"
                ),
                "page_marker": (resolved_evidence or {}).get("page_marker"),
                "paragraph_index": (resolved_evidence or {}).get(
                    "paragraph_index"
                ),
                "anchor_text": (resolved_evidence or {}).get("anchor_text"),
                "validation_version": trace.get("validation_version"),
                "checks": trace.get("checks", {}),
            },
            primary_evidence_found=primary_evidence_found,
            candidate_only=not primary_evidence_found,
            rule_priority=int(rule.get("rule_priority", 100)),
            conflict_group=rule.get("conflict_group"),
            resolution_policy=str(rule.get("resolution_policy", "highest_score")),
            condition_states=condition_states,
            unknown_conditions=unknown_conditions,
            failed_conditions=failed_conditions,
            trigger_ratio=round(trigger_ratio, 4),
        )
        matches.append(result.to_dict())

    ranked_matches = [
        match for match in matches if match.get("match_status") != "not_matched"
    ]
    ranked_matches.sort(
        key=lambda match: (
            match.get("rule_priority", 100),
            -float(match.get("match_score", 0)),
        ),
        reverse=False,
    )

    conflict_happened = False
    conflict_reasons: list[str] = []
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in ranked_matches:
        group = str(row.get("conflict_group") or "")
        if not group:
            continue
        groups.setdefault(group, []).append(row)
    for group, rows in groups.items():
        if len(rows) > 1:
            conflict_happened = True
            conflict_reasons.append(
                f"conflict_group={group} has {len(rows)} rules"
            )
            for row in rows:
                row["conflicting_conditions"] = list(conflict_reasons)

    recommended = ranked_matches[0] if ranked_matches else {}
    return {
        "event_id": event.get("id"),
        "matched_rule_ids": [match["rule_id"] for match in ranked_matches],
        "match_status": recommended.get("match_status", "not_matched"),
        "match_score": recommended.get("match_score", 0.0),
        "trigger_match_reason": recommended.get("trigger_match_reason", {}),
        "condition_states": recommended.get("condition_states", {}),
        "unknown_conditions": recommended.get("unknown_conditions", []),
        "failed_conditions": recommended.get("failed_conditions", []),
        "trigger_ratio": recommended.get("trigger_ratio", 0.0),
        "missing_conditions": recommended.get("missing_conditions", []),
        "conflicting_conditions": recommended.get("conflicting_conditions", []),
        "thresholds_used": recommended.get("thresholds_used", {}),
        "effect_domain": recommended.get("effect_domain", []),
        "severity": recommended.get("severity"),
        "time_window": recommended.get("time_window"),
        "evidence_summary": recommended.get("evidence_summary", {}),
        "primary_evidence_found": recommended.get(
            "primary_evidence_found",
            False,
        ),
        "candidate_only": recommended.get("candidate_only", True),
        "matches": ranked_matches,
        "conflict_detected": conflict_happened,
        "conflict_reasons": conflict_reasons,
        "recommended_rule_id": recommended.get("rule_id"),
    }


def run_match_rule(
    *,
    event_path: Path,
    rules_path: Path = Path("data/processed/corpus/sample_rules.json"),
    kb_root: str | Path | None = None,
) -> dict[str, Any]:
    event = load_json(event_path)
    rules = load_json(rules_path)
    if not isinstance(rules, list):
        raise ValueError("rules file must be a list")
    return match_event_to_rules(event=event, rules=rules, kb_root=kb_root)
