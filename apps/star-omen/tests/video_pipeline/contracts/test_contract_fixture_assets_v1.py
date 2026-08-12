from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from src.video_pipeline.contracts import (
    AstronomyEventV1,
    EvidenceLinkV1,
    ExternalAuditV1,
    ExternalClaimV1,
    ExternalMediaSourceV1,
    RuleAssessmentV1,
    VideoPackageV1,
    canonical_contract_bytes,
)


APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parents[1]
SCHEMA_ROOT = APP_ROOT / "schemas" / "video_pipeline"
REGISTRY_PATH = SCHEMA_ROOT / "schema-registry.json"
MODEL_BY_SCHEMA = {
    "astronomy-event/v1": AstronomyEventV1,
    "rule-assessment/v1": RuleAssessmentV1,
    "video-package/v1": VideoPackageV1,
    "external-media-source/v1": ExternalMediaSourceV1,
    "external-claim/v1": ExternalClaimV1,
    "evidence-link/v1": EvidenceLinkV1,
    "external-audit/v1": ExternalAuditV1,
}
SCHEMA_FILE_BY_ID = {
    "astronomy-event/v1": "astronomy-event.schema.json",
    "rule-assessment/v1": "rule-assessment.schema.json",
    "video-package/v1": "video-package.schema.json",
    "external-media-source/v1": "external-media-source.schema.json",
    "external-claim/v1": "external-claim.schema.json",
    "evidence-link/v1": "evidence-link.schema.json",
    "external-audit/v1": "external-audit.schema.json",
}


def registry_and_manifests() -> tuple[dict, dict[str, tuple[Path, dict]]]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    manifests: dict[str, tuple[Path, dict]] = {}
    for entry in registry["schemas"]:
        relative_path = entry["fixture_manifest_path"]
        if relative_path not in manifests:
            path = WORKSPACE_ROOT / relative_path
            manifests[relative_path] = (
                path,
                json.loads(path.read_text(encoding="utf-8")),
            )
    return registry, manifests


def test_fixture_manifests_are_canonical_and_list_every_contract() -> None:
    _, manifests = registry_and_manifests()
    fixture_schema_ids: list[str] = []
    for manifest_path, manifest in manifests.values():
        manifest_bytes = manifest_path.read_bytes()
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
        fixture_schema_ids.extend(
            entry["schema_id"] for entry in manifest["fixtures"]
        )
    assert set(fixture_schema_ids) == set(MODEL_BY_SCHEMA)
    assert len(fixture_schema_ids) == len(MODEL_BY_SCHEMA)


def test_committed_fixtures_validate_and_are_canonical() -> None:
    registry, manifests = registry_and_manifests()

    for registry_entry in registry["schemas"]:
        manifest_path, manifest = manifests[registry_entry["fixture_manifest_path"]]
        entry = next(
            item
            for item in manifest["fixtures"]
            if item["schema_id"] == registry_entry["schema_id"]
        )
        fixture_path = manifest_path.parent / entry["path"]
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
    registry, manifests = registry_and_manifests()
    for entry in registry["schemas"]:
        manifest_path, _ = manifests[entry["fixture_manifest_path"]]
        assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == entry[
            "fixture_manifest_sha256"
        ]


def test_external_media_contract_fixtures_are_synthetic_only() -> None:
    _, manifests = registry_and_manifests()
    external_manifest_path, external_manifest = next(
        value
        for key, value in manifests.items()
        if "external-media" in key
    )
    source_entry = next(
        item
        for item in external_manifest["fixtures"]
        if item["schema_id"] == "external-media-source/v1"
    )
    source = json.loads(
        (external_manifest_path.parent / source_entry["path"]).read_text(
            encoding="utf-8"
        )
    )
    assert source["creator_display_name"] == "Fixture Creator"
    assert source["fixed_url"].startswith("https://example.invalid/")
    assert "祖山" not in json.dumps(external_manifest, ensure_ascii=False)
