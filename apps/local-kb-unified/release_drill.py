"""Pure, non-mutating validation for the Kaiyuan v2 release drill."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

TARGET_COLLECTION = "local_kb_kaiyuan_v2"
PROTECTED_COLLECTION = "local_kb_default"
INPUT_SCHEMA = "kaiyuan-release-drill-input/v1"
REPORT_SCHEMA = "kaiyuan-release-drill/v1"
MANIFEST_SCHEMA = "corpus-manifest/v1"
MANAGED_BY = "local-kb-unified/v2"
COLLECTION_SCHEMA = "passage-v2"
COLLECTION_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
STAGE_CARD_TYPES = {
    "structured_recall": (
        "xingguan_card",
        "zhusu_card",
        "term_card",
        "extract_card",
        "topic_index",
        "chapter_summary",
    ),
    "primary_evidence": ("fenjuan", "fulltext"),
}

MANIFEST_IDENTITY_FIELDS = (
    "schema_version",
    "corpus_version",
    "ingest_run_id",
    "source_manifest_hash",
    "collection",
    "created_at",
    "managed_by",
    "collection_schema",
)
REQUIRED_HEALTH_CHECKS = (
    "ollama",
    "embedding_model",
    "qdrant",
    "default_collection",
    "corpus_manifest",
    "manifest_collection_match",
)


def _mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _manifest_identity(value: Any, *, observed: bool) -> dict[str, str] | None:
    manifest = _mapping(value)
    if manifest is None:
        return None
    if any(
        not isinstance(manifest.get(field), str) or not manifest[field].strip()
        for field in MANIFEST_IDENTITY_FIELDS
    ):
        return None
    if (
        (observed and manifest.get("meta_status") != "ok")
        or manifest.get("schema_version") != MANIFEST_SCHEMA
        or manifest.get("managed_by") != MANAGED_BY
        or manifest.get("collection_schema") != COLLECTION_SCHEMA
    ):
        return None
    return {field: manifest[field] for field in MANIFEST_IDENTITY_FIELDS}


def _healthy(phase: Mapping[str, Any] | None) -> bool:
    if phase is None:
        return False
    health = _mapping(phase.get("health"))
    checks = _mapping(health.get("checks")) if health else None
    return bool(
        health
        and health.get("status") == "ok"
        and health.get("ready") is True
        and checks
        and all(checks.get(name) is True for name in REQUIRED_HEALTH_CHECKS)
    )


def _smoke_ok(phase: Mapping[str, Any] | None, collection: Any) -> bool:
    if phase is None or not isinstance(collection, str) or not collection:
        return False
    smoke = _mapping(phase.get("smoke"))
    if smoke is None:
        return False
    for stage in ("structured_recall", "primary_evidence"):
        result = _mapping(smoke.get(stage))
        if not result:
            return False
        hits_count = result.get("hits_count")
        if (
            result.get("status") != "ok"
            or result.get("http_status") != 200
            or isinstance(result.get("http_status"), bool)
            or result.get("retrieval_stage") != stage
            or tuple(result.get("card_types", ())) != STAGE_CARD_TYPES[stage]
            or result.get("collection") != collection
            or isinstance(hits_count, bool)
            or not isinstance(hits_count, int)
            or hits_count <= 0
        ):
            return False
    return True


def _protected_fingerprint(phase: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if phase is None:
        return None
    collections = _mapping(phase.get("collections"))
    fingerprint = _mapping(collections.get(PROTECTED_COLLECTION)) if collections else None
    if fingerprint is None:
        return None
    required = ("exists", "points_count", "config_hash")
    if any(field not in fingerprint for field in required):
        return None
    points_count = fingerprint.get("points_count")
    if (
        fingerprint.get("exists") is not True
        or isinstance(points_count, bool)
        or not isinstance(points_count, int)
        or points_count < 0
        or not isinstance(fingerprint.get("config_hash"), str)
        or not fingerprint["config_hash"].strip()
    ):
        return None
    return {field: fingerprint[field] for field in required}


def _collection_exists(phase: Mapping[str, Any] | None, collection: Any) -> bool:
    if phase is None or not isinstance(collection, str) or not collection:
        return False
    collections = _mapping(phase.get("collections"))
    fingerprint = _mapping(collections.get(collection)) if collections else None
    return bool(fingerprint and fingerprint.get("exists") is True)


def validate_release_drill(document: Mapping[str, object]) -> dict[str, object]:
    """Validate recorded release phases without performing any external action."""

    errors: list[dict[str, str]] = []

    def record(check: str, ok: bool, code: str, phase: str = "document") -> bool:
        if not ok:
            errors.append({"code": code, "phase": phase, "field": check})
        return ok

    target = document.get("target_collection")
    before = _mapping(document.get("before_switch"))
    after = _mapping(document.get("after_switch"))
    rollback = _mapping(document.get("after_rollback"))
    previous = before.get("active_collection") if before else None
    previous_is_safe = bool(
        isinstance(previous, str)
        and COLLECTION_NAME_RE.fullmatch(previous)
        and previous != TARGET_COLLECTION
    )

    phase_contracts = (
        document.get("schema_version") == INPUT_SCHEMA
        and before is not None
        and after is not None
        and rollback is not None
        and previous_is_safe
    )
    target_allowed = target == TARGET_COLLECTION

    expected_release = _manifest_identity(document.get("expected_release_manifest"), observed=False)
    release_meta = _manifest_identity(after.get("meta") if after else None, observed=True)
    before_meta = _manifest_identity(before.get("meta") if before else None, observed=True)
    rollback_meta = _manifest_identity(rollback.get("meta") if rollback else None, observed=True)

    checks = {
        "target_allowed": record("target_allowed", target_allowed, "TARGET_COLLECTION_FORBIDDEN"),
        "phase_contracts": record("phase_contracts", phase_contracts, "PHASE_CONTRACT_INVALID"),
        "collection_transition": record(
            "collection_transition",
            previous_is_safe,
            "NO_COLLECTION_TRANSITION" if previous == TARGET_COLLECTION else "ROLLBACK_COLLECTION_INVALID",
            "before_switch",
        ),
        "release_collection": record(
            "release_collection",
            _collection_exists(after, target),
            "RELEASE_COLLECTION_UNAVAILABLE",
            "after_switch",
        ),
        "release_health": record("release_health", _healthy(after), "RELEASE_HEALTH_UNREADY", "after_switch"),
        "release_manifest": record(
            "release_manifest",
            bool(
                expected_release
                and release_meta == expected_release
                and after
                and after.get("active_collection") == target
                and release_meta.get("collection") == target
            ),
            "RELEASE_MANIFEST_MISMATCH",
            "after_switch",
        ),
        "release_smoke": record("release_smoke", _smoke_ok(after, target), "RELEASE_SMOKE_FAILED", "after_switch"),
        "rollback_provenance": record(
            "rollback_provenance",
            bool(rollback and previous and rollback.get("active_collection") == previous),
            "ROLLBACK_COLLECTION_MISMATCH",
            "after_rollback",
        ),
        "rollback_health": record("rollback_health", _healthy(rollback), "ROLLBACK_HEALTH_UNREADY", "after_rollback"),
        "rollback_collection": record(
            "rollback_collection",
            _collection_exists(rollback, previous),
            "ROLLBACK_COLLECTION_UNAVAILABLE",
            "after_rollback",
        ),
        "rollback_manifest": record(
            "rollback_manifest",
            bool(before_meta and rollback_meta == before_meta and rollback_meta.get("collection") == previous),
            "ROLLBACK_MANIFEST_MISMATCH",
            "after_rollback",
        ),
        "rollback_smoke": record("rollback_smoke", _smoke_ok(rollback, previous), "ROLLBACK_SMOKE_FAILED", "after_rollback"),
        "protected_collection_unchanged": record(
            "protected_collection_unchanged",
            bool(
                _protected_fingerprint(before)
                and _protected_fingerprint(before) == _protected_fingerprint(after) == _protected_fingerprint(rollback)
            ),
            "PROTECTED_COLLECTION_DRIFT",
        ),
    }
    return {
        "schema_version": REPORT_SCHEMA,
        "status": "passed" if all(checks.values()) else "failed",
        "target_collection": target if isinstance(target, str) else None,
        "rollback_collection": previous if previous_is_safe else None,
        "checks": checks,
        "errors": errors,
    }
