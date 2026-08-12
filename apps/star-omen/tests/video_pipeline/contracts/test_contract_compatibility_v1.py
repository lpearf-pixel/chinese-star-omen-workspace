from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from src.video_pipeline.contracts import (
    AstronomyEventV1,
    ContractCompatibilityError,
    EvidenceLinkV1,
    ExternalAuditV1,
    ExternalClaimV1,
    ExternalMediaSourceV1,
    RuleAssessmentV1,
    VideoPackageV1,
    validate_contract_compatibility,
)


ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = ROOT.parents[1]
SCHEMA_ROOT = ROOT / "schemas" / "video_pipeline"
REGISTRY_PATH = SCHEMA_ROOT / "schema-registry.json"


@pytest.mark.parametrize(
    ("model", "relative_path"),
    [
        (AstronomyEventV1, "v1/astronomy-event.schema.json"),
        (RuleAssessmentV1, "v1/rule-assessment.schema.json"),
        (VideoPackageV1, "v1/video-package.schema.json"),
        (ExternalMediaSourceV1, "v1/external-media-source.schema.json"),
        (ExternalClaimV1, "v1/external-claim.schema.json"),
        (EvidenceLinkV1, "v1/evidence-link.schema.json"),
        (ExternalAuditV1, "v1/external-audit.schema.json"),
    ],
)
def test_committed_schema_matches_model_schema(model: type, relative_path: str) -> None:
    committed = json.loads((SCHEMA_ROOT / relative_path).read_text(encoding="utf-8"))
    assert committed == model.model_json_schema()


def test_registry_binds_all_contracts_and_fixture_manifest() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert registry["registry_version"] == "video-contract-registry/v1"
    assert registry["compatibility_policy"] == "additive-optional-only"

    entries = {entry["schema_id"]: entry for entry in registry["schemas"]}
    assert set(entries) == {
        "astronomy-event/v1",
        "rule-assessment/v1",
        "video-package/v1",
        "external-media-source/v1",
        "external-claim/v1",
        "evidence-link/v1",
        "external-audit/v1",
    }
    for entry in entries.values():
        assert entry["owner"] == "apps/star-omen"
        assert entry["version"] == 1
        assert (SCHEMA_ROOT / entry["path"]).is_file()
        manifest_path = WORKSPACE_ROOT / entry["fixture_manifest_path"]
        assert manifest_path.is_file()
        assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == entry[
            "fixture_manifest_sha256"
        ]


def base_schema() -> dict:
    return {
        "$id": "urn:test:contract/v1",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"type": "string", "const": "test/v1"},
            "status": {"type": "string", "enum": ["ready", "blocked"]},
            "name": {"type": "string"},
        },
        "required": ["schema_version", "status", "name"],
    }


def test_optional_addition_is_v1_compatible() -> None:
    old = base_schema()
    new = deepcopy(old)
    new["properties"]["note"] = {"type": ["string", "null"], "default": None}

    report = validate_contract_compatibility(old, new)

    assert report.compatible is True
    assert report.issues == []


@pytest.mark.parametrize("mutation", ["remove_required", "add_required", "remove_property"])
def test_required_and_existing_properties_cannot_change(mutation: str) -> None:
    old = base_schema()
    new = deepcopy(old)
    if mutation == "remove_required":
        new["required"].remove("name")
    elif mutation == "add_required":
        new["properties"]["note"] = {"type": "string"}
        new["required"].append("note")
    else:
        del new["properties"]["name"]
        new["required"].remove("name")

    with pytest.raises(ContractCompatibilityError) as exc_info:
        validate_contract_compatibility(old, new)

    assert exc_info.value.report.compatible is False
    assert exc_info.value.report.issues


def test_enum_meaning_cannot_change_in_place() -> None:
    old = base_schema()
    new = deepcopy(old)
    new["properties"]["status"]["enum"] = ["ready", "blocked", "unknown"]

    with pytest.raises(ContractCompatibilityError) as exc_info:
        validate_contract_compatibility(old, new)

    assert any(issue.code == "enum_changed" for issue in exc_info.value.report.issues)


def test_existing_field_type_and_const_cannot_change() -> None:
    old = base_schema()
    changed_type = deepcopy(old)
    changed_type["properties"]["name"]["type"] = "integer"
    with pytest.raises(ContractCompatibilityError):
        validate_contract_compatibility(old, changed_type)

    changed_const = deepcopy(old)
    changed_const["properties"]["schema_version"]["const"] = "test/v2"
    with pytest.raises(ContractCompatibilityError):
        validate_contract_compatibility(old, changed_const)


def test_opening_additional_properties_is_rejected() -> None:
    old = base_schema()
    new = deepcopy(old)
    new["additionalProperties"] = True

    with pytest.raises(ContractCompatibilityError) as exc_info:
        validate_contract_compatibility(old, new)

    assert any(issue.code == "additional_properties_changed" for issue in exc_info.value.report.issues)
