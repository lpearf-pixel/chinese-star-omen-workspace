from __future__ import annotations

from copy import deepcopy
from math import inf, nan

import pytest
from pydantic import ValidationError

from src.video_pipeline.contracts import (
    AstronomyEventV1,
    RuleAssessmentV1,
    VideoPackageV1,
    canonical_contract_bytes,
)


def valid_astronomy_payload() -> dict:
    return {
        "schema_version": "astronomy-event/v1",
        "calculation_id": "calc:2026-07-21:moon-spica",
        "event_id": "event:2026-07-21:moon-spica",
        "event_type": "angular_separation",
        "primary_body": "moon",
        "target_body_or_region": "spica",
        "start_utc": "2026-07-21T10:00:00Z",
        "peak_utc": "2026-07-21T11:00:00Z",
        "end_utc": "2026-07-21T12:00:00Z",
        "observer": {
            "latitude_deg": 31.2304,
            "longitude_deg": 121.4737,
            "elevation_m": 4.0,
            "timezone": "Asia/Shanghai",
        },
        "measurements": [
            {
                "measurement_id": "measurement:angular-separation",
                "kind": "angular_separation_deg",
                "value": 3.25,
                "unit": "deg",
                "reference_frame": "icrs",
            }
        ],
        "visibility": {
            "status": "unknown",
            "target_altitude_deg": None,
            "sun_altitude_deg": None,
            "threshold_version": "visibility/v1",
        },
        "calculation_provenance": {
            "provider": "skyfield",
            "provider_version": "1.49",
            "ephemeris_id": "de440s.bsp",
            "ephemeris_sha256": "a" * 64,
            "timescale_source": "skyfield-timescale",
        },
        "quality_status": "verified",
        "uncertainty_reasons": [],
    }


def valid_assessment_payload() -> dict:
    return {
        "schema_version": "rule-assessment/v1",
        "assessment_id": "assessment:2026-07-21:moon-spica",
        "event_id": "event:2026-07-21:moon-spica",
        "rule_set_version": "rules:v1",
        "matched_rules": [
            {
                "rule_id": "rule:moon-near-spica",
                "status": "matched",
                "score": 1.0,
            }
        ],
        "condition_states": {
            "body": "pass",
            "event_type": "pass",
            "target": "pass",
        },
        "match_status": "matched",
        "conflict_summary": [],
        "recommended_rule_id": "rule:moon-near-spica",
        "provisional_rule_id": None,
        "evidence_references": [
            {
                "evidence_id": "evidence:kaiyuan:001",
                "status": "citable",
                "source_locator": "卷一:1a",
                "content_hash": "b" * 64,
            }
        ],
        "narration_eligibility": "eligible",
        "uncertainty_reasons": [],
    }


def valid_package_payload() -> dict:
    return {
        "schema_version": "video-package/v1",
        "package_id": "package:2026-07-21:moon-spica",
        "event_id": "event:2026-07-21:moon-spica",
        "assessment_id": "assessment:2026-07-21:moon-spica",
        "source_inventory": {
            "astronomy_measurement_ids": ["measurement:angular-separation"],
            "asterism_mapping_ids": ["asterism:spica:角宿一"],
            "citable_passage_ids": ["evidence:kaiyuan:001"],
            "historical_source_ids": ["history:tang-astronomy:001"],
            "modern_interpretation_ids": ["interpretation:open-mouth"],
        },
        "claims": [
            {
                "claim_id": "claim:astronomy:001",
                "claim_class": "astronomy_fact",
                "text": "月亮在视觉上接近角宿一对应的现代恒星。",
                "source_refs": [
                    {
                        "source_package_id": "package:2026-07-21:moon-spica",
                        "reference_type": "astronomy_measurement",
                        "reference_id": "measurement:angular-separation",
                    }
                ],
                "review_status": "approved",
            },
            {
                "claim_id": "claim:classical:001",
                "claim_class": "classical_quote",
                "text": "此处为经过引用校验的古籍原文。",
                "source_refs": [
                    {
                        "source_package_id": "package:2026-07-21:moon-spica",
                        "reference_type": "citable_passage",
                        "reference_id": "evidence:kaiyuan:001",
                    }
                ],
                "review_status": "approved",
            },
        ],
    }


def test_astronomy_event_accepts_strict_valid_payload() -> None:
    event = AstronomyEventV1.model_validate(valid_astronomy_payload())
    assert event.event_id == "event:2026-07-21:moon-spica"
    assert event.peak_utc.isoformat().endswith("+00:00")


def test_unknown_fields_are_rejected() -> None:
    payload = valid_astronomy_payload()
    payload["unexpected"] = "not allowed"

    with pytest.raises(ValidationError):
        AstronomyEventV1.model_validate(payload)


@pytest.mark.parametrize("field", ["start_utc", "peak_utc", "end_utc"])
def test_times_must_be_explicit_utc(field: str) -> None:
    payload = valid_astronomy_payload()
    payload[field] = "2026-07-21T11:00:00+08:00"

    with pytest.raises(ValidationError):
        AstronomyEventV1.model_validate(payload)


@pytest.mark.parametrize("value", [nan, inf, -inf])
def test_non_finite_measurements_are_rejected(value: float) -> None:
    payload = valid_astronomy_payload()
    payload["measurements"][0]["value"] = value

    with pytest.raises(ValidationError):
        AstronomyEventV1.model_validate(payload)


def test_time_order_must_be_start_peak_end() -> None:
    payload = valid_astronomy_payload()
    payload["peak_utc"] = "2026-07-21T13:00:00Z"

    with pytest.raises(ValidationError):
        AstronomyEventV1.model_validate(payload)


def test_measurement_ids_must_be_unique() -> None:
    payload = valid_astronomy_payload()
    payload["measurements"].append(deepcopy(payload["measurements"][0]))

    with pytest.raises(ValidationError):
        AstronomyEventV1.model_validate(payload)


def test_verified_event_requires_measurements_and_ephemeris_hash() -> None:
    no_measurements = valid_astronomy_payload()
    no_measurements["measurements"] = []
    with pytest.raises(ValidationError):
        AstronomyEventV1.model_validate(no_measurements)

    no_hash = valid_astronomy_payload()
    no_hash["calculation_provenance"]["ephemeris_sha256"] = ""
    with pytest.raises(ValidationError):
        AstronomyEventV1.model_validate(no_hash)


def test_candidate_only_assessment_cannot_be_narration_eligible() -> None:
    payload = valid_assessment_payload()
    payload["match_status"] = "candidate_only"

    with pytest.raises(ValidationError):
        RuleAssessmentV1.model_validate(payload)


def test_eligible_assessment_requires_citable_evidence() -> None:
    payload = valid_assessment_payload()
    payload["evidence_references"][0]["status"] = "candidate_only"

    with pytest.raises(ValidationError):
        RuleAssessmentV1.model_validate(payload)


def test_recommended_rule_must_reference_a_matched_rule() -> None:
    payload = valid_assessment_payload()
    payload["recommended_rule_id"] = "rule:not-present"

    with pytest.raises(ValidationError):
        RuleAssessmentV1.model_validate(payload)


def test_claim_ids_must_be_unique() -> None:
    payload = valid_package_payload()
    payload["claims"].append(deepcopy(payload["claims"][0]))

    with pytest.raises(ValidationError):
        VideoPackageV1.model_validate(payload)


def test_claim_source_reference_must_exist_in_matching_inventory() -> None:
    payload = valid_package_payload()
    payload["claims"][0]["source_refs"][0]["reference_id"] = "measurement:missing"

    with pytest.raises(ValidationError):
        VideoPackageV1.model_validate(payload)


def test_claim_source_reference_cannot_cross_package_boundary() -> None:
    payload = valid_package_payload()
    payload["claims"][0]["source_refs"][0]["source_package_id"] = "package:other"

    with pytest.raises(ValidationError):
        VideoPackageV1.model_validate(payload)


def test_claim_class_requires_correct_source_type() -> None:
    payload = valid_package_payload()
    payload["claims"][0]["source_refs"][0] = {
        "source_package_id": payload["package_id"],
        "reference_type": "historical_source",
        "reference_id": "history:tang-astronomy:001",
    }

    with pytest.raises(ValidationError):
        VideoPackageV1.model_validate(payload)


def test_classical_quote_requires_citable_passage_reference() -> None:
    payload = valid_package_payload()
    payload["claims"][1]["source_refs"] = []

    with pytest.raises(ValidationError):
        VideoPackageV1.model_validate(payload)


def test_canonical_bytes_are_stable_and_strict_json() -> None:
    first = AstronomyEventV1.model_validate(valid_astronomy_payload())
    reordered = dict(reversed(list(valid_astronomy_payload().items())))
    second = AstronomyEventV1.model_validate(reordered)

    assert canonical_contract_bytes(first) == canonical_contract_bytes(second)
    assert b"NaN" not in canonical_contract_bytes(first)
    assert canonical_contract_bytes(first).startswith(b'{"calculation_id"')
