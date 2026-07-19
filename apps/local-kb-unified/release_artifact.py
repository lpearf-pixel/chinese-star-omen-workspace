"""Pure assembly of validated Kaiyuan release observations."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import re
from typing import Any

from release_drill import (
    COLLECTION_SCHEMA,
    COLLECTION_NAME_RE,
    INPUT_SCHEMA,
    MANAGED_BY,
    MANIFEST_IDENTITY_FIELDS,
    MANIFEST_SCHEMA,
    PROTECTED_COLLECTION,
    REQUIRED_HEALTH_CHECKS,
    STAGE_CARD_TYPES,
    TARGET_COLLECTION,
    validate_release_drill,
)

OBSERVATION_SCHEMA = "kaiyuan-release-observation/v1"
PHASE_NAMES = ("before_switch", "after_switch", "after_rollback")
OBSERVATION_KEYS = {"schema_version", "phase_name", "captured_at", "phase"}
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class ReleaseArtifactError(RuntimeError):
    def __init__(self, code: str, field: str, *, report: Mapping[str, object] | None = None):
        self.code = code
        self.field = field
        self.report = dict(report) if report is not None else None
        super().__init__(f"{code}: {field}")


def _phase(observation: Any, expected_name: str) -> dict[str, object]:
    if (
        not isinstance(observation, Mapping)
        or set(observation) != OBSERVATION_KEYS
        or observation.get("schema_version") != OBSERVATION_SCHEMA
        or observation.get("phase_name") != expected_name
        or not isinstance(observation.get("captured_at"), str)
        or not isinstance(observation.get("phase"), Mapping)
    ):
        raise ReleaseArtifactError("observation_contract_error", expected_name)
    phase = observation["phase"]
    if set(phase) != {"active_collection", "health", "meta", "smoke", "collections"}:
        raise ReleaseArtifactError("observation_contract_error", expected_name)
    active = phase.get("active_collection")
    if not isinstance(active, str) or COLLECTION_NAME_RE.fullmatch(active) is None:
        raise ReleaseArtifactError("observation_contract_error", expected_name)
    health = _exact_mapping(phase.get("health"), {"status", "ready", "checks"}, expected_name)
    checks = _exact_mapping(health.get("checks"), set(REQUIRED_HEALTH_CHECKS), expected_name)
    if health.get("status") != "ok" or health.get("ready") is not True or any(
        checks.get(name) is not True for name in REQUIRED_HEALTH_CHECKS
    ):
        raise ReleaseArtifactError("observation_contract_error", expected_name)
    meta = _exact_mapping(phase.get("meta"), {"meta_status", *MANIFEST_IDENTITY_FIELDS}, expected_name)
    if meta.get("meta_status") != "ok":
        raise ReleaseArtifactError("observation_contract_error", expected_name)
    _identity(meta, active, "observation_contract_error", expected_name)
    smoke = _exact_mapping(phase.get("smoke"), set(STAGE_CARD_TYPES), expected_name)
    for stage in STAGE_CARD_TYPES:
        result = _exact_mapping(
            smoke.get(stage),
            {"status", "http_status", "retrieval_stage", "card_types", "collection", "hits_count"},
            expected_name,
        )
        hits_count = result.get("hits_count")
        card_types = result.get("card_types")
        if (
            result.get("status") != "ok"
            or result.get("http_status") != 200
            or isinstance(result.get("http_status"), bool)
            or result.get("retrieval_stage") != stage
            or not isinstance(card_types, list)
            or tuple(card_types) != STAGE_CARD_TYPES[stage]
            or result.get("collection") != active
            or isinstance(hits_count, bool)
            or not isinstance(hits_count, int)
            or hits_count <= 0
        ):
            raise ReleaseArtifactError("observation_contract_error", expected_name)
    collections = _exact_mapping(phase.get("collections"), {PROTECTED_COLLECTION, active}, expected_name)
    for fingerprint in collections.values():
        value = _exact_mapping(fingerprint, {"exists", "points_count", "config_hash"}, expected_name)
        points_count = value.get("points_count")
        if (
            value.get("exists") is not True
            or isinstance(points_count, bool)
            or not isinstance(points_count, int)
            or points_count < 0
            or not isinstance(value.get("config_hash"), str)
            or HASH_RE.fullmatch(value["config_hash"]) is None
        ):
            raise ReleaseArtifactError("observation_contract_error", expected_name)
    return dict(phase)


def _exact_mapping(value: Any, keys: set[Any], field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ReleaseArtifactError("observation_contract_error", field)
    return value


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or UTC_TIMESTAMP_RE.fullmatch(value) is None:
        raise ReleaseArtifactError("timestamp_error", field)
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ" if "." in value else "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ReleaseArtifactError("timestamp_error", field) from exc


def _manifest(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ReleaseArtifactError("manifest_contract_error", "expected_manifest")
    return _identity(value, TARGET_COLLECTION, "manifest_contract_error", "expected_manifest")


def _identity(value: Mapping[str, Any], collection: str, code: str, field_name: str) -> dict[str, str]:
    projected: dict[str, str] = {}
    for field in MANIFEST_IDENTITY_FIELDS:
        item = value.get(field)
        if not _safe_text(item):
            raise ReleaseArtifactError(code, field if code == "manifest_contract_error" else field_name)
        projected[field] = item
    if (
        projected["schema_version"] != MANIFEST_SCHEMA
        or projected["managed_by"] != MANAGED_BY
        or projected["collection_schema"] != COLLECTION_SCHEMA
        or projected["collection"] != collection
        or HASH_RE.fullmatch(projected["source_manifest_hash"]) is None
    ):
        raise ReleaseArtifactError(code, field_name)
    return projected


def _safe_text(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return not any(ord(character) < 32 or ord(character) == 127 for character in value)


def assemble_release_artifact(
    *,
    observations: Mapping[str, object],
    expected_manifest: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    if not isinstance(observations, Mapping) or set(observations) != set(PHASE_NAMES):
        raise ReleaseArtifactError("observation_contract_error", "observations")
    document: dict[str, object] = {
        "schema_version": INPUT_SCHEMA,
        "target_collection": TARGET_COLLECTION,
        "expected_release_manifest": _manifest(expected_manifest),
    }
    captured = [_timestamp(observations[name].get("captured_at") if isinstance(observations[name], Mapping) else None, name) for name in PHASE_NAMES]
    if not (captured[0] < captured[1] < captured[2]):
        raise ReleaseArtifactError("timestamp_error", "chronology")
    for name in PHASE_NAMES:
        document[name] = _phase(observations[name], name)
    report = validate_release_drill(document)
    if report["status"] != "passed":
        raise ReleaseArtifactError("drill_validation_failed", "document", report=report)
    return document, report
