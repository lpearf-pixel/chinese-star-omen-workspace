"""Deterministic, non-deleting indexes for verified release evidence bundles."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
import hashlib
import io
import json
import re
from typing import Any
import zipfile

from release_evidence_bundle import (
    BUNDLE_SCHEMA,
    MANIFEST_MEMBER,
    ReleaseEvidenceBundleError,
    load_strict_json_bytes,
    verify_bundle_bytes,
)


ARCHIVE_SCHEMA = "kaiyuan-release-evidence-archive/v1"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
MAX_INDEX_BYTES = 4 * 1024 * 1024
ROOT_KEYS = {"schema_version", "policy", "entries"}
POLICY_KEYS = {"keep_latest", "pinned_bundle_hashes"}
ENTRY_KEYS = {
    "logical_name",
    "bundle_sha256",
    "bundle_schema",
    "release_head",
    "created_at",
    "target_collection",
    "classification",
    "reasons",
}


class ReleaseEvidenceArchiveError(RuntimeError):
    def __init__(self, code: str, field: str):
        self.code = code
        self.field = field
        super().__init__(f"{code}: {field}")


def canonical_index_bytes(index: Mapping[str, object]) -> bytes:
    try:
        return (json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode(
            "utf-8"
        )
    except (UnicodeError, TypeError, ValueError, RecursionError) as exc:
        raise ReleaseEvidenceArchiveError("index_contract_error", "index") from exc


def _created_at(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ" if "." in value else "%Y-%m-%dT%H:%M:%SZ")


def _bundle_manifest(data: bytes) -> dict[str, Any]:
    try:
        verify_bundle_bytes(data)
        with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
            manifest = load_strict_json_bytes(archive.read(MANIFEST_MEMBER), "bundle_manifest")
    except (ReleaseEvidenceBundleError, OSError, ValueError, zipfile.BadZipFile) as exc:
        raise ReleaseEvidenceArchiveError("bundle_verification_failed", "bundle") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != BUNDLE_SCHEMA:
        raise ReleaseEvidenceArchiveError("bundle_verification_failed", "bundle")
    return manifest


def build_archive_index(
    *,
    bundles: Mapping[str, bytes],
    keep_latest: int,
    pinned_hashes: Sequence[str],
) -> dict[str, object]:
    if isinstance(keep_latest, bool) or not isinstance(keep_latest, int) or not 1 <= keep_latest <= 10_000:
        raise ReleaseEvidenceArchiveError("policy_error", "keep_latest")
    if not isinstance(bundles, Mapping) or not bundles:
        raise ReleaseEvidenceArchiveError("logical_name_error", "bundles")
    if not isinstance(pinned_hashes, Sequence) or isinstance(pinned_hashes, (str, bytes)):
        raise ReleaseEvidenceArchiveError("policy_error", "pinned_hashes")
    pins = list(pinned_hashes)
    if any(not isinstance(value, str) or HASH_RE.fullmatch(value) is None for value in pins) or len(set(pins)) != len(pins):
        raise ReleaseEvidenceArchiveError("policy_error", "pinned_hashes")

    entries = []
    seen_hashes = set()
    for logical_name, data in bundles.items():
        if not isinstance(logical_name, str) or NAME_RE.fullmatch(logical_name) is None:
            raise ReleaseEvidenceArchiveError("logical_name_error", "bundle")
        if not isinstance(data, bytes):
            raise ReleaseEvidenceArchiveError("bundle_verification_failed", "bundle")
        bundle_hash = "sha256:" + hashlib.sha256(data).hexdigest()
        if bundle_hash in seen_hashes:
            raise ReleaseEvidenceArchiveError("duplicate_bundle_hash", "bundle")
        seen_hashes.add(bundle_hash)
        manifest = _bundle_manifest(data)
        entries.append(
            {
                "logical_name": logical_name,
                "bundle_sha256": bundle_hash,
                "bundle_schema": manifest["schema_version"],
                "release_head": manifest["release_head"],
                "created_at": manifest["created_at"],
                "target_collection": manifest["target_collection"],
            }
        )
    if any(pin not in seen_hashes for pin in pins):
        raise ReleaseEvidenceArchiveError("unknown_pin", "pinned_hashes")

    latest = set()
    targets = sorted({entry["target_collection"] for entry in entries})
    for target in targets:
        group = [entry for entry in entries if entry["target_collection"] == target]
        group.sort(key=lambda item: (item["release_head"], item["bundle_sha256"]))
        group.sort(key=lambda item: _created_at(item["created_at"]), reverse=True)
        latest.update(entry["bundle_sha256"] for entry in group[:keep_latest])
    pin_set = set(pins)
    for entry in entries:
        reasons = []
        if entry["bundle_sha256"] in pin_set:
            reasons.append("pinned")
        if entry["bundle_sha256"] in latest:
            reasons.append("latest")
        if reasons:
            entry["classification"] = "retain"
            entry["reasons"] = reasons
        else:
            entry["classification"] = "cold_archive_eligible"
            entry["reasons"] = ["outside_keep_latest"]
    entries.sort(key=lambda item: (item["target_collection"], _created_at(item["created_at"]), item["release_head"], item["bundle_sha256"]))
    return {
        "schema_version": ARCHIVE_SCHEMA,
        "policy": {"keep_latest": keep_latest, "pinned_bundle_hashes": sorted(pins)},
        "entries": entries,
    }


def _validate_index_shape(index: Any) -> tuple[Mapping[str, Any], list[Mapping[str, Any]]]:
    if not isinstance(index, Mapping) or set(index) != ROOT_KEYS or index.get("schema_version") != ARCHIVE_SCHEMA:
        raise ReleaseEvidenceArchiveError("index_contract_error", "index")
    policy = index.get("policy")
    entries = index.get("entries")
    if not isinstance(policy, Mapping) or set(policy) != POLICY_KEYS:
        raise ReleaseEvidenceArchiveError("index_contract_error", "policy")
    if not isinstance(entries, list) or not entries:
        raise ReleaseEvidenceArchiveError("index_contract_error", "entries")
    names = set()
    hashes = set()
    validated_entries = []
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != ENTRY_KEYS:
            raise ReleaseEvidenceArchiveError("index_contract_error", "entry")
        name = entry.get("logical_name")
        bundle_hash = entry.get("bundle_sha256")
        if (
            not isinstance(name, str)
            or NAME_RE.fullmatch(name) is None
            or name in names
            or not isinstance(bundle_hash, str)
            or HASH_RE.fullmatch(bundle_hash) is None
            or bundle_hash in hashes
            or entry.get("bundle_schema") != BUNDLE_SCHEMA
            or not isinstance(entry.get("release_head"), str)
            or not isinstance(entry.get("created_at"), str)
            or not isinstance(entry.get("target_collection"), str)
            or entry.get("classification") not in {"retain", "cold_archive_eligible"}
            or not isinstance(entry.get("reasons"), list)
        ):
            raise ReleaseEvidenceArchiveError("index_contract_error", "entry")
        names.add(name)
        hashes.add(bundle_hash)
        validated_entries.append(entry)
    return policy, validated_entries


def verify_archive_index(*, index_bytes: bytes, bundles: Mapping[str, bytes]) -> dict[str, object]:
    if not isinstance(index_bytes, bytes) or len(index_bytes) > MAX_INDEX_BYTES:
        raise ReleaseEvidenceArchiveError("index_contract_error", "index")
    try:
        index = load_strict_json_bytes(index_bytes, "archive_index")
    except ReleaseEvidenceBundleError as exc:
        raise ReleaseEvidenceArchiveError("index_contract_error", "index") from exc
    if not isinstance(index, Mapping) or canonical_index_bytes(index) != index_bytes:
        raise ReleaseEvidenceArchiveError("index_contract_error", "canonical_json")
    policy, entries = _validate_index_shape(index)
    if not isinstance(bundles, Mapping) or set(bundles) != {entry["logical_name"] for entry in entries}:
        raise ReleaseEvidenceArchiveError("index_mismatch", "bundle_map")
    try:
        rebuilt = build_archive_index(
            bundles=bundles,
            keep_latest=policy["keep_latest"],
            pinned_hashes=policy["pinned_bundle_hashes"],
        )
    except ReleaseEvidenceArchiveError:
        raise
    if rebuilt != index:
        raise ReleaseEvidenceArchiveError("index_mismatch", "index")
    retain_count = sum(entry["classification"] == "retain" for entry in entries)
    return {
        "schema_version": ARCHIVE_SCHEMA,
        "status": "verified",
        "bundle_count": len(entries),
        "retain_count": retain_count,
        "cold_archive_eligible_count": len(entries) - retain_count,
    }
