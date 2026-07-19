from __future__ import annotations

import json
from pathlib import Path

from release_artifact import assemble_release_artifact
from release_evidence_archive import build_archive_index
from release_evidence_bundle import create_bundle_bytes


ROOT = Path(__file__).resolve().parents[1]
PHASES = ("before_switch", "after_switch", "after_rollback")


def _release_inputs():
    drill = json.loads((ROOT / "tests" / "fixtures" / "release_drill_v1.json").read_text(encoding="utf-8"))
    drill["expected_release_manifest"]["source_manifest_hash"] = "sha256:" + "a" * 64
    drill["after_switch"]["meta"]["source_manifest_hash"] = "sha256:" + "a" * 64
    for phase_name in ("before_switch", "after_rollback"):
        drill[phase_name]["meta"]["source_manifest_hash"] = "sha256:" + "b" * 64
    for phase_name in PHASES:
        collections = drill[phase_name]["collections"]
        collections["local_kb_default"]["config_hash"] = "sha256:" + "c" * 64
        for collection_name, fingerprint in collections.items():
            if collection_name != "local_kb_default":
                marker = "e" if phase_name == "after_switch" else "d"
                fingerprint["config_hash"] = "sha256:" + marker * 64
    times = {
        "before_switch": "2026-07-18T12:00:00Z",
        "after_switch": "2026-07-18T12:05:00Z",
        "after_rollback": "2026-07-18T12:10:00Z",
    }
    observations = {
        name: {
            "schema_version": "kaiyuan-release-observation/v1",
            "phase_name": name,
            "captured_at": times[name],
            "phase": drill[name],
        }
        for name in PHASES
    }
    assembled, _ = assemble_release_artifact(observations=observations, expected_manifest=drill["expected_release_manifest"])
    return observations, drill["expected_release_manifest"], assembled


def _bundle(marker, created_at):
    observations, manifest, assembled = _release_inputs()
    return create_bundle_bytes(
        observations=observations,
        expected_manifest=manifest,
        assembled_document=assembled,
        release_head=marker * 40,
        created_at=created_at,
    )[0]


def test_build_is_deterministic_and_classifies_latest_and_pinned():
    bundles = {
        "release-old": _bundle("1", "2026-07-18T13:00:00Z"),
        "release-new": _bundle("2", "2026-07-18T15:00:00Z"),
        "release-mid": _bundle("3", "2026-07-18T14:00:00Z"),
    }
    provisional = build_archive_index(bundles=bundles, keep_latest=1, pinned_hashes=[])
    old_hash = next(entry["bundle_sha256"] for entry in provisional["entries"] if entry["logical_name"] == "release-old")

    first = build_archive_index(bundles=bundles, keep_latest=1, pinned_hashes=[old_hash])
    second = build_archive_index(bundles=dict(reversed(tuple(bundles.items()))), keep_latest=1, pinned_hashes=[old_hash])

    assert first == second
    assert first["schema_version"] == "kaiyuan-release-evidence-archive/v1"
    by_name = {entry["logical_name"]: entry for entry in first["entries"]}
    assert (by_name["release-new"]["classification"], by_name["release-new"]["reasons"]) == ("retain", ["latest"])
    assert (by_name["release-old"]["classification"], by_name["release-old"]["reasons"]) == ("retain", ["pinned"])
    assert (by_name["release-mid"]["classification"], by_name["release-mid"]["reasons"]) == (
        "cold_archive_eligible",
        ["outside_keep_latest"],
    )
