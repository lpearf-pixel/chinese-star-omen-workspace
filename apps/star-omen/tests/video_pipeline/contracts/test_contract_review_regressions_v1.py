from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from src.video_pipeline.contracts import (
    ContractCompatibilityError,
    VideoPackageV1,
    validate_contract_compatibility,
)
from tests.video_pipeline.contracts.test_contract_compatibility_v1 import base_schema
from tests.video_pipeline.contracts.test_contract_models_v1 import valid_package_payload


def valid_package_with_ascii_ids() -> dict:
    payload = valid_package_payload()
    payload["source_inventory"]["asterism_mapping_ids"] = [
        "asterism:spica:jiao-xiu-1"
    ]
    return payload


def test_video_package_valid_fixture_is_actually_accepted() -> None:
    package = VideoPackageV1.model_validate(valid_package_with_ascii_ids())
    assert package.package_id == "package:2026-07-21:moon-spica"
    assert len(package.claims) == 2


def test_non_ascii_display_name_is_not_a_stable_identifier() -> None:
    payload = valid_package_with_ascii_ids()
    package = VideoPackageV1.model_validate(payload)
    assert package.source_inventory.asterism_mapping_ids == [
        "asterism:spica:jiao-xiu-1"
    ]

    payload["source_inventory"]["asterism_mapping_ids"] = [
        "asterism:spica:角宿一"
    ]
    with pytest.raises(ValidationError):
        VideoPackageV1.model_validate(payload)


def nested_schema() -> dict:
    schema = base_schema()
    schema["$defs"] = {
        "NestedStatus": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["ready", "blocked"],
                }
            },
            "required": ["status"],
        }
    }
    schema["properties"]["nested"] = {"$ref": "#/$defs/NestedStatus"}
    schema["required"].append("nested")
    return schema


def test_nested_enum_change_is_rejected() -> None:
    old = nested_schema()
    new = deepcopy(old)
    new["$defs"]["NestedStatus"]["properties"]["status"]["enum"] = [
        "ready",
        "blocked",
        "unknown",
    ]

    with pytest.raises(ContractCompatibilityError) as exc_info:
        validate_contract_compatibility(old, new)

    assert any(issue.code == "enum_changed" for issue in exc_info.value.report.issues)
    assert any("$defs.NestedStatus" in issue.path for issue in exc_info.value.report.issues)


def test_nested_required_and_type_changes_are_rejected() -> None:
    old = nested_schema()

    changed_required = deepcopy(old)
    changed_required["$defs"]["NestedStatus"]["required"] = []
    with pytest.raises(ContractCompatibilityError):
        validate_contract_compatibility(old, changed_required)

    changed_type = deepcopy(old)
    changed_type["$defs"]["NestedStatus"]["properties"]["status"][
        "type"
    ] = "integer"
    with pytest.raises(ContractCompatibilityError):
        validate_contract_compatibility(old, changed_type)


def test_new_optional_nested_property_is_compatible() -> None:
    old = nested_schema()
    new = deepcopy(old)
    new["$defs"]["NestedStatus"]["properties"]["note"] = {
        "type": ["string", "null"],
        "default": None,
    }

    report = validate_contract_compatibility(old, new)
    assert report.compatible is True
