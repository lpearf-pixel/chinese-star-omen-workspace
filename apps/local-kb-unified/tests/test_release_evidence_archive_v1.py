from __future__ import annotations

import json
from pathlib import Path
from copy import deepcopy
import subprocess
import sys

import pytest

from release_artifact import assemble_release_artifact
from release_evidence_archive import ReleaseEvidenceArchiveError, build_archive_index, canonical_index_bytes, verify_archive_index
from release_evidence_bundle import create_bundle_bytes


ROOT = Path(__file__).resolve().parents[1]
PHASES = ("before_switch", "after_switch", "after_rollback")
CREATE_CLI = ROOT / "scripts" / "create_release_evidence_archive.py"
VERIFY_CLI = ROOT / "scripts" / "verify_release_evidence_archive.py"


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


@pytest.mark.parametrize("value", [True, 0, -1, "1", 10_001])
def test_keep_latest_policy_fails_closed(value):
    with pytest.raises(ReleaseEvidenceArchiveError) as caught:
        build_archive_index(bundles={"release": _bundle("1", "2026-07-18T13:00:00Z")}, keep_latest=value, pinned_hashes=[])
    assert (caught.value.code, caught.value.field) == ("policy_error", "keep_latest")


@pytest.mark.parametrize("name", ["", "../release", "a/b", " release", "x" * 129, "évidence"])
def test_unsafe_logical_names_fail_closed(name):
    with pytest.raises(ReleaseEvidenceArchiveError) as caught:
        build_archive_index(bundles={name: _bundle("1", "2026-07-18T13:00:00Z")}, keep_latest=1, pinned_hashes=[])
    assert caught.value.code == "logical_name_error"


def test_duplicate_bundle_bytes_under_two_names_fail_closed():
    bundle = _bundle("1", "2026-07-18T13:00:00Z")
    with pytest.raises(ReleaseEvidenceArchiveError) as caught:
        build_archive_index(bundles={"one": bundle, "two": bundle}, keep_latest=1, pinned_hashes=[])
    assert caught.value.code == "duplicate_bundle_hash"


@pytest.mark.parametrize(
    "pins",
    [["sha256:" + "A" * 64], ["sha256:" + "a" * 64] * 2, ["sha256:" + "f" * 64], [[]]],
)
def test_invalid_duplicate_or_unknown_pins_fail_closed(pins):
    with pytest.raises(ReleaseEvidenceArchiveError) as caught:
        build_archive_index(
            bundles={"release": _bundle("1", "2026-07-18T13:00:00Z")},
            keep_latest=1,
            pinned_hashes=pins,
        )
    expected = "unknown_pin" if pins == ["sha256:" + "f" * 64] else "policy_error"
    assert caught.value.code == expected


def test_invalid_or_trailing_bundle_bytes_fail_closed_without_lower_level_error():
    with pytest.raises(ReleaseEvidenceArchiveError) as caught:
        build_archive_index(
            bundles={"release": _bundle("1", "2026-07-18T13:00:00Z") + b"SECRET"},
            keep_latest=1,
            pinned_hashes=[],
        )
    assert (caught.value.code, caught.value.field) == ("bundle_verification_failed", "bundle")


def test_pin_and_latest_overlap_has_fixed_reason_order():
    bundle = _bundle("1", "2026-07-18T13:00:00Z")
    bundle_hash = "sha256:" + __import__("hashlib").sha256(bundle).hexdigest()
    index = build_archive_index(bundles={"release": bundle}, keep_latest=1, pinned_hashes=[bundle_hash])
    assert index["entries"][0]["reasons"] == ["pinned", "latest"]


def test_verify_rebuilds_exact_canonical_index_and_bundle_map():
    bundles = {
        "old": _bundle("1", "2026-07-18T13:00:00Z"),
        "new": _bundle("2", "2026-07-18T14:00:00Z"),
    }
    index = build_archive_index(bundles=bundles, keep_latest=1, pinned_hashes=[])
    encoded = canonical_index_bytes(index)

    assert verify_archive_index(index_bytes=encoded, bundles=bundles) == {
        "schema_version": "kaiyuan-release-evidence-archive/v1",
        "status": "verified",
        "bundle_count": 2,
        "retain_count": 1,
        "cold_archive_eligible_count": 1,
    }


@pytest.mark.parametrize("case", ["extra_key", "classification", "order", "noncanonical", "missing_bundle"])
def test_verify_rejects_index_or_bundle_map_drift(case):
    bundles = {
        "old": _bundle("1", "2026-07-18T13:00:00Z"),
        "new": _bundle("2", "2026-07-18T14:00:00Z"),
    }
    index = build_archive_index(bundles=bundles, keep_latest=1, pinned_hashes=[])
    changed = deepcopy(index)
    verify_bundles = dict(bundles)
    if case == "extra_key":
        changed["source_path"] = "/tmp/secret"
    elif case == "classification":
        changed["entries"][0]["classification"] = "retain"
    elif case == "order":
        changed["entries"].reverse()
    elif case == "missing_bundle":
        verify_bundles.pop("old")
    encoded = canonical_index_bytes(changed)
    if case == "noncanonical":
        encoded += b" "

    with pytest.raises(ReleaseEvidenceArchiveError) as caught:
        verify_archive_index(index_bytes=encoded, bundles=verify_bundles)

    assert caught.value.code in {"index_contract_error", "index_mismatch"}


def _write_bundles(tmp_path):
    paths = {}
    for name, marker, created_at in (
        ("old", "1", "2026-07-18T13:00:00Z"),
        ("new", "2", "2026-07-18T14:00:00Z"),
    ):
        path = tmp_path / f"{name}.zip"
        path.write_bytes(_bundle(marker, created_at))
        paths[name] = path
    return paths


def _bindings(paths):
    result = []
    for name, path in paths.items():
        result.extend(["--bundle", f"{name}={path}"])
    return result


def test_create_and_verify_archive_clis_are_atomic_and_path_free(tmp_path):
    paths = _write_bundles(tmp_path)
    output = tmp_path / "archive-index.json"
    create_command = [
        sys.executable,
        str(CREATE_CLI),
        *_bindings(paths),
        "--keep-latest",
        "1",
        "--out",
        str(output),
    ]

    created = subprocess.run(create_command, text=True, capture_output=True, check=False)
    assert created.returncode == 0
    assert json.loads(created.stdout)["status"] == "created"
    assert str(tmp_path) not in output.read_text(encoding="utf-8")

    verified = subprocess.run(
        [sys.executable, str(VERIFY_CLI), "--index", str(output), *_bindings(paths)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert verified.returncode == 0
    assert json.loads(verified.stdout)["status"] == "verified"

    repeated = subprocess.run(create_command, text=True, capture_output=True, check=False)
    assert repeated.returncode == 2
    assert repeated.stderr == "release evidence archive input error: output_exists:out\n"
    assert not list(tmp_path.glob(".archive-index.json.*"))


@pytest.mark.parametrize("bindings", [["unsafe/path=/tmp/a"], ["same=/tmp/a", "same=/tmp/b"], ["missing-separator"]])
def test_cli_rejects_unsafe_duplicate_or_malformed_bindings_without_echoing_paths(tmp_path, bindings):
    command = [sys.executable, str(CREATE_CLI)]
    for binding in bindings:
        command.extend(["--bundle", binding])
    command.extend(["--keep-latest", "1", "--out", str(tmp_path / "index.json")])

    result = subprocess.run(command, text=True, capture_output=True, check=False)

    assert result.returncode == 2
    assert result.stderr == "release evidence archive input error: invalid_bundle_binding:bundle\n"
    assert "/tmp/a" not in result.stderr


def test_latest_sort_preserves_far_future_microsecond_precision():
    bundles = {
        "older": _bundle("1", "9999-01-01T00:00:00.000001Z"),
        "newer": _bundle("2", "9999-01-01T00:00:00.000002Z"),
    }

    index = build_archive_index(bundles=bundles, keep_latest=1, pinned_hashes=[])
    by_name = {entry["logical_name"]: entry for entry in index["entries"]}

    assert by_name["newer"]["classification"] == "retain"
    assert by_name["older"]["classification"] == "cold_archive_eligible"


def test_bounded_reader_never_requests_more_than_limit_plus_one():
    from scripts.create_release_evidence_archive import _read_bounded

    class GuardedStream:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, size):
            assert size == 6
            return b"x" * size

    class GuardedPath:
        def open(self, mode):
            assert mode == "rb"
            return GuardedStream()

    with pytest.raises(ReleaseEvidenceArchiveError) as caught:
        _read_bounded(GuardedPath(), limit=5, field="bundle")

    assert caught.value.code == "input_too_large"


def test_makefiles_do_not_encode_whitespace_unsafe_bundle_lists():
    assert "create-release-evidence-archive:" not in (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "create-release-evidence-archive:" not in (ROOT.parents[1] / "Makefile").read_text(encoding="utf-8")
