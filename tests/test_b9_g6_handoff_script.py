from __future__ import annotations

import hashlib
import json
import os
import plistlib
import subprocess
import sys
import tarfile
from pathlib import Path

from scripts import b9_g6_handoff as handoff


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/b9_g6_handoff.py"
REQUIRED_SOURCE_FILES = (
    "local-capability-evidence.json",
    "renderer-review-input.json",
    "renderer-hard-gate.json",
    "ai-assisted-visual-review.json",
    "human-experience-confirmation.json",
    "assisted-renderer-review.json",
    "ocr-observations.json",
    "ffprobe-preview.json",
    "preview.mp4",
    "scene.ssc",
    "preview-command.json",
    "package-manifest.json",
)
SCREENSHOTS = {
    "01-stellarium-overview.png": b"overview-png",
    "subtitle-01.png": b"subtitle-one-png",
}
EXPECTED_MEMBER_NAMES = [
    *REQUIRED_SOURCE_FILES,
    "screenshot-sha256.txt",
    "screenshots",
    "screenshots/01-stellarium-overview.png",
    "screenshots/subtitle-01.png",
]


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def make_stellarium_app(root: Path, *, version: str = "26.1") -> Path:
    app = root / "Stellarium.app"
    contents = app / "Contents"
    contents.mkdir(parents=True)
    with (contents / "Info.plist").open("wb") as handle:
        plistlib.dump({"CFBundleShortVersionString": version}, handle)
    return app


def make_evidence(root: Path, *, capability_version: str = "26.1.0") -> Path:
    evidence = root / "evidence"
    screenshots = evidence / "screenshots"
    screenshots.mkdir(parents=True)
    for filename in REQUIRED_SOURCE_FILES:
        path = evidence / filename
        if filename == "local-capability-evidence.json":
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "local-capability-evidence/v1",
                        "stellarium_version": capability_version,
                    }
                ),
                encoding="utf-8",
            )
        else:
            path.write_bytes(f"fixture:{filename}".encode())
    for filename, content in SCREENSHOTS.items():
        (screenshots / filename).write_bytes(content)
    (evidence / "screenshot-sha256.txt").write_text(
        "bad  /Users/example/private.png\n",
        encoding="utf-8",
    )
    (evidence / "collector.log").write_text("private log\n", encoding="utf-8")
    (evidence / "._preview.mp4").write_bytes(b"appledouble")
    (screenshots / "._subtitle-01.png").write_bytes(b"appledouble")
    return evidence


def run_handoff(
    root: Path,
    *,
    stellarium_version: str = "26.1",
    capability_version: str = "26.1.0",
    output_name: str = "evidence.tar.gz",
) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    app = make_stellarium_app(root, version=stellarium_version)
    evidence = make_evidence(root, capability_version=capability_version)
    output = root / output_name
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--evidence-dir",
            str(evidence),
            "--stellarium-app",
            str(app),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    return completed, evidence, output


def archive_names(path: Path) -> list[str]:
    with tarfile.open(path, "r:gz") as archive:
        return archive.getnames()


def read_archive_member(path: Path, name: str) -> bytes:
    with tarfile.open(path, "r:gz") as archive:
        member = archive.extractfile(name)
        assert member is not None
        return member.read()


def test_rejects_capability_version_that_differs_from_actual_app(tmp_path: Path) -> None:
    completed, _, output = run_handoff(
        tmp_path,
        stellarium_version="26.1",
        capability_version="26.2.0",
    )

    assert completed.returncode == 1
    assert (
        "capability Stellarium version 26.2.0 does not match "
        "the installed Stellarium version 26.1.0"
    ) in completed.stderr
    assert not output.exists()


def test_prints_normalized_app_version_before_capability_build(tmp_path: Path) -> None:
    app = make_stellarium_app(tmp_path, version="26.1")

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--stellarium-app",
            str(app),
            "--print-stellarium-version",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "26.1.0\n"


def test_capability_version_uses_the_same_file_identity_as_archive(
    tmp_path: Path,
) -> None:
    evidence = make_evidence(tmp_path, capability_version="26.1.0")
    path = evidence / "local-capability-evidence.json"
    original = path.read_bytes()
    source = handoff._regular_source(
        path,
        archive_name="local-capability-evidence.json",
    )
    version, bound_source = handoff._bind_capability_source(source)
    path.write_text(
        json.dumps(
            {
                "schema_version": "local-capability-evidence/v1",
                "stellarium_version": "26.2.0",
            }
        ),
        encoding="utf-8",
    )

    assert version == "26.1.0"
    assert bound_source.content == original


def test_builds_fixed_archive_with_relative_inventory(tmp_path: Path) -> None:
    completed, evidence, output = run_handoff(tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert archive_names(output) == EXPECTED_MEMBER_NAMES
    expected_inventory = "".join(
        f"{sha256(content)}  screenshots/{filename}\n"
        for filename, content in SCREENSHOTS.items()
    ).encode()
    assert read_archive_member(output, "screenshot-sha256.txt") == expected_inventory
    assert (evidence / "screenshot-sha256.txt").read_text(encoding="utf-8").startswith(
        "bad  /Users/"
    )


def test_excludes_appledouble_and_unrelated_files(tmp_path: Path) -> None:
    completed, _, output = run_handoff(tmp_path)

    assert completed.returncode == 0, completed.stderr
    names = archive_names(output)
    assert all(not Path(name).name.startswith("._") for name in names)
    assert "collector.log" not in names
    assert "screenshot-sha256.txt" in names


def test_rejects_symlinked_evidence_member(tmp_path: Path) -> None:
    app = make_stellarium_app(tmp_path)
    evidence = make_evidence(tmp_path)
    target = evidence / "preview.mp4"
    target.unlink()
    target.symlink_to(evidence / "scene.ssc")
    output = tmp_path / "evidence.tar.gz"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--evidence-dir",
            str(evidence),
            "--stellarium-app",
            str(app),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 1
    assert "preview.mp4 must be a regular non-symlink file" in completed.stderr
    assert not output.exists()


def test_existing_output_is_preserved(tmp_path: Path) -> None:
    app = make_stellarium_app(tmp_path)
    evidence = make_evidence(tmp_path)
    output = tmp_path / "evidence.tar.gz"
    output.write_bytes(b"keep-existing")

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--evidence-dir",
            str(evidence),
            "--stellarium-app",
            str(app),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 1
    assert "archive output already exists" in completed.stderr
    assert output.read_bytes() == b"keep-existing"


def test_identical_inputs_create_identical_archive_bytes(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first, _, first_output = run_handoff(first_root)
    second, _, second_output = run_handoff(second_root)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first_output.read_bytes() == second_output.read_bytes()


def test_rejects_non_26_stellarium_series(tmp_path: Path) -> None:
    completed, _, output = run_handoff(
        tmp_path,
        stellarium_version="27.0",
        capability_version="27.0.0",
    )

    assert completed.returncode == 1
    assert "Stellarium version must be in supported series 26.x" in completed.stderr
    assert not output.exists()


def test_rejects_more_than_thirty_screenshots(tmp_path: Path) -> None:
    app = make_stellarium_app(tmp_path)
    evidence = make_evidence(tmp_path)
    for index in range(29):
        (evidence / "screenshots" / f"extra-{index:02d}.png").write_bytes(
            f"extra-{index}".encode()
        )
    output = tmp_path / "evidence.tar.gz"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--evidence-dir",
            str(evidence),
            "--stellarium-app",
            str(app),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 1
    assert "evidence supports at most 30 screenshots" in completed.stderr
    assert not output.exists()
