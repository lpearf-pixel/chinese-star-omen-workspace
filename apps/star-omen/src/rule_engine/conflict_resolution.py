from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable


SUPPORTED_POLICIES = {
    "highest_score",
    "highest_priority",
    "prefer_primary_evidence",
    "manual_review",
}


@dataclass(frozen=True)
class ConflictResolutionResult:
    matches: list[dict[str, Any]]
    recommended_rule_id: str | None
    provisional_recommended_rule_id: str | None
    recommendation_status: str
    conflict_detected: bool
    conflict_reasons: list[str]
    conflict_trace: list[dict[str, Any]]


def _validated_rows(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for match in matches:
        if not isinstance(match, dict):
            raise ValueError("each conflict match must be a mapping")
        row = dict(match)
        rule_id = row.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise ValueError("rule_id must be a non-empty string")
        rule_id = rule_id.strip()
        if rule_id in seen_ids:
            raise ValueError(f"duplicate rule_id {rule_id!r}")
        seen_ids.add(rule_id)
        row["rule_id"] = rule_id

        priority = row.get("rule_priority", 100)
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise ValueError(f"rule {rule_id!r} rule_priority must be an integer")
        row["rule_priority"] = priority
        score = row.get("match_score", 0.0)
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError(f"rule {rule_id!r} match_score must be finite numeric")
        if not math.isfinite(float(score)):
            raise ValueError(f"rule {rule_id!r} match_score must be finite numeric")
        row["match_score"] = float(score)
        evidence = row.get("primary_evidence_found", False)
        if not isinstance(evidence, bool):
            raise ValueError(
                f"rule {rule_id!r} primary_evidence_found must be boolean"
            )
        row["primary_evidence_found"] = evidence

        policy = row.get("resolution_policy") or "highest_score"
        if not isinstance(policy, str):
            raise ValueError(f"rule {rule_id!r} resolution_policy must be a string")
        policy = policy.strip() or "highest_score"
        if policy not in SUPPORTED_POLICIES:
            raise ValueError(f"unsupported resolution_policy {policy!r}")
        row["resolution_policy"] = policy
        rows.append(row)
    return rows


def _score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -float(row["match_score"]),
        int(row["rule_priority"]),
        -int(row["primary_evidence_found"]),
        row["rule_id"],
    )


def _priority_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(row["rule_priority"]),
        -float(row["match_score"]),
        -int(row["primary_evidence_found"]),
        row["rule_id"],
    )


def _evidence_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -int(row["primary_evidence_found"]),
        -float(row["match_score"]),
        int(row["rule_priority"]),
        row["rule_id"],
    )


POLICY_KEYS: dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]] = {
    "highest_score": _score_key,
    "highest_priority": _priority_key,
    "prefer_primary_evidence": _evidence_key,
    "manual_review": _score_key,
}


def resolve_rule_conflicts(
    matches: list[dict[str, Any]],
) -> ConflictResolutionResult:
    rows = _validated_rows(matches)
    groups: dict[str, list[dict[str, Any]]] = {}
    independent: list[dict[str, Any]] = []
    for row in rows:
        group = row.get("conflict_group")
        if group is None or (isinstance(group, str) and not group.strip()):
            row["resolution_status"] = "independent"
            row["suppressed"] = False
            row["suppression_reason"] = None
            independent.append(row)
            continue
        if not isinstance(group, str):
            raise ValueError(
                f"rule {row['rule_id']!r} conflict_group must be a string or null"
            )
        group = group.strip()
        row["conflict_group"] = group
        groups.setdefault(group, []).append(row)

    selected: list[dict[str, Any]] = list(independent)
    manual_provisional: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    reasons: list[str] = []
    conflict_detected = False

    for group, group_rows in groups.items():
        policies = sorted({row["resolution_policy"] for row in group_rows})
        if len(policies) != 1:
            raise ValueError(
                f"conflict_group {group!r} declares multiple resolution policies: "
                + ", ".join(policies)
            )
        policy = policies[0]
        ordered = sorted(group_rows, key=POLICY_KEYS[policy])
        has_conflict = len(ordered) > 1
        if has_conflict:
            conflict_detected = True
            reasons.append(
                f"conflict_group={group} has {len(ordered)} rules; policy={policy}"
            )

        selected_rule_id: str | None
        provisional_rule_id: str | None = None
        suppressed_ids: list[str] = []
        if policy == "manual_review" and has_conflict:
            selected_rule_id = None
            provisional_rule_id = ordered[0]["rule_id"]
            manual_provisional.append(ordered[0])
            for row in ordered:
                row["resolution_status"] = "manual_review"
                row["suppressed"] = False
                row["suppression_reason"] = None
            status = "manual_review"
        else:
            winner = ordered[0]
            selected.append(winner)
            selected_rule_id = winner["rule_id"]
            winner["resolution_status"] = "selected"
            winner["suppressed"] = False
            winner["suppression_reason"] = None
            for row in ordered[1:]:
                row["resolution_status"] = "suppressed"
                row["suppressed"] = True
                row["suppression_reason"] = (
                    f"selected {selected_rule_id!r} by {policy}"
                )
                suppressed_ids.append(row["rule_id"])
            status = "selected"

        trace.append(
            {
                "conflict_group": group,
                "resolution_policy": policy,
                "candidate_rule_ids": [row["rule_id"] for row in group_rows],
                "ordered_rule_ids": [row["rule_id"] for row in ordered],
                "selected_rule_id": selected_rule_id,
                "provisional_rule_id": provisional_rule_id,
                "suppressed_rule_ids": suppressed_ids,
                "status": status,
            }
        )

    recommendation = min(selected, key=_priority_key) if selected else None
    provisional = (
        min(manual_provisional, key=_priority_key)
        if recommendation is None and manual_provisional
        else None
    )
    if recommendation is not None:
        recommendation_status = "selected"
    elif provisional is not None:
        recommendation_status = "manual_review"
    else:
        recommendation_status = "not_matched"

    return ConflictResolutionResult(
        matches=rows,
        recommended_rule_id=(recommendation or {}).get("rule_id"),
        provisional_recommended_rule_id=(provisional or {}).get("rule_id"),
        recommendation_status=recommendation_status,
        conflict_detected=conflict_detected,
        conflict_reasons=reasons,
        conflict_trace=trace,
    )
