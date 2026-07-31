from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, Sequence

from pydantic import Field, model_validator

from .calibration import (
    ReviewerSlotV1,
    StableId,
    StrictCalibrationModel,
    canonical_calibration_bytes,
    publish_no_overwrite,
    validate_reviewer_slots,
)
from .passage_inventory import PassageInventoryV1, PassageRecordV1


CelestialCategory = Literal[
    "sun",
    "moon",
    "five_planets",
    "lunar_mansions",
    "guest_star",
    "comet",
    "meteor",
    "eclipse",
    "cloud_qi",
]
RelationTerm = Literal["合", "犯", "入", "守", "掩", "离", "留", "逆"]
SentenceComplexity = Literal["simple", "compound", "cross_passage"]
Computability = Literal[
    "computable",
    "partially_computable",
    "not_computable",
]
EvidenceRisk = Literal["low", "medium", "high"]
SpecialCaseTag = Literal["ambiguous", "duplicate", "conflict"]
PilotSplit = Literal["development", "validation"]

REQUIRED_CELESTIAL_CATEGORIES = frozenset(CelestialCategory.__args__)
REQUIRED_RELATION_TERMS = frozenset(RelationTerm.__args__)
REQUIRED_SENTENCE_COMPLEXITIES = frozenset(SentenceComplexity.__args__)
REQUIRED_COMPUTABILITY = frozenset(Computability.__args__)
REQUIRED_EVIDENCE_RISKS = frozenset(EvidenceRisk.__args__)
REQUIRED_SPECIAL_CASE_TAGS = frozenset(SpecialCaseTag.__args__)


class PilotSelectionCaseV1(StrictCalibrationModel):
    case_id: StableId
    passage_id: StableId
    split: PilotSplit
    celestial_categories: tuple[CelestialCategory, ...] = Field(min_length=1)
    relation_terms: tuple[RelationTerm, ...] = Field(min_length=1)
    sentence_complexity: SentenceComplexity
    computability: Computability
    evidence_risk: EvidenceRisk
    special_case_tags: tuple[SpecialCaseTag, ...] = ()

    @model_validator(mode="after")
    def validate_values(self) -> "PilotSelectionCaseV1":
        for name, values in (
            ("celestial_categories", self.celestial_categories),
            ("relation_terms", self.relation_terms),
            ("special_case_tags", self.special_case_tags),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must contain unique values")
        return self


class PilotSelectionV1(StrictCalibrationModel):
    schema_version: Literal["pilot-selection/v1"]
    pilot_id: StableId
    inventory_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    annotation_guide_version: StableId
    cases: tuple[PilotSelectionCaseV1, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_cases(self) -> "PilotSelectionV1":
        case_ids = [item.case_id for item in self.cases]
        passage_ids = [item.passage_id for item in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("selection case IDs must be unique")
        if len(passage_ids) != len(set(passage_ids)):
            raise ValueError("selection passage IDs must be unique across splits")
        if case_ids != sorted(case_ids):
            raise ValueError("selection cases must be sorted by case_id")
        return self


class PilotWorksheetCaseV1(StrictCalibrationModel):
    case_id: StableId
    passage_id: StableId
    source_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    split: PilotSplit
    volume: str = Field(min_length=1, max_length=80)
    celestial_categories: tuple[CelestialCategory, ...]
    relation_terms: tuple[RelationTerm, ...]
    sentence_complexity: SentenceComplexity
    computability: Computability
    evidence_risk: EvidenceRisk
    special_case_tags: tuple[SpecialCaseTag, ...]
    source_locator: str = Field(min_length=1)
    page_marker: str | None
    heading_path: tuple[str, ...]
    paragraph_index: int = Field(strict=True, ge=0)
    raw_text: str = Field(min_length=1)
    raw_content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    expected_label: None = None


def _shared_content_hash(
    *,
    pilot_id: str,
    inventory_fingerprint: str,
    annotation_guide_version: str,
    cases: Sequence[PilotWorksheetCaseV1],
) -> str:
    payload = {
        "pilot_id": pilot_id,
        "inventory_fingerprint": inventory_fingerprint,
        "annotation_guide_version": annotation_guide_version,
        "cases": [case.model_dump(mode="json") for case in cases],
    }
    return hashlib.sha256(canonical_calibration_bytes(payload)).hexdigest()


class PilotWorksheetV1(StrictCalibrationModel):
    schema_version: Literal["pilot-worksheet/v1"]
    worksheet_id: StableId
    pilot_id: StableId
    reviewer_slot: Literal["reviewer_a", "reviewer_b"]
    reviewer_id: StableId
    inventory_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    annotation_guide_version: StableId
    shared_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    human_review_completed: Literal[False] = False
    cases: tuple[PilotWorksheetCaseV1, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_shared_content(self) -> "PilotWorksheetV1":
        expected = _shared_content_hash(
            pilot_id=self.pilot_id,
            inventory_fingerprint=self.inventory_fingerprint,
            annotation_guide_version=self.annotation_guide_version,
            cases=self.cases,
        )
        if self.shared_content_sha256 != expected:
            raise ValueError("worksheet shared content hash does not match cases")
        return self


def _coverage_error(selection: PilotSelectionV1) -> str | None:
    actual_categories = {
        value for case in selection.cases for value in case.celestial_categories
    }
    actual_relations = {
        value for case in selection.cases for value in case.relation_terms
    }
    actual_complexities = {case.sentence_complexity for case in selection.cases}
    actual_computability = {case.computability for case in selection.cases}
    actual_risks = {case.evidence_risk for case in selection.cases}
    actual_special = {
        value for case in selection.cases for value in case.special_case_tags
    }
    missing = {
        "celestial_categories": sorted(
            REQUIRED_CELESTIAL_CATEGORIES - actual_categories
        ),
        "relation_terms": sorted(REQUIRED_RELATION_TERMS - actual_relations),
        "sentence_complexity": sorted(
            REQUIRED_SENTENCE_COMPLEXITIES - actual_complexities
        ),
        "computability": sorted(REQUIRED_COMPUTABILITY - actual_computability),
        "evidence_risk": sorted(REQUIRED_EVIDENCE_RISKS - actual_risks),
        "special_case_tags": sorted(REQUIRED_SPECIAL_CASE_TAGS - actual_special),
        "splits": sorted({"development", "validation"} - {c.split for c in selection.cases}),
    }
    missing = {name: values for name, values in missing.items() if values}
    return json.dumps(missing, ensure_ascii=False, sort_keys=True) if missing else None


def _worksheet_case(
    selection: PilotSelectionCaseV1,
    passage: PassageRecordV1,
) -> PilotWorksheetCaseV1:
    return PilotWorksheetCaseV1(
        case_id=selection.case_id,
        passage_id=selection.passage_id,
        source_fingerprint=passage.source_fingerprint,
        split=selection.split,
        volume=passage.source_volume or passage.source_locator,
        celestial_categories=selection.celestial_categories,
        relation_terms=selection.relation_terms,
        sentence_complexity=selection.sentence_complexity,
        computability=selection.computability,
        evidence_risk=selection.evidence_risk,
        special_case_tags=selection.special_case_tags,
        source_locator=passage.source_locator,
        page_marker=passage.page_marker,
        heading_path=passage.heading_path,
        paragraph_index=passage.paragraph_index,
        raw_text=passage.raw_text,
        raw_content_hash=passage.raw_content_hash,
    )


def _worksheet_id(
    *,
    pilot_id: str,
    reviewer_id: str,
    reviewer_slot: str,
    shared_content_sha256: str,
) -> str:
    seed = {
        "pilot_id": pilot_id,
        "reviewer_id": reviewer_id,
        "shared_content_sha256": shared_content_sha256,
    }
    digest = hashlib.sha256(canonical_calibration_bytes(seed)).hexdigest()
    return f"pilot-worksheet:{reviewer_slot}:{digest[:24]}"


def build_pilot_worksheets(
    *,
    selection: PilotSelectionV1,
    inventory: PassageInventoryV1,
    slots: Sequence[ReviewerSlotV1],
) -> tuple[PilotWorksheetV1, PilotWorksheetV1]:
    selection = PilotSelectionV1.model_validate(selection.model_dump(mode="json"))
    inventory = PassageInventoryV1.model_validate(inventory.model_dump(mode="json"))
    slots = tuple(
        ReviewerSlotV1.model_validate(slot.model_dump(mode="json")) for slot in slots
    )
    validate_reviewer_slots(
        pilot_id=selection.pilot_id,
        reviewer_ids=[slot.reviewer_id for slot in slots],
        slots=slots,
    )
    if selection.inventory_fingerprint != inventory.source_fingerprint:
        raise ValueError("selection inventory fingerprint does not match inventory")
    coverage_error = _coverage_error(selection)
    if coverage_error is not None:
        raise ValueError(f"pilot coverage is incomplete: {coverage_error}")

    passages = {item.passage_id: item for item in inventory.passages}
    ambiguous_passage_ids = {
        passage_id
        for anchor in inventory.ambiguous_anchors
        for passage_id in anchor.passage_ids
    }
    selected: list[tuple[PilotSelectionCaseV1, PassageRecordV1]] = []
    for case in selection.cases:
        passage = passages.get(case.passage_id)
        if passage is None:
            raise ValueError(f"unknown passage in pilot selection: {case.passage_id}")
        if passage.passage_id in ambiguous_passage_ids:
            raise ValueError(
                f"source-ambiguous passage cannot enter pilot: {passage.passage_id}"
            )
        selected.append((case, passage))
    volumes = {
        passage.source_volume
        for _, passage in selected
        if passage.source_volume is not None
    }
    if len(volumes) < 2:
        raise ValueError("pilot coverage must span at least two source volumes")

    cases = tuple(_worksheet_case(case, passage) for case, passage in selected)
    shared_hash = _shared_content_hash(
        pilot_id=selection.pilot_id,
        inventory_fingerprint=selection.inventory_fingerprint,
        annotation_guide_version=selection.annotation_guide_version,
        cases=cases,
    )
    worksheets = tuple(
        PilotWorksheetV1(
            schema_version="pilot-worksheet/v1",
            worksheet_id=_worksheet_id(
                pilot_id=selection.pilot_id,
                reviewer_id=slot.reviewer_id,
                reviewer_slot=slot.slot,
                shared_content_sha256=shared_hash,
            ),
            pilot_id=selection.pilot_id,
            reviewer_slot=slot.slot,
            reviewer_id=slot.reviewer_id,
            inventory_fingerprint=selection.inventory_fingerprint,
            annotation_guide_version=selection.annotation_guide_version,
            shared_content_sha256=shared_hash,
            cases=cases,
        )
        for slot in sorted(slots, key=lambda item: item.slot)
    )
    return worksheets


def canonical_worksheet_bytes(worksheet: PilotWorksheetV1) -> bytes:
    worksheet = PilotWorksheetV1.model_validate(worksheet.model_dump(mode="json"))
    return canonical_calibration_bytes(worksheet)


def publish_pilot_worksheets(
    output_directory: str | Path,
    worksheets: Sequence[PilotWorksheetV1],
) -> tuple[Path, Path]:
    validated = tuple(
        sorted(
            (
                PilotWorksheetV1.model_validate(item.model_dump(mode="json"))
                for item in worksheets
            ),
            key=lambda item: item.reviewer_slot,
        )
    )
    if len(validated) != 2 or {item.reviewer_slot for item in validated} != {
        "reviewer_a",
        "reviewer_b",
    }:
        raise ValueError("exactly one reviewer_a and one reviewer_b worksheet required")
    if len({item.shared_content_sha256 for item in validated}) != 1:
        raise ValueError("reviewer worksheets must bind identical shared content")
    output = Path(output_directory)
    paths = tuple(output / f"{item.reviewer_slot}.json" for item in validated)
    if any(path.exists() for path in paths):
        raise FileExistsError("pilot worksheet output already exists")
    for path, worksheet in zip(paths, validated, strict=True):
        publish_no_overwrite(path, canonical_worksheet_bytes(worksheet))
    return paths


__all__ = [
    "PilotSelectionCaseV1",
    "PilotSelectionV1",
    "PilotWorksheetCaseV1",
    "PilotWorksheetV1",
    "build_pilot_worksheets",
    "canonical_worksheet_bytes",
    "publish_pilot_worksheets",
]
