from __future__ import annotations

import hashlib
import json
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = APP_ROOT.parents[1]
FIXTURE_ROOT = WORKSPACE_ROOT / "tests" / "fixtures" / "astronomy" / "v1"


def canonical_json_bytes(payload: object) -> bytes:
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


def test_astronomy_fixture_manifest_is_canonical_and_hash_bound() -> None:
    manifest_path = FIXTURE_ROOT / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)

    assert manifest_bytes == canonical_json_bytes(manifest)
    assert manifest["schema_version"] == "astronomy-fixture-manifest/v1"
    assert len(manifest["fixtures"]) == 1
    fixture = manifest["fixtures"][0]
    fixture_path = FIXTURE_ROOT / fixture["path"]
    fixture_bytes = fixture_path.read_bytes()
    assert hashlib.sha256(fixture_bytes).hexdigest() == fixture["sha256"]
    assert fixture_bytes == canonical_json_bytes(json.loads(fixture_bytes))


def test_published_skyfield_fixture_records_source_frame_and_tolerances() -> None:
    payload = json.loads(
        (FIXTURE_ROOT / "skyfield-published-almanac-examples.json").read_text(
            encoding="utf-8"
        )
    )

    assert payload["schema_version"] == "scientific-golden-fixture/v1"
    assert payload["fixture_id"] == "skyfield-published-almanac-v1"
    assert payload["source"]["publisher"] == "Skyfield"
    assert payload["source"]["retrieved_at"] == "2026-07-22"
    assert payload["ephemeris_logical_name"] == "de421.bsp"
    assert payload["time_scale"] == "utc"
    assert payload["reference_frame"] == "geocentric-apparent-ecliptic"
    assert payload["moon_phase_angle"]["expected_deg"] == 51.3
    assert payload["moon_phase_angle"]["tolerance_deg"] == 0.05
    assert payload["phase_transitions"][0]["tolerance_seconds"] == 1
    assert payload["phase_transitions"][1]["tolerance_seconds"] == 1
    assert payload["independent_dynamic_reference"]["status"] == "not-yet-recorded"
    assert payload["independent_dynamic_reference"]["reason"]
