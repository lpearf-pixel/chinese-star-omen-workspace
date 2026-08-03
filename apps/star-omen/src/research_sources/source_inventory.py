from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping

from kb_contracts import ResearchAccessionV1
from pydantic import ValidationError


PACKAGE_RELATIVE = PurePosixPath(
    "corpus/research_sources/related-wikisource"
)
SHARED_FIELDS = (
    "page_title",
    "oldid",
    "raw_path",
    "raw_sha256",
    "raw_byte_count",
    "capture_status",
)


class SourceInventoryError(ValueError):
    """Deterministic, machine-safe failure from Layer-A inventory loading."""

    def __init__(
        self,
        *,
        code: str,
        accession_id: str,
        field: str,
        expected: object,
        actual: object,
    ) -> None:
        safe_accession_id = _redact_error_label(accession_id, "<invalid-identifier>")
        safe_field = _redact_error_label(
            field, "<invalid-field>", allow_relative_path=True
        )
        self.code = code
        self.accession_id = safe_accession_id
        self.field = safe_field
        safe_expected = _redact_machine_paths(expected)
        safe_actual = _redact_machine_paths(actual)
        self.expected = safe_expected
        self.actual = safe_actual
        super().__init__(
            f"source-inventory[{code}] accession_id={safe_accession_id!r} "
            f"field={safe_field!r} expected={safe_expected!r} actual={safe_actual!r}"
        )


@dataclass(frozen=True, slots=True)
class SourceInventory:
    accessions: tuple[ResearchAccessionV1, ...]
    family_count: int
    raw_file_count: int
    total_raw_byte_count: int

    @property
    def accession_ids(self) -> tuple[str, ...]:
        return tuple(item.accession_id for item in self.accessions)

    def get(self, accession_id: str) -> ResearchAccessionV1:
        for item in self.accessions:
            if item.accession_id == accession_id:
                return item
        raise KeyError(accession_id)


def _fail(
    code: str,
    accession_id: str,
    field: str,
    expected: object,
    actual: object,
) -> None:
    raise SourceInventoryError(
        code=code,
        accession_id=accession_id,
        field=field,
        expected=expected,
        actual=actual,
    )


def _redact_machine_paths(value: object) -> object:
    if isinstance(value, str):
        machine_signatures = ("/workspace/", "/tmp/", "/Users/")
        windows_embedded = re.search(r"(?:^|[^A-Za-z])[A-Za-z]:\\", value)
        unc_embedded = "\\\\" in value
        if (
            PurePosixPath(value).is_absolute()
            or PureWindowsPath(value).is_absolute()
            or any(signature in value for signature in machine_signatures)
            or windows_embedded is not None
            or unc_embedded
        ):
            return "<absolute-path>"
        return value
    if isinstance(value, tuple):
        return tuple(_redact_machine_paths(item) for item in value)
    if isinstance(value, list):
        return [_redact_machine_paths(item) for item in value]
    if isinstance(value, dict):
        return {
            _redact_machine_paths(key): _redact_machine_paths(item)
            for key, item in value.items()
        }
    if isinstance(value, Path):
        return _redact_machine_paths(str(value))
    return value


def _redact_error_label(
    value: str, replacement: str, *, allow_relative_path: bool = False
) -> str:
    redacted = _redact_machine_paths(value)
    if redacted != value or (not allow_relative_path and ("/" in value or "\\" in value)):
        return replacement
    return value


def _reject_symlink_components(
    *,
    root: Path,
    lexical_path: Path,
    accession_id: str,
    field: str,
    display_path: str,
) -> None:
    try:
        relative = lexical_path.relative_to(root)
    except ValueError:
        _fail(
            "path-outside-package",
            accession_id,
            field,
            "repository-relative non-symlink path",
            display_path,
        )
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            _fail(
                "symlink-path-forbidden",
                accession_id,
                field,
                "non-symlink path",
                display_path,
            )


def _read_json(path: Path, display_path: str, accession_id: str) -> Any:
    try:
        raw = path.read_bytes()
    except (OSError, RuntimeError) as exc:
        _fail(
            "missing-json-file",
            accession_id,
            display_path,
            "readable file",
            type(exc).__name__,
        )
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail(
            "invalid-json",
            accession_id,
            display_path,
            "UTF-8 JSON",
            type(exc).__name__,
        )


def _confined_repo_path(
    *,
    repo_root: Path,
    package_root: Path,
    declared: object,
    accession_id: str,
    field: str,
) -> Path:
    if not isinstance(declared, str) or not declared:
        _fail("invalid-path", accession_id, field, "non-empty POSIX path", declared)
    if "\x00" in declared or "\\" in declared:
        _fail("path-outside-package", accession_id, field, "canonical path", declared)
    pure = PurePosixPath(declared)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != declared:
        _fail("path-outside-package", accession_id, field, "canonical path", declared)
    lexical = repo_root / Path(*pure.parts)
    _reject_symlink_components(
        root=repo_root,
        lexical_path=lexical,
        accession_id=accession_id,
        field=field,
        display_path=declared,
    )
    try:
        candidate = lexical.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        _fail(
            "invalid-path",
            accession_id,
            field,
            "resolvable non-symlink path",
            type(exc).__name__,
        )
    try:
        candidate.relative_to(package_root)
    except ValueError:
        _fail(
            "path-outside-package",
            accession_id,
            field,
            PACKAGE_RELATIVE.as_posix(),
            declared,
        )
    return candidate


def _require_mapping(value: object, accession_id: str, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail("invalid-shape", accession_id, field, "object", type(value).__name__)
    return value


def _require_list(value: object, accession_id: str, field: str) -> list[Any]:
    if not isinstance(value, list):
        _fail("invalid-shape", accession_id, field, "array", type(value).__name__)
    return value


def _unique_id(
    seen: set[str], value: object, *, code: str, field: str, accession_id: str
) -> str:
    if not isinstance(value, str) or not value:
        _fail("invalid-identifier", accession_id, field, "non-empty string", value)
    if value in seen:
        _fail(code, value, field, "unique", "duplicate")
    seen.add(value)
    return value


def _require_count(
    document: Mapping[str, Any],
    *,
    field: str,
    actual: int,
    accession_id: str,
) -> None:
    expected = document.get(field)
    if isinstance(expected, bool) or not isinstance(expected, int) or expected != actual:
        _fail("count-mismatch", accession_id, field, actual, expected)


def load_source_inventory(repo_root: Path) -> SourceInventory:
    """Load, join, and byte-replay the immutable related-Wikisource package."""

    try:
        root = Path(repo_root).resolve(strict=True)
        package_lexical = root / Path(*PACKAGE_RELATIVE.parts)
        _reject_symlink_components(
            root=root,
            lexical_path=package_lexical,
            accession_id="__manifest__",
            field="package_root",
            display_path=PACKAGE_RELATIVE.as_posix(),
        )
        package_root = package_lexical.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        _fail(
            "missing-repository-root",
            "__manifest__",
            "repo_root",
            "repository containing related-Wikisource package",
            type(exc).__name__,
        )
    try:
        package_root.relative_to(root)
    except ValueError:
        _fail(
            "path-outside-repository",
            "__manifest__",
            "package_root",
            PACKAGE_RELATIVE.as_posix(),
            "symlink escape",
        )

    manifest_path = package_root / "accession-manifest.json"
    _reject_symlink_components(
        root=root,
        lexical_path=manifest_path,
        accession_id="__manifest__",
        field="accession-manifest.json",
        display_path=f"{PACKAGE_RELATIVE.as_posix()}/accession-manifest.json",
    )
    manifest = _require_mapping(
        _read_json(
            manifest_path,
            f"{PACKAGE_RELATIVE.as_posix()}/accession-manifest.json",
            "__manifest__",
        ),
        "__manifest__",
        "accession-manifest.json",
    )
    families = _require_list(manifest.get("families"), "__manifest__", "families")
    compact_items = _require_list(
        manifest.get("accessions"), "__manifest__", "accessions"
    )

    family_ids: set[str] = set()
    metadata_paths: set[str] = set()
    family_documents: dict[str, list[Mapping[str, Any]]] = {}
    detailed_by_id: dict[str, tuple[str, Mapping[str, Any]]] = {}
    detailed_ids: set[str] = set()

    for ordinal, raw_family in enumerate(families):
        marker = f"__family__:{ordinal}"
        family = _require_mapping(raw_family, marker, "families")
        family_id = _unique_id(
            family_ids,
            family.get("family_id"),
            code="duplicate-family-id",
            field="family_id",
            accession_id=marker,
        )
        metadata_declared = family.get("accession_metadata_path")
        if not isinstance(metadata_declared, str):
            _fail(
                "invalid-path",
                f"__family__:{family_id}",
                "accession_metadata_path",
                "non-empty POSIX path",
                metadata_declared,
            )
        if metadata_declared in metadata_paths:
            _fail(
                "duplicate-metadata-path",
                f"__family__:{family_id}",
                "accession_metadata_path",
                "unique",
                metadata_declared,
            )
        metadata_paths.add(metadata_declared)
        metadata_path = _confined_repo_path(
            repo_root=root,
            package_root=package_root,
            declared=metadata_declared,
            accession_id=f"__family__:{family_id}",
            field="accession_metadata_path",
        )
        details_raw = _read_json(
            metadata_path,
            metadata_declared,
            f"__family__:{family_id}",
        )
        details = _require_list(
            details_raw,
            f"__family__:{family_id}",
            "accession_metadata_path",
        )
        parsed_details: list[Mapping[str, Any]] = []
        for raw_detail in details:
            detail = _require_mapping(
                raw_detail, f"__family__:{family_id}", "accession record"
            )
            accession_id = _unique_id(
                detailed_ids,
                detail.get("accession_id"),
                code="duplicate-accession-id",
                field="accession_id",
                accession_id=f"__family__:{family_id}",
            )
            detailed_by_id[accession_id] = (family_id, detail)
            parsed_details.append(detail)
        family_documents[family_id] = parsed_details
        _require_count(
            family,
            field="accession_count",
            actual=len(parsed_details),
            accession_id=f"__family__:{family_id}",
        )

    compact_by_id: dict[str, Mapping[str, Any]] = {}
    compact_ids: set[str] = set()
    compact_family_counts = {family_id: 0 for family_id in family_ids}
    for raw_compact in compact_items:
        compact = _require_mapping(raw_compact, "__manifest__", "accessions")
        accession_id = _unique_id(
            compact_ids,
            compact.get("accession_id"),
            code="duplicate-accession-id",
            field="accession_id",
            accession_id="__manifest__",
        )
        family_id = compact.get("family_id")
        if family_id not in family_ids:
            _fail(
                "unknown-family",
                accession_id,
                "family_id",
                sorted(family_ids),
                family_id,
            )
        compact_family_counts[family_id] += 1
        compact_by_id[accession_id] = compact

    missing_details = sorted(compact_ids - detailed_ids)
    if missing_details:
        _fail(
            "missing-detailed-record",
            missing_details[0],
            "accession_id",
            "present",
            "missing",
        )
    unindexed_details = sorted(detailed_ids - compact_ids)
    if unindexed_details:
        _fail(
            "unindexed-detailed-record",
            unindexed_details[0],
            "accession_id",
            "indexed",
            "unindexed",
        )

    raw_paths: set[str] = set()
    validated: list[ResearchAccessionV1] = []
    for accession_id in sorted(compact_ids):
        compact = compact_by_id[accession_id]
        container_family, detail = detailed_by_id[accession_id]
        if compact.get("family_id") != container_family:
            _fail(
                "family-mismatch",
                accession_id,
                "family_id",
                compact.get("family_id"),
                container_family,
            )
        for field in SHARED_FIELDS:
            compact_value = compact.get(field)
            detail_value = detail.get(field)
            if (
                type(compact_value) is not type(detail_value)
                or compact_value != detail_value
            ):
                _fail(
                    "field-mismatch",
                    accession_id,
                    field,
                    compact_value,
                    detail_value,
                )
        if "schema_version" in detail or "family_id" in detail:
            _fail(
                "reserved-detailed-field",
                accession_id,
                "schema_version/family_id",
                "absent",
                "present",
            )
        payload = dict(detail)
        payload["schema_version"] = "research-accession/v1"
        payload["family_id"] = container_family
        try:
            accession = ResearchAccessionV1.model_validate(payload)
        except ValidationError as exc:
            first = exc.errors(include_url=False, include_input=False)[0]
            location = ".".join(str(part) for part in first.get("loc", ()))
            _fail(
                "invalid-detailed-record",
                accession_id,
                location or "accession",
                "research-accession/v1",
                first.get("msg", "validation error"),
            )
        if accession.raw_path is not None:
            if accession.raw_path in raw_paths:
                _fail(
                    "duplicate-raw-path",
                    accession_id,
                    "raw_path",
                    "unique",
                    accession.raw_path,
                )
            raw_paths.add(accession.raw_path)
            raw_file = _confined_repo_path(
                repo_root=root,
                package_root=package_root,
                declared=accession.raw_path,
                accession_id=accession_id,
                field="raw_path",
            )
            try:
                raw_bytes = raw_file.read_bytes()
            except OSError as exc:
                _fail(
                    "missing-raw-file",
                    accession_id,
                    "raw_path",
                    accession.raw_path,
                    type(exc).__name__,
                )
            actual_count = len(raw_bytes)
            if accession.raw_byte_count != actual_count:
                _fail(
                    "raw-byte-count-mismatch",
                    accession_id,
                    "raw_byte_count",
                    accession.raw_byte_count,
                    actual_count,
                )
            actual_sha = hashlib.sha256(raw_bytes).hexdigest()
            if accession.raw_sha256 != actual_sha:
                _fail(
                    "raw-sha256-mismatch",
                    accession_id,
                    "raw_sha256",
                    accession.raw_sha256,
                    actual_sha,
                )
        validated.append(accession)

    for family_id, details in family_documents.items():
        if compact_family_counts[family_id] != len(details):
            _fail(
                "family-count-mismatch",
                f"__family__:{family_id}",
                "accession_count",
                len(details),
                compact_family_counts[family_id],
            )

    filesystem_raw_paths: set[str] = set()
    for raw_file in package_root.rglob("*.wikitext"):
        display = raw_file.relative_to(root).as_posix()
        _reject_symlink_components(
            root=root,
            lexical_path=raw_file,
            accession_id="__manifest__",
            field="raw_file_count",
            display_path=display,
        )
        if raw_file.is_file():
            filesystem_raw_paths.add(display)
    if filesystem_raw_paths != raw_paths:
        extras = sorted(filesystem_raw_paths - raw_paths)
        missing = sorted(raw_paths - filesystem_raw_paths)
        _fail(
            "raw-file-set-mismatch",
            "__manifest__",
            "raw_file_count",
            {"declared": sorted(raw_paths)},
            {"unindexed": extras, "missing": missing},
        )

    _require_count(
        manifest,
        field="family_count",
        actual=len(family_ids),
        accession_id="__manifest__",
    )
    _require_count(
        manifest,
        field="accession_count",
        actual=len(validated),
        accession_id="__manifest__",
    )
    _require_count(
        manifest,
        field="raw_file_count",
        actual=len(filesystem_raw_paths),
        accession_id="__manifest__",
    )
    total_raw_bytes = sum(item.raw_byte_count or 0 for item in validated)
    _require_count(
        manifest,
        field="total_raw_byte_count",
        actual=total_raw_bytes,
        accession_id="__manifest__",
    )

    return SourceInventory(
        accessions=tuple(validated),
        family_count=len(family_ids),
        raw_file_count=len(filesystem_raw_paths),
        total_raw_byte_count=total_raw_bytes,
    )


__all__ = [
    "SourceInventory",
    "SourceInventoryError",
    "load_source_inventory",
]
