from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from src.video_pipeline.contracts import (
    AstronomyEventV1,
    RuleAssessmentV1,
    VideoPackageV1,
    canonical_contract_bytes,
)


APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parents[1]
SCHEMA_ROOT = APP_ROOT / "schemas" / "video_pipeline"
FIXTURE_ROOT = WORKSPACE_ROOT / "tests" / "fixtures" / "video-package" / "v1"
MODEL_BY_SCHEMA = {
    "astronomy-event/v1": AstronomyEventV1,
    "rule-assessment/v1": RuleAssessmentV1,
    "video-package/v1": VideoPackageV1,
}
SCHEMA_FILE_BY_ID = {
    "astronomy-event/v1": "astronomy-event.schema.json",
    "rule-assessment/v1": "rule-assessment.schema.json",
    "video-package/v1": "video-package.schema.json",
}


def test_fixture_manifest_is_canonical_and_lists_every_contract() -> None:
    manifest_path = FIXTURE_ROOT / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)

    assert manifest_bytes == (
        json.dumps(
            manifest,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    assert {entry["schema_id"] for entry in manifest["fixtures"]} == set(
        MODEL_BY_SCHEMA
    )
    assert len(manifest["fixtures"]) == len(MODEL_BY_SCHEMA)


def test_committed_fixtures_validate_and_are_canonical() -> None:
    manifest = json.loads((FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8"))

    for entry in manifest["fixtures"]:
        fixture_path = FIXTURE_ROOT / entry["path"]
        fixture_bytes = fixture_path.read_bytes()
        assert hashlib.sha256(fixture_bytes).hexdigest() == entry["sha256"]

        payload = json.loads(fixture_bytes)
        model_type = MODEL_BY_SCHEMA[entry["schema_id"]]
        model = model_type.model_validate(payload)
        assert canonical_contract_bytes(model) + b"\n" == fixture_bytes

        schema = json.loads(
            (
                SCHEMA_ROOT
                / "v1"
                / SCHEMA_FILE_BY_ID[entry["schema_id"]]
            ).read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)


def test_registry_fixture_hash_matches_manifest_bytes() -> None:
    registry = json.loads(
        (SCHEMA_ROOT / "schema-registry.json").read_text(encoding="utf-8")
    )
    manifest_bytes = (FIXTURE_ROOT / "manifest.json").read_bytes()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    assert {
        entry["fixture_manifest_sha256"] for entry in registry["schemas"]
    } == {manifest_sha256}
