from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Literal

from kb_text_core.rule_passages import (
    RulePassageRecord,
    build_passage_records,
    compare_passage_records,
)
from kb_text_core import parse_kaiyuan_passages
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.connectors.kb_contract import infer_metadata_from_path


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


class PassageRecordV1(_StrictModel):
    passage_id: str = Field(pattern=r"^passage:sha256:[0-9a-f]{64}$")
    kb_book_id: str
    book_title: str
    card_type: Literal["fenjuan", "fulltext"]
    source_path: str
    source_locator: str
    source_volume: str | None
    page_marker: str | None
    heading_path: tuple[str, ...]
    paragraph_index: int = Field(strict=True, ge=0)
    raw_start: int = Field(strict=True, ge=0)
    raw_end: int = Field(strict=True, gt=0)
    raw_text: str
    normalized_text: str
    raw_content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    normalized_content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    source_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    duplicate_sources: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_paths(self) -> "PassageRecordV1":
        if Path(self.source_path).is_absolute() or ".." in Path(self.source_path).parts:
            raise ValueError("source_path must be a safe relative path")
        if any(
            Path(path).is_absolute() or ".." in Path(path).parts
            for path in self.duplicate_sources
        ):
            raise ValueError("duplicate_sources must be safe relative paths")
        return self


class AmbiguousAnchorV1(_StrictModel):
    kb_book_id: str
    source_locator: str
    page_marker: str | None
    paragraph_index: int
    passage_ids: tuple[str, ...] = Field(min_length=2)


class PassageInventoryV1(_StrictModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:rule-passage-inventory/v1"},
    )

    schema_version: Literal["rule-passage-inventory/v1"]
    source_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    passages: tuple[PassageRecordV1, ...] = Field(min_length=1)
    ambiguous_anchors: tuple[AmbiguousAnchorV1, ...] = ()

    @model_validator(mode="after")
    def validate_inventory(self) -> "PassageInventoryV1":
        passage_ids = [item.passage_id for item in self.passages]
        if len(passage_ids) != len(set(passage_ids)):
            raise ValueError("passages must contain unique passage IDs")
        if passage_ids != sorted(passage_ids):
            raise ValueError("passages must be sorted by passage_id")
        return self


class ChangedPassageV1(_StrictModel):
    anchor: tuple[str, str, str, int]
    previous_passage_id: str
    current_passage_id: str


class SourceChangeReportV1(_StrictModel):
    schema_version: Literal["rule-source-change-report/v1"]
    status: Literal["unchanged", "source_changed"]
    previous_source_fingerprint: str
    current_source_fingerprint: str
    invalidated_passage_ids: tuple[str, ...]
    unchanged_passage_ids: tuple[str, ...]
    added_passage_ids: tuple[str, ...]
    removed_passage_ids: tuple[str, ...]
    changed: tuple[ChangedPassageV1, ...]
    ambiguous_anchors: tuple[tuple[str, str, str, int], ...]


def canonical_inventory_bytes(inventory: PassageInventoryV1) -> bytes:
    return (
        json.dumps(
            inventory.model_dump(mode="json", exclude_none=False),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def build_rule_passage_inventory(kb_root: str | Path) -> PassageInventoryV1:
    root = Path(kb_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("kb_root must be an existing directory")
    passages = []
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.md"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise ValueError("primary source must not be a symlink")
        inferred = infer_metadata_from_path(str(path))
        card_type = str(inferred.get("card_type") or "")
        if card_type not in {"fenjuan", "fulltext"}:
            continue
        relative = path.relative_to(root).as_posix()
        raw = path.read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(raw)
        text = raw.decode("utf-8")
        parsed = parse_kaiyuan_passages(
            text,
            source_path=relative,
            card_type=card_type,
            kb_book_id=str(inferred.get("kb_book_id") or "kaiyuan_zhanjing"),
            book_title=str(inferred.get("book_title") or "唐開元占經"),
        )
        passages.extend(replace(item, source_path=relative) for item in parsed)
    if not passages:
        raise ValueError("kb_root contains no recognized primary passages")
    records, ambiguities = build_passage_records(passages)
    source_fingerprint = "sha256:" + digest.hexdigest()
    return PassageInventoryV1(
        schema_version="rule-passage-inventory/v1",
        source_fingerprint=source_fingerprint,
        passages=tuple(
            sorted(
                (
                    PassageRecordV1.model_validate(
                        {
                            **item.to_dict(),
                            "source_fingerprint": source_fingerprint,
                        }
                    )
                    for item in records
                ),
                key=lambda item: item.passage_id,
            )
        ),
        ambiguous_anchors=tuple(
            AmbiguousAnchorV1.model_validate(
                {
                    "kb_book_id": item.kb_book_id,
                    "source_locator": item.source_locator,
                    "page_marker": item.page_marker,
                    "paragraph_index": item.paragraph_index,
                    "passage_ids": item.passage_ids,
                }
            )
            for item in ambiguities
        ),
    )


def _as_core_record(item: PassageRecordV1) -> RulePassageRecord:
    return RulePassageRecord(
        passage_id=item.passage_id,
        kb_book_id=item.kb_book_id,
        book_title=item.book_title,
        card_type=item.card_type,
        source_path=item.source_path,
        source_locator=item.source_locator,
        source_volume=item.source_volume,
        page_marker=item.page_marker,
        heading_path=item.heading_path,
        paragraph_index=item.paragraph_index,
        raw_start=item.raw_start,
        raw_end=item.raw_end,
        raw_text=item.raw_text,
        normalized_text=item.normalized_text,
        raw_content_hash=item.raw_content_hash,
        normalized_content_hash=item.normalized_content_hash,
        duplicate_sources=item.duplicate_sources,
    )


def compare_source_fingerprint(
    previous: PassageInventoryV1,
    current: PassageInventoryV1,
) -> SourceChangeReportV1:
    report = compare_passage_records(
        (_as_core_record(item) for item in previous.passages),
        (_as_core_record(item) for item in current.passages),
    )
    return SourceChangeReportV1(
        schema_version="rule-source-change-report/v1",
        status=report.status,
        previous_source_fingerprint=previous.source_fingerprint,
        current_source_fingerprint=current.source_fingerprint,
        invalidated_passage_ids=report.invalidated_passage_ids,
        unchanged_passage_ids=report.unchanged_passage_ids,
        added_passage_ids=report.added_passage_ids,
        removed_passage_ids=report.removed_passage_ids,
        changed=tuple(
            ChangedPassageV1(
                anchor=item.anchor,
                previous_passage_id=item.previous_passage_id,
                current_passage_id=item.current_passage_id,
            )
            for item in report.changed
        ),
        ambiguous_anchors=report.ambiguous_anchors,
    )
