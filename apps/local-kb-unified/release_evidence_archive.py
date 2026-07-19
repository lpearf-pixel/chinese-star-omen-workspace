"""Deterministic, non-deleting indexes for verified release evidence bundles."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import io
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


class ReleaseEvidenceArchiveError(RuntimeError):
    def __init__(self, code: str, field: str):
        self.code = code
        self.field = field
        super().__init__(f"{code}: {field}")


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
    if len(set(pins)) != len(pins) or any(not isinstance(value, str) or HASH_RE.fullmatch(value) is None for value in pins):
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
        group.sort(
            key=lambda item: (
                -_created_at(item["created_at"]).replace(tzinfo=timezone.utc).timestamp(),
                item["release_head"],
                item["bundle_sha256"],
            )
        )
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
