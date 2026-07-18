from __future__ import annotations

import math

import pytest

from src.rule_engine.conditions import (
    ConditionEvaluation,
    ConditionState,
    evaluate_max_numeric,
    evaluate_min_numeric,
    evaluate_required_visibility,
)
from src.rule_engine.minimal_matcher import match_event_to_rules


RULE = {
    "id": "rule-mars-heart",
    "trigger": {
        "body": "Mars",
        "event_type": "guarding",
        "target": "Heart",
    },
    "effect_domain": ["state"],
    "severity": "high",
    "rule_priority": 10,
    "evidence": {"card_type": "term_card"},
}

COMPLETE_EVENT = {
    "id": "event-mars-heart",
    "body": "Mars",
    "event_type": "guarding",
    "target_asterism": "Heart",
    "related_asterisms": [],
    "angular_distance_deg": 0.8,
    "duration_days": 4,
    "visibility": {"is_visible": True},
}

THRESHOLDS = {
    "guarding": {
        "angular_distance_threshold_deg": 1.2,
        "min_duration_days": 3,
        "visibility_required": True,
    }
}


def test_condition_contract_serializes_stable_states():
    assert [state.value for state in ConditionState] == ["pass", "fail", "unknown"]
    evaluation = ConditionEvaluation(
        name="angular_distance",
        state=ConditionState.UNKNOWN,
        required=True,
        expected={"max_deg": 1.2},
        actual=None,
        reason="missing_value",
    )
    assert evaluation.to_dict() == {
        "state": "unknown",
        "required": True,
        "expected": {"max_deg": 1.2},
        "actual": None,
        "reason": "missing_value",
    }


@pytest.mark.parametrize(
    "value,expected_state,reason",
    [
        (0.8, ConditionState.PASS, "within_maximum"),
        (1.3, ConditionState.FAIL, "above_maximum"),
        (None, ConditionState.UNKNOWN, "missing_value"),
        ("", ConditionState.UNKNOWN, "empty_value"),
        (True, ConditionState.UNKNOWN, "invalid_numeric"),
        ("not-a-number", ConditionState.UNKNOWN, "invalid_numeric"),
        (math.nan, ConditionState.UNKNOWN, "non_finite_numeric"),
        (math.inf, ConditionState.UNKNOWN, "non_finite_numeric"),
    ],
)
def test_max_numeric_condition_is_three_valued(value, expected_state, reason):
    result = evaluate_max_numeric(
        "angular_distance",
        value,
        threshold=1.2,
        expected_key="max_deg",
    )
    assert result.state is expected_state
    assert result.reason == reason


@pytest.mark.parametrize(
    "value,expected_state,reason",
    [
        (4, ConditionState.PASS, "meets_minimum"),
        (2, ConditionState.FAIL, "below_minimum"),
        (None, ConditionState.UNKNOWN, "missing_value"),
        (False, ConditionState.UNKNOWN, "invalid_numeric"),
        ("bad", ConditionState.UNKNOWN, "invalid_numeric"),
    ],
)
def test_min_numeric_condition_is_three_valued(value, expected_state, reason):
    result = evaluate_min_numeric(
        "duration",
        value,
        threshold=3,
        expected_key="min_days",
    )
    assert result.state is expected_state
    assert result.reason == reason


@pytest.mark.parametrize(
    "visibility,expected_state,reason",
    [
        ({"is_visible": True}, ConditionState.PASS, "visible"),
        ({"is_visible": False}, ConditionState.FAIL, "not_visible"),
        ({}, ConditionState.UNKNOWN, "missing_value"),
        (None, ConditionState.UNKNOWN, "missing_value"),
        ({"is_visible": "yes"}, ConditionState.UNKNOWN, "invalid_visibility"),
        (True, ConditionState.UNKNOWN, "invalid_visibility"),
    ],
)
def test_required_visibility_is_three_valued(visibility, expected_state, reason):
    result = evaluate_required_visibility(visibility)
    assert result.state is expected_state
    assert result.reason == reason


def test_invalid_configured_numeric_threshold_is_a_configuration_error():
    with pytest.raises(ValueError, match="angular_distance.*finite numeric threshold"):
        evaluate_max_numeric(
            "angular_distance",
            0.8,
            threshold="not-configured-correctly",
            expected_key="max_deg",
        )


def _run(monkeypatch, event, *, thresholds=THRESHOLDS, citable=False):
    monkeypatch.setattr(
        "src.rule_engine.minimal_matcher.load_event_thresholds",
        lambda: thresholds,
    )
    monkeypatch.setattr(
        "src.rule_engine.minimal_matcher.resolve_evidence",
        lambda evidence, kb_root=None: {
            "status": "citable" if citable else "candidate_only",
            "card_type": "fenjuan" if citable else "term_card",
            "source_locator": "KR3g0018_031" if citable else None,
            "anchor_text": "熒惑守心" if citable else None,
        },
    )
    return match_event_to_rules(event=event, rules=[RULE])


def _match(result):
    assert len(result["matches"]) == 1
    return result["matches"][0]


def test_missing_angular_distance_is_insufficient_data(monkeypatch):
    event = {**COMPLETE_EVENT, "angular_distance_deg": None}
    result = _run(monkeypatch, event)
    match = _match(result)
    assert result["match_status"] == "insufficient_data"
    assert match["condition_states"]["angular_distance"]["state"] == "unknown"
    assert match["unknown_conditions"] == ["angular_distance"]
    assert match["failed_conditions"] == []
    assert match["missing_conditions"] == ["angular_distance"]
    assert match["trigger_ratio"] == pytest.approx(5 / 6, abs=0.0001)


@pytest.mark.parametrize(
    "field,value,condition",
    [
        ("duration_days", None, "duration"),
        ("angular_distance_deg", "bad", "angular_distance"),
        ("angular_distance_deg", math.nan, "angular_distance"),
        ("angular_distance_deg", math.inf, "angular_distance"),
        ("visibility", None, "visibility"),
    ],
)
def test_missing_or_invalid_required_measurement_is_unknown(
    monkeypatch,
    field,
    value,
    condition,
):
    event = {**COMPLETE_EVENT, field: value}
    result = _run(monkeypatch, event)
    match = _match(result)
    assert result["match_status"] == "insufficient_data"
    assert match["condition_states"][condition]["state"] == "unknown"
    assert condition in match["unknown_conditions"]


def test_known_threshold_failure_is_partial_match(monkeypatch):
    event = {**COMPLETE_EVENT, "angular_distance_deg": 2.0}
    result = _run(monkeypatch, event)
    match = _match(result)
    assert result["match_status"] == "partial_match"
    assert match["failed_conditions"] == ["angular_distance"]
    assert match["unknown_conditions"] == []
    assert match["condition_states"]["angular_distance"]["state"] == "fail"


def test_known_failure_takes_precedence_over_another_unknown(monkeypatch):
    event = {
        **COMPLETE_EVENT,
        "angular_distance_deg": 2.0,
        "duration_days": None,
    }
    result = _run(monkeypatch, event)
    match = _match(result)
    assert result["match_status"] == "partial_match"
    assert match["failed_conditions"] == ["angular_distance"]
    assert match["unknown_conditions"] == ["duration"]


def test_required_visibility_false_is_a_known_failure(monkeypatch):
    event = {**COMPLETE_EVENT, "visibility": {"is_visible": False}}
    result = _run(monkeypatch, event)
    match = _match(result)
    assert result["match_status"] == "partial_match"
    assert match["condition_states"]["visibility"]["state"] == "fail"


def test_core_identity_mismatch_is_not_matched(monkeypatch):
    event = {**COMPLETE_EVENT, "target_asterism": "Tail"}
    result = _run(monkeypatch, event)
    assert result["match_status"] == "not_matched"
    assert result["matches"] == []


def test_complete_data_and_citable_evidence_is_matched(monkeypatch):
    result = _run(monkeypatch, COMPLETE_EVENT, citable=True)
    match = _match(result)
    assert result["match_status"] == "matched"
    assert match["trigger_ratio"] == 1.0
    assert match["unknown_conditions"] == []
    assert match["failed_conditions"] == []
    assert match["primary_evidence_found"] is True


def test_complete_data_without_citable_evidence_is_candidate_only(monkeypatch):
    result = _run(monkeypatch, COMPLETE_EVENT, citable=False)
    match = _match(result)
    assert result["match_status"] == "candidate_only"
    assert match["trigger_ratio"] == 1.0
    assert match["candidate_only"] is True


def test_unconfigured_optional_conditions_do_not_enter_ratio(monkeypatch):
    event = {
        "id": COMPLETE_EVENT["id"],
        "body": COMPLETE_EVENT["body"],
        "event_type": COMPLETE_EVENT["event_type"],
        "target_asterism": COMPLETE_EVENT["target_asterism"],
    }
    result = _run(monkeypatch, event, thresholds={"guarding": {}})
    match = _match(result)
    assert set(match["condition_states"]) == {"body", "event_type", "target"}
    assert match["trigger_ratio"] == 1.0
    assert result["match_status"] == "candidate_only"
