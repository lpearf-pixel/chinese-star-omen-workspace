from __future__ import annotations

import hashlib
import json
import re
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

_MAX_ASSET_BYTES = 1024 * 1024
_MAX_SOURCE_BYTES = 256 * 1024
_APP_ROOT = Path(__file__).resolve().parents[3]
_STABLE_ID_PATTERN = r"^[a-z0-9][a-z0-9._:/-]{0,159}$"
_PINNED_REVISION_RE = re.compile(r"^(?:[0-9a-f]{40,64}|[0-9]{4}-[0-9]{2}-[0-9]{2})$")
_SNAPSHOT_PATH_RE = r"^data/video_pipeline/sources/[a-z0-9][a-z0-9._-]{0,127}\.json$"


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


def _parse_asterism_status(value: object) -> AsterismStatus:
    if isinstance(value, AsterismStatus):
        return value
    if isinstance(value, str):
        try:
            return AsterismStatus(value)
        except ValueError as exc:
            raise ValueError("unknown asterism status") from exc
    raise TypeError("asterism status must be a string")


AsterismStatusValue = Annotated[AsterismStatus, BeforeValidator(_parse_asterism_status)]


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
    content_hash_algorithm: Literal["sha256"]
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    snapshot_path: str = Field(pattern=_SNAPSHOT_PATH_RE)
    upstream_content_id_algorithm: Literal["git-sha1"] | None = None
    upstream_content_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    locator: str = Field(min_length=1, max_length=512)
    reference_frame: str | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_pin(self) -> "CatalogSourceV1":
        if not _PINNED_REVISION_RE.fullmatch(self.revision):
            raise ValueError("catalog source revision must be pinned")
        if (self.upstream_content_id_algorithm is None) != (
            self.upstream_content_id is None
        ):
            raise ValueError("upstream content ID algorithm and value must appear together")
        if self.source_type == "git-file" and self.upstream_content_id is None:
            raise ValueError("git-file source requires a pinned upstream content ID")
        return self


class ReferenceCoordinatesV1(_StrictModel):
    frame: Literal["icrs"]
    epoch: Literal["J2000", "J1991.25"]
    ra_deg: float = Field(strict=True, ge=0.0, lt=360.0, allow_inf_nan=False)
    dec_deg: float = Field(strict=True, ge=-90.0, le=90.0, allow_inf_nan=False)
    pm_ra_cosdec_mas_per_year: float | None = Field(
        default=None,
        strict=True,
        allow_inf_nan=False,
    )
    pm_dec_mas_per_year: float | None = Field(
        default=None,
        strict=True,
        allow_inf_nan=False,
    )

    @model_validator(mode="after")
    def validate_proper_motion_pair(self) -> "ReferenceCoordinatesV1":
        if (self.pm_ra_cosdec_mas_per_year is None) != (
            self.pm_dec_mas_per_year is None
        ):
            raise ValueError("proper-motion components must appear together")
        return self


class AsterismEntryV1(_StrictModel):
    modern_object_id: str = Field(pattern=_STABLE_ID_PATTERN)
    traditional_star_id: str = Field(pattern=_STABLE_ID_PATTERN)
    asterism_id: str = Field(pattern=_STABLE_ID_PATTERN)
    canonical_chinese_name: str = Field(min_length=1, max_length=128)
    aliases: list[str] = Field(default_factory=list)
    catalog_epoch: Literal["J2000", "J1991.25"]
    reference_coordinates: ReferenceCoordinatesV1
    source_refs: list[str] = Field(min_length=1)
    mapping_method: Literal["catalog-identity", "catalog-membership", "region-definition"]
    confidence: float = Field(strict=True, ge=0.0, le=1.0, allow_inf_nan=False)
    editorial_status: AsterismStatusValue

    @model_validator(mode="after")
    def validate_status_claim(self) -> "AsterismEntryV1":
        if self.catalog_epoch != self.reference_coordinates.epoch:
            raise ValueError("catalog epoch must match reference-coordinate epoch")
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


class AsterismDefinitionV1(_StrictModel):
    asterism_id: str = Field(pattern=_STABLE_ID_PATTERN)
    canonical_chinese_name: str = Field(min_length=1, max_length=128)
    aliases: list[str] = Field(default_factory=list)
    member_object_ids: list[str] = Field(min_length=1)
    related_object_ids: list[str] = Field(default_factory=list)
    defining_star_object_id: str = Field(pattern=_STABLE_ID_PATTERN)
    line_segments: list[list[str]] = Field(default_factory=list)
    source_refs: list[str] = Field(min_length=1)
    completeness_status: Literal[
        "partial",
        "complete",
        "complete_gold_sample",
        "ambiguous",
    ]

    @model_validator(mode="after")
    def validate_definition(self) -> "AsterismDefinitionV1":
        if len(self.member_object_ids) != len(set(self.member_object_ids)):
            raise ValueError("asterism member object IDs must be unique")
        if len(self.related_object_ids) != len(set(self.related_object_ids)):
            raise ValueError("asterism related object IDs must be unique")
        if set(self.member_object_ids) & set(self.related_object_ids):
            raise ValueError("member and related object IDs must be disjoint")
        if self.defining_star_object_id not in self.member_object_ids:
            raise ValueError("defining star must be an asterism member")
        if self.completeness_status != "partial" and not self.line_segments:
            raise ValueError("non-partial asterisms require line segments")
        allowed_endpoints = set(self.member_object_ids) | set(self.related_object_ids)
        for segment in self.line_segments:
            if len(segment) < 2:
                raise ValueError("asterism line segments require at least two objects")
            if any(endpoint not in allowed_endpoints for endpoint in segment):
                raise ValueError("asterism line segment references an unknown endpoint")
        return self


class LunarMansionDefinitionV1(_StrictModel):
    mansion_id: str = Field(pattern=_STABLE_ID_PATTERN)
    sequence_index: int = Field(strict=True, ge=1, le=28)
    west_boundary_object_id: str = Field(pattern=_STABLE_ID_PATTERN)
    east_boundary_object_id: str = Field(pattern=_STABLE_ID_PATTERN)
    boundary_model: Literal["polar-great-circles"]
    coordinate_system: Literal["apparent-equatorial-of-date"]
    provenance_class: Literal["derived_region"]
    source_refs: list[str] = Field(min_length=1)
    completeness_status: Literal[
        "partial",
        "complete_gold_sample",
        "complete_region_cycle",
    ]

    @model_validator(mode="after")
    def validate_boundaries(self) -> "LunarMansionDefinitionV1":
        if self.west_boundary_object_id == self.east_boundary_object_id:
            raise ValueError("mansion boundaries must be distinct")
        return self


class AsterismResolutionV1(_StrictModel):
    schema_version: Literal["asterism-resolution/v1"] = "asterism-resolution/v1"
    query: str = Field(min_length=1, max_length=256)
    status: AsterismStatusValue
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
    lunar_mansion_cycle_status: Literal["partial", "complete"] = "partial"
    sources: list[CatalogSourceV1]
    entries: list[AsterismEntryV1]
    asterisms: list[AsterismDefinitionV1] = Field(default_factory=list)
    lunar_mansions: list[LunarMansionDefinitionV1] = Field(default_factory=list)

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
            aliases = [
                entry.modern_object_id,
                entry.traditional_star_id,
                entry.canonical_chinese_name,
                *entry.aliases,
            ]
            normalized_aliases = [self._normalize_alias(alias) for alias in aliases]
            if len(normalized_aliases) != len(set(normalized_aliases)):
                raise ValueError("entry aliases must be unique")
            for alias in normalized_aliases:
                previous = alias_owner.get(alias)
                if previous is not None and previous != entry.modern_object_id:
                    raise ValueError("catalog alias must be globally unique")
                alias_owner[alias] = entry.modern_object_id

        entry_by_id = {entry.modern_object_id: entry for entry in self.entries}
        asterism_ids = [definition.asterism_id for definition in self.asterisms]
        if len(asterism_ids) != len(set(asterism_ids)):
            raise ValueError("asterism definition IDs must be unique")
        asterism_alias_owner: dict[str, str] = {}
        for definition in self.asterisms:
            if any(source_ref not in source_set for source_ref in definition.source_refs):
                raise ValueError("asterism references an unknown catalog source")
            for object_id in definition.member_object_ids:
                entry = entry_by_id.get(object_id)
                if entry is None:
                    raise ValueError("asterism references an unknown member object")
                if entry.asterism_id != definition.asterism_id:
                    raise ValueError("asterism member belongs to a different asterism")
                if definition.completeness_status in {
                    "complete",
                    "complete_gold_sample",
                } and entry.editorial_status not in {
                    AsterismStatus.VERIFIED_IDENTITY,
                    AsterismStatus.VERIFIED_MEMBERSHIP,
                }:
                    raise ValueError("complete asterism members must be verified")
            for object_id in definition.related_object_ids:
                if object_id not in entry_by_id:
                    raise ValueError("asterism references an unknown related object")
            if definition.completeness_status == "ambiguous" and not any(
                entry_by_id[object_id].editorial_status is AsterismStatus.AMBIGUOUS
                for object_id in definition.member_object_ids
            ):
                raise ValueError("ambiguous asterism requires an ambiguous member")
            names = [
                definition.asterism_id,
                definition.canonical_chinese_name,
                *definition.aliases,
            ]
            for name in names:
                normalized = self._normalize_alias(name)
                previous = asterism_alias_owner.get(normalized)
                if previous is not None and previous != definition.asterism_id:
                    raise ValueError("asterism alias must be globally unique")
                asterism_alias_owner[normalized] = definition.asterism_id

        mansion_ids = [mansion.mansion_id for mansion in self.lunar_mansions]
        if len(mansion_ids) != len(set(mansion_ids)):
            raise ValueError("lunar mansion IDs must be unique")
        sequence_indices = [mansion.sequence_index for mansion in self.lunar_mansions]
        if len(sequence_indices) != len(set(sequence_indices)):
            raise ValueError("lunar mansion sequence indices must be unique")
        asterism_id_set = set(asterism_ids)
        for mansion in self.lunar_mansions:
            if mansion.mansion_id not in asterism_id_set:
                raise ValueError("lunar mansion lacks an asterism definition")
            if any(source_ref not in source_set for source_ref in mansion.source_refs):
                raise ValueError("lunar mansion references an unknown catalog source")
            if mansion.west_boundary_object_id not in entry_by_id:
                raise ValueError("lunar mansion references an unknown west boundary")
            if mansion.east_boundary_object_id not in entry_by_id:
                raise ValueError("lunar mansion references an unknown east boundary")
            definition = next(
                item for item in self.asterisms if item.asterism_id == mansion.mansion_id
            )
            if mansion.west_boundary_object_id != definition.defining_star_object_id:
                raise ValueError("lunar mansion west boundary must be the defining star")
        if self.lunar_mansion_cycle_status == "complete":
            ordered = sorted(self.lunar_mansions, key=lambda item: item.sequence_index)
            if [item.sequence_index for item in ordered] != list(range(1, 29)):
                raise ValueError(
                    "complete lunar mansion catalog requires sequence indices 1 through 28"
                )
            west_boundaries = [item.west_boundary_object_id for item in ordered]
            if len(set(west_boundaries)) != 28:
                raise ValueError(
                    "complete lunar mansion catalog requires 28 unique west boundaries"
                )
            if any(item.completeness_status == "partial" for item in ordered):
                raise ValueError(
                    "complete lunar mansion cycle cannot contain partial mansion regions"
                )
            for current, following in zip(
                ordered,
                ordered[1:] + ordered[:1],
                strict=True,
            ):
                if current.east_boundary_object_id != following.west_boundary_object_id:
                    raise ValueError(
                        "lunar mansion cycle is broken between sequence "
                        f"{current.sequence_index} and {following.sequence_index}"
                    )
        return self

    def entry(self, modern_object_id: str) -> AsterismEntryV1:
        for entry in self.entries:
            if entry.modern_object_id == modern_object_id:
                return entry
        raise KeyError(modern_object_id)

    def asterism(self, query: str) -> AsterismDefinitionV1:
        normalized = self._normalize_alias(query)
        for definition in self.asterisms:
            aliases = {
                self._normalize_alias(definition.asterism_id),
                self._normalize_alias(definition.canonical_chinese_name),
                *(self._normalize_alias(alias) for alias in definition.aliases),
            }
            if normalized in aliases:
                return definition
        raise KeyError(query)

    def mansion(self, query: str) -> LunarMansionDefinitionV1:
        definition = self.asterism(query)
        for mansion in self.lunar_mansions:
            if mansion.mansion_id == definition.asterism_id:
                return mansion
        raise KeyError(query)

    def resolve(self, query: str) -> AsterismResolutionV1:
        normalized = self._normalize_alias(query)
        for entry in self.entries:
            aliases = {
                self._normalize_alias(entry.modern_object_id),
                self._normalize_alias(entry.traditional_star_id),
                self._normalize_alias(entry.canonical_chinese_name),
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


def _canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _validate_source_snapshots(catalog: AsterismCatalogV1) -> None:
    for source in catalog.sources:
        relative = Path(source.snapshot_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("catalog source snapshot path must be confined")
        snapshot = (_APP_ROOT / relative).resolve(strict=True)
        if not snapshot.is_relative_to(_APP_ROOT):
            raise ValueError("catalog source snapshot escaped app root")
        if snapshot.is_symlink() or not snapshot.is_file():
            raise ValueError("catalog source snapshot must be a regular file")
        if snapshot.stat().st_size > _MAX_SOURCE_BYTES:
            raise ValueError("catalog source snapshot is too large")
        raw = snapshot.read_bytes()
        try:
            payload = json.loads(raw.decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("catalog source snapshot must be canonical JSON") from exc
        if raw != _canonical_json_bytes(payload):
            raise ValueError("catalog source snapshot is not canonical JSON")
        if hashlib.sha256(raw).hexdigest() != source.content_hash:
            raise ValueError("catalog source snapshot sha256 mismatch")
        if payload.get("source_id") != source.source_id:
            raise ValueError("catalog source snapshot source_id mismatch")
        if payload.get("revision") != source.revision:
            raise ValueError("catalog source snapshot revision mismatch")


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
    _validate_source_snapshots(catalog)
    return AsterismCatalogSnapshotV1(
        logical_name=asset_path.name,
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_size=len(raw),
        catalog=catalog,
    )
