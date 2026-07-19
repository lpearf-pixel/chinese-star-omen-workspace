"""Pure assembly of validated Kaiyuan release observations."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import re
from typing import Any

from release_drill import (
    COLLECTION_SCHEMA,
    INPUT_SCHEMA,
    MANAGED_BY,
    MANIFEST_IDENTITY_FIELDS,
    MANIFEST_SCHEMA,
    TARGET_COLLECTION,
    validate_release_drill,
)

OBSERVATION_SCHEMA = "kaiyuan-release-observation/v1"
PHASE_NAMES = ("before_switch", "after_switch", "after_rollback")
OBSERVATION_KEYS = {"schema_version", "phase_name", "captured_at", "phase"}
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


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
    return dict(observation["phase"])


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
    projected = {}
    for field in MANIFEST_IDENTITY_FIELDS:
        item = value.get(field)
        if not isinstance(item, str) or not item.strip():
            raise ReleaseArtifactError("manifest_contract_error", field)
        projected[field] = item
    if (
        projected["schema_version"] != MANIFEST_SCHEMA
        or projected["managed_by"] != MANAGED_BY
        or projected["collection_schema"] != COLLECTION_SCHEMA
        or projected["collection"] != TARGET_COLLECTION
    ):
        raise ReleaseArtifactError("manifest_contract_error", "expected_manifest")
    return projected


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
