from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import warnings
import zipfile

import pytest

from release_artifact import assemble_release_artifact
from release_evidence_bundle import ReleaseEvidenceBundleError, create_bundle_bytes, verify_bundle_bytes


ROOT = Path(__file__).resolve().parents[1]
PHASES = ("before_switch", "after_switch", "after_rollback")
MEMBERS = (
    "before-switch.json",
    "after-switch.json",
    "after-rollback.json",
    "expected-manifest-identity.json",
    "release-drill-input.json",
    "validation-report.json",
    "bundle-manifest.json",
)
CREATE_CLI = ROOT / "scripts" / "create_release_evidence_bundle.py"
VERIFY_CLI = ROOT / "scripts" / "verify_release_evidence_bundle.py"


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
    assembled, _ = assemble_release_artifact(observations=observations, expected_manifest=drill["expected_release_manifest"])
    return observations, drill["expected_release_manifest"], assembled


def test_create_and_verify_deterministic_bundle():
    observations, manifest, assembled = _valid_inputs()
    arguments = {
        "observations": observations,
        "expected_manifest": manifest,
        "assembled_document": assembled,
        "release_head": "1" * 40,
        "created_at": "2026-07-18T12:15:00Z",
    }

    first, creator_summary = create_bundle_bytes(**arguments)
    second, _ = create_bundle_bytes(**arguments)

    assert first == second
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert tuple(archive.namelist()) == MEMBERS
    assert creator_summary["status"] == "created"
    assert creator_summary["member_count"] == 7

    verified = verify_bundle_bytes(first)
    assert verified == {
        "schema_version": "kaiyuan-release-evidence-bundle/v1",
        "status": "verified",
        "release_head": "1" * 40,
        "target_collection": "local_kb_kaiyuan_v2",
        "member_count": 7,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("release_head", "A" * 40),
        ("release_head", "1" * 39),
        ("release_head", "refs/heads/stable/kaiyuan-v2"),
        ("created_at", "2026-07-18T12:15:00+00:00"),
        ("created_at", "not-a-date"),
    ],
)
def test_creator_rejects_invalid_explicit_provenance(field, value):
    observations, manifest, assembled = _valid_inputs()
    arguments = {
        "observations": observations,
        "expected_manifest": manifest,
        "assembled_document": assembled,
        "release_head": "1" * 40,
        "created_at": "2026-07-18T12:15:00Z",
    }
    arguments[field] = value

    with pytest.raises(ReleaseEvidenceBundleError) as caught:
        create_bundle_bytes(**arguments)

    assert (caught.value.code, caught.value.field) == ("provenance_error", field)


def test_creator_rejects_supplied_assembled_document_drift():
    observations, manifest, assembled = _valid_inputs()
    assembled["after_switch"]["active_collection"] = "other"

    with pytest.raises(ReleaseEvidenceBundleError) as caught:
        create_bundle_bytes(
            observations=observations,
            expected_manifest=manifest,
            assembled_document=assembled,
            release_head="1" * 40,
            created_at="2026-07-18T12:15:00Z",
        )

    assert caught.value.code == "assembly_mismatch"


def _bundle_bytes():
    observations, manifest, assembled = _valid_inputs()
    return create_bundle_bytes(
        observations=observations,
        expected_manifest=manifest,
        assembled_document=assembled,
        release_head="1" * 40,
        created_at="2026-07-18T12:15:00Z",
    )[0]


def _rewrite_bundle(data, mutate):
    with zipfile.ZipFile(io.BytesIO(data)) as source:
        entries = [(info, source.read(info)) for info in source.infolist()]
    mutate(entries)
    output = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(output, "w") as target:
            for info, content in entries:
                target.writestr(info, content)
    return output.getvalue()


@pytest.mark.parametrize("case", ["comment", "extra", "compressed", "duplicate", "unexpected", "traversal"])
def test_verifier_rejects_noncanonical_archive_structure(case):
    def mutate(entries):
        if case == "comment":
            entries[0][0].comment = b"x"
        elif case == "extra":
            entries[0][0].extra = b"\x01\x00\x00\x00"
        elif case == "compressed":
            entries[0][0].compress_type = zipfile.ZIP_DEFLATED
        elif case == "duplicate":
            entries.append(entries[0])
        elif case == "unexpected":
            info = zipfile.ZipInfo("unexpected.json")
            entries.append((info, b"{}\n"))
        else:
            entries[0][0].filename = "../before-switch.json"

    tampered = _rewrite_bundle(_bundle_bytes(), mutate)

    with pytest.raises(ReleaseEvidenceBundleError) as caught:
        verify_bundle_bytes(tampered)

    assert caught.value.code == "archive_contract_error"


def test_verifier_rejects_member_hash_tampering():
    def mutate(entries):
        info, content = entries[0]
        entries[0] = (info, content + b" ")

    with pytest.raises(ReleaseEvidenceBundleError) as caught:
        verify_bundle_bytes(_rewrite_bundle(_bundle_bytes(), mutate))

    assert caught.value.code in {"inventory_mismatch", "member_size_mismatch", "member_hash_mismatch"}


@pytest.mark.parametrize("content", [b'{"schema_version":"x","schema_version":"y"}\n', b'{"value":NaN}\n'])
def test_verifier_rejects_duplicate_or_nonfinite_bundle_manifest_json(content):
    def mutate(entries):
        for index, (info, _) in enumerate(entries):
            if info.filename == "bundle-manifest.json":
                entries[index] = (info, content)

    with pytest.raises(ReleaseEvidenceBundleError) as caught:
        verify_bundle_bytes(_rewrite_bundle(_bundle_bytes(), mutate))

    assert caught.value.code == "bundle_manifest_error"


def test_verifier_rejects_semantic_tampering_after_inventory_is_recomputed():
    def mutate(entries):
        members = {info.filename: [info, content] for info, content in entries}
        observation = json.loads(members["after-switch.json"][1])
        observation["phase_name"] = "before_switch"
        changed = (json.dumps(observation, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
        members["after-switch.json"][1] = changed
        manifest = json.loads(members["bundle-manifest.json"][1])
        item = manifest["inventory"][1]
        item["size"] = len(changed)
        import hashlib

        item["sha256"] = "sha256:" + hashlib.sha256(changed).hexdigest()
        members["bundle-manifest.json"][1] = (
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        entries[:] = [(members[info.filename][0], members[info.filename][1]) for info, _ in entries]

    with pytest.raises(ReleaseEvidenceBundleError):
        verify_bundle_bytes(_rewrite_bundle(_bundle_bytes(), mutate))


def test_verifier_rejects_noncanonical_json_even_with_recomputed_inventory():
    def mutate(entries):
        members = {info.filename: [info, content] for info, content in entries}
        changed = members["before-switch.json"][1] + b" "
        members["before-switch.json"][1] = changed
        manifest = json.loads(members["bundle-manifest.json"][1])
        item = manifest["inventory"][0]
        item["size"] = len(changed)
        import hashlib

        item["sha256"] = "sha256:" + hashlib.sha256(changed).hexdigest()
        members["bundle-manifest.json"][1] = (
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        entries[:] = [(members[info.filename][0], members[info.filename][1]) for info, _ in entries]

    with pytest.raises(ReleaseEvidenceBundleError) as caught:
        verify_bundle_bytes(_rewrite_bundle(_bundle_bytes(), mutate))

    assert caught.value.code == "archive_contract_error"


def test_verifier_rejects_trailing_bytes_outside_deterministic_zip():
    with pytest.raises(ReleaseEvidenceBundleError) as caught:
        verify_bundle_bytes(_bundle_bytes() + b"SECRET")

    assert caught.value.code == "archive_contract_error"


def test_creator_normalizes_assembler_contract_error_without_input_content():
    observations, manifest, assembled = _valid_inputs()
    observations["after_switch"]["phase"]["health"]["ready"] = False

    with pytest.raises(ReleaseEvidenceBundleError) as caught:
        create_bundle_bytes(
            observations=observations,
            expected_manifest=manifest,
            assembled_document=assembled,
            release_head="1" * 40,
            created_at="2026-07-18T12:15:00Z",
        )

    assert (caught.value.code, caught.value.field) == ("input_contract_error", "release_artifact")
    assert "after_switch" not in str(caught.value)


def _write_cli_inputs(tmp_path):
    observations, manifest, assembled = _valid_inputs()
    paths = {}
    for name, value in observations.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        paths[name] = path
    paths["manifest"] = tmp_path / "manifest.json"
    paths["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    paths["assembled"] = tmp_path / "assembled.json"
    paths["assembled"].write_text(json.dumps(assembled), encoding="utf-8")
    return paths


def _create_command(paths, output):
    return [
        sys.executable,
        str(CREATE_CLI),
        "--before-switch",
        str(paths["before_switch"]),
        "--after-switch",
        str(paths["after_switch"]),
        "--after-rollback",
        str(paths["after_rollback"]),
        "--expected-manifest",
        str(paths["manifest"]),
        "--assembled-input",
        str(paths["assembled"]),
        "--release-head",
        "1" * 40,
        "--created-at",
        "2026-07-18T12:15:00Z",
        "--out",
        str(output),
    ]


def test_create_and_verify_clis_publish_once_without_temp_residue(tmp_path):
    paths = _write_cli_inputs(tmp_path)
    output = tmp_path / "release-evidence.zip"

    created = subprocess.run(_create_command(paths, output), text=True, capture_output=True, check=False)
    assert created.returncode == 0
    summary = json.loads(created.stdout)
    assert summary["status"] == "created"
    assert summary["bundle_sha256"].startswith("sha256:")
    assert output.exists()

    verified = subprocess.run(
        [sys.executable, str(VERIFY_CLI), "--bundle", str(output)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert verified.returncode == 0
    assert json.loads(verified.stdout)["status"] == "verified"

    repeated = subprocess.run(_create_command(paths, output), text=True, capture_output=True, check=False)
    assert repeated.returncode == 2
    assert repeated.stderr == "release evidence bundle input error: output_exists:out\n"
    assert not list(tmp_path.glob(".release-evidence.zip.*"))
