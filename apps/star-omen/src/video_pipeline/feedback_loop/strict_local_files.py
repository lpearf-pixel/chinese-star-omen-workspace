from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from src.video_pipeline.contracts.external_media_v1 import ExternalAuditBundleV1
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalEvidenceQueryPlanV1,
    LocalKBSourceSnapshotV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
    canonical_contract_sha256,
)


T = TypeVar("T", bound=BaseModel)
_MAX_DEPTH = 64
_MAX_NODES = 100_000


@dataclass(frozen=True)
class StrictJSONDocument(Generic[T]):
    raw_bytes: bytes
    raw_sha256: str
    canonical_sha256: str
    value: T


def _stat_identity(metadata: os.stat_result) -> tuple[int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _read_bounded(fd: int, max_bytes: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    remaining = max_bytes + 1
    while remaining:
        chunk = os.read(fd, min(64 * 1024, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    result = b"".join(chunks)
    if len(result) > max_bytes:
        raise ValueError("input exceeds limit")
    return result


def _no_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_json_constant(_: str) -> object:
    raise ValueError("non-finite JSON constant")


def _validate_graph(value: object) -> None:
    stack: list[tuple[object, int]] = [(value, 0)]
    nodes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > _MAX_NODES or depth > _MAX_DEPTH:
            raise ValueError("JSON graph exceeds limits")
        if isinstance(current, float) and not math.isfinite(current):
            raise ValueError("non-finite JSON number")
        if isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)


def _read_stable_bytes(path: Path, *, max_bytes: int) -> bytes:
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
    flags |= getattr(os, "O_NOCTTY", 0)
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
            raise ValueError("input is not an eligible regular file")
        first = _read_bounded(fd, max_bytes)
        between = os.fstat(fd)
        second = _read_bounded(fd, max_bytes)
        after = os.fstat(fd)
        if (
            _stat_identity(before) != _stat_identity(between)
            or _stat_identity(before) != _stat_identity(after)
            or first != second
        ):
            raise ValueError("input changed during read")
        return first
    finally:
        os.close(fd)


def _validate_rights(audit_bundle: ExternalAuditBundleV1) -> None:
    allowed = {
        "metadata_only",
        "quotation_for_research",
        "permission_confirmed",
        "public_domain",
    }
    if any(
        capture.rights_status not in allowed for capture in audit_bundle.source.captures
    ):
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.RIGHTS_REJECTED)


def _validate_raw_audit_authority_flags(decoded: object) -> None:
    if not isinstance(decoded, dict):
        raise ValueError("audit bundle must be an object")
    audit = decoded.get("audit")
    if not isinstance(audit, dict):
        raise ValueError("audit must be an object")
    if (
        audit.get("research_only") is not True
        or audit.get("grants_rule_authority") is not False
        or audit.get("grants_classical_authority") is not False
    ):
        raise ValueError("audit authority flags must use exact JSON booleans")


def _load_strict_json(
    path: Path,
    *,
    max_bytes: int,
    model: type[T],
) -> StrictJSONDocument[T]:
    try:
        raw_bytes = _read_stable_bytes(path, max_bytes=max_bytes)
        decoded = json.loads(
            raw_bytes.decode("utf-8", "strict"),
            object_pairs_hook=_no_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
        _validate_graph(decoded)
        if model is ExternalAuditBundleV1:
            _validate_raw_audit_authority_flags(decoded)
        value = model.model_validate(decoded)
    except (OSError, UnicodeDecodeError, ValueError, ValidationError, RecursionError):
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.INVALID_LOCAL_INPUT) from None

    if isinstance(value, ExternalAuditBundleV1):
        _validate_rights(value)
    return StrictJSONDocument(
        raw_bytes=raw_bytes,
        raw_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        canonical_sha256=canonical_contract_sha256(value),
        value=value,
    )


def load_external_audit_v1(path: Path) -> StrictJSONDocument[ExternalAuditBundleV1]:
    return _load_strict_json(
        path,
        max_bytes=2 * 1024 * 1024,
        model=ExternalAuditBundleV1,
    )


def load_query_plan_v1(path: Path) -> StrictJSONDocument[LocalEvidenceQueryPlanV1]:
    return _load_strict_json(path, max_bytes=256 * 1024, model=LocalEvidenceQueryPlanV1)


def load_source_snapshot_v1(path: Path) -> StrictJSONDocument[LocalKBSourceSnapshotV1]:
    return _load_strict_json(path, max_bytes=256 * 1024, model=LocalKBSourceSnapshotV1)
