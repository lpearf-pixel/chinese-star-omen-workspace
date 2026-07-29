from __future__ import annotations

import hashlib
import re
from datetime import timezone
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from src.video_pipeline.contracts import AstronomyEventV1
from src.video_pipeline.contracts._common import StableId, StrictContractModel, ensure_unique
from src.video_pipeline.editorial import EditorialPackageV1

_REQUIRED_COMMANDS = (
    "core.clear",
    "core.setGuiVisible",
    "core.setDate",
    "core.setTimeRate",
    "core.setObserverLocation",
    "core.selectObjectByName",
    "core.wait",
    "StelMovementMgr.setFlagTracking",
    "StelMovementMgr.zoomTo",
)
_OBJECT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._+\-]{0,79}$")
_FORBIDDEN_TOKENS = (
    "include(",
    "eval(",
    "screenshot",
    "../",
    "file://",
    "http://",
    "https://",
    "system(",
    "exec(",
    "/users/",
    "/tmp/",
    "\\",
)
_SETUP_COMMANDS = (
    "core.clear",
    "core.setGuiVisible",
    "core.setTimeRate",
    "core.setDate",
    "core.setObserverLocation",
)
_SHOT_COMMANDS = (
    "core.selectObjectByName",
    "StelMovementMgr.setFlagTracking",
    "StelMovementMgr.zoomTo",
    "core.wait",
)
_RESTORE_LINES = (
    "StelMovementMgr.setFlagTracking(false);",
    "core.setTimeRate(1.0);",
    "core.setGuiVisible(true);",
)
_WAIT_RE = re.compile(r"^core\.wait\(([0-9]+)\.([0-9]{3})\);$")


class StellariumCapabilityV1(StrictContractModel):
    schema_version: Literal["stellarium-capability/v1"]
    stellarium_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    api_series: Literal["26.x"]
    commands: list[str]

    @model_validator(mode="after")
    def validate_commands(self) -> "StellariumCapabilityV1":
        ensure_unique(self.commands, "Stellarium capability commands")
        if any(command not in _REQUIRED_COMMANDS for command in self.commands):
            raise ValueError("capability contains unsupported commands")
        return self


class StellariumScriptV1(StrictContractModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
        validate_default=True,
    )

    schema_version: Literal["stellarium-script/v1"] = "stellarium-script/v1"
    script_id: StableId
    event_id: StableId
    editorial_package_id: StableId
    stellarium_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    commands: list[str]
    total_wait_ms: int = Field(strict=True, ge=0)
    content: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_script(self) -> "StellariumScriptV1":
        version = _version_tuple(self.stellarium_version)
        if version < (26, 0, 0) or version >= (27, 0, 0):
            raise ValueError("Stellarium script version is outside supported 26.x range")
        if not self.content.endswith("\n") or self.content.endswith("\n\n"):
            raise ValueError("Stellarium script must end with one newline")
        if hashlib.sha256(self.content.encode("utf-8")).hexdigest() != self.sha256:
            raise ValueError("Stellarium script hash mismatch")
        commands, total_wait_ms = _analyze_canonical_script(self.content)
        if commands != self.commands:
            raise ValueError("Stellarium script command inventory mismatch")
        if total_wait_ms != self.total_wait_ms:
            raise ValueError("Stellarium script wait duration metadata mismatch")
        return self


def _version_tuple(value: str) -> tuple[int, int, int]:
    try:
        parts = tuple(int(part) for part in value.split("."))
    except ValueError as exc:
        raise ValueError("invalid Stellarium version") from exc
    if len(parts) != 3:
        raise ValueError("invalid Stellarium version")
    return parts  # type: ignore[return-value]


def _script_date(event: AstronomyEventV1) -> str:
    utc = event.peak_utc.astimezone(timezone.utc).replace(microsecond=0)
    return utc.strftime("%Y-%m-%dT%H:%M:%S")


def _parse_command(line: str) -> str:
    patterns: tuple[tuple[str, str], ...] = (
        ("core.clear", r'^core\.clear\("natural"\);$'),
        ("core.setGuiVisible", r"^core\.setGuiVisible\((?:true|false)\);$"),
        (
            "core.setDate",
            r'^core\.setDate\("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", "utc", true\);$',
        ),
        ("core.setTimeRate", r"^core\.setTimeRate\((?:0\.0|1\.0)\);$"),
        (
            "core.setObserverLocation",
            r'^core\.setObserverLocation\(-?[0-9]+\.[0-9]{6}, -?[0-9]+\.[0-9]{6}, -?[0-9]+\.[0-9]{3}, 0\.0, "[A-Za-z0-9][A-Za-z0-9 ._+\-]{0,79}", "Earth"\);$',
        ),
        (
            "core.selectObjectByName",
            r'^core\.selectObjectByName\("[A-Za-z0-9][A-Za-z0-9 ._+\-]{0,79}", true\);$',
        ),
        ("core.wait", r"^core\.wait\([0-9]+\.[0-9]{3}\);$"),
        (
            "StelMovementMgr.setFlagTracking",
            r"^StelMovementMgr\.setFlagTracking\((?:true|false)\);$",
        ),
        (
            "StelMovementMgr.zoomTo",
            r"^StelMovementMgr\.zoomTo\([0-9]+\.[0-9]{3}, 0\.0\);$",
        ),
    )
    for command, pattern in patterns:
        if re.fullmatch(pattern, line):
            return command
    raise ValueError(f"unsupported or invalid Stellarium command: {line!r}")


def validate_stellarium_script(content: str) -> list[str]:
    lowered = content.casefold()
    if any(token in lowered for token in _FORBIDDEN_TOKENS):
        raise ValueError("forbidden token in Stellarium script")
    if "\r" in content or "\x00" in content:
        raise ValueError("invalid control character in Stellarium script")
    commands: list[str] = []
    for raw_line in content.splitlines():
        if not raw_line:
            continue
        command = _parse_command(raw_line)
        if command not in commands:
            commands.append(command)
    if not commands:
        raise ValueError("Stellarium script has no commands")
    return commands


def _analyze_canonical_script(content: str) -> tuple[list[str], int]:
    commands = validate_stellarium_script(content)
    lines = content.splitlines()
    if any(not line for line in lines):
        raise ValueError("Stellarium script template cannot contain blank lines")
    minimum_lines = len(_SETUP_COMMANDS) + len(_SHOT_COMMANDS) + len(_RESTORE_LINES)
    if len(lines) < minimum_lines:
        raise ValueError("Stellarium script template is incomplete")

    setup = lines[: len(_SETUP_COMMANDS)]
    if tuple(_parse_command(line) for line in setup) != _SETUP_COMMANDS:
        raise ValueError("Stellarium script setup command order is not canonical")
    if setup[0] != 'core.clear("natural");':
        raise ValueError("Stellarium script clear command is not canonical")
    if setup[1] != "core.setGuiVisible(false);":
        raise ValueError("Stellarium script must hide the GUI during rendering")
    if setup[2] != "core.setTimeRate(0.0);":
        raise ValueError("Stellarium script must pause time during rendering")

    if tuple(lines[-len(_RESTORE_LINES) :]) != _RESTORE_LINES:
        raise ValueError("Stellarium script restore command order is not canonical")

    shot_lines = lines[len(_SETUP_COMMANDS) : -len(_RESTORE_LINES)]
    if not shot_lines or len(shot_lines) % len(_SHOT_COMMANDS) != 0:
        raise ValueError("Stellarium script shot template is not canonical")

    total_wait_ms = 0
    for offset in range(0, len(shot_lines), len(_SHOT_COMMANDS)):
        group = shot_lines[offset : offset + len(_SHOT_COMMANDS)]
        if tuple(_parse_command(line) for line in group) != _SHOT_COMMANDS:
            raise ValueError("Stellarium script shot command order is not canonical")
        if group[1] != "StelMovementMgr.setFlagTracking(true);":
            raise ValueError("Stellarium shot must enable tracking")
        wait_match = _WAIT_RE.fullmatch(group[3])
        if wait_match is None:
            raise ValueError("Stellarium wait command is invalid")
        total_wait_ms += int(wait_match.group(1)) * 1000 + int(wait_match.group(2))
    return commands, total_wait_ms


def canonical_stellarium_bytes(script: StellariumScriptV1) -> bytes:
    return script.content.encode("utf-8")


def generate_stellarium_script(
    *,
    event: AstronomyEventV1,
    editorial: EditorialPackageV1,
    capability: StellariumCapabilityV1,
) -> StellariumScriptV1:
    editorial = EditorialPackageV1.model_validate(editorial.model_dump(mode="json"))
    if editorial.video_package.event_id != event.event_id:
        raise ValueError("editorial package event does not match astronomy event")
    version = _version_tuple(capability.stellarium_version)
    if version < (26, 0, 0) or version >= (27, 0, 0):
        raise ValueError("Stellarium version is outside supported 26.x range")
    missing = set(_REQUIRED_COMMANDS) - set(capability.commands)
    if missing:
        raise ValueError(f"Stellarium capability is missing commands: {sorted(missing)!r}")

    for object_name in editorial.render_object_names.values():
        if not _OBJECT_NAME_RE.fullmatch(object_name):
            raise ValueError("invalid Stellarium object name")

    observer = event.observer
    lines = [
        'core.clear("natural");',
        "core.setGuiVisible(false);",
        "core.setTimeRate(0.0);",
        f'core.setDate("{_script_date(event)}", "utc", true);',
        (
            "core.setObserverLocation("
            f"{observer.longitude_deg:.6f}, {observer.latitude_deg:.6f}, "
            f'{observer.elevation_m:.3f}, 0.0, "Kaiyuan Observer", "Earth");'
        ),
    ]
    total_wait_ms = 0
    for shot in editorial.shots:
        object_name = editorial.render_object_names.get(shot.target_object_id)
        if object_name is None:
            raise ValueError("shot target has no Stellarium object mapping")
        duration_ms = shot.end_ms - shot.start_ms
        if duration_ms <= 0:
            raise ValueError("shot duration must be positive")
        total_wait_ms += duration_ms
        lines.extend(
            [
                f'core.selectObjectByName("{object_name}", true);',
                "StelMovementMgr.setFlagTracking(true);",
                f"StelMovementMgr.zoomTo({shot.fov_deg:.3f}, 0.0);",
                f"core.wait({duration_ms / 1000.0:.3f});",
            ]
        )
    if total_wait_ms != editorial.total_duration_ms:
        raise ValueError("Stellarium shot waits do not match editorial duration")
    lines.extend(_RESTORE_LINES)
    content = "\n".join(lines) + "\n"
    commands, analyzed_wait_ms = _analyze_canonical_script(content)
    if analyzed_wait_ms != total_wait_ms:
        raise ValueError("Stellarium generated wait duration is inconsistent")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    script_id = f"stellarium-script:{digest[:32]}"
    return StellariumScriptV1(
        script_id=script_id,
        event_id=event.event_id,
        editorial_package_id=editorial.editorial_package_id,
        stellarium_version=capability.stellarium_version,
        commands=commands,
        total_wait_ms=total_wait_ms,
        content=content,
        sha256=digest,
    )


__all__ = [
    "StellariumCapabilityV1",
    "StellariumScriptV1",
    "canonical_stellarium_bytes",
    "generate_stellarium_script",
    "validate_stellarium_script",
]
