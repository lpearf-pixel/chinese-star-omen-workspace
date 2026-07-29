from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from src.video_pipeline.contracts._common import StableId, StrictContractModel
from src.video_pipeline.editorial import EditorialPackageV1


class SubtitleCueV1(StrictContractModel):
    schema_version: Literal["subtitle-cue/v1"] = "subtitle-cue/v1"
    index: int = Field(strict=True, ge=1)
    claim_id: StableId
    start_ms: int = Field(strict=True, ge=0)
    end_ms: int = Field(strict=True, gt=0)
    text: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="after")
    def validate_cue(self) -> "SubtitleCueV1":
        if self.end_ms <= self.start_ms:
            raise ValueError("subtitle cue end must be after start")
        if any(character in self.text for character in ("\n", "\r", "\x00")):
            raise ValueError("subtitle cue text must be a single safe line")
        return self


class SrtDocumentV1(StrictContractModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
        validate_default=True,
    )

    schema_version: Literal["srt-document/v1"] = "srt-document/v1"
    editorial_package_id: StableId
    total_duration_ms: int = Field(strict=True, ge=1)
    cues: list[SubtitleCueV1]
    content: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_document(self) -> "SrtDocumentV1":
        if not self.cues:
            raise ValueError("SRT document requires cues")
        if self.cues[0].start_ms != 0:
            raise ValueError("SRT timeline must start at zero")
        if self.cues[-1].end_ms != self.total_duration_ms:
            raise ValueError("SRT timeline must cover the full editorial duration")
        if [cue.index for cue in self.cues] != list(range(1, len(self.cues) + 1)):
            raise ValueError("SRT cue indexes must be contiguous")
        for left, right in zip(self.cues, self.cues[1:], strict=False):
            if left.end_ms != right.start_ms:
                raise ValueError("SRT cues must be continuous and non-overlapping")
        canonical = _render_srt(self.cues)
        if canonical != self.content:
            raise ValueError("SRT content does not match cue metadata")
        if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != self.sha256:
            raise ValueError("SRT content hash mismatch")
        return self


def _timestamp(milliseconds: int) -> str:
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _render_srt(cues: list[SubtitleCueV1]) -> str:
    blocks = [
        f"{cue.index}\n{_timestamp(cue.start_ms)} --> {_timestamp(cue.end_ms)}\n{cue.text}"
        for cue in cues
    ]
    return "\n\n".join(blocks) + "\n"


def generate_srt(editorial: EditorialPackageV1 | dict) -> SrtDocumentV1:
    package = (
        editorial
        if isinstance(editorial, EditorialPackageV1)
        else EditorialPackageV1.model_validate(editorial)
    )
    claims = {claim.claim_id: claim for claim in package.video_package.claims}
    cues = [
        SubtitleCueV1(
            index=index,
            claim_id=shot.claim_id,
            start_ms=shot.start_ms,
            end_ms=shot.end_ms,
            text=claims[shot.claim_id].text,
        )
        for index, shot in enumerate(package.shots, start=1)
    ]
    content = _render_srt(cues)
    return SrtDocumentV1(
        editorial_package_id=package.editorial_package_id,
        total_duration_ms=package.total_duration_ms,
        cues=cues,
        content=content,
        sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )


def canonical_srt_bytes(document: SrtDocumentV1) -> bytes:
    validated = SrtDocumentV1.model_validate(document.model_dump(mode="json"))
    return validated.content.encode("utf-8")


__all__ = [
    "SrtDocumentV1",
    "SubtitleCueV1",
    "canonical_srt_bytes",
    "generate_srt",
]
