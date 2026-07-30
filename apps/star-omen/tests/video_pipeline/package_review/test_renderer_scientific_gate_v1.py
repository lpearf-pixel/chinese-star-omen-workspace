from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from src.video_pipeline.assisted_review import verify_recomputed_astronomy
from src.video_pipeline.contracts import AstronomyEventV1


FIXTURE = (
    Path(__file__).resolve().parents[5]
    / "tests"
    / "fixtures"
    / "evidence"
    / "v1"
    / "july-21-event.json"
)
DE421_SHA256 = "a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc"


def event(
    *,
    value: float,
    ephemeris_sha256: str = DE421_SHA256,
    reference_frame: str = "topocentric-apparent",
) -> AstronomyEventV1:
    payload = deepcopy(
        AstronomyEventV1.model_validate_json(
            FIXTURE.read_text(encoding="utf-8")
        ).model_dump(mode="json")
    )
    payload["event_type"] = "angular-separation"
    payload["measurements"][0].update(
        {
            "kind": "angular-separation-deg",
            "value": value,
            "reference_frame": reference_frame,
        }
    )
    payload["calculation_provenance"].update(
        {
            "provider": "skyfield",
            "provider_version": "1.51",
            "ephemeris_id": "de421.bsp",
            "ephemeris_sha256": ephemeris_sha256,
            "timescale_source": "skyfield-builtin",
        }
    )
    return AstronomyEventV1.model_validate(payload)


def issue_codes(
    packaged: AstronomyEventV1,
    recomputed: AstronomyEventV1,
) -> list[str]:
    return [
        issue.code
        for issue in verify_recomputed_astronomy(
            packaged=packaged,
            recomputed=recomputed,
        )
    ]


def test_scientific_gate_accepts_exact_provider_recomputation() -> None:
    verified = event(value=5.405)

    assert issue_codes(verified, verified) == []


def test_scientific_gate_rejects_hand_authored_july_separation() -> None:
    packaged = event(
        value=3.25,
        ephemeris_sha256="a" * 64,
        reference_frame="icrs",
    )
    recomputed = event(value=5.405)

    assert issue_codes(packaged, recomputed) == [
        "astronomy.measurement_mismatch",
        "astronomy.provenance_placeholder",
        "astronomy.recomputation_mismatch",
    ]


def test_scientific_gate_rejects_time_observer_target_and_provenance_drift() -> None:
    packaged = event(value=5.405)
    recomputed_payload = packaged.model_dump(mode="json")
    recomputed_payload["start_utc"] = "2026-07-21T11:01:00Z"
    recomputed_payload["peak_utc"] = "2026-07-21T11:01:00Z"
    recomputed_payload["end_utc"] = "2026-07-21T11:01:00Z"
    recomputed_payload["observer"]["longitude_deg"] = 120.0
    recomputed_payload["target_body_or_region"] = "mars"
    recomputed_payload["calculation_provenance"]["provider_version"] = "1.52"
    recomputed = AstronomyEventV1.model_validate(recomputed_payload)

    assert issue_codes(packaged, recomputed) == [
        "astronomy.observer_mismatch",
        "astronomy.provenance_mismatch",
        "astronomy.target_mismatch",
        "astronomy.time_mismatch",
    ]


def test_scientific_gate_rejects_missing_or_duplicate_angular_measurement() -> None:
    packaged = event(value=5.405)
    missing_payload = packaged.model_dump(mode="json")
    missing_payload["measurements"][0]["kind"] = "moon-phase-angle-deg"
    missing = AstronomyEventV1.model_validate(missing_payload)

    duplicate_payload = packaged.model_dump(mode="json")
    duplicate_payload["measurements"].append(
        deepcopy(duplicate_payload["measurements"][0])
    )
    duplicate_payload["measurements"][1][
        "measurement_id"
    ] = "measurement:angular-separation-copy"
    duplicate = AstronomyEventV1.model_validate(duplicate_payload)

    assert issue_codes(missing, packaged) == ["astronomy.measurement_mismatch"]
    assert issue_codes(duplicate, packaged) == ["astronomy.measurement_mismatch"]


def test_scientific_gate_rejects_event_and_calculation_identity_drift() -> None:
    packaged = event(value=5.405)
    recomputed_payload = packaged.model_dump(mode="json")
    recomputed_payload["event_id"] = "event:separation:moon:hip:65474:other"
    recomputed_payload["calculation_id"] = "calc:separation:moon:hip:65474:other"
    recomputed = AstronomyEventV1.model_validate(recomputed_payload)

    assert issue_codes(packaged, recomputed) == ["astronomy.target_mismatch"]
