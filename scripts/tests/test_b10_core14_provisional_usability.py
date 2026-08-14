import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTER = (
    ROOT
    / "corpus"
    / "research_sources"
    / "b10-core14"
    / "provisional-usability-stratification.json"
)

CORE14 = {
    "C02",
    "C03",
    "C09",
    "C11",
    "C13",
    "C14",
    "C24",
    "C31",
    "C33",
    "C41",
    "C43",
    "C44",
    "C45",
    "C47",
}
PROVISIONAL = {
    "C02",
    "C09",
    "C11",
    "C13",
    "C14",
    "C31",
    "C41",
    "C43",
    "C44",
    "C45",
    "C47",
}
ISOLATED = {"C03", "C24", "C33"}


def test_core14_provisional_usability_is_an_exact_fail_closed_partition():
    data = json.loads(REGISTER.read_text(encoding="utf-8"))

    assert data["schema_version"] == "b10-core14-provisional-usability/v1"
    assert data["scope"]["case_count"] == 14
    assert set(data["scope"]["case_ids"]) == CORE14
    assert len(data["scope"]["case_ids"]) == len(CORE14)

    rows = data["cases"]
    assert len(rows) == 14
    by_id = {row["case_id"]: row for row in rows}
    assert len(by_id) == 14
    assert set(by_id) == CORE14

    provisional = {
        case_id
        for case_id, row in by_id.items()
        if row["operational_status"]
        == "provisional_usable_pending_reviewer_b"
    }
    isolated = {
        case_id
        for case_id, row in by_id.items()
        if row["operational_status"] == "isolated_evidence_supplement"
    }
    assert provisional == PROVISIONAL
    assert isolated == ISOLATED
    assert provisional.isdisjoint(isolated)
    assert provisional | isolated == CORE14

    for case_id in PROVISIONAL:
        row = by_id[case_id]
        assert row["internal_research_use_allowed"] is True
        assert row["provisional_citation_eligible"] is True
        assert row["final_human_approval"] is False
        assert row["reviewer_b_confirmation_required"] is True
        assert row["formal_release_eligible"] is False

    expected_isolated_states = {
        "C03": "needs_review",
        "C24": "ambiguous",
        "C33": "needs_review",
    }
    for case_id, evidence_state in expected_isolated_states.items():
        row = by_id[case_id]
        assert row["evidence_state"] == evidence_state
        assert row["internal_research_use_allowed"] is False
        assert row["provisional_citation_eligible"] is False
        assert row["final_human_approval"] is False
        assert row["reviewer_b_confirmation_required"] is True
        assert row["formal_release_eligible"] is False
        assert row["isolation_reason"]

    assert data["review_state"] == {
        "reviewer_a_state": "USER_CONFIRMED_EVIDENCE_REVISED_READY_FOR_RETURN",
        "reviewer_b_state": "UNLABELLED_HUMAN_REVIEW_NOT_STARTED",
        "reviewer_b_completed": False,
        "two_distinct_humans_gate_passed": False,
    }
    assert data["authorization_gates"] == {
        "threshold_freeze_authorized": False,
        "formal_rule_release_authorized": False,
        "official_ingest_authorized": False,
        "official_promotion_authorized": False,
        "b10_pr_d_start_authorized": False,
    }
