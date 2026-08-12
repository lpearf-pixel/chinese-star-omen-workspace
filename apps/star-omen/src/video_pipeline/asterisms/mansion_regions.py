from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .catalog import AsterismDefinitionV1, LunarMansionDefinitionV1


_STABLE_ID_PATTERN = r"^[a-z0-9][a-z0-9._:/-]{0,159}$"


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


class EquatorialPositionV1(_StrictModel):
    object_id: str = Field(pattern=_STABLE_ID_PATTERN)
    ra_deg: float = Field(strict=True, ge=0.0, lt=360.0, allow_inf_nan=False)
    dec_deg: float = Field(strict=True, ge=-90.0, le=90.0, allow_inf_nan=False)
    reference_frame: Literal["apparent-equatorial-of-date", "icrs-j2000"]


class AngularThresholdV1(_StrictModel):
    threshold_id: str = Field(pattern=_STABLE_ID_PATTERN)
    max_separation_deg: float = Field(
        strict=True,
        gt=0.0,
        le=180.0,
        allow_inf_nan=False,
    )


class MansionRelationAssessmentV1(_StrictModel):
    schema_version: Literal["mansion-relation-assessment/v1"] = (
        "mansion-relation-assessment/v1"
    )
    mansion_id: str = Field(pattern=_STABLE_ID_PATTERN)
    relation_term: str = Field(min_length=1, max_length=32)
    reference_frame: Literal["apparent-equatorial-of-date", "icrs-j2000"]
    target_position: EquatorialPositionV1
    west_boundary_position: EquatorialPositionV1
    east_boundary_position: EquatorialPositionV1
    nearest_member_position: EquatorialPositionV1
    interpretation_status: Literal[
        "ambiguous_relation",
        "objective_measurement_only",
        "unsupported_single_time_relation",
    ]
    inferred_classical_relation: Literal["犯", "入", "守", "留"] | None = None
    in_mansion_region: bool
    nearest_member_object_id: str = Field(pattern=_STABLE_ID_PATTERN)
    nearest_member_angular_separation_deg: float = Field(
        strict=True,
        ge=0.0,
        le=180.0,
        allow_inf_nan=False,
    )
    near_asterism_status: Literal[
        "not_evaluated",
        "within_threshold",
        "outside_threshold",
    ]
    threshold_id: str | None = Field(default=None, pattern=_STABLE_ID_PATTERN)


class MansionRelationObservationV1(_StrictModel):
    schema_version: Literal["mansion-relation-observation/v1"] = (
        "mansion-relation-observation/v1"
    )
    body_id: str = Field(pattern=_STABLE_ID_PATTERN)
    at_utc: datetime
    asterism_catalog_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    assessment: MansionRelationAssessmentV1

    @field_validator("at_utc")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observation time must be explicit UTC")
        if value.utcoffset() != timedelta(0):
            raise ValueError("observation time must be expressed in UTC")
        return value


def _inside_circular_interval(*, value: float, west: float, east: float) -> bool:
    if west == east:
        raise ValueError("mansion boundary right ascensions must be distinct")
    if west < east:
        return west <= value < east
    return value >= west or value < east


def _angular_separation_deg(
    first: EquatorialPositionV1,
    second: EquatorialPositionV1,
) -> float:
    first_ra = math.radians(first.ra_deg)
    first_dec = math.radians(first.dec_deg)
    second_ra = math.radians(second.ra_deg)
    second_dec = math.radians(second.dec_deg)
    cosine = (
        math.sin(first_dec) * math.sin(second_dec)
        + math.cos(first_dec)
        * math.cos(second_dec)
        * math.cos(first_ra - second_ra)
    )
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def assess_single_time_relation(
    *,
    relation_term: str,
    asterism: AsterismDefinitionV1,
    mansion: LunarMansionDefinitionV1,
    target: EquatorialPositionV1,
    west_boundary: EquatorialPositionV1,
    east_boundary: EquatorialPositionV1,
    members: list[EquatorialPositionV1],
    near_threshold: AngularThresholdV1 | None = None,
) -> MansionRelationAssessmentV1:
    term = relation_term.strip()
    if not term:
        raise ValueError("relation term must not be empty")
    if mansion.mansion_id != asterism.asterism_id:
        raise ValueError("mansion and asterism IDs must match")
    if west_boundary.object_id != mansion.west_boundary_object_id:
        raise ValueError("west boundary object ID does not match the mansion")
    if east_boundary.object_id != mansion.east_boundary_object_id:
        raise ValueError("east boundary object ID does not match the mansion")
    if [member.object_id for member in members] != asterism.member_object_ids:
        raise ValueError("member object IDs must match the asterism definition")

    frames = {
        target.reference_frame,
        west_boundary.reference_frame,
        east_boundary.reference_frame,
        *(member.reference_frame for member in members),
    }
    if len(frames) != 1:
        raise ValueError("all positions must use the same reference frame")

    nearest_member, nearest_separation = min(
        (
            (member, _angular_separation_deg(target, member))
            for member in members
        ),
        key=lambda item: item[1],
    )
    in_region = _inside_circular_interval(
        value=target.ra_deg,
        west=west_boundary.ra_deg,
        east=east_boundary.ra_deg,
    )

    if near_threshold is None:
        near_status = "not_evaluated"
        threshold_id = None
    else:
        near_status = (
            "within_threshold"
            if nearest_separation <= near_threshold.max_separation_deg
            else "outside_threshold"
        )
        threshold_id = near_threshold.threshold_id

    if term in {"临", "臨"}:
        interpretation_status = "ambiguous_relation"
    elif term in {"犯", "入", "守", "留"}:
        interpretation_status = "unsupported_single_time_relation"
    else:
        interpretation_status = "objective_measurement_only"

    return MansionRelationAssessmentV1(
        mansion_id=mansion.mansion_id,
        relation_term=term,
        reference_frame=target.reference_frame,
        target_position=target,
        west_boundary_position=west_boundary,
        east_boundary_position=east_boundary,
        nearest_member_position=nearest_member,
        interpretation_status=interpretation_status,
        inferred_classical_relation=None,
        in_mansion_region=in_region,
        nearest_member_object_id=nearest_member.object_id,
        nearest_member_angular_separation_deg=nearest_separation,
        near_asterism_status=near_status,
        threshold_id=threshold_id,
    )
