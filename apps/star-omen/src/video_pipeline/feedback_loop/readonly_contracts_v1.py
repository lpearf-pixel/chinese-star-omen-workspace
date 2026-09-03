from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Annotated, Literal, Mapping, Protocol, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from src.video_pipeline.contracts._common import (
    Sha256Hex,
    StableId,
    canonical_contract_bytes,
)
from src.video_pipeline.contracts.external_media_v1 import ExternalAuditBundleV1


def _reject_corpus_version_preprocessing(value: object) -> object:
    if not isinstance(value, str):
        raise ValueError("corpus version must be a string")
    if value != value.strip() or any(
        character.isspace() or ord(character) < 0x20 or ord(character) == 0x7F
        for character in value
    ):
        raise ValueError("corpus version must not contain whitespace or controls")
    return value


def _validate_corpus_version(value: str) -> str:
    for format_string in ("%Y%m%dT%H%M%SZ", "%Y-%m-%dT%H%M%SZ"):
        try:
            parsed = datetime.strptime(value, format_string)
        except ValueError:
            continue
        if parsed.strftime(format_string) == value:
            return value
    raise ValueError("corpus version must be a canonical producer timestamp")


CorpusVersion = Annotated[
    str,
    BeforeValidator(_reject_corpus_version_preprocessing),
    StringConstraints(
        strict=True,
        pattern=r"^(?:[0-9]{8}|[0-9]{4}-[0-9]{2}-[0-9]{2})T[0-9]{6}Z$",
    ),
    AfterValidator(_validate_corpus_version),
]


class StrictContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
    )


def _json_array_to_tuple(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    raise ValueError("value must be a JSON array")


class LocalEvidenceProbeRequestV1(StrictContractModel):
    request_id: StableId
    source_id: StableId
    audit_id: StableId
    claim_id: StableId
    query: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=4000)]
    kb_book_id: Annotated[
        str, StringConstraints(strict=True, min_length=1, max_length=256)
    ]
    query_mode: Literal["evidence"]
    top_k: Annotated[int, Field(strict=True, ge=1, le=20)]


class LocalEvidenceQueryPlanV1(StrictContractModel):
    schema_version: Literal["local-evidence-query-plan/v1"]
    plan_id: StableId
    policy_version: Literal["vfl-readonly-probe/1.0.0"]
    source_id: StableId
    audit_id: StableId
    execution_scope: Literal["hermetic_test", "reviewed_live"]
    collection: Annotated[
        str, StringConstraints(strict=True, min_length=1, max_length=256)
    ]
    kb_book_id: Annotated[
        str, StringConstraints(strict=True, min_length=1, max_length=256)
    ]
    expected_corpus_version: CorpusVersion
    requests: Annotated[
        tuple[LocalEvidenceProbeRequestV1, ...],
        BeforeValidator(_json_array_to_tuple),
    ]

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        if not self.requests:
            raise ValueError("requests must not be empty")
        request_ids = tuple(item.request_id for item in self.requests)
        claim_ids = tuple(item.claim_id for item in self.requests)
        if len(set(request_ids)) != len(request_ids):
            raise ValueError("request IDs must be unique")
        if len(set(claim_ids)) != len(claim_ids):
            raise ValueError("claim IDs must be unique")
        if claim_ids != tuple(sorted(claim_ids)):
            raise ValueError("requests must use canonical claim order")
        if any(
            item.source_id != self.source_id
            or item.audit_id != self.audit_id
            or item.kb_book_id != self.kb_book_id
            for item in self.requests
        ):
            raise ValueError("request identities must match the plan")
        ephemeral_collection = re.fullmatch(
            r"test_vfl_ephemeral_[a-z0-9_]+", self.collection
        )
        if self.collection != "local_kb_kaiyuan_v2" and not ephemeral_collection:
            raise ValueError("collection is not allowed")
        if (
            self.execution_scope == "reviewed_live"
            and self.collection != "local_kb_kaiyuan_v2"
        ) or (self.execution_scope == "hermetic_test" and not ephemeral_collection):
            raise ValueError("execution scope and collection do not agree")
        return self


class LocalKBSourceFileV1(StrictContractModel):
    relative_path: Annotated[
        str, StringConstraints(strict=True, min_length=1, max_length=4096)
    ]
    size_bytes: Annotated[int, Field(strict=True, ge=0, le=64 * 1024 * 1024)]
    sha256: Sha256Hex

    @model_validator(mode="after")
    def validate_relative_path(self) -> Self:
        value = self.relative_path
        path = PurePosixPath(value)
        if (
            value.startswith("/")
            or "\\" in value
            or "//" in value
            or path.as_posix() != value
            or any(part in {"", ".", ".."} for part in path.parts)
            or path.suffix != ".md"
        ):
            raise ValueError("source path is not canonical")
        normalized = f"/{value}"
        if (
            "/分卷/" not in normalized
            and "全文合併版" not in normalized
            and "全文合并版" not in normalized
        ):
            raise ValueError("source path is not scanner-eligible")
        return self


class LocalKBSourceSnapshotV1(StrictContractModel):
    schema_version: Literal["local-kb-source-snapshot/v1"]
    snapshot_id: StableId
    corpus_version: CorpusVersion
    collection: Annotated[
        str, StringConstraints(strict=True, min_length=1, max_length=256)
    ]
    kb_book_id: Annotated[
        str, StringConstraints(strict=True, min_length=1, max_length=256)
    ]
    files: Annotated[
        tuple[LocalKBSourceFileV1, ...],
        BeforeValidator(_json_array_to_tuple),
    ]
    tree_sha256: Sha256Hex

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        paths = tuple(item.relative_path for item in self.files)
        if paths != tuple(sorted(paths)) or len(set(paths)) != len(paths):
            raise ValueError("snapshot files must be sorted and unique")
        payload = [item.model_dump(mode="json") for item in self.files]
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if hashlib.sha256(canonical).hexdigest() != self.tree_sha256:
            raise ValueError("snapshot tree hash does not match")
        return self


@dataclass(frozen=True, slots=True)
class SourceSnapshotBindingV1:
    canonical_kb_root: Path
    snapshot_sha256: str
    collection: str
    kb_book_id: str
    corpus_version: str


class ReadOnlyTwoStageRetriever(Protocol):
    @property
    def source_binding(self) -> SourceSnapshotBindingV1: ...

    def two_stage_retrieve(self, query: str, **kwargs: object) -> Mapping[str, object]: ...


class ReadOnlyErrorCode(StrEnum):
    INVALID_LOCAL_INPUT = "invalid_local_input"
    RIGHTS_REJECTED = "rights_rejected"
    PLAN_MISMATCH = "plan_mismatch"
    SNAPSHOT_MISMATCH = "snapshot_mismatch"
    ENDPOINT_REJECTED = "endpoint_rejected"
    CREDENTIAL_UNAVAILABLE = "credential_unavailable"
    TRANSPORT_FAILED = "transport_failed"
    RESPONSE_CONTRACT_REJECTED = "response_contract_rejected"
    EVIDENCE_PROJECTION_REJECTED = "evidence_projection_rejected"
    SOURCE_INTEGRITY_FAILED = "source_integrity_failed"
    OUTPUT_CONFLICT = "output_conflict"


class ReadOnlyAdapterError(RuntimeError):
    code: ReadOnlyErrorCode
    failed_claim_id: str | None

    def __init__(
        self,
        code: ReadOnlyErrorCode,
        *,
        failed_claim_id: str | None = None,
    ) -> None:
        self.code = code
        self.failed_claim_id = failed_claim_id
        super().__init__(code.value)


def bind_production_query_plan_to_audit(
    *,
    plan: LocalEvidenceQueryPlanV1,
    audit_bundle: ExternalAuditBundleV1,
) -> None:
    if (
        plan.execution_scope != "reviewed_live"
        or plan.collection != "local_kb_kaiyuan_v2"
        or plan.source_id != audit_bundle.source.source_id
        or plan.audit_id != audit_bundle.audit.audit_id
    ):
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.PLAN_MISMATCH)
    claim_ids = tuple(sorted(claim.claim_id for claim in audit_bundle.claims))
    if tuple(request.claim_id for request in plan.requests) != claim_ids:
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.PLAN_MISMATCH)


def bind_source_snapshot_to_plan(
    *,
    snapshot: LocalKBSourceSnapshotV1,
    plan: LocalEvidenceQueryPlanV1,
) -> None:
    if (
        snapshot.collection != plan.collection
        or snapshot.kb_book_id != plan.kb_book_id
        or snapshot.corpus_version != plan.expected_corpus_version
    ):
        raise ReadOnlyAdapterError(ReadOnlyErrorCode.SNAPSHOT_MISMATCH)


def canonical_contract_sha256(model: BaseModel) -> str:
    return hashlib.sha256(canonical_contract_bytes(model)).hexdigest()
