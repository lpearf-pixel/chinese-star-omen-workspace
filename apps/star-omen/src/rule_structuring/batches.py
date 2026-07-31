from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .passage_inventory import PassageInventoryV1


class BatchError(ValueError):
    pass


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


def _canonical(value: object) -> bytes:
    payload = (
        value.model_dump(mode="json", exclude_none=False)
        if isinstance(value, BaseModel)
        else value
    )
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_batch_bytes(value: BaseModel) -> bytes:
    return _canonical(value) + b"\n"


class BatchV1(_StrictModel):
    batch_id: str = Field(pattern=r"^batch:sha256:[0-9a-f]{64}$")
    input_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    inventory_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    tool_version: Literal["rule-batches/v1"]
    batch_size: int = Field(strict=True, ge=100, le=500)
    batch_index: int = Field(strict=True, ge=0)
    passage_ids: tuple[str, ...] = Field(min_length=1)


class BatchPlanV1(_StrictModel):
    schema_version: Literal["rule-batch-plan/v1"]
    inventory_fingerprint: str
    batch_size: int
    batches: tuple[BatchV1, ...]


def plan_batches(
    inventory: PassageInventoryV1,
    batch_size: int = 200,
) -> BatchPlanV1:
    if (
        isinstance(batch_size, bool)
        or not isinstance(batch_size, int)
        or not 100 <= batch_size <= 500
    ):
        raise BatchError("batch_size must be an integer from 100 to 500")
    passage_ids = sorted(item.passage_id for item in inventory.passages)
    batches = []
    for index, start in enumerate(range(0, len(passage_ids), batch_size)):
        members = tuple(passage_ids[start : start + batch_size])
        identity = {
            "task_type": "rule_structuring",
            "inventory_fingerprint": inventory.source_fingerprint,
            "tool_version": "rule-batches/v1",
            "batch_size": batch_size,
            "passage_ids": members,
        }
        digest = hashlib.sha256(_canonical(identity)).hexdigest()
        input_hash = "sha256:" + hashlib.sha256(
            _canonical({"passage_ids": members})
        ).hexdigest()
        batches.append(
            BatchV1(
                batch_id=f"batch:sha256:{digest}",
                input_hash=input_hash,
                inventory_fingerprint=inventory.source_fingerprint,
                tool_version="rule-batches/v1",
                batch_size=batch_size,
                batch_index=index,
                passage_ids=members,
            )
        )
    return BatchPlanV1(
        schema_version="rule-batch-plan/v1",
        inventory_fingerprint=inventory.source_fingerprint,
        batch_size=batch_size,
        batches=tuple(batches),
    )


class CompletedItemV1(_StrictModel):
    passage_id: str
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class FailedItemV1(_StrictModel):
    passage_id: str
    reason_code: str
    detail: str


class DeferredItemV1(_StrictModel):
    passage_id: str
    reason_code: str
    detail: str


class BatchCheckpointV1(_StrictModel):
    schema_version: Literal["rule-batch-checkpoint/v1"]
    batch_id: str = Field(pattern=r"^batch:sha256:[0-9a-f]{64}$")
    input_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    sequence: int = Field(strict=True, ge=0)
    status: Literal["in_progress", "completed"]
    completed: tuple[CompletedItemV1, ...] = ()
    failed: tuple[FailedItemV1, ...] = ()
    deferred: tuple[DeferredItemV1, ...] = ()

    @classmethod
    def new(cls, batch: BatchV1) -> "BatchCheckpointV1":
        return cls(
            schema_version="rule-batch-checkpoint/v1",
            batch_id=batch.batch_id,
            input_hash=batch.input_hash,
            sequence=0,
            status="in_progress",
        )

    @model_validator(mode="after")
    def validate_sets(self) -> "BatchCheckpointV1":
        groups = [
            {item.passage_id for item in self.completed},
            {item.passage_id for item in self.failed},
            {item.passage_id for item in self.deferred},
        ]
        if any(
            len(group) != len(items)
            for group, items in zip(
                groups, (self.completed, self.failed, self.deferred)
            )
        ):
            raise ValueError("checkpoint groups must contain unique passage IDs")
        if any(groups[left] & groups[right] for left in range(3) for right in range(left + 1, 3)):
            raise ValueError("checkpoint groups must be disjoint")
        return self

    def with_completed(
        self, passage_id: str, output_sha256: str
    ) -> "BatchCheckpointV1":
        if passage_id in {
            item.passage_id
            for item in (*self.completed, *self.failed, *self.deferred)
        }:
            raise BatchError("passage already has a checkpoint outcome")
        return self.model_copy(
            update={
                "sequence": self.sequence + 1,
                "completed": tuple(
                    sorted(
                        (*self.completed, CompletedItemV1(
                            passage_id=passage_id,
                            output_sha256=output_sha256,
                        )),
                        key=lambda item: item.passage_id,
                    )
                ),
            }
        )

    def _with_outcome(
        self,
        batch: BatchV1,
        passage_id: str,
        *,
        field_name: Literal["failed", "deferred"],
        reason_code: str,
        detail: str,
    ) -> "BatchCheckpointV1":
        resume_batch(batch, self)
        if passage_id not in batch.passage_ids:
            raise BatchError("passage is outside batch")
        if passage_id in {
            item.passage_id
            for item in (*self.completed, *self.failed, *self.deferred)
        }:
            raise BatchError("passage already has a checkpoint outcome")
        model = FailedItemV1 if field_name == "failed" else DeferredItemV1
        values = tuple(
            sorted(
                (
                    *getattr(self, field_name),
                    model(
                        passage_id=passage_id,
                        reason_code=reason_code,
                        detail=detail,
                    ),
                ),
                key=lambda item: item.passage_id,
            )
        )
        return self.model_copy(
            update={"sequence": self.sequence + 1, field_name: values}
        )

    def with_failed(
        self,
        batch: BatchV1,
        passage_id: str,
        reason_code: str,
        detail: str,
    ) -> "BatchCheckpointV1":
        return self._with_outcome(
            batch,
            passage_id,
            field_name="failed",
            reason_code=reason_code,
            detail=detail,
        )

    def with_deferred(
        self,
        batch: BatchV1,
        passage_id: str,
        reason_code: str,
        detail: str,
    ) -> "BatchCheckpointV1":
        return self._with_outcome(
            batch,
            passage_id,
            field_name="deferred",
            reason_code=reason_code,
            detail=detail,
        )

    def finalize(self, batch: BatchV1) -> "BatchCheckpointV1":
        outcomes = {
            item.passage_id
            for item in (*self.completed, *self.failed, *self.deferred)
        }
        if outcomes != set(batch.passage_ids):
            raise BatchError("cannot finalize before every passage has an outcome")
        return self.model_copy(
            update={"sequence": self.sequence + 1, "status": "completed"}
        )


class BatchStateV1(_StrictModel):
    batch_id: str
    status: Literal["in_progress", "completed"]
    remaining_passage_ids: tuple[str, ...]
    checkpoint_sequence: int


def resume_batch(batch: BatchV1, checkpoint: BatchCheckpointV1) -> BatchStateV1:
    if checkpoint.batch_id != batch.batch_id or checkpoint.input_hash != batch.input_hash:
        raise BatchError("checkpoint identity mismatch")
    outcomes = {
        item.passage_id
        for item in (*checkpoint.completed, *checkpoint.failed, *checkpoint.deferred)
    }
    if not outcomes <= set(batch.passage_ids):
        raise BatchError("checkpoint contains passage outside batch")
    remaining = tuple(item for item in batch.passage_ids if item not in outcomes)
    expected_status = "completed" if not remaining else "in_progress"
    if checkpoint.status != expected_status:
        raise BatchError("checkpoint status does not match coverage")
    return BatchStateV1(
        batch_id=batch.batch_id,
        status=expected_status,
        remaining_passage_ids=remaining,
        checkpoint_sequence=checkpoint.sequence,
    )


def write_checkpoint_no_overwrite(
    output: str | Path,
    checkpoint: BatchCheckpointV1,
) -> None:
    path = Path(output)
    encoded = _canonical(checkpoint) + b"\n"
    temporary: Path | None = None
    linking = False
    try:
        if path.exists():
            raise BatchError("output_exists")
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        linking = True
        os.link(temporary, path)
    except FileExistsError as exc:
        raise BatchError("output_exists" if linking else "output_write_failed") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
