from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from math import inf, nan
from pathlib import Path

import pytest
from pydantic import ValidationError

from kb_contracts.omen_rule_v2 import (
    OmenRuleV2,
    canonical_omen_rule_bytes,
    migrate_omen_rule_v1,
)
from kb_contracts.rule_candidate_v2 import (
    RuleCandidateV2,
    RuleProposalV2,
    canonical_rule_candidate_bytes,
    derive_candidate_id,
    proposal_sha256,
)

ROOT = Path(__file__).resolve().parents[3]
RULE_FIXTURES = ROOT / "tests/fixtures/rules/v2"


def proposal_payload() -> dict:
    return {
        "tradition": "tang_kaiyuan",
        "trigger": {
            "body_or_actor": ["mars"],
            "event_type": "station",
            "target_object_or_region": ["heart"],
            "relation_terms": ["守"],
            "required_measurements": ["angular_separation_deg"],
            "sequence_conditions": [],
            "visibility_conditions": ["visible"],
        },
        "actors": ["mars", "heart"],
        "relation": "守",
        "spatial_conditions": [
            {
                "condition_id": "condition:spatial:heart",
                "kind": "target_region",
                "operator": "within",
                "value": "heart",
            }
        ],
        "temporal_conditions": [],
        "observational_properties": [],
        "effect": {
            "effect_domain": ["leadership", "politics"],
            "subject_scope": ["ruler"],
            "polarity": "adverse",
            "description": "主君有忧。",
            "historical_context": [],
        },
        "severity": "high",
        "time_window": None,
        "exceptions": [],
        "conflict_group": None,
        "rule_priority": 100,
        "resolution_policy": "manual_adjudication",
        "computability": {
            "status": "partially_computable",
            "required_measurements": ["angular_separation_deg"],
            "reasons": ["古文未给出角距阈值。"],
        },
        "uncertainty": [],
        "editorial_notes": [],
    }


def extractor_payload() -> dict:
    return {
        "extractor_type": "deterministic",
        "extractor_name": "kaiyuan-patterns",
        "extractor_version": "1.0.0",
        "pattern_version": "patterns/v1",
        "model_provider": None,
        "model_name": None,
        "prompt_hash": None,
    }


def spans_payload() -> list[dict]:
    return [
        {
            "passage_id": "passage:kaiyuan:031:0001",
            "raw_start": 12,
            "raw_end": 19,
            "raw_text": "荧惑守心，主君忧",
            "raw_content_hash": "a" * 64,
        }
    ]


def candidate_payload() -> dict:
    extractor = extractor_payload()
    passage_ids = ["passage:kaiyuan:031:0001"]
    spans = spans_payload()
    proposal = proposal_payload()
    candidate_id = derive_candidate_id(
        extractor=extractor,
        source_passage_ids=passage_ids,
        raw_spans=spans,
        proposal=proposal,
    )
    return {
        "schema_version": "rule-candidate/v2",
        "candidate_id": candidate_id,
        "extractor": extractor,
        "source_passage_ids": passage_ids,
        "raw_spans": spans,
        "proposal": proposal,
        "proposal_sha256": proposal_sha256(proposal),
        "status": "needs_review",
        "history": [
            {
                "event_id": "candidate-event:0001",
                "sequence": 1,
                "event_type": "created",
                "actor_type": "extractor",
                "actor_id": "kaiyuan-patterns:1.0.0",
                "recorded_at": "2026-07-30T20:00:00Z",
                "reason": "deterministic pattern match",
                "proposal_sha256": proposal_sha256(proposal),
                "source_candidate_ids": [],
                "resulting_candidate_ids": [candidate_id],
                "resulting_rule_id": None,
            }
        ],
    }


def evidence_payload() -> dict:
    return {
        "evidence_id": "evidence:kaiyuan:031:0001",
        "status": "citable",
        "passage_id": "passage:kaiyuan:031:0001",
        "kb_book_id": "kaiyuan_zhanjing",
        "source_locator": "KR3g0018_031",
        "page_marker": "31:1a",
        "heading_path": ["卷三十一", "五星占"],
        "paragraph_index": 1,
        "raw_start": 12,
        "raw_end": 19,
        "raw_content_hash": "a" * 64,
        "normalized_content_hash": "b" * 64,
        "source_fingerprint": "c" * 64,
        "quote": "荧惑守心，主君忧",
    }


def rule_payload() -> dict:
    return {
        "schema_version": "omen-rule/v2",
        "rule_id": "rule:kaiyuan:0001",
        "rule_version": 1,
        "supersedes_rule_version": None,
        "source_candidate_ids": [candidate_payload()["candidate_id"]],
        "source_passage_ids": ["passage:kaiyuan:031:0001"],
        "content": proposal_payload(),
        "evidence": [evidence_payload()],
        "review": {
            "status": "approved",
            "reviewer_id": "reviewer:human:01",
            "approved_at": "2026-07-30T21:00:00Z",
            "annotation_guide_version": "kaiyuan-rule-annotation/v1",
            "decision_reason": "原文、定位和结构字段经人工复核。",
        },
        "provenance": {
            "rule_id_assigned_by": "human_review",
            "created_from_candidate_ids": [candidate_payload()["candidate_id"]],
            "created_at": "2026-07-30T21:00:00Z",
            "source_release_head": "d" * 40,
        },
        "version_history": [
            {
                "rule_version": 1,
                "content_sha256": proposal_sha256(proposal_payload()),
                "reviewer_id": "reviewer:human:01",
                "recorded_at": "2026-07-30T21:00:00Z",
                "reason": "initial approval",
            }
        ],
    }


def test_candidate_identity_is_stable_and_bound_to_all_inputs() -> None:
    payload = candidate_payload()
    candidate = RuleCandidateV2.model_validate(payload)
    reordered = deepcopy(payload)
    reordered["proposal"] = dict(reversed(list(reordered["proposal"].items())))

    assert RuleCandidateV2.model_validate(reordered).candidate_id == candidate.candidate_id
    assert candidate.candidate_id.startswith("candidate:sha256:")
    assert canonical_rule_candidate_bytes(candidate) == canonical_rule_candidate_bytes(
        RuleCandidateV2.model_validate(reordered)
    )

    changed = deepcopy(payload)
    changed["raw_spans"][0]["raw_start"] += 1
    with pytest.raises(ValidationError, match="candidate_id"):
        RuleCandidateV2.model_validate(changed)


def test_candidate_rejects_unknown_fields_duplicates_and_unstable_order() -> None:
    unknown = candidate_payload()
    unknown["unexpected"] = True
    with pytest.raises(ValidationError):
        RuleCandidateV2.model_validate(unknown)

    duplicate = candidate_payload()
    duplicate["source_passage_ids"].append(duplicate["source_passage_ids"][0])
    with pytest.raises(ValidationError, match="source_passage_ids"):
        RuleCandidateV2.model_validate(duplicate)

    unsorted = candidate_payload()
    unsorted["source_passage_ids"] = [
        "passage:kaiyuan:032:0001",
        "passage:kaiyuan:031:0001",
    ]
    with pytest.raises(ValidationError, match="sorted"):
        RuleCandidateV2.model_validate(unsorted)

    duplicate_span = candidate_payload()
    duplicate_span["raw_spans"].append(deepcopy(duplicate_span["raw_spans"][0]))
    with pytest.raises(ValidationError, match="raw_spans"):
        RuleCandidateV2.model_validate(duplicate_span)


def test_candidate_history_is_append_only_shaped_and_state_consistent() -> None:
    payload = candidate_payload()
    payload["history"].append(deepcopy(payload["history"][0]))
    with pytest.raises(ValidationError, match="history"):
        RuleCandidateV2.model_validate(payload)

    rejected = candidate_payload()
    rejected["status"] = "rejected"
    with pytest.raises(ValidationError, match="terminal"):
        RuleCandidateV2.model_validate(rejected)

    tampered_history = candidate_payload()
    tampered_history["history"][0]["proposal_sha256"] = "f" * 64
    with pytest.raises(ValidationError, match="history.*proposal"):
        RuleCandidateV2.model_validate(tampered_history)


def test_model_or_extractor_cannot_approve_candidate() -> None:
    payload = candidate_payload()
    candidate_id = payload["candidate_id"]
    payload["status"] = "approved"
    payload["history"].append(
        {
            "event_id": "candidate-event:0002",
            "sequence": 2,
            "event_type": "approved",
            "actor_type": "model",
            "actor_id": "model:example",
            "recorded_at": "2026-07-30T20:01:00Z",
            "reason": "model attempted approval",
            "proposal_sha256": payload["proposal_sha256"],
            "source_candidate_ids": [candidate_id],
            "resulting_candidate_ids": [candidate_id],
            "resulting_rule_id": "rule:not-allowed",
        }
    )

    with pytest.raises(ValidationError, match="reviewer"):
        RuleCandidateV2.model_validate(payload)


def test_blank_nested_semantics_are_rejected() -> None:
    blank_actor = proposal_payload()
    blank_actor["actors"] = [" "]
    with pytest.raises(ValidationError):
        RuleProposalV2.model_validate(blank_actor)

    blank_uncertainty = proposal_payload()
    blank_uncertainty["uncertainty"] = [""]
    with pytest.raises(ValidationError):
        RuleProposalV2.model_validate(blank_uncertainty)


@pytest.mark.parametrize("value", [nan, inf, -inf])
def test_non_finite_numeric_values_are_rejected(value: float) -> None:
    candidate = candidate_payload()
    candidate["proposal"]["rule_priority"] = value
    with pytest.raises(ValidationError):
        RuleCandidateV2.model_validate(candidate)


def test_formal_rule_requires_human_approval_and_citable_evidence() -> None:
    rule = OmenRuleV2.model_validate(rule_payload())
    assert rule.review.status == "approved"

    model_assigned = rule_payload()
    model_assigned["provenance"]["rule_id_assigned_by"] = "model"
    with pytest.raises(ValidationError):
        OmenRuleV2.model_validate(model_assigned)

    non_citable = rule_payload()
    non_citable["evidence"][0]["status"] = "candidate_only"
    with pytest.raises(ValidationError, match="citable"):
        OmenRuleV2.model_validate(non_citable)


def test_rule_identity_version_and_history_fail_closed() -> None:
    duplicate = rule_payload()
    duplicate["source_candidate_ids"].append(duplicate["source_candidate_ids"][0])
    with pytest.raises(ValidationError, match="source_candidate_ids"):
        OmenRuleV2.model_validate(duplicate)

    missing_previous = rule_payload()
    missing_previous["rule_version"] = 2
    missing_previous["version_history"][0]["rule_version"] = 2
    with pytest.raises(ValidationError, match="supersedes"):
        OmenRuleV2.model_validate(missing_previous)

    overwritten = rule_payload()
    overwritten["version_history"][0]["content_sha256"] = "f" * 64
    with pytest.raises(ValidationError, match="content_sha256"):
        OmenRuleV2.model_validate(overwritten)


def test_canonical_rule_json_is_stable_strict_and_utc_normalized() -> None:
    first = OmenRuleV2.model_validate(rule_payload())
    reordered = dict(reversed(list(rule_payload().items())))
    second = OmenRuleV2.model_validate(reordered)

    assert canonical_omen_rule_bytes(first) == canonical_omen_rule_bytes(second)
    assert canonical_omen_rule_bytes(first).startswith(b'{"content"')
    assert b"NaN" not in canonical_omen_rule_bytes(first)
    assert first.review.approved_at == datetime(2026, 7, 30, 21, tzinfo=timezone.utc)


def test_v1_read_is_explicit_and_never_silently_promotes() -> None:
    legacy = {
        "id": "legacy-rule-1",
        "source_text": "荧惑守心，主君忧",
        "source_book": "唐开元占经",
        "source_chapter": "卷三十一",
        "trigger": {
            "body": "荧惑",
            "event_type": "守",
            "target": "心",
            "qualifiers": [],
        },
        "effect_domain": ["leadership"],
        "validation_status": "unverified",
        "evidence": None,
        "severity": "high",
        "time_window": None,
        "interpretation": None,
        "modern_translation": None,
        "linked_cases": [],
        "notes": None,
    }

    report = migrate_omen_rule_v1(legacy)

    assert report.source_schema_version == "omen-rule/v1"
    assert report.target_schema_version == "omen-rule/v2"
    assert report.status == "needs_review"
    assert report.migrated_rule is None
    assert "missing_citable_evidence" in report.issue_codes
    assert canonical_omen_rule_bytes(report).endswith(b"}")


def test_v1_reader_rejects_unknown_legacy_shape_with_report() -> None:
    report = migrate_omen_rule_v1({"id": "legacy-rule-1", "unexpected": True})

    assert report.status == "rejected"
    assert report.migrated_rule is None
    assert "invalid_v1_shape" in report.issue_codes


def test_candidate_and_rule_contract_fixtures_are_canonical() -> None:
    candidate_bytes = (RULE_FIXTURES / "rule-candidate.valid.json").read_bytes()
    rule_bytes = (RULE_FIXTURES / "omen-rule.valid.json").read_bytes()

    candidate = RuleCandidateV2.model_validate_json(candidate_bytes)
    rule = OmenRuleV2.model_validate_json(rule_bytes)

    assert canonical_rule_candidate_bytes(candidate) + b"\n" == candidate_bytes
    assert canonical_omen_rule_bytes(rule) + b"\n" == rule_bytes
    assert candidate.candidate_id in rule.source_candidate_ids
    assert [item.sequence for item in candidate.history] == [1]
    assert [item.rule_version for item in rule.version_history] == [1]
