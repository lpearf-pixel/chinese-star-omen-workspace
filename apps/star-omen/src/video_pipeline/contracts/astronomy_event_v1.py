from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ._common import (
    FiniteFloat,
    Sha256Hex,
    StableId,
    StrictContractModel,
    UtcDateTime,
    ensure_unique,
)


class ObserverV1(StrictContractModel):
    latitude_deg: FiniteFloat = Field(ge=-90.0, le=90.0)
    longitude_deg: FiniteFloat = Field(ge=-180.0, le=180.0)
    elevation_m: FiniteFloat
    timezone: str = Field(min_length=1, max_length=80)


class MeasurementV1(StrictContractModel):
    measurement_id: StableId
    kind: StableId
    value: FiniteFloat
    unit: str = Field(min_length=1, max_length=32)
    reference_frame: str = Field(min_length=1, max_length=64)


class VisibilityV1(StrictContractModel):
    status: Literal["visible", "not_visible", "unknown"]
    target_altitude_deg: FiniteFloat | None = None
    sun_altitude_deg: FiniteFloat | None = None
    threshold_version: StableId


class CalculationProvenanceV1(StrictContractModel):
    provider: StableId
    provider_version: str = Field(min_length=1, max_length=64)
    ephemeris_id: str = Field(min_length=1, max_length=128)
    ephemeris_sha256: Sha256Hex
    timescale_source: str = Field(min_length=1, max_length=128)


class AstronomyEventV1(StrictContractModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:astronomy-event/v1"},
    )

    schema_version: Literal["astronomy-event/v1"]
    calculation_id: StableId
    event_id: StableId
    event_type: StableId
    primary_body: StableId
    target_body_or_region: StableId
    start_utc: UtcDateTime
    peak_utc: UtcDateTime
    end_utc: UtcDateTime
    observer: ObserverV1
    measurements: list[MeasurementV1]
    visibility: VisibilityV1
    calculation_provenance: CalculationProvenanceV1
    quality_status: Literal["verified", "insufficient_data", "invalid"]
    uncertainty_reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_event(self) -> "AstronomyEventV1":
        if not self.start_utc <= self.peak_utc <= self.end_utc:
            raise ValueError("event times must satisfy start_utc <= peak_utc <= end_utc")
        ensure_unique(
            [item.measurement_id for item in self.measurements],
            "measurements",
        )
        if self.quality_status == "verified" and not self.measurements:
            raise ValueError("verified events require at least one measurement")
        return self
