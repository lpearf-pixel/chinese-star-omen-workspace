from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.video_pipeline.contracts import AstronomyEventV1, RuleAssessmentV1
from tests.video_pipeline.contracts.test_contract_models_v1 import (
    valid_assessment_payload,
    valid_astronomy_payload,
)


@pytest.mark.parametrize("value", [True, "3.25"])
def test_measurements_reject_bool_and_numeric_strings(value: object) -> None:
    payload = valid_astronomy_payload()
    payload["measurements"][0]["value"] = value

    with pytest.raises(ValidationError):
        AstronomyEventV1.model_validate(payload)


@pytest.mark.parametrize("field", ["latitude_deg", "longitude_deg", "elevation_m"])
def test_observer_numbers_reject_strings_and_bool(field: str) -> None:
    payload = valid_astronomy_payload()
    payload["observer"][field] = "1.0"
    with pytest.raises(ValidationError):
        AstronomyEventV1.model_validate(payload)

    payload = valid_astronomy_payload()
    payload["observer"][field] = True
    with pytest.raises(ValidationError):
        AstronomyEventV1.model_validate(payload)


def test_matched_assessment_requires_at_least_one_matched_rule() -> None:
    payload = valid_assessment_payload()
    payload["matched_rules"] = []
    payload["recommended_rule_id"] = None

    with pytest.raises(ValidationError):
        RuleAssessmentV1.model_validate(payload)


def test_recommended_rule_must_have_matched_status() -> None:
    payload = valid_assessment_payload()
    payload["matched_rules"][0]["status"] = "candidate_only"

    with pytest.raises(ValidationError):
        RuleAssessmentV1.model_validate(payload)


def test_non_matched_assessment_cannot_have_formal_recommendation() -> None:
    payload = valid_assessment_payload()
    payload["match_status"] = "partial_match"
    payload["narration_eligibility"] = "blocked"

    with pytest.raises(ValidationError):
        RuleAssessmentV1.model_validate(payload)


def test_condition_state_keys_must_be_stable_identifiers() -> None:
    payload = valid_assessment_payload()
    payload["condition_states"] = {" 身份条件 ": "pass"}

    with pytest.raises(ValidationError):
        RuleAssessmentV1.model_validate(payload)


def test_visible_status_requires_altitude_measurements() -> None:
    payload = valid_astronomy_payload()
    payload["visibility"]["status"] = "visible"

    with pytest.raises(ValidationError):
        AstronomyEventV1.model_validate(payload)


def test_unknown_visibility_may_omit_altitude_measurements() -> None:
    payload = deepcopy(valid_astronomy_payload())
    payload["visibility"]["status"] = "unknown"

    event = AstronomyEventV1.model_validate(payload)
    assert event.visibility.status == "unknown"
