import math

import pytest

from src.rule_engine.conflict_resolution import resolve_rule_conflicts


def _row(
    rule_id: str,
    *,
    score: float = 0.8,
    priority: int = 20,
    evidence: bool = False,
    group: str | None = "group-a",
    policy: str = "highest_score",
) -> dict:
    return {
        "rule_id": rule_id,
        "match_status": "matched" if evidence else "candidate_only",
        "match_score": score,
        "rule_priority": priority,
        "primary_evidence_found": evidence,
        "conflict_group": group,
        "resolution_policy": policy,
    }


@pytest.mark.parametrize(
    ("policy", "rows", "winner"),
    [
        (
            "highest_score",
            [_row("low", score=0.4), _row("high", score=0.9)],
            "high",
        ),
        (
            "highest_priority",
            [
                _row("late", score=0.9, priority=50, policy="highest_priority"),
                _row("early", score=0.4, priority=5, policy="highest_priority"),
            ],
            "early",
        ),
        (
            "prefer_primary_evidence",
            [
                _row(
                    "candidate",
                    score=0.99,
                    priority=1,
                    policy="prefer_primary_evidence",
                ),
                _row(
                    "primary",
                    score=0.2,
                    priority=100,
                    evidence=True,
                    policy="prefer_primary_evidence",
                ),
            ],
            "primary",
        ),
    ],
)
def test_automatic_policy_selects_and_retains_suppressed_rows(policy, rows, winner):
    result = resolve_rule_conflicts(rows)

    assert result.recommended_rule_id == winner
    assert result.recommendation_status == "selected"
    assert [row["rule_id"] for row in result.matches] == [row["rule_id"] for row in rows]
    selected = next(row for row in result.matches if row["rule_id"] == winner)
    suppressed = next(row for row in result.matches if row["rule_id"] != winner)
    assert selected["resolution_status"] == "selected"
    assert selected["suppressed"] is False
    assert suppressed["resolution_status"] == "suppressed"
    assert suppressed["suppressed"] is True
    assert winner in suppressed["suppression_reason"]
    assert result.conflict_trace[0]["resolution_policy"] == policy


def test_policy_ties_end_with_ascending_rule_id():
    rows = [_row("rule-z", evidence=True), _row("rule-a", evidence=True)]

    result = resolve_rule_conflicts(rows)

    assert result.recommended_rule_id == "rule-a"
    assert result.conflict_trace[0]["ordered_rule_ids"] == ["rule-a", "rule-z"]


def test_manual_review_withholds_formal_recommendation_and_exposes_provisional():
    rows = [
        _row("rule-b", score=0.5, policy="manual_review"),
        _row("rule-a", score=0.9, policy="manual_review"),
    ]

    result = resolve_rule_conflicts(rows)

    assert result.recommended_rule_id is None
    assert result.provisional_recommended_rule_id == "rule-a"
    assert result.recommendation_status == "manual_review"
    assert all(row["suppressed"] is False for row in result.matches)
    assert all(row["resolution_status"] == "manual_review" for row in result.matches)
    assert result.conflict_trace[0]["selected_rule_id"] is None
    assert result.conflict_trace[0]["provisional_rule_id"] == "rule-a"


def test_single_manual_review_row_is_selected_without_a_conflict():
    result = resolve_rule_conflicts([_row("only", policy="manual_review")])

    assert result.recommended_rule_id == "only"
    assert result.provisional_recommended_rule_id is None
    assert result.conflict_detected is False


def test_ungrouped_rows_remain_independent_candidates():
    rows = [
        _row("priority-winner", priority=1, group=None),
        _row("score-winner", score=1.0, priority=20, group=None),
    ]

    result = resolve_rule_conflicts(rows)

    assert result.recommended_rule_id == "priority-winner"
    assert all(row["resolution_status"] == "independent" for row in result.matches)
    assert result.conflict_detected is False


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (
            [_row("a"), _row("b", policy="highest_priority")],
            "conflict_group 'group-a' declares multiple resolution policies",
        ),
        ([_row("a", policy="mystery")], "unsupported resolution_policy 'mystery'"),
        ([_row("")], "rule_id must be a non-empty string"),
        ([_row("dup"), _row("dup")], "duplicate rule_id 'dup'"),
        ([_row("a", priority=True)], "rule_priority must be an integer"),
        ([_row("a", score=math.inf)], "match_score must be finite numeric"),
        (
            [{**_row("a"), "primary_evidence_found": 1}],
            "primary_evidence_found must be boolean",
        ),
    ],
)
def test_invalid_resolution_contract_fails_closed(rows, message):
    with pytest.raises(ValueError, match=message):
        resolve_rule_conflicts(rows)
