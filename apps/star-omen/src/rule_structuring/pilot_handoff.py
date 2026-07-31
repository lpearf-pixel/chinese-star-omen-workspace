from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .calibration import (
    ReviewerSlotV1,
    StableId,
    StrictCalibrationModel,
    publish_no_overwrite,
)
from .passage_inventory import (
    build_rule_passage_inventory,
    canonical_inventory_bytes,
)
from .pilot_worksheets import (
    PilotSelectionV1,
    build_pilot_worksheets,
    canonical_worksheet_bytes,
    publish_pilot_worksheets,
)


class ReviewerSlotSetV1(StrictCalibrationModel):
    schema_version: Literal["reviewer-slot-set/v1"]
    pilot_id: StableId
    slots: tuple[ReviewerSlotV1, ...] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_slots(self) -> "ReviewerSlotSetV1":
        if {slot.slot for slot in self.slots} != {"reviewer_a", "reviewer_b"}:
            raise ValueError("slot set must contain reviewer_a and reviewer_b")
        if any(slot.pilot_id != self.pilot_id for slot in self.slots):
            raise ValueError("slot pilot does not match slot-set pilot")
        return self


def _read_regular(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required regular file missing: {path.name}")
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError(f"input file exceeds 16 MiB: {path.name}")
    return path.read_bytes()


def prepare_pilot_handoff(
    *,
    kb_root: str | Path,
    selection_path: str | Path,
    reviewer_slots_path: str | Path,
    output_directory: str | Path,
) -> dict[str, object]:
    selection = PilotSelectionV1.model_validate_json(
        _read_regular(Path(selection_path))
    )
    slot_set = ReviewerSlotSetV1.model_validate_json(
        _read_regular(Path(reviewer_slots_path))
    )
    if slot_set.pilot_id != selection.pilot_id:
        raise ValueError("selection pilot does not match reviewer slot set")
    inventory = build_rule_passage_inventory(kb_root)
    worksheets = build_pilot_worksheets(
        selection=selection,
        inventory=inventory,
        slots=slot_set.slots,
    )
    publish_pilot_worksheets(output_directory, worksheets)
    worksheet_sha256 = {
        worksheet.reviewer_slot: hashlib.sha256(
            canonical_worksheet_bytes(worksheet)
        ).hexdigest()
        for worksheet in worksheets
    }
    return {
        "schema_version": "pilot-handoff-result/v1",
        "pilot_id": selection.pilot_id,
        "inventory_fingerprint": inventory.source_fingerprint,
        "case_count": len(selection.cases),
        "human_review_completed": False,
        "worksheet_sha256": dict(sorted(worksheet_sha256.items())),
    }


def export_pilot_inventory(
    *,
    kb_root: str | Path,
    output_path: str | Path,
) -> dict[str, object]:
    inventory = build_rule_passage_inventory(kb_root)
    data = canonical_inventory_bytes(inventory)
    publish_no_overwrite(Path(output_path), data)
    return {
        "schema_version": inventory.schema_version,
        "source_fingerprint": inventory.source_fingerprint,
        "passage_count": len(inventory.passages),
        "ambiguous_anchor_count": len(inventory.ambiguous_anchors),
        "inventory_sha256": hashlib.sha256(data).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a real-corpus B10 calibration pilot handoff."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    inventory_parser = subparsers.add_parser(
        "inventory",
        help="Export a canonical passage inventory for manual pilot selection.",
    )
    inventory_parser.add_argument("--kb-root", type=Path, required=True)
    inventory_parser.add_argument("--out", type=Path, required=True)
    worksheet_parser = subparsers.add_parser(
        "worksheets",
        help="Build unlabelled reviewer A/B worksheets from a reviewed selection.",
    )
    worksheet_parser.add_argument("--kb-root", type=Path, required=True)
    worksheet_parser.add_argument("--selection", type=Path, required=True)
    worksheet_parser.add_argument("--reviewer-slots", type=Path, required=True)
    worksheet_parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "inventory":
        result = export_pilot_inventory(
            kb_root=args.kb_root,
            output_path=args.out,
        )
    else:
        result = prepare_pilot_handoff(
            kb_root=args.kb_root,
            selection_path=args.selection,
            reviewer_slots_path=args.reviewer_slots,
            output_directory=args.out_dir,
        )
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = [
    "ReviewerSlotSetV1",
    "export_pilot_inventory",
    "main",
    "prepare_pilot_handoff",
]
