from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from skyfield import almanac
from skyfield.api import Loader, Star, load_file, wgs84
from skyfield.framelib import ecliptic_frame

from src.interfaces.astronomy import EphemerisPoint
from src.video_pipeline.asterisms.catalog import (
    AsterismCatalogSnapshotV1,
    AsterismStatus,
)
from src.video_pipeline.contracts import (
    AstronomyEventV1,
    CalculationProvenanceV1,
    MeasurementV1,
    ObserverV1,
    VisibilityV1,
)

from .conventions import ScientificConventionsSnapshotV1
from .ephemeris import (
    AstronomyToolchainManifestV1,
    EphemerisFileSpecV1,
    VerifiedEphemerisFile,
    build_toolchain_manifest,
    verify_ephemeris_file,
)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be explicit UTC")
    if value.utcoffset() != timedelta(0):
        raise ValueError("datetime must be expressed in UTC")
    return value.astimezone(timezone.utc)


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


class ScientificObservationV1(_StrictModel):
    schema_version: Literal["scientific-observation/v1"] = "scientific-observation/v1"
    object_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._:/-]{0,159}$")
    at_utc: datetime
    identity_ra_deg: float = Field(strict=True, ge=0.0, lt=360.0, allow_inf_nan=False)
    identity_dec_deg: float = Field(strict=True, ge=-90.0, le=90.0, allow_inf_nan=False)
    apparent_ra_deg: float = Field(strict=True, ge=0.0, lt=360.0, allow_inf_nan=False)
    apparent_dec_deg: float = Field(strict=True, ge=-90.0, le=90.0, allow_inf_nan=False)
    ecliptic_longitude_deg: float = Field(strict=True, ge=0.0, lt=360.0, allow_inf_nan=False)
    ecliptic_latitude_deg: float = Field(strict=True, ge=-90.0, le=90.0, allow_inf_nan=False)
    topocentric_altitude_deg: float | None = Field(default=None, strict=True, ge=-90.0, le=90.0, allow_inf_nan=False)
    topocentric_azimuth_deg: float | None = Field(default=None, strict=True, ge=0.0, lt=360.0, allow_inf_nan=False)
    mapping_status: str | None = None

    @field_validator("at_utc")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        return _ensure_utc(value)

    @model_validator(mode="after")
    def validate_altaz_pair(self) -> "ScientificObservationV1":
        if (self.topocentric_altitude_deg is None) != (
            self.topocentric_azimuth_deg is None
        ):
            raise ValueError("topocentric altitude and azimuth must be supplied together")
        return self


class MoonPhaseEventV1(_StrictModel):
    schema_version: Literal["moon-phase-event/v1"] = "moon-phase-event/v1"
    phase_index: int = Field(strict=True, ge=0, le=3)
    phase_name: Literal["new-moon", "first-quarter", "full-moon", "last-quarter"]
    utc: datetime

    @field_validator("utc")
    @classmethod
    def validate_utc(cls, value: datetime) -> datetime:
        return _ensure_utc(value)


_BODY_KEYS = {
    "sun": "sun",
    "moon": "moon",
    "mercury": "mercury",
    "venus": "venus",
    "mars": "mars barycenter",
    "jupiter": "jupiter barycenter",
    "saturn": "saturn barycenter",
}
_PHASE_NAMES = {
    0: "new-moon",
    1: "first-quarter",
    2: "full-moon",
    3: "last-quarter",
}


def _round_utc_second(value: datetime) -> datetime:
    value = value.astimezone(timezone.utc)
    if value.microsecond >= 500_000:
        value += timedelta(seconds=1)
    return value.replace(microsecond=0)


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


class SkyfieldEphemerisProvider:
    """Offline-only Skyfield provider backed by a verified local BSP file."""

    def __init__(
        self,
        *,
        verified_ephemeris: VerifiedEphemerisFile,
        conventions: ScientificConventionsSnapshotV1,
        catalog: AsterismCatalogSnapshotV1,
    ) -> None:
        verified_ephemeris.assert_unchanged()
        self.verified_ephemeris = verified_ephemeris
        self.conventions = conventions
        self.catalog = catalog
        loader = Loader(
            str(verified_ephemeris.path.parent),
            verbose=False,
            expire=False,
        )
        self._timescale = loader.timescale(builtin=True)
        ephemeris = load_file(str(verified_ephemeris.path))
        try:
            verified_ephemeris.assert_unchanged()
        except Exception:
            close = getattr(ephemeris, "close", None)
            if callable(close):
                close()
            raise
        self._ephemeris = ephemeris
        skyfield_version = _package_version("skyfield")
        if skyfield_version is None:
            raise RuntimeError("skyfield package version is unavailable")
        self.toolchain_manifest: AstronomyToolchainManifestV1 = build_toolchain_manifest(
            verified_ephemeris=verified_ephemeris,
            conventions=conventions,
            catalog=catalog,
            skyfield_version=skyfield_version,
            skyfield_data_version=_package_version("skyfield-data"),
        )

    @classmethod
    def from_local_ephemeris(
        cls,
        *,
        ephemeris_path: str | Path,
        ephemeris_spec: EphemerisFileSpecV1,
        conventions: ScientificConventionsSnapshotV1,
        catalog: AsterismCatalogSnapshotV1,
    ) -> "SkyfieldEphemerisProvider":
        verified = verify_ephemeris_file(ephemeris_path, ephemeris_spec)
        return cls(
            verified_ephemeris=verified,
            conventions=conventions,
            catalog=catalog,
        )

    def _time(self, value: datetime):
        return self._timescale.from_datetime(_ensure_utc(value))

    def _target(self, body_id: str):
        key = _BODY_KEYS.get(body_id)
        if key is None:
            raise ValueError(f"unsupported body: {body_id}")
        return self._ephemeris[key]

    def _observer_vector(self, observer: ObserverV1):
        location = wgs84.latlon(
            latitude_degrees=observer.latitude_deg,
            longitude_degrees=observer.longitude_deg,
            elevation_m=observer.elevation_m,
        )
        return self._ephemeris["earth"] + location

    def _observation_from_target(
        self,
        *,
        object_id: str,
        target: object,
        at_utc: datetime,
        observer: ObserverV1,
        identity_coordinates: tuple[float, float] | None = None,
        mapping_status: str | None = None,
    ) -> ScientificObservationV1:
        utc = _ensure_utc(at_utc)
        t = self._time(utc)
        earth = self._ephemeris["earth"]
        astrometric = earth.at(t).observe(target)
        identity_ra, identity_dec, _ = astrometric.radec()
        apparent = astrometric.apparent()
        apparent_ra, apparent_dec, _ = apparent.radec(epoch="date")
        ecliptic_latitude, ecliptic_longitude, _ = apparent.frame_latlon(
            ecliptic_frame
        )
        topocentric = self._observer_vector(observer).at(t).observe(target).apparent()
        altitude, azimuth, _ = topocentric.altaz()
        if identity_coordinates is None:
            identity_ra_deg = float(identity_ra.hours * 15.0)
            identity_dec_deg = float(identity_dec.degrees)
        else:
            identity_ra_deg, identity_dec_deg = identity_coordinates
        return ScientificObservationV1(
            object_id=object_id,
            at_utc=utc,
            identity_ra_deg=identity_ra_deg % 360.0,
            identity_dec_deg=identity_dec_deg,
            apparent_ra_deg=float(apparent_ra.hours * 15.0) % 360.0,
            apparent_dec_deg=float(apparent_dec.degrees),
            ecliptic_longitude_deg=float(ecliptic_longitude.degrees) % 360.0,
            ecliptic_latitude_deg=float(ecliptic_latitude.degrees),
            topocentric_altitude_deg=float(altitude.degrees),
            topocentric_azimuth_deg=float(azimuth.degrees) % 360.0,
            mapping_status=mapping_status,
        )

    def observe_body(
        self,
        *,
        body_id: str,
        at_utc: datetime,
        observer: ObserverV1,
    ) -> ScientificObservationV1:
        return self._observation_from_target(
            object_id=body_id,
            target=self._target(body_id),
            at_utc=at_utc,
            observer=observer,
        )

    def observe_catalog_star(
        self,
        *,
        modern_object_id: str,
        at_utc: datetime,
        observer: ObserverV1,
    ) -> ScientificObservationV1:
        resolution = self.catalog.catalog.resolve(modern_object_id)
        if resolution.status not in {
            AsterismStatus.VERIFIED_IDENTITY,
            AsterismStatus.VERIFIED_MEMBERSHIP,
        } or resolution.reference_coordinates is None:
            raise ValueError("catalog object is not a verified star mapping")
        coordinates = resolution.reference_coordinates
        star = Star(
            ra_hours=coordinates.ra_deg / 15.0,
            dec_degrees=coordinates.dec_deg,
        )
        return self._observation_from_target(
            object_id=resolution.modern_object_id or modern_object_id,
            target=star,
            at_utc=at_utc,
            observer=observer,
            identity_coordinates=(coordinates.ra_deg, coordinates.dec_deg),
            mapping_status=resolution.status.value,
        )

    def get_points(
        self,
        *,
        bodies: list[str],
        at: list[datetime],
    ) -> list[EphemerisPoint]:
        points: list[EphemerisPoint] = []
        earth = self._ephemeris["earth"]
        for body_id in bodies:
            target = self._target(body_id)
            for timestamp in at:
                utc = _ensure_utc(timestamp)
                apparent = earth.at(self._time(utc)).observe(target).apparent()
                ra, dec, _ = apparent.radec()
                lat, lon, _ = apparent.frame_latlon(ecliptic_frame)
                points.append(
                    EphemerisPoint(
                        body=body_id,
                        datetime_utc=utc,
                        ra_deg=float(ra.hours * 15.0) % 360.0,
                        dec_deg=float(dec.degrees),
                        ecl_lon_deg=float(lon.degrees) % 360.0,
                        ecl_lat_deg=float(lat.degrees),
                    )
                )
        return points

    def moon_phase_degrees(self, at_utc: datetime) -> float:
        phase = almanac.moon_phase(self._ephemeris, self._time(at_utc))
        return float(phase.degrees) % 360.0

    def find_moon_phases(
        self,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[MoonPhaseEventV1]:
        start = _ensure_utc(start_utc)
        end = _ensure_utc(end_utc)
        if not start < end:
            raise ValueError("moon phase search requires start_utc < end_utc")
        times, phases = almanac.find_discrete(
            self._time(start),
            self._time(end),
            almanac.moon_phases(self._ephemeris),
        )
        events: list[MoonPhaseEventV1] = []
        for skyfield_time, phase in zip(times, phases, strict=True):
            index = int(phase)
            events.append(
                MoonPhaseEventV1(
                    phase_index=index,
                    phase_name=_PHASE_NAMES[index],
                    utc=_round_utc_second(skyfield_time.utc_datetime()),
                )
            )
        return events

    def _calculation_provenance(self) -> CalculationProvenanceV1:
        return CalculationProvenanceV1(
            provider="skyfield",
            provider_version=self.toolchain_manifest.skyfield_version,
            ephemeris_id=self.verified_ephemeris.logical_name,
            ephemeris_sha256=self.verified_ephemeris.sha256,
            timescale_source=self.toolchain_manifest.timescale_source,
        )

    def _visibility(
        self,
        *,
        body_observation: ScientificObservationV1,
        at_utc: datetime,
        observer: ObserverV1,
    ) -> VisibilityV1:
        sun = self.observe_body(body_id="sun", at_utc=at_utc, observer=observer)
        return VisibilityV1(
            status="unknown",
            target_altitude_deg=body_observation.topocentric_altitude_deg,
            sun_altitude_deg=sun.topocentric_altitude_deg,
            threshold_version="visibility/v1",
        )

    def calculate_moon_phase_event(
        self,
        *,
        at_utc: datetime,
        observer: ObserverV1,
    ) -> AstronomyEventV1:
        utc = _ensure_utc(at_utc)
        stamp = utc.strftime("%Y%m%dT%H%M%SZ").lower()
        moon = self.observe_body(body_id="moon", at_utc=utc, observer=observer)
        return AstronomyEventV1(
            schema_version="astronomy-event/v1",
            calculation_id=f"calc:moon-phase:{stamp}",
            event_id=f"event:moon-phase:{stamp}",
            event_type="moon-phase-angle",
            primary_body="moon",
            target_body_or_region="sun",
            start_utc=utc,
            peak_utc=utc,
            end_utc=utc,
            observer=observer,
            measurements=[
                MeasurementV1(
                    measurement_id="measurement:moon-phase-angle",
                    kind="moon-phase-angle-deg",
                    value=self.moon_phase_degrees(utc),
                    unit="deg",
                    reference_frame="geocentric-apparent-ecliptic",
                )
            ],
            visibility=self._visibility(
                body_observation=moon,
                at_utc=utc,
                observer=observer,
            ),
            calculation_provenance=self._calculation_provenance(),
            quality_status="verified",
            uncertainty_reasons=[],
        )

    def calculate_angular_separation_event(
        self,
        *,
        primary_body: str,
        target_modern_object_id: str,
        at_utc: datetime,
        observer: ObserverV1,
    ) -> AstronomyEventV1:
        utc = _ensure_utc(at_utc)
        resolution = self.catalog.catalog.resolve(target_modern_object_id)
        if resolution.status not in {
            AsterismStatus.VERIFIED_IDENTITY,
            AsterismStatus.VERIFIED_MEMBERSHIP,
        } or resolution.reference_coordinates is None:
            raise ValueError("target star is not a verified catalog mapping")
        body = self._target(primary_body)
        star = Star(
            ra_hours=resolution.reference_coordinates.ra_deg / 15.0,
            dec_degrees=resolution.reference_coordinates.dec_deg,
        )
        t = self._time(utc)
        observer_vector = self._observer_vector(observer)
        body_apparent = observer_vector.at(t).observe(body).apparent()
        star_apparent = observer_vector.at(t).observe(star).apparent()
        separation = float(body_apparent.separation_from(star_apparent).degrees)
        body_observation = self.observe_body(
            body_id=primary_body,
            at_utc=utc,
            observer=observer,
        )
        stamp = utc.strftime("%Y%m%dT%H%M%SZ").lower()
        return AstronomyEventV1(
            schema_version="astronomy-event/v1",
            calculation_id=f"calc:separation:{primary_body}:{target_modern_object_id}:{stamp}",
            event_id=f"event:separation:{primary_body}:{target_modern_object_id}:{stamp}",
            event_type="angular-separation",
            primary_body=primary_body,
            target_body_or_region=target_modern_object_id,
            start_utc=utc,
            peak_utc=utc,
            end_utc=utc,
            observer=observer,
            measurements=[
                MeasurementV1(
                    measurement_id="measurement:angular-separation",
                    kind="angular-separation-deg",
                    value=separation,
                    unit="deg",
                    reference_frame="topocentric-apparent",
                )
            ],
            visibility=self._visibility(
                body_observation=body_observation,
                at_utc=utc,
                observer=observer,
            ),
            calculation_provenance=self._calculation_provenance(),
            quality_status="verified",
            uncertainty_reasons=[],
        )
