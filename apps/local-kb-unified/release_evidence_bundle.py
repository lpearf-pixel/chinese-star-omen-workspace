"""Deterministic offline evidence bundles for Kaiyuan release drills."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import hashlib
import io
import json
import re
from typing import Any
import zipfile

from release_artifact import PHASE_NAMES, ReleaseArtifactError, assemble_release_artifact
from release_drill import TARGET_COLLECTION, validate_release_drill


BUNDLE_SCHEMA = "kaiyuan-release-evidence-bundle/v1"
TOOL_NAME = "local-kb-unified/release-evidence-bundle"
TOOL_VERSION = "1"
MANIFEST_MEMBER = "bundle-manifest.json"
EVIDENCE_MEMBERS = (
    ("before-switch.json", "before_switch", "release_observation"),
    ("after-switch.json", "after_switch", "release_observation"),
    ("after-rollback.json", "after_rollback", "release_observation"),
    ("expected-manifest-identity.json", "expected_manifest", "manifest_identity"),
    ("release-drill-input.json", "assembled_document", "release_drill_input"),
    ("validation-report.json", "validation_report", "release_drill_report"),
)
MEMBER_NAMES = tuple(item[0] for item in EVIDENCE_MEMBERS) + (MANIFEST_MEMBER,)
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ZIP_MODE = 0o100644 << 16
MAX_BUNDLE_BYTES = 8 * 1024 * 1024
MAX_MEMBER_BYTES = 2 * 1024 * 1024
MANIFEST_KEYS = {"schema_version", "release_head", "created_at", "target_collection", "tool", "inventory"}


class ReleaseEvidenceBundleError(RuntimeError):
    def __init__(self, code: str, field: str):
        self.code = code
        self.field = field
        super().__init__(f"{code}: {field}")


def _reject_constant(value: str):
    raise ValueError("non-finite token")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def load_strict_json_bytes(data: bytes, field: str):
    try:
        value = json.loads(
            data.decode("utf-8"),
            parse_constant=_reject_constant,
            object_pairs_hook=_unique_object,
        )
        _require_bounded_json(value)
        return value
    except (UnicodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise ReleaseEvidenceBundleError("invalid_json", field) from exc


def _require_bounded_json(value: Any, *, max_depth: int = 128, max_nodes: int = 100_000) -> None:
    pending = [(value, 0)]
    visited = 0
    while pending:
        item, depth = pending.pop()
        visited += 1
        if depth > max_depth or visited > max_nodes:
            raise ValueError("JSON structure exceeds safety limit")
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode(
        "utf-8"
    )


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = ZIP_MODE
    return info


def _timestamp(value: str) -> bool:
    if not isinstance(value, str) or UTC_RE.fullmatch(value) is None:
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ" if "." in value else "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def create_bundle_bytes(
    *,
    observations: Mapping[str, object],
    expected_manifest: Mapping[str, object],
    assembled_document: Mapping[str, object],
    release_head: str,
    created_at: str,
) -> tuple[bytes, dict[str, object]]:
    if not isinstance(release_head, str) or HEAD_RE.fullmatch(release_head) is None:
        raise ReleaseEvidenceBundleError("provenance_error", "release_head")
    if not _timestamp(created_at):
        raise ReleaseEvidenceBundleError("provenance_error", "created_at")
    if not isinstance(assembled_document, Mapping):
        raise ReleaseEvidenceBundleError("assembly_mismatch", "assembled_document")
    try:
        rebuilt, report = assemble_release_artifact(observations=observations, expected_manifest=expected_manifest)
    except ReleaseArtifactError as exc:
        code = "drill_validation_failed" if exc.code == "drill_validation_failed" else "input_contract_error"
        raise ReleaseEvidenceBundleError(code, "release_artifact") from exc
    if dict(assembled_document) != rebuilt:
        raise ReleaseEvidenceBundleError("assembly_mismatch", "assembled_document")

    values = {
        **{name: observations[name] for name in PHASE_NAMES},
        "expected_manifest": rebuilt["expected_release_manifest"],
        "assembled_document": rebuilt,
        "validation_report": report,
    }
    members: dict[str, bytes] = {}
    inventory = []
    for member_name, value_name, role in EVIDENCE_MEMBERS:
        encoded = _canonical_json(values[value_name])
        members[member_name] = encoded
        inventory.append(
            {
                "name": member_name,
                "role": role,
                "size": len(encoded),
                "sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(),
            }
        )
    bundle_manifest = {
        "schema_version": BUNDLE_SCHEMA,
        "release_head": release_head,
        "created_at": created_at,
        "target_collection": TARGET_COLLECTION,
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "inventory": inventory,
    }
    members[MANIFEST_MEMBER] = _canonical_json(bundle_manifest)

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
        for name in MEMBER_NAMES:
            archive.writestr(_zip_info(name), members[name])
    data = output.getvalue()
    return data, {
        "schema_version": BUNDLE_SCHEMA,
        "status": "created",
        "release_head": release_head,
        "target_collection": TARGET_COLLECTION,
        "member_count": len(MEMBER_NAMES),
    }


def verify_bundle_bytes(data: bytes) -> dict[str, object]:
    if not isinstance(data, bytes) or len(data) > MAX_BUNDLE_BYTES:
        raise ReleaseEvidenceBundleError("archive_contract_error", "bundle")
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
            infos = archive.infolist()
            if archive.comment or tuple(info.filename for info in infos) != MEMBER_NAMES or any(
                info.date_time != ZIP_TIMESTAMP
                or info.compress_type != zipfile.ZIP_STORED
                or info.flag_bits & 1
                or info.comment
                or info.extra
                or info.create_system != 3
                or info.external_attr != ZIP_MODE
                or info.file_size > MAX_MEMBER_BYTES
                for info in infos
            ):
                raise ReleaseEvidenceBundleError("archive_contract_error", "members")
            members = {info.filename: archive.read(info) for info in infos}
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise ReleaseEvidenceBundleError("archive_contract_error", "bundle") from exc

    try:
        manifest = load_strict_json_bytes(members[MANIFEST_MEMBER], "bundle_manifest")
    except ReleaseEvidenceBundleError as exc:
        raise ReleaseEvidenceBundleError("bundle_manifest_error", "bundle_manifest") from exc
    if _canonical_json(manifest) != members[MANIFEST_MEMBER]:
        raise ReleaseEvidenceBundleError("bundle_manifest_error", "canonical_json")
    if (
        not isinstance(manifest, dict)
        or set(manifest) != MANIFEST_KEYS
        or manifest.get("schema_version") != BUNDLE_SCHEMA
        or manifest.get("target_collection") != TARGET_COLLECTION
        or manifest.get("tool") != {"name": TOOL_NAME, "version": TOOL_VERSION}
        or not HEAD_RE.fullmatch(manifest.get("release_head", ""))
        or not _timestamp(manifest.get("created_at"))
    ):
        raise ReleaseEvidenceBundleError("bundle_manifest_error", "provenance")
    inventory = manifest.get("inventory")
    if not isinstance(inventory, list) or len(inventory) != len(EVIDENCE_MEMBERS):
        raise ReleaseEvidenceBundleError("inventory_mismatch", "inventory")
    for expected, item in zip(EVIDENCE_MEMBERS, inventory):
        name, _, role = expected
        encoded = members[name]
        if not isinstance(item, dict) or item.get("name") != name or item.get("role") != role or set(item) != {
            "name",
            "role",
            "size",
            "sha256",
        }:
            raise ReleaseEvidenceBundleError("inventory_mismatch", name)
        if isinstance(item.get("size"), bool) or item.get("size") != len(encoded):
            raise ReleaseEvidenceBundleError("member_size_mismatch", name)
        if item.get("sha256") != "sha256:" + hashlib.sha256(encoded).hexdigest():
            raise ReleaseEvidenceBundleError("member_hash_mismatch", name)

    try:
        parsed = {name: load_strict_json_bytes(members[name], name) for name, _, _ in EVIDENCE_MEMBERS}
        observations = {name: parsed[member] for member, name, _ in EVIDENCE_MEMBERS[:3]}
        rebuilt, report = assemble_release_artifact(
            observations=observations,
            expected_manifest=parsed["expected-manifest-identity.json"],
        )
    except ReleaseArtifactError as exc:
        code = "drill_validation_failed" if exc.code == "drill_validation_failed" else "assembly_mismatch"
        raise ReleaseEvidenceBundleError(code, "evidence_members") from exc
    except (ReleaseEvidenceBundleError, KeyError, TypeError, ValueError) as exc:
        raise ReleaseEvidenceBundleError("assembly_mismatch", "evidence_members") from exc
    if any(_canonical_json(parsed[name]) != members[name] for name, _, _ in EVIDENCE_MEMBERS):
        raise ReleaseEvidenceBundleError("archive_contract_error", "canonical_json")
    if rebuilt != parsed["release-drill-input.json"]:
        raise ReleaseEvidenceBundleError("assembly_mismatch", "release_drill_input")
    if validate_release_drill(rebuilt) != parsed["validation-report.json"] or report != parsed["validation-report.json"]:
        raise ReleaseEvidenceBundleError("drill_validation_failed", "validation_report")
    expected_bytes, _ = create_bundle_bytes(
        observations=observations,
        expected_manifest=parsed["expected-manifest-identity.json"],
        assembled_document=parsed["release-drill-input.json"],
        release_head=manifest["release_head"],
        created_at=manifest["created_at"],
    )
    if data != expected_bytes:
        raise ReleaseEvidenceBundleError("archive_contract_error", "deterministic_bytes")
    return {
        "schema_version": BUNDLE_SCHEMA,
        "status": "verified",
        "release_head": manifest["release_head"],
        "target_collection": TARGET_COLLECTION,
        "member_count": len(MEMBER_NAMES),
    }
