from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ._common import StableId, StrictContractModel, ensure_unique


ReferenceType = Literal[
    "astronomy_measurement",
    "asterism_mapping",
    "citable_passage",
    "historical_source",
    "modern_interpretation",
]
ClaimClass = Literal[
    "astronomy_fact",
    "classical_quote",
    "historical_context",
    "modern_interpretation",
    "production_instruction",
]


class SourceInventoryV1(StrictContractModel):
    astronomy_measurement_ids: list[StableId] = Field(default_factory=list)
    asterism_mapping_ids: list[StableId] = Field(default_factory=list)
    citable_passage_ids: list[StableId] = Field(default_factory=list)
    historical_source_ids: list[StableId] = Field(default_factory=list)
    modern_interpretation_ids: list[StableId] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_inventory(self) -> "SourceInventoryV1":
        groups = {
            "astronomy_measurement_ids": self.astronomy_measurement_ids,
            "asterism_mapping_ids": self.asterism_mapping_ids,
            "citable_passage_ids": self.citable_passage_ids,
            "historical_source_ids": self.historical_source_ids,
            "modern_interpretation_ids": self.modern_interpretation_ids,
        }
        all_ids: list[str] = []
        for name, values in groups.items():
            ensure_unique(list(values), name)
            all_ids.extend(values)
        ensure_unique(all_ids, "source_inventory")
        return self


class SourceReferenceV1(StrictContractModel):
    source_package_id: StableId
    reference_type: ReferenceType
    reference_id: StableId


class ClaimV1(StrictContractModel):
    claim_id: StableId
    claim_class: ClaimClass
    text: str = Field(min_length=1, max_length=4000)
    source_refs: list[SourceReferenceV1]
    review_status: Literal["pending", "approved", "rejected", "needs_revision"]


class VideoPackageV1(StrictContractModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:video-package/v1"},
    )

    schema_version: Literal["video-package/v1"]
    package_id: StableId
    event_id: StableId
    assessment_id: StableId
    source_inventory: SourceInventoryV1
    claims: list[ClaimV1]

    @model_validator(mode="after")
    def validate_claims(self) -> "VideoPackageV1":
        ensure_unique([claim.claim_id for claim in self.claims], "claims")
        inventory = {
            "astronomy_measurement": set(self.source_inventory.astronomy_measurement_ids),
            "asterism_mapping": set(self.source_inventory.asterism_mapping_ids),
            "citable_passage": set(self.source_inventory.citable_passage_ids),
            "historical_source": set(self.source_inventory.historical_source_ids),
            "modern_interpretation": set(
                self.source_inventory.modern_interpretation_ids
            ),
        }
        allowed_types = {
            "astronomy_fact": {"astronomy_measurement", "asterism_mapping"},
            "classical_quote": {"citable_passage"},
            "historical_context": {"historical_source"},
            "modern_interpretation": {"modern_interpretation"},
            "production_instruction": set(),
        }
        for claim in self.claims:
            refs = claim.source_refs
            if claim.claim_class == "production_instruction":
                if refs:
                    raise ValueError("production_instruction claims cannot cite research sources")
                continue
            if not refs:
                raise ValueError(f"{claim.claim_class} claims require source_refs")
            if claim.claim_class == "classical_quote" and not any(
                ref.reference_type == "citable_passage" for ref in refs
            ):
                raise ValueError("classical_quote requires a citable_passage reference")
            seen_refs: set[tuple[str, str]] = set()
            for ref in refs:
                if ref.source_package_id != self.package_id:
                    raise ValueError("source references cannot cross package boundaries")
                if ref.reference_type not in allowed_types[claim.claim_class]:
                    raise ValueError(
                        f"{claim.claim_class} cannot reference {ref.reference_type}"
                    )
                if ref.reference_id not in inventory[ref.reference_type]:
                    raise ValueError("source reference is missing from matching inventory")
                key = (ref.reference_type, ref.reference_id)
                if key in seen_refs:
                    raise ValueError("claim source references must be unique")
                seen_refs.add(key)
        return self
