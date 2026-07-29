from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Literal

from pydantic import Field, model_validator

from src.video_pipeline.contracts._common import StrictContractModel, ensure_unique

_REQUIRED_FEATURES = {"lavfi-color", "subtitles", "libx264"}
_SAFE_FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class PreviewCapabilityV1(StrictContractModel):
    schema_version: Literal["preview-capability/v1"] = "preview-capability/v1"
    ffmpeg_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    enabled_features: list[str]
    max_timeout_seconds: int = Field(strict=True, ge=1, le=120)

    @model_validator(mode="after")
    def validate_features(self) -> "PreviewCapabilityV1":
        ensure_unique(self.enabled_features, "preview capability features")
        if not set(self.enabled_features).issubset(_REQUIRED_FEATURES):
            raise ValueError("preview capability contains unsupported feature")
        return self


class PreviewCommandV1(StrictContractModel):
    schema_version: Literal["preview-command/v1"] = "preview-command/v1"
    argv: list[str]
    timeout_seconds: int = Field(strict=True, ge=1, le=120)
    output_path: str
    width: Literal[1080] = 1080
    height: Literal[1920] = 1920
    duration_ms: Literal[80000] = 80000
    shell: Literal[False] = False

    @model_validator(mode="after")
    def validate_command(self) -> "PreviewCommandV1":
        if not self.argv or self.argv[0] != "ffmpeg":
            raise ValueError("preview command must invoke ffmpeg directly")
        if self.argv[-1] != self.output_path:
            raise ValueError("preview output metadata does not match argv")
        if any(";" in value or "&&" in value or "\x00" in value for value in self.argv):
            raise ValueError("unsafe preview argv")
        return self


def _safe_relative_file(value: str, *, suffix: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("preview path must be a non-empty relative file")
    if "\\" in value or ";" in value or "&&" in value or "\x00" in value:
        raise ValueError("unsafe preview path")
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 1 or path.name in {".", ".."}:
        raise ValueError("preview path must be a confined relative file")
    if not _SAFE_FILE_RE.fullmatch(path.name) or path.suffix.lower() != suffix:
        raise ValueError("preview path is invalid")
    return path.name


def build_minimal_preview_command(
    *,
    subtitle_path: str,
    output_path: str,
    duration_ms: int,
    capability: PreviewCapabilityV1,
) -> PreviewCommandV1:
    capability = PreviewCapabilityV1.model_validate(capability.model_dump(mode="json"))
    missing = _REQUIRED_FEATURES - set(capability.enabled_features)
    if missing:
        raise ValueError(f"preview capability is missing features: {sorted(missing)!r}")
    if isinstance(duration_ms, bool) or duration_ms != 80_000:
        raise ValueError("B9 preview duration must be exactly 80000 ms")
    subtitle = _safe_relative_file(subtitle_path, suffix=".srt")
    output = _safe_relative_file(output_path, suffix=".mp4")
    duration_seconds = f"{duration_ms / 1000.0:.3f}"
    argv = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-n",
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s=1080x1920:r=30:d={duration_seconds}",
        "-vf",
        f"subtitles={subtitle}",
        "-t",
        duration_seconds,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        output,
    ]
    return PreviewCommandV1(
        argv=argv,
        timeout_seconds=capability.max_timeout_seconds,
        output_path=output,
    )


__all__ = [
    "PreviewCapabilityV1",
    "PreviewCommandV1",
    "build_minimal_preview_command",
]
