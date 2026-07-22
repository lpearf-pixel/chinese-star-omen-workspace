from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError as JsonSchemaValidationError
from pydantic import ValidationError

from src.video_pipeline.contracts import VideoPackageV1
from tests.video_pipeline.contracts.test_contract_models_v1 import valid_package_payload


APP_ROOT = Path(__file__).resolve().parents[3]
RULE_SCHEMA_PATH = (
    APP_ROOT
    / "schemas"
    / "video_pipeline"
    / "v1"
    / "rule-assessment.schema.json"
)


def valid_ascii_package() -> dict:
    payload = valid_package_payload()
    payload["source_inventory"]["asterism_mapping_ids"] = [
        "asterism:spica:jiao-xiu-1"
    ]
    return payload


def test_json_schema_rejects_unstable_condition_state_key() -> None:
    schema = json.loads(RULE_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload = {
        "schema_version": "rule-assessment/v1",
        "assessment_id": "assessment:1",
        "event_id": "event:1",
        "rule_set_version": "rules:v1",
        "matched_rules": [],
        "condition_states": {" 身份条件 ": "pass"},
        "match_status": "not_matched",
        "evidence_references": [],
        "narration_eligibility": "blocked",
    }

    with pytest.raises(JsonSchemaValidationError):
        Draft202012Validator(schema).validate(payload)


def test_duplicate_claim_id_fails_from_otherwise_valid_package() -> None:
    payload = valid_ascii_package()
    payload["claims"].append(deepcopy(payload["claims"][0]))
    with pytest.raises(ValidationError):
        VideoPackageV1.model_validate(payload)


def test_dangling_claim_reference_fails_from_otherwise_valid_package() -> None:
    payload = valid_ascii_package()
    payload["claims"][0]["source_refs"][0]["reference_id"] = "measurement:missing"
    with pytest.raises(ValidationError):
        VideoPackageV1.model_validate(payload)


def test_cross_package_reference_fails_from_otherwise_valid_package() -> None:
    payload = valid_ascii_package()
    payload["claims"][0]["source_refs"][0]["source_package_id"] = "package:other"
    with pytest.raises(ValidationError):
        VideoPackageV1.model_validate(payload)


def test_wrong_claim_source_type_fails_from_otherwise_valid_package() -> None:
    payload = valid_ascii_package()
    payload["claims"][0]["source_refs"][0] = {
        "source_package_id": payload["package_id"],
        "reference_type": "historical_source",
        "reference_id": "history:tang-astronomy:001",
    }
    with pytest.raises(ValidationError):
        VideoPackageV1.model_validate(payload)


def test_classical_quote_without_citable_ref_fails_from_valid_package() -> None:
    payload = valid_ascii_package()
    payload["claims"][1]["source_refs"] = []
    with pytest.raises(ValidationError):
        VideoPackageV1.model_validate(payload)
