from __future__ import annotations

import hashlib
import re
from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

_MAX_ASSET_BYTES = 1024 * 1024
_STABLE_ID_PATTERN = r"^[a-z0-9][a-z0-9._:/-]{0,159}$"
_PINNED_REVISION_RE = re.compile(r"^(?:[0-9a-f]{40,64}|[0-9]{4}-[0-9]{2}-[0-9]{2})$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


class AsterismStatus(StrEnum):
    VERIFIED_IDENTITY = "verified_identity"
    VERIFIED_MEMBERSHIP = "verified_membership"
    REGION_ONLY = "region_only"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"


class AsterismNarrationPolicy(StrEnum):
    EXPLICIT_STAR_NAME = "explicit_star_name"
    EXPLICIT_MEMBERSHIP = "explicit_membership"
    REGION_LIMITED = "region_limited"
    BLOCKED = "blocked"


class CatalogSourceV1(_StrictModel):
    source_id: str = Field(pattern=_STABLE_ID_PATTERN)
    source_type: Literal["git-file", "catalog-record"]
    title: str = Field(min_length=1, max_length=256)
    revision: str = Field(min_length=10, max_length=64)
    path_or_record: str = Field(min_length=1, max_length=512)
    content_sha: str | None = Field(default=None, pattern=r"^[0-9a-f]{40,64}$")
    locator: str = Field(min_length=1, max_length=512)
    reference_frame: str | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_pin(self) -> "CatalogSourceV1":
        if not _PINNED_REVISION_RE.fullmatch(self.revision):
            raise ValueError("catalog source revision must be pinned")
        if self.source_type == "git-file" and self.content_sha is None:
            raise ValueError("git-file source requires content_sha")
        return self


class ReferenceCoordinatesV1(_StrictModel):
    frame: Literal["icrs"]
    epoch: Literal["J2000"]
    ra_deg: float = Field(strict=True, ge=0.0, lt=360.0, allow_inf_nan=False)
    dec_deg: float = Field(strict=True, ge=-90.0, le=90.0, allow_inf_nan=False)


class AsterismEntryV1(_StrictModel):
    modern_object_id: str = Field(pattern=_STABLE_ID_PATTERN)
    traditional_star_id: str = Field(pattern=_STABLE_ID_PATTERN)
    asterism_id: str = Field(pattern=_STABLE_ID_PATTERN)
    canonical_chinese_name: str = Field(min_length=1, max_length=128)
    aliases: list[str] = Field(default_factory=list)
    catalog_epoch: Literal["J2000"]
    reference_coordinates: ReferenceCoordinatesV1
    source_refs: list[str] = Field(min_length=1)
    mapping_method: Literal["catalog-identity", "catalog-membership", "region-definition"]
    confidence: float = Field(strict=True, ge=0.0, le=1.0, allow_inf_nan=False)
    editorial_status: AsterismStatus

    @model_validator(mode="after")
    def validate_status_claim(self) -> "AsterismEntryV1":
        if self.editorial_status is AsterismStatus.VERIFIED_IDENTITY:
            if self.mapping_method != "catalog-identity" or self.confidence < 0.95:
                raise ValueError("verified_identity requires catalog identity confidence >= 0.95")
            if len(self.source_refs) < 2:
                raise ValueError("verified_identity requires at least two source references")
        if self.editorial_status is AsterismStatus.VERIFIED_MEMBERSHIP:
            if self.mapping_method not in {"catalog-identity", "catalog-membership"}:
                raise ValueError("verified_membership requires a catalog mapping")
            if self.confidence < 0.8:
                raise ValueError("verified_membership confidence must be >= 0.8")
        if self.editorial_status is AsterismStatus.REGION_ONLY:
            if self.mapping_method != "region-definition":
                raise ValueError("region_only requires a region definition")
        return self


class AsterismResolutionV1(_StrictModel):
    schema_version: Literal["asterism-resolution/v1"] = "asterism-resolution/v1"
    query: str = Field(min_length=1, max_length=256)
    status: AsterismStatus
    narration_policy: AsterismNarrationPolicy
    modern_object_id: str | None = Field(default=None, pattern=_STABLE_ID_PATTERN)
    traditional_star_id: str | None = Field(default=None, pattern=_STABLE_ID_PATTERN)
    asterism_id: str | None = Field(default=None, pattern=_STABLE_ID_PATTERN)
    canonical_chinese_name: str | None = None
    reference_coordinates: ReferenceCoordinatesV1 | None = None
    confidence: float | None = Field(default=None, strict=True, ge=0.0, le=1.0, allow_inf_nan=False)
    source_refs: list[str] = Field(default_factory=list)


class AsterismCatalogV1(_StrictModel):
    schema_version: Literal["asterism-catalog/v1"]
    catalog_id: str = Field(pattern=_STABLE_ID_PATTERN)
    catalog_version: int = Field(strict=True, ge=1)
    sources: list[CatalogSourceV1]
    entries: list[AsterismEntryV1]

    @staticmethod
    def _normalize_alias(value: str) -> str:
        normalized = " ".join(value.strip().casefold().split())
        if not normalized:
            raise ValueError("catalog alias must not be empty")
        return normalized

    @model_validator(mode="after")
    def validate_catalog(self) -> "AsterismCatalogV1":
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("catalog source IDs must be unique")
        source_set = set(source_ids)
        modern_ids = [entry.modern_object_id for entry in self.entries]
        traditional_ids = [entry.traditional_star_id for entry in self.entries]
        if len(modern_ids) != len(set(modern_ids)):
            raise ValueError("modern object IDs must be unique")
        if len(traditional_ids) != len(set(traditional_ids)):
            raise ValueError("traditional star IDs must be unique")

        alias_owner: dict[str, str] = {}
        for entry in self.entries:
            if any(source_ref not in source_set for source_ref in entry.source_refs):
                raise ValueError("entry references an unknown catalog source")
            aliases = [entry.modern_object_id, *entry.aliases]
            normalized_aliases = [self._normalize_alias(alias) for alias in aliases]
            if len(normalized_aliases) != len(set(normalized_aliases)):
                raise ValueError("entry aliases must be unique")
            for alias in normalized_aliases:
                previous = alias_owner.get(alias)
                if previous is not None and previous != entry.modern_object_id:
                    raise ValueError("catalog alias must be globally unique")
                alias_owner[alias] = entry.modern_object_id
        return self

    def entry(self, modern_object_id: str) -> AsterismEntryV1:
        for entry in self.entries:
            if entry.modern_object_id == modern_object_id:
                return entry
        raise KeyError(modern_object_id)

    def resolve(self, query: str) -> AsterismResolutionV1:
        normalized = self._normalize_alias(query)
        for entry in self.entries:
            aliases = {
                self._normalize_alias(entry.modern_object_id),
                *(self._normalize_alias(alias) for alias in entry.aliases),
            }
            if normalized in aliases:
                policy = {
                    AsterismStatus.VERIFIED_IDENTITY: AsterismNarrationPolicy.EXPLICIT_STAR_NAME,
                    AsterismStatus.VERIFIED_MEMBERSHIP: AsterismNarrationPolicy.EXPLICIT_MEMBERSHIP,
                    AsterismStatus.REGION_ONLY: AsterismNarrationPolicy.REGION_LIMITED,
                    AsterismStatus.AMBIGUOUS: AsterismNarrationPolicy.BLOCKED,
                    AsterismStatus.UNRESOLVED: AsterismNarrationPolicy.BLOCKED,
                }[entry.editorial_status]
                return AsterismResolutionV1(
                    query=entry.modern_object_id,
                    status=entry.editorial_status,
                    narration_policy=policy,
                    modern_object_id=entry.modern_object_id,
                    traditional_star_id=entry.traditional_star_id,
                    asterism_id=entry.asterism_id,
                    canonical_chinese_name=entry.canonical_chinese_name,
                    reference_coordinates=entry.reference_coordinates,
                    confidence=entry.confidence,
                    source_refs=list(entry.source_refs),
                )
        return AsterismResolutionV1(
            query=normalized,
            status=AsterismStatus.UNRESOLVED,
            narration_policy=AsterismNarrationPolicy.BLOCKED,
        )


class AsterismCatalogSnapshotV1(_StrictModel):
    schema_version: Literal["asterism-catalog-snapshot/v1"] = "asterism-catalog-snapshot/v1"
    logical_name: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}\.ya?ml$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(strict=True, gt=0, le=_MAX_ASSET_BYTES)
    catalog: AsterismCatalogV1


def load_asterism_catalog(path: str | Path) -> AsterismCatalogSnapshotV1:
    asset_path = Path(path)
    if asset_path.is_symlink():
        raise ValueError("asterism catalog must not be a symlink")
    if not asset_path.exists():
        raise FileNotFoundError(asset_path)
    if not asset_path.is_file():
        raise ValueError("asterism catalog must be a regular file")
    if asset_path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("asterism catalog must use yaml")
    size = asset_path.stat().st_size
    if size <= 0:
        raise ValueError("asterism catalog is empty")
    if size > _MAX_ASSET_BYTES:
        raise ValueError("asterism catalog is too large")
    raw = asset_path.read_bytes()
    try:
        payload = yaml.safe_load(raw.decode("utf-8", errors="strict"))
    except UnicodeDecodeError as exc:
        raise ValueError("asterism catalog must be strict UTF-8") from exc
    except yaml.YAMLError as exc:
        raise ValueError("asterism catalog is invalid YAML") from exc
    if not isinstance(payload, dict):
        raise ValueError("asterism catalog root must be a mapping")
    catalog = AsterismCatalogV1.model_validate(payload)
    return AsterismCatalogSnapshotV1(
        logical_name=asset_path.name,
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_size=len(raw),
        catalog=catalog,
    )
