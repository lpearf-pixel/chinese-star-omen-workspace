from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import PurePosixPath
from typing import Annotated, Any, Literal
from urllib.parse import ParseResult, parse_qs, unquote, urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)


_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")
_CASE_ID_RE = re.compile(r"^C[0-9]{2}$")
_RAW_ROOT = PurePosixPath("corpus/research_sources/related-wikisource")
_WIKISOURCE_HOST = "zh.wikisource.org"

SafeId = Annotated[
    str,
    Field(strict=True, min_length=1, max_length=160, pattern=_SAFE_ID_RE.pattern),
]
Sha256Hex = Annotated[str, Field(strict=True, pattern=r"^[0-9a-f]{64}$")]
PositiveOldId = Annotated[int, Field(strict=True, gt=0)]
RawByteCount = Annotated[int, Field(strict=True, ge=0)]
NonEmptyText = Annotated[str, Field(strict=True, min_length=1, max_length=10_000)]


def _has_exact_wikisource_origin(parsed: ParseResult) -> bool:
    try:
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.hostname == _WIKISOURCE_HOST
        and parsed.username is None
        and parsed.password is None
        and port is None
    )


def _floating_title_from_path(path: str) -> str | None:
    for prefix in ("/wiki/", "/zh-hant/"):
        if path.startswith(prefix):
            encoded_title = path[len(prefix) :]
            return (
                _normalize_mediawiki_title(unquote(encoded_title))
                if encoded_title
                else None
            )
    return None


def _normalize_mediawiki_title(value: str) -> str:
    return value.replace("_", " ")


class CaptureStatus(str, Enum):
    COMPLETE = "complete"
    UNAVAILABLE = "unavailable"
    PARTIAL_WITH_REASON = "partial_with_reason"


class ResearchAccessionV1(BaseModel):
    """Immutable fixed-source preservation record for the research layer.

    ``work_normalized_candidate``, ``version_family``,
    ``independent_witness_note``, and an uncertain ``author_or_compiler`` are
    compatibility-preserved legacy hypothesis strings. They are retained
    verbatim for round-trip fidelity; none is an authority assertion, witness
    approval, reviewer decision, or production-ingest decision.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:research-accession/v1"},
    )

    schema_version: Literal["research-accession/v1"]
    accession_id: SafeId
    family_id: SafeId
    work_printed: NonEmptyText
    work_normalized_candidate: NonEmptyText
    page_title: NonEmptyText
    oldid: PositiveOldId | None = None
    permanent_url: NonEmptyText | None = None
    floating_url: NonEmptyText
    revision_timestamp: datetime | None = None
    accessed_on: date
    locator: NonEmptyText
    version_family: NonEmptyText
    author_or_compiler: NonEmptyText
    license_note: NonEmptyText
    independent_witness_note: NonEmptyText
    core14_cases: tuple[str, ...] = ()
    relevant_excerpt: str = Field(strict=True, max_length=100_000)
    excerpt_locator: NonEmptyText
    raw_path: str | None = Field(default=None, strict=True)
    raw_sha256: Sha256Hex | None = None
    raw_byte_count: RawByteCount | None = None
    capture_status: CaptureStatus
    capture_note: NonEmptyText
    failure_reason: NonEmptyText | None = None

    @field_validator(
        "work_printed",
        "work_normalized_candidate",
        "page_title",
        "floating_url",
        "locator",
        "version_family",
        "author_or_compiler",
        "license_note",
        "independent_witness_note",
        "excerpt_locator",
        "capture_note",
    )
    @classmethod
    def validate_required_text_verbatim(
        cls, value: str, info: ValidationInfo
    ) -> str:
        if not value.strip():
            raise ValueError(f"{info.field_name} must not be blank")
        return value

    @field_validator("permanent_url", "failure_reason")
    @classmethod
    def validate_optional_text_verbatim(
        cls, value: str | None, info: ValidationInfo
    ) -> str | None:
        if value is not None and not value.strip():
            raise ValueError(f"{info.field_name} must not be blank")
        return value

    @field_validator("accessed_on", mode="before")
    @classmethod
    def validate_accessed_on_input(cls, value: object) -> date:
        if isinstance(value, datetime):
            raise ValueError("accessed_on must be a date, not a datetime")
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
                raise ValueError("accessed_on string must use YYYY-MM-DD")
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError("accessed_on must be a valid calendar date") from exc
        raise ValueError("accessed_on must be YYYY-MM-DD or a date object")

    @field_validator("revision_timestamp")
    @classmethod
    def validate_revision_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("revision_timestamp must include an explicit UTC offset")
        if value.utcoffset() != timedelta(0):
            raise ValueError("revision_timestamp must be expressed in UTC")
        return value

    @field_validator("core14_cases")
    @classmethod
    def validate_core14_cases(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(_CASE_ID_RE.fullmatch(value) is None for value in values):
            raise ValueError("core14_cases must match C followed by two digits")
        if len(values) != len(set(values)):
            raise ValueError("core14_cases must contain unique case IDs")
        if values != tuple(sorted(values)):
            raise ValueError("core14_cases must be sorted")
        return values

    @field_validator("raw_path")
    @classmethod
    def validate_raw_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if "\x00" in value or "\\" in value:
            raise ValueError("raw_path must use repository-relative POSIX syntax")
        path = PurePosixPath(value)
        if path.as_posix() != value:
            raise ValueError("raw_path must use exact canonical POSIX syntax")
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("raw_path must be confined to the research source package")
        root_parts = _RAW_ROOT.parts
        if path.parts[: len(root_parts)] != root_parts or path == _RAW_ROOT:
            raise ValueError("raw_path must be under the research source package")
        return value

    @model_validator(mode="after")
    def validate_capture_boundary(self) -> "ResearchAccessionV1":
        raw_identity = (self.raw_path, self.raw_sha256, self.raw_byte_count)
        present_count = sum(value is not None for value in raw_identity)
        if present_count not in (0, len(raw_identity)):
            raise ValueError(
                "raw identity fields raw_path, raw_sha256 and raw_byte_count "
                "must be all present or all absent"
            )

        if self.capture_status is CaptureStatus.COMPLETE:
            if self.failure_reason is not None:
                raise ValueError(
                    "failure_reason must be null when capture_status is complete"
                )
            required: dict[str, Any] = {
                "oldid": self.oldid,
                "permanent_url": self.permanent_url,
                "revision_timestamp": self.revision_timestamp,
                "raw_path": self.raw_path,
                "raw_sha256": self.raw_sha256,
                "raw_byte_count": self.raw_byte_count,
            }
            missing = [name for name, value in required.items() if value is None]
            if missing:
                raise ValueError(
                    "complete capture requires " + ", ".join(sorted(missing))
                )
        elif not self.failure_reason:
            raise ValueError("failure_reason is required for non-complete captures")

        if self.capture_status is CaptureStatus.UNAVAILABLE and present_count:
            raise ValueError("unavailable capture cannot declare a raw identity")

        floating = urlparse(self.floating_url)
        floating_title = _floating_title_from_path(floating.path)
        if (
            not _has_exact_wikisource_origin(floating)
            or floating.params
            or floating.query
            or floating.fragment
            or floating_title != _normalize_mediawiki_title(self.page_title)
        ):
            raise ValueError(
                "floating_url must be the matching HTTPS zh.wikisource.org "
                "wiki or zh-hant route"
            )

        if self.permanent_url is not None:
            if self.oldid is None:
                raise ValueError("permanent_url requires oldid")
            parsed = urlparse(self.permanent_url)
            try:
                query = parse_qs(
                    parsed.query,
                    keep_blank_values=True,
                    strict_parsing=True,
                )
            except ValueError as exc:
                raise ValueError("permanent_url contains an invalid query") from exc
            title_values = query.get("title")
            if (
                not _has_exact_wikisource_origin(parsed)
                or parsed.path != "/w/index.php"
                or parsed.params
                or parsed.fragment
                or set(query) != {"title", "oldid"}
                or title_values is None
                or len(title_values) != 1
                or _normalize_mediawiki_title(title_values[0])
                != _normalize_mediawiki_title(self.page_title)
                or query.get("oldid") != [str(self.oldid)]
            ):
                raise ValueError(
                    "permanent_url must be the exact HTTPS zh.wikisource.org "
                    "revision route for page_title and oldid"
                )
        return self

    def canonical_json_bytes(self) -> bytes:
        return json.dumps(
            self.model_dump(mode="json", exclude_none=False),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")


__all__ = ["CaptureStatus", "ResearchAccessionV1"]
