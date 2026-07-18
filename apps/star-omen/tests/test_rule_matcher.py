import json
from pathlib import Path

import pytest

from src.rule_engine.minimal_matcher import run_match_rule


def test_match_rule_minimal_closure_outputs_required_fields():
    out = run_match_rule(event_path=Path("data/examples/events/mars_guarding_xin_demo.json"))
    assert "rule_mars_guarding_xin_001" in out["matched_rule_ids"]
    assert "thresholds_used" in out
    row = out["matches"][0]
    for field in [
        "trigger_match_reason",
        "condition_states",
        "unknown_conditions",
        "failed_conditions",
        "trigger_ratio",
        "match_status",
        "match_score",
        "missing_conditions",
        "conflicting_conditions",
        "thresholds_used",
        "effect_domain",
        "severity",
        "time_window",
        "evidence_summary",
        "primary_evidence_found",
        "candidate_only",
    ]:
        assert field in row


def test_match_rule_moon_event_matches_moon_rule():
    out = run_match_rule(event_path=Path("data/examples/events/moon_invading_xin_demo.json"))
    assert "rule_moon_invading_xin_001" in out["matched_rule_ids"]


def test_match_rule_jupiter_saturn_conjunction():
    out = run_match_rule(
        event_path=Path("data/examples/events/jupiter_saturn_conjunction_demo.json")
    )
    assert "rule_jupiter_saturn_conjunction_001" in out["matched_rule_ids"]


def test_match_rule_conflict_resolution_and_sorting():
    out = run_match_rule(
        event_path=Path("data/examples/events/mars_guarding_xin_demo.json"),
        rules_path=Path("data/examples/rules/conflict_rules_demo.json"),
    )
    assert out["conflict_detected"] is True
    assert out["recommended_rule_id"] == "rule_mars_guarding_xin_high_priority"
    assert out["matched_rule_ids"][0] == "rule_mars_guarding_xin_high_priority"
    assert out["recommendation_status"] == "selected"
    assert out["provisional_recommended_rule_id"] is None
    assert out["conflict_trace"][0]["selected_rule_id"] == (
        "rule_mars_guarding_xin_high_priority"
    )
    suppressed = next(
        row
        for row in out["matches"]
        if row["rule_id"] == "rule_mars_guarding_xin_low_priority"
    )
    assert suppressed["suppressed"] is True
    assert suppressed["resolution_status"] == "suppressed"


def test_match_rule_manual_review_withholds_recommendation(tmp_path):
    rules = json.loads(
        Path("data/examples/rules/conflict_rules_demo.json").read_text(
            encoding="utf-8"
        )
    )
    for rule in rules:
        rule["resolution_policy"] = "manual_review"
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")

    out = run_match_rule(
        event_path=Path("data/examples/events/mars_guarding_xin_demo.json"),
        rules_path=rules_path,
    )

    assert out["conflict_detected"] is True
    assert out["recommended_rule_id"] is None
    assert out["provisional_recommended_rule_id"] is not None
    assert out["recommendation_status"] == "manual_review"
    assert all(row["suppressed"] is False for row in out["matches"])
    assert all(row["resolution_status"] == "manual_review" for row in out["matches"])


def test_matcher_does_not_coerce_invalid_rule_priority(tmp_path):
    rules = json.loads(
        Path("data/examples/rules/conflict_rules_demo.json").read_text(
            encoding="utf-8"
        )
    )
    rules[0]["rule_priority"] = True
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="rule_priority must be an integer"):
        run_match_rule(
            event_path=Path("data/examples/events/mars_guarding_xin_demo.json"),
            rules_path=rules_path,
        )


def test_conflict_reasons_do_not_leak_to_singleton_group(tmp_path):
    rules = json.loads(
        Path("data/examples/rules/conflict_rules_demo.json").read_text(
            encoding="utf-8"
        )
    )
    singleton = dict(rules[0])
    singleton["id"] = "singleton-winner"
    singleton["rule_priority"] = 1
    singleton["conflict_group"] = "singleton-group"
    rules.append(singleton)
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")

    out = run_match_rule(
        event_path=Path("data/examples/events/mars_guarding_xin_demo.json"),
        rules_path=rules_path,
    )

    assert out["recommended_rule_id"] == "singleton-winner"
    winner = next(row for row in out["matches"] if row["rule_id"] == "singleton-winner")
    assert winner["conflicting_conditions"] == []
    assert out["conflicting_conditions"] == []


def test_match_rule_structured_only_event_is_insufficient_data():
    out = run_match_rule(
        event_path=Path("data/examples/events/structured_only_demo.json"),
        rules_path=Path("data/examples/rules/structured_only_rules_demo.json"),
    )
    assert out["match_status"] == "insufficient_data"
    assert out["unknown_conditions"] == [
        "angular_distance",
        "duration",
        "visibility",
    ]
    assert out["primary_evidence_found"] is False
    assert out["candidate_only"] is True
