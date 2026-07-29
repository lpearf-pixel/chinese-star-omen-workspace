from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.video_pipeline.editorial import (
    HistoricalContextAssetV1,
    ModernInterpretationAssetV1,
    compile_editorial_package,
    load_editorial_template,
)
from src.video_pipeline.stellarium import (
    StellariumCapabilityV1,
    canonical_stellarium_bytes,
    generate_stellarium_script,
    validate_stellarium_script,
)
from tests.video_pipeline.editorial.helpers import (
    TEMPLATE_PATH,
    historical_asset_payload,
    july_inputs,
    modern_asset_payload,
    stellarium_capability_payload,
)


def july_editorial():
    event, result, mapping = july_inputs()
    editorial = compile_editorial_package(
        event=event,
        assessment=result.assessment,
        evidence_bundle=result.evidence_bundle,
        asterism_mapping=mapping,
        historical_assets=[HistoricalContextAssetV1.model_validate(historical_asset_payload())],
        modern_assets=[ModernInterpretationAssetV1.model_validate(modern_asset_payload())],
        classical_quotes=[],
        template=load_editorial_template(TEMPLATE_PATH),
    )
    return event, editorial


def capability() -> StellariumCapabilityV1:
    return StellariumCapabilityV1.model_validate(stellarium_capability_payload())


def test_generated_script_matches_event_utc_location_and_objects() -> None:
    event, editorial = july_editorial()

    script = generate_stellarium_script(
        event=event,
        editorial=editorial,
        capability=capability(),
    )
    text = script.content

    assert script.schema_version == "stellarium-script/v1"
    assert script.event_id == event.event_id
    assert script.editorial_package_id == editorial.editorial_package_id
    assert 'core.setDate("2026-07-21T11:00:00", "utc", true);' in text
    assert (
        'core.setObserverLocation(121.473700, 31.230400, 4.000, 0.0, '
        '"Kaiyuan Observer", "Earth");'
        in text
    )
    assert 'core.selectObjectByName("Moon", true);' in text
    assert 'core.selectObjectByName("Spica", true);' in text
    assert text.count("core.wait(") == len(editorial.shots)
    assert script.total_wait_ms == 80_000
    assert validate_stellarium_script(script.content) == script.commands


def test_repeated_script_generation_is_byte_identical() -> None:
    event, editorial = july_editorial()

    first = generate_stellarium_script(
        event=event,
        editorial=editorial,
        capability=capability(),
    )
    second = generate_stellarium_script(
        event=event,
        editorial=editorial,
        capability=capability(),
    )

    assert first == second
    assert canonical_stellarium_bytes(first) == canonical_stellarium_bytes(second)
    assert first.content.encode("utf-8") == canonical_stellarium_bytes(first)
    assert first.sha256 == __import__("hashlib").sha256(first.content.encode("utf-8")).hexdigest()


def test_script_uses_only_fixed_command_allowlist_and_no_paths() -> None:
    event, editorial = july_editorial()
    script = generate_stellarium_script(
        event=event,
        editorial=editorial,
        capability=capability(),
    )

    assert set(script.commands) == {
        "core.clear",
        "core.setGuiVisible",
        "core.setDate",
        "core.setTimeRate",
        "core.setObserverLocation",
        "core.selectObjectByName",
        "core.wait",
        "StelMovementMgr.setFlagTracking",
        "StelMovementMgr.zoomTo",
    }
    forbidden = ["include(", "eval(", "screenshot", "../", "/Users/", "file://", "http://", "https://", "system(", "exec("]
    assert not any(token in script.content for token in forbidden)


@pytest.mark.parametrize(
    "bad_line",
    [
        'include("../../secret.inc");',
        'eval("core.wait(1)");',
        'core.screenshot("shot", false, "/tmp");',
        'system("rm -rf /");',
        'core.selectObjectByName("Moon\ncore.wait(99)", true);',
    ],
)
def test_validator_rejects_paths_includes_eval_and_injection(bad_line: str) -> None:
    with pytest.raises(ValueError, match="forbidden|unsupported|invalid"):
        validate_stellarium_script(bad_line + "\n")


def test_old_or_incomplete_capability_is_blocked() -> None:
    event, editorial = july_editorial()
    old = stellarium_capability_payload()
    old["stellarium_version"] = "25.4.0"
    with pytest.raises(ValueError, match="version"):
        generate_stellarium_script(
            event=event,
            editorial=editorial,
            capability=StellariumCapabilityV1.model_validate(old),
        )

    missing = stellarium_capability_payload()
    missing["commands"].remove("core.setObserverLocation")
    with pytest.raises(ValueError, match="capability"):
        generate_stellarium_script(
            event=event,
            editorial=editorial,
            capability=StellariumCapabilityV1.model_validate(missing),
        )


def test_object_name_injection_and_unknown_target_are_rejected() -> None:
    event, editorial = july_editorial()
    snapshot = load_editorial_template(TEMPLATE_PATH)
    payload = snapshot.template.model_dump(mode="json")
    payload["object_names"]["moon"] = 'Moon"); core.wait(99); //'
    with pytest.raises(ValidationError):
        load_editorial_template(payload)

    changed = editorial.model_copy(
        update={
            "shots": [
                editorial.shots[0].model_copy(update={"target_object_id": "unknown:object"}),
                *editorial.shots[1:],
            ]
        }
    )
    with pytest.raises(ValueError, match="object"):
        generate_stellarium_script(
            event=event,
            editorial=changed,
            capability=capability(),
        )


def test_event_and_editorial_identity_mismatch_is_rejected() -> None:
    event, editorial = july_editorial()
    other = editorial.model_copy(
        update={
            "video_package": editorial.video_package.model_copy(
                update={"event_id": "event:other"}
            )
        }
    )

    with pytest.raises(ValueError, match="event"):
        generate_stellarium_script(
            event=event,
            editorial=other,
            capability=capability(),
        )
