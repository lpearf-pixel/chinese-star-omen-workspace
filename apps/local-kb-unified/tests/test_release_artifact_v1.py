from __future__ import annotations

import json
import os
from pathlib import Path
from copy import deepcopy
import hashlib
import subprocess
import sys

import pytest

from release_artifact import ReleaseArtifactError, assemble_release_artifact


ROOT = Path(__file__).resolve().parents[1]
PHASES = ("before_switch", "after_switch", "after_rollback")
CLI = ROOT / "scripts" / "assemble_release_artifact.py"


def _valid_inputs():
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
    return observations, drill["expected_release_manifest"]


def test_assemble_builds_exact_b6_input_and_passes_existing_validator():
    observations, manifest = _valid_inputs()

    document, report = assemble_release_artifact(
        observations=observations,
        expected_manifest=manifest,
    )

    assert set(document) == {
        "schema_version",
        "target_collection",
        "expected_release_manifest",
        "before_switch",
        "after_switch",
        "after_rollback",
    }
    assert document["schema_version"] == "kaiyuan-release-drill-input/v1"
    assert document["target_collection"] == "local_kb_kaiyuan_v2"
    assert report["status"] == "passed"


@pytest.mark.parametrize(
    "case",
    [
        "extra_key",
        "wrong_schema",
        "swapped_phase",
        "non_mapping_phase",
        "timezone_offset",
        "invalid_date",
        "non_increasing",
    ],
)
def test_observation_envelopes_and_chronology_fail_closed(case):
    observations, manifest = _valid_inputs()
    if case == "extra_key":
        observations["before_switch"]["unexpected"] = True
    elif case == "wrong_schema":
        observations["before_switch"]["schema_version"] = "kaiyuan-release-observation/v0"
    elif case == "swapped_phase":
        observations["before_switch"]["phase_name"] = "after_switch"
    elif case == "non_mapping_phase":
        observations["before_switch"]["phase"] = []
    elif case == "timezone_offset":
        observations["before_switch"]["captured_at"] = "2026-07-18T12:00:00+00:00"
    elif case == "invalid_date":
        observations["before_switch"]["captured_at"] = "not-a-date"
    elif case == "non_increasing":
        observations["after_switch"]["captured_at"] = observations["before_switch"]["captured_at"]

    with pytest.raises(ReleaseArtifactError) as caught:
        assemble_release_artifact(observations=observations, expected_manifest=manifest)

    expected = "timestamp_error" if case in {"timezone_offset", "invalid_date", "non_increasing"} else "observation_contract_error"
    assert caught.value.code == expected


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("corpus_version", ""),
        ("ingest_run_id", None),
        ("collection", "local_kb_other_v2"),
        ("schema_version", "corpus-manifest/v0"),
        ("managed_by", "other"),
        ("collection_schema", "passage-v1"),
    ],
)
def test_manifest_identity_is_projected_and_strict(field, value):
    observations, manifest = _valid_inputs()
    manifest = {**manifest, field: value, "unreviewed_payload": "SECRET"}

    with pytest.raises(ReleaseArtifactError) as caught:
        assemble_release_artifact(observations=observations, expected_manifest=manifest)

    assert caught.value.code == "manifest_contract_error"
    assert "SECRET" not in str(caught.value)


def test_b6_validation_failure_exposes_only_safe_report():
    observations, manifest = _valid_inputs()
    broken = deepcopy(observations)
    broken["after_switch"]["phase"]["collections"]["local_kb_default"]["config_hash"] = "sha256:" + "f" * 64

    with pytest.raises(ReleaseArtifactError) as caught:
        assemble_release_artifact(observations=broken, expected_manifest=manifest)

    assert caught.value.code == "drill_validation_failed"
    assert caught.value.report["status"] == "failed"
    assert caught.value.report["errors"] == [
        {"code": "PROTECTED_COLLECTION_DRIFT", "phase": "document", "field": "protected_collection_unchanged"}
    ]


@pytest.mark.parametrize(
    "inject",
    [
        lambda phase: phase.update({"raw_body": "SECRET SOURCE CONTENT"}),
        lambda phase: phase["health"].update({"raw_status": "SECRET"}),
        lambda phase: phase["smoke"]["primary_evidence"].update({"hits": [{"snippet": "SECRET"}]}),
        lambda phase: phase["meta"].update({"api_key": "SECRET"}),
        lambda phase: phase["collections"]["local_kb_default"].update({"payload": "SECRET"}),
    ],
)
def test_phase_projection_rejects_unallowlisted_content(inject):
    observations, manifest = _valid_inputs()
    inject(observations["after_switch"]["phase"])

    with pytest.raises(ReleaseArtifactError) as caught:
        assemble_release_artifact(observations=observations, expected_manifest=manifest)

    assert caught.value.code == "observation_contract_error"
    assert "SECRET" not in str(caught.value)


@pytest.mark.parametrize(
    "inject",
    [
        lambda phase: phase["health"].update({"status": {"api_key": "SECRET"}}),
        lambda phase: phase["smoke"]["structured_recall"].update({"status": {"raw_body": "SECRET"}}),
        lambda phase: phase["collections"]["local_kb_kaiyuan_v2"].update(
            {"config_hash": {"snippet": "SECRET"}}
        ),
    ],
)
def test_phase_allowed_values_cannot_carry_content(inject):
    observations, manifest = _valid_inputs()
    inject(observations["after_switch"]["phase"])

    with pytest.raises(ReleaseArtifactError) as caught:
        assemble_release_artifact(observations=observations, expected_manifest=manifest)

    assert caught.value.code == "observation_contract_error"
    assert "SECRET" not in str(caught.value)


@pytest.mark.parametrize("card_types", [1, None])
def test_non_iterable_card_types_is_stable_contract_error(card_types):
    observations, manifest = _valid_inputs()
    observations["after_switch"]["phase"]["smoke"]["structured_recall"]["card_types"] = card_types

    with pytest.raises(ReleaseArtifactError) as caught:
        assemble_release_artifact(observations=observations, expected_manifest=manifest)

    assert caught.value.code == "observation_contract_error"


def test_fingerprint_requires_real_sha256_hex():
    observations, manifest = _valid_inputs()
    observations["after_switch"]["phase"]["collections"]["local_kb_kaiyuan_v2"]["config_hash"] = (
        "sha256:SECRET_SOURCE_CONTENT"
    )

    with pytest.raises(ReleaseArtifactError) as caught:
        assemble_release_artifact(observations=observations, expected_manifest=manifest)

    assert caught.value.code == "observation_contract_error"


def _write_cli_inputs(tmp_path: Path):
    observations, manifest = _valid_inputs()
    paths = {}
    for name, payload in observations.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        paths[name] = path
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return paths, manifest_path


def _run_cli(paths, manifest_path, output):
    return subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--before-switch", str(paths["before_switch"]),
            "--after-switch", str(paths["after_switch"]),
            "--after-rollback", str(paths["after_rollback"]),
            "--expected-manifest", str(manifest_path),
            "--out", str(output),
        ],
        cwd=ROOT,
        env=dict(os.environ),
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_atomically_creates_validated_artifact_and_safe_hash_summary(tmp_path: Path):
    paths, manifest_path = _write_cli_inputs(tmp_path)
    output = tmp_path / "release-drill.actual.json"

    result = _run_cli(paths, manifest_path, output)

    assert result.returncode == 0
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["schema_version"] == "kaiyuan-release-drill-input/v1"
    summary = json.loads(result.stdout)
    assert summary["status"] == "assembled"
    assert summary["artifact_sha256"].startswith("sha256:")
    assert summary["artifact_sha256"] == "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest()
    assert "local_kb_default" not in result.stdout
    assert result.stderr == ""
    assert list(tmp_path.glob(".release-drill.actual.json.*")) == []


def test_cli_rejects_duplicate_json_key_without_output(tmp_path: Path):
    paths, manifest_path = _write_cli_inputs(tmp_path)
    paths["before_switch"].write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8")
    output = tmp_path / "release-drill.actual.json"

    result = _run_cli(paths, manifest_path, output)

    assert result.returncode == 2
    assert result.stderr == "release artifact input error: invalid_json:before_switch\n"
    assert not output.exists()


def test_cli_rejects_excessively_nested_json_without_traceback(tmp_path: Path):
    paths, manifest_path = _write_cli_inputs(tmp_path)
    paths["before_switch"].write_text("[" * 2000 + "0" + "]" * 2000, encoding="utf-8")
    output = tmp_path / "release-drill.actual.json"

    result = _run_cli(paths, manifest_path, output)

    assert result.returncode == 2
    assert result.stderr == "release artifact input error: invalid_json:before_switch\n"
    assert "Traceback" not in result.stderr
    assert not output.exists()


def test_cli_b6_failure_returns_safe_report_without_output(tmp_path: Path):
    paths, manifest_path = _write_cli_inputs(tmp_path)
    payload = json.loads(paths["after_switch"].read_text(encoding="utf-8"))
    payload["phase"]["collections"]["local_kb_default"]["config_hash"] = "sha256:" + "f" * 64
    paths["after_switch"].write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "release-drill.actual.json"

    result = _run_cli(paths, manifest_path, output)

    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "failed"
    assert result.stderr == "release artifact validation error: drill_validation_failed:document\n"
    assert not output.exists()


def test_cli_refuses_existing_output_without_modification(tmp_path: Path):
    paths, manifest_path = _write_cli_inputs(tmp_path)
    output = tmp_path / "release-drill.actual.json"
    output.write_bytes(b"existing\n")

    result = _run_cli(paths, manifest_path, output)

    assert result.returncode == 2
    assert result.stderr == "release artifact input error: output_exists:out\n"
    assert output.read_bytes() == b"existing\n"


def test_cli_parent_file_failure_has_stable_content_free_error(tmp_path: Path):
    paths, manifest_path = _write_cli_inputs(tmp_path)
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("private path sentinel", encoding="utf-8")

    result = _run_cli(paths, manifest_path, parent_file / "artifact.json")

    assert result.returncode == 2
    assert result.stderr == "release artifact input error: output_write_failed:out\n"
    assert "Traceback" not in result.stderr
    assert "not-a-directory" not in result.stderr


def test_cli_rejects_surrogate_identity_without_traceback(tmp_path: Path):
    paths, manifest_path = _write_cli_inputs(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["corpus_version"] = "release\ud800"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "artifact.json"

    result = _run_cli(paths, manifest_path, output)

    assert result.returncode == 2
    assert result.stderr == "release artifact input error: manifest_contract_error:corpus_version\n"
    assert "Traceback" not in result.stderr
    assert not output.exists()


def test_cli_unknown_argument_omits_untrusted_value(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, str(CLI), "--unknown", "SECRET-SENTINEL"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stderr == "release artifact input error: invalid_arguments:arguments\n"
    assert "SECRET-SENTINEL" not in result.stderr


@pytest.mark.parametrize("invalid_bytes", [b'{"value":NaN}', b"\xff\xfe"])
def test_cli_rejects_non_finite_or_invalid_utf8_without_output(tmp_path: Path, invalid_bytes: bytes):
    paths, manifest_path = _write_cli_inputs(tmp_path)
    paths["before_switch"].write_bytes(invalid_bytes)
    output = tmp_path / "release-drill.actual.json"

    result = _run_cli(paths, manifest_path, output)

    assert result.returncode == 2
    assert not output.exists()
    assert "NaN" not in result.stderr


def test_assembler_production_source_has_no_live_or_mutation_imports():
    source = "\n".join(
        (ROOT / name).read_text(encoding="utf-8")
        for name in ("release_artifact.py", "scripts/assemble_release_artifact.py")
    )
    for forbidden in (
        "import requests",
        "qdrant_client",
        ".upsert(",
        ".delete(",
        ".create_collection(",
        ".recreate_collection(",
        " ingest(",
    ):
        assert forbidden not in source
