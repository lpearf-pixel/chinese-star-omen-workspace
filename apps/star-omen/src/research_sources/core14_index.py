from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Mapping

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


CORE14_MANIFEST_PATH = PurePosixPath(
    "corpus/research_sources/b10-core14/accession-manifest.json"
)
CORE14_MANIFEST_SHA256 = (
    "a038dcd684990810f89cd9b84f9e30ad7464505ce6bef81ad02da5e00785f968"
)
AUDIT_PATHS = {
    "early": "corpus/research_sources/b10-core14/audit-early.json",
    "middle": "corpus/research_sources/b10-core14/audit-middle.json",
    "late": "corpus/research_sources/b10-core14/audit-late.json",
}
_CASE_ID_RE = re.compile(r"^C[0-9]{2}$")
_ATOM_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]*$")


class Core14IndexError(ValueError):
    """Deterministic failure while binding the Core14 target vocabulary."""


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class Core14AuditRefV0(_FrozenModel):
    name: Literal["early", "middle", "late"]
    path: str = Field(strict=True, min_length=1)
    sha256: str = Field(strict=True, pattern=r"^[0-9a-f]{64}$")
    case_ids: tuple[str, ...]
    atom_ids: tuple[str, ...]

    @field_validator("case_ids", "atom_ids")
    @classmethod
    def validate_sorted_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != tuple(sorted(set(value))):
            raise ValueError("identifiers must be sorted and unique")
        return value

    @field_validator("case_ids")
    @classmethod
    def validate_case_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(_CASE_ID_RE.fullmatch(item) is None for item in value):
            raise ValueError("case IDs are invalid")
        return value

    @field_validator("atom_ids")
    @classmethod
    def validate_atom_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(_ATOM_ID_RE.fullmatch(item) is None for item in value):
            raise ValueError("atom IDs are invalid")
        return value


class Core14CaseTargetV0(_FrozenModel):
    case_id: str = Field(strict=True, pattern=r"^C[0-9]{2}$")
    atom_ids: tuple[str, ...]

    @field_validator("atom_ids")
    @classmethod
    def validate_atoms(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or value != tuple(sorted(set(value))):
            raise ValueError("atom_ids must be non-empty, sorted, and unique")
        if any(_ATOM_ID_RE.fullmatch(atom) is None for atom in value):
            raise ValueError("atom_ids must be stable identifiers")
        return value


class Core14TargetIndexV0(_FrozenModel):
    schema_version: Literal["core14-target-index/pilot-v0"] = (
        "core14-target-index/pilot-v0"
    )
    manifest_path: Literal[
        "corpus/research_sources/b10-core14/accession-manifest.json"
    ]
    manifest_sha256: str = Field(strict=True, pattern=r"^[0-9a-f]{64}$")
    audits: tuple[Core14AuditRefV0, ...]
    cases: tuple[Core14CaseTargetV0, ...]

    @model_validator(mode="after")
    def validate_closed_unique_index(self) -> "Core14TargetIndexV0":
        if tuple(audit.name for audit in self.audits) != ("early", "middle", "late"):
            raise ValueError("audits must contain early, middle, and late in order")
        expected_paths = {
            "early": AUDIT_PATHS["early"],
            "middle": AUDIT_PATHS["middle"],
            "late": AUDIT_PATHS["late"],
        }
        if any(audit.path != expected_paths[audit.name] for audit in self.audits):
            raise ValueError("audit name and fixed path are inconsistent")
        if self.cases != tuple(sorted(self.cases, key=lambda item: item.case_id)):
            raise ValueError("cases must be sorted")
        case_ids = [case.case_id for case in self.cases]
        atoms = [atom for case in self.cases for atom in case.atom_ids]
        if len(case_ids) != len(set(case_ids)) or len(atoms) != len(set(atoms)):
            raise ValueError("case and atom IDs must be globally unique")
        audit_case_ids = [case_id for audit in self.audits for case_id in audit.case_ids]
        audit_atom_ids = [atom_id for audit in self.audits for atom_id in audit.atom_ids]
        if (
            len(audit_case_ids) != len(set(audit_case_ids))
            or set(audit_case_ids) != set(case_ids)
        ):
            raise ValueError("audit case targets must exactly partition cases")
        if (
            len(audit_atom_ids) != len(set(audit_atom_ids))
            or set(audit_atom_ids) != set(atoms)
        ):
            raise ValueError("audit atom targets must exactly partition atoms")
        return self

    @property
    def audit_sha256(self) -> dict[str, str]:
        return {audit.name: audit.sha256 for audit in self.audits}

    @property
    def case_ids(self) -> tuple[str, ...]:
        return tuple(case.case_id for case in self.cases)

    @property
    def atom_ids(self) -> tuple[str, ...]:
        return tuple(sorted(atom for case in self.cases for atom in case.atom_ids))

    def contains_case(self, case_id: str) -> bool:
        return case_id in self.case_ids

    def contains_atom(self, case_id: str, atom_id: str) -> bool:
        return any(
            case.case_id == case_id and atom_id in case.atom_ids for case in self.cases
        )


def _load_json_bytes(path: Path, *, code: str) -> tuple[bytes, Mapping[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise Core14IndexError(f"{code}:unreadable:{type(exc).__name__}") from None
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Core14IndexError(f"{code}:invalid-json:{type(exc).__name__}") from None
    if not isinstance(document, Mapping):
        raise Core14IndexError(f"{code}:invalid-shape")
    return raw, document


def _fixed_repo_file(root: Path, relative: PurePosixPath, *, code: str) -> Path:
    lexical = root / Path(*relative.parts)
    current = root
    try:
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise Core14IndexError(f"{code}:symlink-forbidden")
        resolved = lexical.resolve(strict=True)
        resolved.relative_to(root)
    except Core14IndexError:
        raise
    except (OSError, RuntimeError, ValueError) as exc:
        raise Core14IndexError(f"{code}:unreadable:{type(exc).__name__}") from None
    return resolved


def load_core14_target_index(repo_root: Path) -> Core14TargetIndexV0:
    """Load the three hash-bound Core14 audits as a closed target index."""

    try:
        root = Path(repo_root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise Core14IndexError(
            f"core14-root:unreadable:{type(exc).__name__}"
        ) from None

    manifest_file = _fixed_repo_file(
        root, CORE14_MANIFEST_PATH, code="core14-manifest"
    )
    manifest_raw, manifest = _load_json_bytes(manifest_file, code="core14-manifest")
    manifest_sha = hashlib.sha256(manifest_raw).hexdigest()
    if manifest_sha != CORE14_MANIFEST_SHA256:
        raise Core14IndexError("core14-manifest-sha256-mismatch")

    declared: dict[str, str] = {}
    files = manifest.get("files")
    if not isinstance(files, list):
        raise Core14IndexError("core14-manifest:missing-files")
    for item in files:
        if not isinstance(item, Mapping):
            raise Core14IndexError("core14-manifest:invalid-file-entry")
        path = item.get("path")
        sha = item.get("sha256")
        if isinstance(path, str) and path in AUDIT_PATHS.values():
            if not isinstance(sha, str):
                raise Core14IndexError("core14-manifest:invalid-audit-sha256")
            if path in declared:
                raise Core14IndexError("core14-manifest:duplicate-audit-declaration")
            declared[path] = sha
    if set(declared) != set(AUDIT_PATHS.values()):
        raise Core14IndexError("core14-manifest:missing-audit-declaration")

    audit_refs: list[Core14AuditRefV0] = []
    case_to_atoms: dict[str, tuple[str, ...]] = {}
    seen_atoms: set[str] = set()
    lineage = manifest.get("workbook_lineage")
    if not isinstance(lineage, Mapping) or not isinstance(lineage.get("cases"), list):
        raise Core14IndexError("core14-manifest:invalid-workbook-lineage")
    lineage_cases = lineage["cases"]
    if (
        any(not isinstance(case_id, str) for case_id in lineage_cases)
        or lineage_cases != sorted(set(lineage_cases))
    ):
        raise Core14IndexError("core14-manifest:invalid-lineage-cases")
    for name, relative in AUDIT_PATHS.items():
        audit_file = _fixed_repo_file(
            root, PurePosixPath(relative), code=f"core14-audit:{name}"
        )
        try:
            audit_raw = audit_file.read_bytes()
        except OSError as exc:
            raise Core14IndexError(
                f"core14-audit:{name}:unreadable:{type(exc).__name__}"
            ) from None
        actual_sha = hashlib.sha256(audit_raw).hexdigest()
        if actual_sha != declared[relative]:
            raise Core14IndexError(f"audit-sha256-mismatch:{name}")
        try:
            audit = json.loads(audit_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise Core14IndexError(
                f"core14-audit:{name}:invalid-json:{type(exc).__name__}"
            ) from None
        if not isinstance(audit, Mapping) or not isinstance(audit.get("cases"), list):
            raise Core14IndexError(f"core14-audit:{name}:invalid-shape")

        audit_cases: list[str] = []
        audit_atoms: list[str] = []
        for raw_case in audit["cases"]:
            if not isinstance(raw_case, Mapping):
                raise Core14IndexError(f"core14-audit:{name}:invalid-case")
            case_id = raw_case.get("case_id")
            rules = raw_case.get("atomic_rules")
            if (
                not isinstance(case_id, str)
                or _CASE_ID_RE.fullmatch(case_id) is None
                or not isinstance(rules, list)
                or not rules
            ):
                raise Core14IndexError(f"core14-audit:{name}:invalid-case-target")
            if case_id in case_to_atoms:
                raise Core14IndexError(f"duplicate-core14-case:{case_id}")
            atoms: list[str] = []
            for rule in rules:
                atom_id = rule.get("id") if isinstance(rule, Mapping) else None
                if (
                    not isinstance(atom_id, str)
                    or _ATOM_ID_RE.fullmatch(atom_id) is None
                ):
                    raise Core14IndexError(f"core14-audit:{name}:invalid-atom")
                if atom_id in seen_atoms:
                    raise Core14IndexError(f"duplicate-core14-atom:{atom_id}")
                seen_atoms.add(atom_id)
                atoms.append(atom_id)
            case_to_atoms[case_id] = tuple(sorted(atoms))
            audit_cases.append(case_id)
            audit_atoms.extend(atoms)

        try:
            audit_refs.append(
                Core14AuditRefV0(
                    name=name,
                    path=relative,
                    sha256=actual_sha,
                    case_ids=tuple(sorted(audit_cases)),
                    atom_ids=tuple(sorted(audit_atoms)),
                )
            )
        except ValidationError as exc:
            raise Core14IndexError(
                f"core14-audit:{name}:invalid-target-index"
            ) from None

    if set(case_to_atoms) != set(lineage_cases):
        raise Core14IndexError("core14-manifest:lineage-case-mismatch")
    try:
        return Core14TargetIndexV0(
            manifest_path=CORE14_MANIFEST_PATH.as_posix(),
            manifest_sha256=manifest_sha,
            audits=tuple(audit_refs),
            cases=tuple(
                Core14CaseTargetV0(case_id=case_id, atom_ids=atoms)
                for case_id, atoms in sorted(case_to_atoms.items())
            ),
        )
    except ValidationError:
        raise Core14IndexError("core14-index:invalid-closure") from None


__all__ = [
    "Core14AuditRefV0",
    "Core14CaseTargetV0",
    "Core14IndexError",
    "Core14TargetIndexV0",
    "CORE14_MANIFEST_SHA256",
    "load_core14_target_index",
]
