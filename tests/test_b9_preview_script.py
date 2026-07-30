from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/b9_preview.py"


def write_executable(path: Path, source: str) -> Path:
    path.write_text(source, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def fake_ffmpeg(tmp_path: Path) -> Path:
    return write_executable(
        tmp_path / "fake-ffmpeg",
        f"""#!{sys.executable}
import json
import os
import pathlib
import sys

args = sys.argv[1:]
log = pathlib.Path(os.environ["FAKE_FFMPEG_LOG"])
with log.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(args) + "\\n")

mode = os.environ.get("FAKE_FFMPEG_MODE", "ok")
if args == ["-version"]:
    print("ffmpeg version 8.1.2")
    raise SystemExit(0)
if args == ["-hide_banner", "-filters"]:
    if mode != "missing-filter":
        print(" ... subtitles V->V Render text subtitles onto input video using libass")
    raise SystemExit(0)
if args == ["-hide_banner", "-encoders"]:
    print(" V....D libx264 H.264 / AVC / MPEG-4 AVC")
    raise SystemExit(0)

output = pathlib.Path(args[-1])
if output.name != "preview.mp4" and mode == "smoke-fails":
    print("No option name near 'smoke.srt'", file=sys.stderr)
    raise SystemExit(234)
if output.name == "preview.mp4" and mode == "final-fails-after-output":
    output.write_bytes(b"concurrent-or-partial-output")
    raise SystemExit(70)
output.write_bytes(b"fake-mp4")
""",
    )


def fake_ffprobe(tmp_path: Path) -> Path:
    return write_executable(
        tmp_path / "fake-ffprobe",
        f"""#!{sys.executable}
import pathlib
import sys

if sys.argv[1:] == ["-version"]:
    print("ffprobe version 8.1.2")
    raise SystemExit(0)
path = pathlib.Path(sys.argv[-1])
raise SystemExit(0 if path.is_file() and path.stat().st_size else 1)
""",
    )


def package_dir(tmp_path: Path) -> Path:
    package = tmp_path / "package"
    package.mkdir()
    (package / "subtitles.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n字幕测试\n",
        encoding="utf-8",
    )
    (package / "preview-command.json").write_text(
        json.dumps(
            {
                "schema_version": "preview-command/v1",
                "argv": [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-n",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=black:s=1080x1920:r=30:d=80.000",
                    "-vf",
                    "subtitles=subtitles.srt",
                    "-t",
                    "80.000",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    "preview.mp4",
                ],
                "timeout_seconds": 120,
                "output_path": "preview.mp4",
                "width": 1080,
                "height": 1920,
                "duration_ms": 80000,
                "shell": False,
            }
        ),
        encoding="utf-8",
    )
    return package


def run_preview(
    package: Path,
    ffmpeg: Path,
    ffprobe: Path,
    log: Path,
    *,
    mode: str = "ok",
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "B9_FFMPEG_BIN": str(ffmpeg),
            "B9_FFPROBE_BIN": str(ffprobe),
            "FAKE_FFMPEG_LOG": str(log),
            "FAKE_FFMPEG_MODE": mode,
        }
    )
    return subprocess.run(
        [sys.executable, str(RUNNER), "--package-dir", str(package)],
        cwd=ROOT,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )


def logged_calls(path: Path) -> list[list[str]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_preflight_rejects_missing_subtitles_filter_before_preview(tmp_path: Path) -> None:
    package = package_dir(tmp_path)
    log = tmp_path / "ffmpeg.log"

    completed = run_preview(
        package,
        fake_ffmpeg(tmp_path),
        fake_ffprobe(tmp_path),
        log,
        mode="missing-filter",
    )

    assert completed.returncode == 1
    assert "required FFmpeg filter missing: subtitles" in completed.stderr
    assert str(tmp_path / "fake-ffmpeg") in completed.stderr
    assert "B9_FFMPEG_BIN" in completed.stderr
    assert "B9_FFPROBE_BIN" in completed.stderr
    assert not (package / "preview.mp4").exists()
    assert all(call[-1:] != ["preview.mp4"] for call in logged_calls(log))


def test_preflight_rejects_advertised_filter_when_real_smoke_fails(
    tmp_path: Path,
) -> None:
    package = package_dir(tmp_path)
    log = tmp_path / "ffmpeg.log"

    completed = run_preview(
        package,
        fake_ffmpeg(tmp_path),
        fake_ffprobe(tmp_path),
        log,
        mode="smoke-fails",
    )

    assert completed.returncode == 1
    assert "FFmpeg subtitle smoke failed" in completed.stderr
    assert "B9_FFMPEG_BIN" in completed.stderr
    assert not (package / "preview.mp4").exists()
    assert all(call[-1:] != ["preview.mp4"] for call in logged_calls(log))


def test_verified_overrides_execute_frozen_preview_argv(tmp_path: Path) -> None:
    package = package_dir(tmp_path)
    log = tmp_path / "ffmpeg.log"
    ffmpeg = fake_ffmpeg(tmp_path)

    completed = run_preview(
        package,
        ffmpeg,
        fake_ffprobe(tmp_path),
        log,
    )

    assert completed.returncode == 0, completed.stderr
    assert "B9 preview created: preview.mp4" in completed.stdout
    assert (package / "preview.mp4").read_bytes() == b"fake-mp4"
    expected = json.loads(
        (package / "preview-command.json").read_text(encoding="utf-8")
    )["argv"][1:]
    assert logged_calls(log)[-1] == expected


def test_existing_preview_fails_without_invoking_ffmpeg(tmp_path: Path) -> None:
    package = package_dir(tmp_path)
    (package / "preview.mp4").write_bytes(b"keep")
    log = tmp_path / "ffmpeg.log"

    completed = run_preview(
        package,
        fake_ffmpeg(tmp_path),
        fake_ffprobe(tmp_path),
        log,
    )

    assert completed.returncode == 1
    assert "preview output already exists" in completed.stderr
    assert (package / "preview.mp4").read_bytes() == b"keep"
    assert not log.exists()


def test_tampered_frozen_argv_is_rejected_before_ffmpeg(tmp_path: Path) -> None:
    package = package_dir(tmp_path)
    command_path = package / "preview-command.json"
    payload = json.loads(command_path.read_text(encoding="utf-8"))
    payload["argv"][5:5] = ["-i", "https://example.invalid/video"]
    command_path.write_text(json.dumps(payload), encoding="utf-8")
    log = tmp_path / "ffmpeg.log"

    completed = run_preview(
        package,
        fake_ffmpeg(tmp_path),
        fake_ffprobe(tmp_path),
        log,
    )

    assert completed.returncode == 1
    assert "invalid frozen argv" in completed.stderr
    assert not log.exists()
    assert not (package / "preview.mp4").exists()


def test_failed_preview_never_deletes_output_created_during_execution(
    tmp_path: Path,
) -> None:
    package = package_dir(tmp_path)
    log = tmp_path / "ffmpeg.log"

    completed = run_preview(
        package,
        fake_ffmpeg(tmp_path),
        fake_ffprobe(tmp_path),
        log,
        mode="final-fails-after-output",
    )

    assert completed.returncode == 1
    assert "B9 preview command failed" in completed.stderr
    assert (package / "preview.mp4").read_bytes() == b"concurrent-or-partial-output"


def test_make_target_is_the_canonical_preview_entrypoint(tmp_path: Path) -> None:
    package = package_dir(tmp_path)
    log = tmp_path / "ffmpeg.log"
    env = os.environ.copy()
    env.update(
        {
            "FAKE_FFMPEG_LOG": str(log),
            "FAKE_FFMPEG_MODE": "ok",
        }
    )

    completed = subprocess.run(
        [
            "make",
            "b9-preview",
            f"B9_OUTPUT_DIR={package}",
            f"B9_FFMPEG_BIN={fake_ffmpeg(tmp_path)}",
            f"B9_FFPROBE_BIN={fake_ffprobe(tmp_path)}",
            f"PYTHON={sys.executable}",
        ],
        cwd=ROOT,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "B9 preview created: preview.mp4" in completed.stdout
    assert (package / "preview.mp4").is_file()
