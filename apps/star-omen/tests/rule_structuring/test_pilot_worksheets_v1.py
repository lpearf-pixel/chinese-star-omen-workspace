from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.rule_structuring.calibration import issue_anonymous_reviewer_slots
from src.rule_structuring.calibration import canonical_calibration_bytes
from src.rule_structuring.passage_inventory import build_rule_passage_inventory
from src.rule_structuring.pilot_handoff import main, prepare_pilot_handoff
from src.rule_structuring.pilot_worksheets import (
    PilotSelectionCaseV1,
    PilotSelectionV1,
    build_pilot_worksheets,
    canonical_worksheet_bytes,
    publish_pilot_worksheets,
)


TEXT = """# 占候

<pb:KR3g0018_WYG_{volume}-1a>

{sentence}
"""


def _inventory(tmp_path: Path):
    root = tmp_path / "kb"
    volume_31 = root / "古籍/唐開元占經/分卷/KR3g0018_031.md"
    volume_72 = root / "古籍/唐開元占經/分卷/KR3g0018_072.md"
    volume_31.parent.mkdir(parents=True, exist_ok=True)
    volume_31.write_text(
        TEXT.format(volume="031", sentence="荧惑守心，太白犯昴。"),
        encoding="utf-8",
    )
    volume_72.write_text(
        TEXT.format(
            volume="072",
            sentence="日月合，客星入宿，彗星逆行。\n\n流星离宿，云气掩月。",
        ),
        encoding="utf-8",
    )
    return build_rule_passage_inventory(root)


def _selection(tmp_path: Path) -> PilotSelectionV1:
    inventory = _inventory(tmp_path)
    first, second, third = inventory.passages
    shared = {
        "celestial_categories": [
            "sun",
            "moon",
            "five_planets",
            "lunar_mansions",
            "guest_star",
            "comet",
            "meteor",
            "eclipse",
            "cloud_qi",
        ],
        "relation_terms": ["合", "犯", "入", "守", "掩", "离", "留", "逆"],
        "special_case_tags": ["ambiguous", "duplicate", "conflict"],
    }
    cases = [
        PilotSelectionCaseV1(
            case_id="pilot-case:development:001",
            passage_id=first.passage_id,
            split="development",
            sentence_complexity="simple",
            computability="computable",
            evidence_risk="low",
            **shared,
        ),
        PilotSelectionCaseV1(
            case_id="pilot-case:validation:001",
            passage_id=second.passage_id,
            split="validation",
            sentence_complexity="compound",
            computability="partially_computable",
            evidence_risk="medium",
            **shared,
        ),
        PilotSelectionCaseV1(
            case_id="pilot-case:validation:002",
            passage_id=third.passage_id,
            split="validation",
            sentence_complexity="cross_passage",
            computability="not_computable",
            evidence_risk="high",
            **shared,
        ),
    ]
    return PilotSelectionV1(
        schema_version="pilot-selection/v1",
        pilot_id="pilot:kaiyuan-b10-pr-c-v1",
        inventory_fingerprint=inventory.source_fingerprint,
        annotation_guide_version="kaiyuan-rule-annotation/v1",
        cases=cases,
    )


def test_builder_emits_slot_specific_unlabelled_identical_worksheets(
    tmp_path: Path,
) -> None:
    inventory = _inventory(tmp_path)
    selection = _selection(tmp_path)
    slots = issue_anonymous_reviewer_slots(selection.pilot_id)

    reviewer_a, reviewer_b = build_pilot_worksheets(
        selection=selection,
        inventory=inventory,
        slots=slots,
    )

    assert reviewer_a.reviewer_id == slots[0].reviewer_id
    assert reviewer_b.reviewer_id == slots[1].reviewer_id
    assert reviewer_a.shared_content_sha256 == reviewer_b.shared_content_sha256
    assert reviewer_a.cases == reviewer_b.cases
    assert reviewer_a.human_review_completed is False
    assert reviewer_b.human_review_completed is False
    assert all(case.expected_label is None for case in reviewer_a.cases)
    assert all(case.raw_text for case in reviewer_a.cases)
    assert all(case.split != "holdout" for case in reviewer_a.cases)
    assert canonical_worksheet_bytes(reviewer_a) == canonical_worksheet_bytes(
        build_pilot_worksheets(
            selection=selection,
            inventory=inventory,
            slots=slots,
        )[0]
    )


def test_builder_rejects_incomplete_coverage_and_inventory_drift(
    tmp_path: Path,
) -> None:
    inventory = _inventory(tmp_path)
    selection = _selection(tmp_path)
    incomplete = selection.model_copy(
        update={
            "cases": (
                selection.cases[0].model_copy(
                    update={"celestial_categories": ("five_planets",)}
                ),
            )
        }
    )
    with pytest.raises(ValueError, match="coverage"):
        build_pilot_worksheets(
            selection=incomplete,
            inventory=inventory,
            slots=issue_anonymous_reviewer_slots(selection.pilot_id),
        )

    drifted = selection.model_copy(
        update={"inventory_fingerprint": "sha256:" + "f" * 64}
    )
    with pytest.raises(ValueError, match="fingerprint"):
        build_pilot_worksheets(
            selection=drifted,
            inventory=inventory,
            slots=issue_anonymous_reviewer_slots(selection.pilot_id),
        )


def test_builder_rejects_unknown_passages_holdout_and_duplicate_case_ids(
    tmp_path: Path,
) -> None:
    inventory = _inventory(tmp_path)
    selection = _selection(tmp_path)
    slots = issue_anonymous_reviewer_slots(selection.pilot_id)

    unknown = selection.model_copy(
        update={
            "cases": (
                selection.cases[0].model_copy(
                    update={"passage_id": "passage:sha256:" + "f" * 64}
                ),
                *selection.cases[1:],
            )
        }
    )
    with pytest.raises(ValueError, match="unknown passage"):
        build_pilot_worksheets(selection=unknown, inventory=inventory, slots=slots)

    with pytest.raises(ValueError, match="holdout"):
        PilotSelectionCaseV1.model_validate(
            {**selection.cases[0].model_dump(mode="json"), "split": "holdout"}
        )

    with pytest.raises(ValueError, match="unique"):
        PilotSelectionV1.model_validate(
            {
                **selection.model_dump(mode="json"),
                "cases": [
                    selection.cases[0].model_dump(mode="json"),
                    selection.cases[0].model_dump(mode="json"),
                ],
            }
        )


def test_publish_worksheets_is_order_independent_and_no_overwrite(
    tmp_path: Path,
) -> None:
    inventory = _inventory(tmp_path)
    selection = _selection(tmp_path)
    worksheets = build_pilot_worksheets(
        selection=selection,
        inventory=inventory,
        slots=issue_anonymous_reviewer_slots(selection.pilot_id),
    )
    output = tmp_path / "worksheets"

    paths = publish_pilot_worksheets(output, tuple(reversed(worksheets)))

    assert [path.name for path in paths] == ["reviewer_a.json", "reviewer_b.json"]
    assert paths[0].read_bytes() == canonical_worksheet_bytes(worksheets[0])
    assert paths[1].read_bytes() == canonical_worksheet_bytes(worksheets[1])
    with pytest.raises(FileExistsError):
        publish_pilot_worksheets(output, worksheets)


def test_publish_rejects_cross_slot_content_tamper(tmp_path: Path) -> None:
    inventory = _inventory(tmp_path)
    selection = _selection(tmp_path)
    reviewer_a, reviewer_b = build_pilot_worksheets(
        selection=selection,
        inventory=inventory,
        slots=issue_anonymous_reviewer_slots(selection.pilot_id),
    )
    tampered_case = reviewer_b.cases[0].model_copy(update={"raw_text": "篡改"})
    tampered_b = reviewer_b.model_copy(
        update={"cases": (tampered_case, *reviewer_b.cases[1:])}
    )

    with pytest.raises(ValueError, match="shared content"):
        publish_pilot_worksheets(
            tmp_path / "tampered",
            (reviewer_a, tampered_b),
        )


def test_local_handoff_reads_real_inventory_selection_and_slot_manifest(
    tmp_path: Path,
) -> None:
    root = tmp_path / "kb"
    inventory = _inventory(tmp_path)
    selection = _selection(tmp_path)
    selection_path = tmp_path / "pilot-selection.json"
    selection_path.write_bytes(canonical_calibration_bytes(selection))
    slots = issue_anonymous_reviewer_slots(selection.pilot_id)
    slots_path = tmp_path / "reviewer-slots.json"
    slots_path.write_bytes(
        canonical_calibration_bytes(
            {
                "schema_version": "reviewer-slot-set/v1",
                "pilot_id": selection.pilot_id,
                "slots": [slot.model_dump(mode="json") for slot in slots],
            }
        )
    )

    result = prepare_pilot_handoff(
        kb_root=root,
        selection_path=selection_path,
        reviewer_slots_path=slots_path,
        output_directory=tmp_path / "handoff",
    )

    assert result["pilot_id"] == selection.pilot_id
    assert result["inventory_fingerprint"] == inventory.source_fingerprint
    assert result["case_count"] == 3
    assert result["human_review_completed"] is False
    assert sorted(result["worksheet_sha256"]) == ["reviewer_a", "reviewer_b"]
    assert not any(str(tmp_path) in str(value) for value in result.values())


def test_cli_exports_inventory_then_builds_worksheets(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "kb"
    inventory = _inventory(tmp_path)
    selection = _selection(tmp_path)
    selection_path = tmp_path / "pilot-selection.json"
    selection_path.write_bytes(canonical_calibration_bytes(selection))
    slots = issue_anonymous_reviewer_slots(selection.pilot_id)
    slots_path = tmp_path / "reviewer-slots.json"
    slots_path.write_bytes(
        canonical_calibration_bytes(
            {
                "schema_version": "reviewer-slot-set/v1",
                "pilot_id": selection.pilot_id,
                "slots": [slot.model_dump(mode="json") for slot in slots],
            }
        )
    )
    inventory_path = tmp_path / "passage-inventory.json"

    assert main(
        [
            "inventory",
            "--kb-root",
            str(root),
            "--out",
            str(inventory_path),
        ]
    ) == 0
    inventory_result = json.loads(capsys.readouterr().out)
    assert inventory_result["source_fingerprint"] == inventory.source_fingerprint
    assert inventory_result["passage_count"] == 3
    assert inventory_path.is_file()

    assert main(
        [
            "worksheets",
            "--kb-root",
            str(root),
            "--selection",
            str(selection_path),
            "--reviewer-slots",
            str(slots_path),
            "--out-dir",
            str(tmp_path / "handoff"),
        ]
    ) == 0
    handoff_result = json.loads(capsys.readouterr().out)
    assert handoff_result["case_count"] == 3
