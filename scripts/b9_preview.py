#!/usr/bin/env python3
"""Fail-closed runtime preflight and executor for the B9 preview package."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


_EXPECTED_PREVIEW_ARGV = [
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
]
_EXPECTED_PREVIEW_KEYS = {
    "schema_version",
    "argv",
    "timeout_seconds",
    "output_path",
    "width",
    "height",
    "duration_ms",
    "shell",
}


class PreviewRuntimeError(RuntimeError):
    """An actionable B9 preview runtime failure."""


def _regular_file(path: Path, *, label: str) -> Path:
    if not path.is_file() or path.is_symlink():
        raise PreviewRuntimeError(f"{label} must be a regular non-symlink file")
    return path


def _resolve_executable(*, command: str, override_name: str) -> Path:
    requested = os.environ.get(override_name, "").strip() or command
    resolved = shutil.which(requested)
    if resolved is None:
        raise PreviewRuntimeError(
            f"{command} executable not found; set {override_name} to an executable path"
        )
    path = Path(resolved).resolve()
    _regular_file(path, label=f"{command} executable")
    if not os.access(path, os.X_OK):
        raise PreviewRuntimeError(f"{command} executable is not executable: {path}")
    return path


def _run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            cwd=cwd,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise PreviewRuntimeError(
            f"command timed out after {timeout}s: {Path(argv[0]).name}"
        ) from exc
    except OSError as exc:
        raise PreviewRuntimeError(
            f"unable to execute {Path(argv[0]).name}: {exc}"
        ) from exc


def _require_success(
    completed: subprocess.CompletedProcess[str],
    *,
    message: str,
) -> subprocess.CompletedProcess[str]:
    if completed.returncode == 0:
        return completed
    detail = completed.stderr.strip().splitlines()
    suffix = f": {detail[-1]}" if detail else ""
    raise PreviewRuntimeError(f"{message} (exit {completed.returncode}){suffix}")


def _version(executable: Path, *, command: str) -> str:
    completed = _require_success(
        _run([str(executable), "-version"], timeout=10),
        message=f"unable to query {command} version",
    )
    match = re.search(
        rf"(?m)^{re.escape(command)} version ([0-9]+\.[0-9]+(?:\.[0-9]+)?)\b",
        completed.stdout,
    )
    if match is None:
        raise PreviewRuntimeError(f"unable to parse {command} version output")
    return match.group(1)


def _require_feature(
    executable: Path,
    *,
    listing_arg: str,
    feature: str,
    feature_kind: str,
) -> None:
    completed = _require_success(
        _run([str(executable), "-hide_banner", listing_arg], timeout=10),
        message=f"unable to inspect FFmpeg {feature_kind}s",
    )
    if re.search(rf"(?m)(?:^|\s){re.escape(feature)}(?:\s|$)", completed.stdout) is None:
        raise PreviewRuntimeError(
            f"required FFmpeg {feature_kind} missing: {feature}"
        )


def _subtitle_smoke(ffmpeg: Path, ffprobe: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="b9-ffmpeg-preflight-") as raw_root:
        root = Path(raw_root)
        (root / "smoke.srt").write_text(
            "1\n00:00:00,000 --> 00:00:00,100\nB9\n",
            encoding="utf-8",
        )
        output = root / "smoke.mp4"
        completed = _run(
            [
                str(ffmpeg),
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=16x16:r=1:d=0.100",
                "-vf",
                "subtitles=smoke.srt",
                "-frames:v",
                "1",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-y",
                "smoke.mp4",
            ],
            cwd=root,
            timeout=20,
        )
        try:
            _require_success(
                completed,
                message=(
                    "FFmpeg subtitle smoke failed; verify a build with libass "
                    "and set B9_FFMPEG_BIN/B9_FFPROBE_BIN explicitly"
                ),
            )
        except PreviewRuntimeError:
            raise
        _regular_file(output, label="FFmpeg subtitle smoke output")
        _require_success(
            _run(
                [
                    str(ffprobe),
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=codec_name",
                    "-of",
                    "default=nw=1:nk=1",
                    str(output),
                ],
                timeout=10,
            ),
            message="ffprobe could not inspect the FFmpeg subtitle smoke output",
        )


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PreviewRuntimeError(f"duplicate JSON key in preview command: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise PreviewRuntimeError(f"non-finite JSON value in preview command: {value}")


def _load_preview_command(package: Path) -> tuple[list[str], int]:
    command_path = _regular_file(
        package / "preview-command.json",
        label="preview-command.json",
    )
    try:
        payload = json.loads(
            command_path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreviewRuntimeError(f"invalid preview-command.json: {exc}") from exc
    if not isinstance(payload, dict):
        raise PreviewRuntimeError("preview-command.json must contain one object")
    argv = payload.get("argv")
    timeout = payload.get("timeout_seconds")
    if (
        set(payload) != _EXPECTED_PREVIEW_KEYS
        or payload.get("schema_version") != "preview-command/v1"
        or payload.get("shell") is not False
        or payload.get("output_path") != "preview.mp4"
        or payload.get("width") != 1080
        or payload.get("height") != 1920
        or payload.get("duration_ms") != 80_000
        or argv != _EXPECTED_PREVIEW_ARGV
    ):
        raise PreviewRuntimeError("preview-command.json contains an invalid frozen argv")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 120:
        raise PreviewRuntimeError("preview command timeout must be an integer from 1 to 120")
    return argv, timeout


def run_preview(package_dir: str | Path) -> Path:
    package = Path(package_dir).resolve()
    if not package.is_dir() or package.is_symlink():
        raise PreviewRuntimeError("package directory must be an existing real directory")
    _regular_file(package / "subtitles.srt", label="subtitles.srt")
    output = package / "preview.mp4"
    if output.exists() or output.is_symlink():
        raise PreviewRuntimeError("preview output already exists: preview.mp4")
    frozen_argv, timeout = _load_preview_command(package)

    ffmpeg = _resolve_executable(
        command="ffmpeg",
        override_name="B9_FFMPEG_BIN",
    )
    ffprobe = _resolve_executable(
        command="ffprobe",
        override_name="B9_FFPROBE_BIN",
    )
    try:
        ffmpeg_version = _version(ffmpeg, command="ffmpeg")
        ffprobe_version = _version(ffprobe, command="ffprobe")
        _require_feature(
            ffmpeg,
            listing_arg="-filters",
            feature="subtitles",
            feature_kind="filter",
        )
        _require_feature(
            ffmpeg,
            listing_arg="-encoders",
            feature="libx264",
            feature_kind="encoder",
        )
        _subtitle_smoke(ffmpeg, ffprobe)
    except PreviewRuntimeError as exc:
        raise PreviewRuntimeError(
            f"{exc}; selected ffmpeg={ffmpeg}; selected ffprobe={ffprobe}; "
            "override with B9_FFMPEG_BIN and B9_FFPROBE_BIN"
        ) from exc
    print(
        "B9 FFmpeg preflight passed: "
        f"ffmpeg={ffmpeg} version={ffmpeg_version} "
        f"ffprobe={ffprobe} version={ffprobe_version}"
    )

    runtime_argv = [str(ffmpeg), *frozen_argv[1:]]
    completed = _run(runtime_argv, cwd=package, timeout=timeout)
    try:
        _require_success(completed, message="B9 preview command failed")
        _regular_file(output, label="preview.mp4")
    except PreviewRuntimeError as exc:
        if output.exists() or output.is_symlink():
            raise PreviewRuntimeError(
                f"{exc}; preview.mp4 was preserved for diagnosis"
            ) from exc
        raise
    print("B9 preview created: preview.mp4")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preflight FFmpeg and execute one frozen B9 preview package."
    )
    parser.add_argument("--package-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run_preview(args.package_dir)
    except PreviewRuntimeError as exc:
        print(f"B9 preview failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
