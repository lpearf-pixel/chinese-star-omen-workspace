from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from src.video_pipeline.feedback_loop.contracts_v1 import FeedbackLoopRunV1
from src.video_pipeline.package import PackageManifestV1, verify_package_members


APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parents[1]
CLI_PATH = APP_ROOT / "scripts" / "run_video_feedback_loop.py"
AUDIT_PATH = (
    APP_ROOT
    / "data"
    / "video_pipeline"
    / "external_media"
    / "祖山觀"
    / "audits"
    / "episode-22.bundle.json"
)
FIXTURE_ROOT = WORKSPACE_ROOT / "tests" / "fixtures" / "video-feedback-loop" / "v1"
PROBES_PATH = FIXTURE_ROOT / "episode-22-probes.json"
OUTCOME_PATH = FIXTURE_ROOT / "synthetic-human-outcome.json"
BASE_PACKAGE_PATHS = {
    "external-audit-bundle.json",
    "local-evidence-probes.json",
    "feedback-observations.json",
    "improvement-candidates.json",
    "video-production-request.json",
    "manual-publication-handoff.json",
    "feedback-loop-run.json",
    "manifest.json",
}


def subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    paths = [
        str(WORKSPACE_ROOT / "packages" / "kb-contracts" / "python"),
        str(WORKSPACE_ROOT / "packages" / "kb-text-core" / "python"),
    ]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        cwd=APP_ROOT,
        env=subprocess_env(),
        capture_output=True,
        text=True,
        check=False,
    )


def run_good_cli(output: Path, *, outcome: Path | None = None):
    args = [
        "--audit",
        str(AUDIT_PATH),
        "--probes",
        str(PROBES_PATH),
        "--output",
        str(output),
    ]
    if outcome is not None:
        args.extend(["--outcome", str(outcome)])
    return run_cli(*args)


def package_members(output: Path, manifest: PackageManifestV1) -> dict[str, bytes]:
    return {
        entry.path: (output / entry.path).read_bytes() for entry in manifest.members
    }


def assert_no_staging(output: Path) -> None:
    assert not list(output.parent.glob(f".{output.name}.*"))


def assert_failed_without_output(
    result: subprocess.CompletedProcess[str], output: Path
) -> None:
    assert result.returncode != 0
    assert result.stderr.strip()
    assert not output.exists()
    assert_no_staging(output)


def test_cli_publishes_a_complete_hash_verified_offline_package(tmp_path: Path) -> None:
    """Catches a CLI that omits lifecycle members or bypasses package verification."""
    output = tmp_path / "episode-22-run"

    result = run_good_cli(output)

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout.strip() == str(output)
    assert {path.name for path in output.iterdir()} == BASE_PACKAGE_PATHS
    manifest = PackageManifestV1.model_validate(
        json.loads((output / "manifest.json").read_bytes())
    )
    members = package_members(output, manifest)
    assert verify_package_members(manifest, members) is True
    run = FeedbackLoopRunV1.model_validate(
        json.loads((output / "feedback-loop-run.json").read_bytes())
    )
    assert run.source_id.endswith(":episode-22")
    assert {probe.claim_id for probe in run.local_probes} == {
        "claim:douyin:zushan:episode-22:01",
        "claim:douyin:zushan:episode-22:02",
    }
    assert run.outcome is None
    assert run.learning_update_proposal is None
    assert run.manual_publication_handoff.auto_publish_allowed is False
    assert all(item.apply_allowed is False for item in run.improvement_candidates)
    assert_no_staging(output)


def test_cli_optional_outcome_adds_only_a_non_applying_proposal(tmp_path: Path) -> None:
    """Catches an optional human decision being dropped or treated as authority."""
    output = tmp_path / "episode-22-outcome-run"

    result = run_good_cli(output, outcome=OUTCOME_PATH)

    assert result.returncode == 0, result.stderr
    assert {path.name for path in output.iterdir()} == BASE_PACKAGE_PATHS | {
        "feedback-outcome.json",
        "learning-update-proposal.json",
    }
    run = FeedbackLoopRunV1.model_validate(
        json.loads((output / "feedback-loop-run.json").read_bytes())
    )
    assert run.outcome is not None
    assert run.outcome.decision == "human_reviewed"
    assert run.learning_update_proposal is not None
    assert run.learning_update_proposal.apply_allowed is False
    assert_no_staging(output)


def test_cli_rejects_duplicate_json_keys_before_model_validation(tmp_path: Path) -> None:
    """Catches the JSON decoder silently keeping the last duplicate field."""
    raw = PROBES_PATH.read_bytes()
    duplicate = raw.replace(
        b'"schema_version":',
        b'"schema_version":"local-evidence-probe/v1","schema_version":',
        1,
    )
    probes = tmp_path / "duplicate-probes.json"
    probes.write_bytes(duplicate)
    output = tmp_path / "duplicate-run"

    result = run_cli(
        "--audit",
        str(AUDIT_PATH),
        "--probes",
        str(probes),
        "--output",
        str(output),
    )

    assert_failed_without_output(result, output)
    assert "duplicate" in result.stderr.lower()
    assert "schema_version" in result.stderr


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_cli_rejects_nonfinite_json_constants(
    tmp_path: Path, constant: str
) -> None:
    """Catches non-standard JSON numbers reaching Pydantic as numeric values."""
    probes = tmp_path / f"nonfinite-{constant.removeprefix('-')}.json"
    raw = PROBES_PATH.read_text(encoding="utf-8").replace(
        '"notes":[', f'"notes":[{constant},', 1
    )
    probes.write_text(raw, encoding="utf-8")
    output = tmp_path / f"nonfinite-{constant.removeprefix('-')}-run"

    result = run_cli(
        "--audit",
        str(AUDIT_PATH),
        "--probes",
        str(probes),
        "--output",
        str(output),
    )

    assert_failed_without_output(result, output)
    assert "non-finite" in result.stderr.lower()
    assert constant in result.stderr


def test_cli_rejects_malformed_probe_model_without_partial_output(tmp_path: Path) -> None:
    """Catches valid JSON with a contract-invalid probe state being published."""
    payload = json.loads(PROBES_PATH.read_bytes())
    payload[0]["result_state"] = "classical_source_confirmed"
    probes = tmp_path / "malformed-probes.json"
    probes.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    output = tmp_path / "malformed-run"

    result = run_cli(
        "--audit",
        str(AUDIT_PATH),
        "--probes",
        str(probes),
        "--output",
        str(output),
    )

    assert_failed_without_output(result, output)
    assert "result_state" in result.stderr
    assert "validation" in result.stderr.lower()


def test_cli_rejects_an_absent_output_parent_without_partial_output(
    tmp_path: Path,
) -> None:
    """Catches implicit parent creation or staging outside an approved directory."""
    output = tmp_path / "absent-parent" / "run"

    result = run_good_cli(output)

    assert_failed_without_output(result, output)
    assert "parent" in result.stderr.lower()


def test_cli_refuses_an_occupied_destination_without_modifying_it(
    tmp_path: Path,
) -> None:
    """Catches replacement or partial mutation of a pre-existing destination."""
    output = tmp_path / "occupied-run"
    output.mkdir()
    marker = output / "preserve.txt"
    marker.write_text("user-owned\n", encoding="utf-8")
    before_hash = hashlib.sha256(marker.read_bytes()).hexdigest()

    result = run_good_cli(output)

    assert result.returncode != 0
    assert result.stderr.strip()
    assert "exist" in result.stderr.lower() or "occupied" in result.stderr.lower()
    assert marker.read_text(encoding="utf-8") == "user-owned\n"
    assert hashlib.sha256(marker.read_bytes()).hexdigest() == before_hash
    assert {path.name for path in output.iterdir()} == {"preserve.txt"}
    assert_no_staging(output)


@pytest.mark.parametrize(
    ("variables", "missing_name"),
    [
        ({}, "VFL_AUDIT"),
        ({"VFL_AUDIT": str(AUDIT_PATH)}, "VFL_PROBES"),
        (
            {
                "VFL_AUDIT": str(AUDIT_PATH),
                "VFL_PROBES": str(PROBES_PATH),
            },
            "VFL_OUTPUT",
        ),
    ],
)
def test_make_target_requires_each_explicit_input(
    variables: dict[str, str], missing_name: str
) -> None:
    """Catches a root target silently choosing an input or output default."""
    result = subprocess.run(
        [
            "make",
            "-s",
            "vfl-s0-run",
            f"PYTHON={sys.executable}",
            *(f"{name}={value}" for name, value in variables.items()),
        ],
        cwd=WORKSPACE_ROOT,
        env=subprocess_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert missing_name in result.stderr
    assert "required" in result.stderr.lower()


def test_make_target_omits_empty_outcome_and_passes_nonempty_outcome(
    tmp_path: Path,
) -> None:
    """Catches an empty --outcome argument or failure to forward a supplied outcome."""
    without_outcome = tmp_path / "make-without-outcome"
    with_outcome = tmp_path / "make-with-outcome"
    common = [
        "make",
        "-s",
        "vfl-s0-run",
        f"PYTHON={sys.executable}",
        f"VFL_AUDIT={AUDIT_PATH}",
        f"VFL_PROBES={PROBES_PATH}",
    ]

    empty_result = subprocess.run(
        [*common, f"VFL_OUTPUT={without_outcome}", "VFL_OUTCOME="],
        cwd=WORKSPACE_ROOT,
        env=subprocess_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert empty_result.returncode == 0, empty_result.stderr
    assert not (without_outcome / "feedback-outcome.json").exists()

    outcome_result = subprocess.run(
        [
            *common,
            f"VFL_OUTPUT={with_outcome}",
            f"VFL_OUTCOME={OUTCOME_PATH}",
        ],
        cwd=WORKSPACE_ROOT,
        env=subprocess_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert outcome_result.returncode == 0, outcome_result.stderr
    assert (with_outcome / "feedback-outcome.json").is_file()
    proposal = json.loads(
        (with_outcome / "learning-update-proposal.json").read_bytes()
    )
    assert proposal["apply_allowed"] is False


def test_make_target_preserves_shell_metacharacters_in_all_path_values(
    tmp_path: Path,
) -> None:
    """Catches Make reparsing caller-supplied path bytes as shell source."""
    literal_output = tmp_path / "run-`printf vfl_substituted`"
    substituted_output = tmp_path / "run-vfl_substituted"
    common = [
        "make",
        "-s",
        "vfl-s0-run",
        f"PYTHON={sys.executable}",
        f"VFL_AUDIT={AUDIT_PATH}",
        f"VFL_PROBES={PROBES_PATH}",
        f"VFL_OUTPUT={literal_output}",
        "VFL_OUTCOME=",
    ]

    backtick_result = subprocess.run(
        common,
        cwd=WORKSPACE_ROOT,
        env=subprocess_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert backtick_result.returncode == 0, backtick_result.stderr
    assert not substituted_output.exists()
    assert (literal_output / "feedback-loop-run.json").is_file()

    quoted_audit = tmp_path / 'audit-"literal-quoted".json'
    quoted_probes = tmp_path / 'probes-"literal-quoted".json'
    quoted_outcome = tmp_path / 'outcome-"literal-quoted".json'
    quoted_output = tmp_path / 'run-"literal-quoted"'
    quoted_audit.write_bytes(AUDIT_PATH.read_bytes())
    quoted_probes.write_bytes(PROBES_PATH.read_bytes())
    quoted_outcome.write_bytes(OUTCOME_PATH.read_bytes())

    quote_result = subprocess.run(
        [
            "make",
            "-s",
            "vfl-s0-run",
            f"PYTHON={sys.executable}",
            f"VFL_AUDIT={quoted_audit}",
            f"VFL_PROBES={quoted_probes}",
            f"VFL_OUTPUT={quoted_output}",
            f"VFL_OUTCOME={quoted_outcome}",
        ],
        cwd=WORKSPACE_ROOT,
        env=subprocess_env(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert quote_result.returncode == 0, quote_result.stderr
    assert (quoted_output / "feedback-outcome.json").is_file()
    assert (quoted_output / "learning-update-proposal.json").is_file()
