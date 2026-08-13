from __future__ import annotations

from typing import Literal

from pydantic import AnyHttpUrl, ConfigDict, Field, model_validator

from ._common import (
    FiniteFloat,
    Sha256Hex,
    StableId,
    StrictContractModel,
    UtcDateTime,
    ensure_unique,
)


ReviewStatus = Literal["candidate", "human_verified", "rejected"]
AuditDisposition = Literal[
    "supported_exact",
    "partial",
    "source_missing",
    "ambiguous",
    "contradicted",
    "modern_inference_only",
]


def _validate_review(
    review_status: ReviewStatus,
    reviewer_id: str | None,
) -> None:
    if review_status == "candidate" and reviewer_id is not None:
        raise ValueError("candidate records cannot claim a reviewer_id")
    if review_status in {"human_verified", "rejected"} and reviewer_id is None:
        raise ValueError(f"{review_status} records require reviewer_id")


class MediaCaptureV1(StrictContractModel):
    capture_id: StableId
    capture_type: Literal[
        "title",
        "description",
        "transcript",
        "subtitle",
        "ocr",
        "image",
    ]
    content_sha256: Sha256Hex
    content_locator: str = Field(min_length=1, max_length=2048)
    captured_at_utc: UtcDateTime
    rights_status: Literal[
        "quotation_for_research",
        "permission_confirmed",
        "public_domain",
        "metadata_only",
        "unknown",
    ]
    rights_note: str = Field(min_length=1, max_length=2000)


class ExternalMediaSourceV1(StrictContractModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:external-media-source/v1"},
    )

    schema_version: Literal["external-media-source/v1"]
    source_id: StableId
    platform: Literal[
        "youtube",
        "bilibili",
        "weixin",
        "xiaohongshu",
        "douyin",
        "weibo",
        "other",
    ]
    creator_id: StableId
    creator_display_name: str = Field(min_length=1, max_length=256)
    creator_account_locator: str = Field(min_length=1, max_length=512)
    platform_work_id: str = Field(min_length=1, max_length=512)
    fixed_url: AnyHttpUrl
    published_at_utc: UtcDateTime
    capture_status: Literal["captured", "metadata_only", "source_missing"]
    captures: list[MediaCaptureV1] = Field(default_factory=list)
    capture_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_capture_state(self) -> "ExternalMediaSourceV1":
        ensure_unique([capture.capture_id for capture in self.captures], "captures")
        if self.capture_status == "captured" and not self.captures:
            raise ValueError("captured source requires captures")
        if self.capture_status == "source_missing" and self.captures:
            raise ValueError("source_missing cannot contain captures")
        if self.capture_status == "metadata_only" and any(
            capture.capture_type not in {"title", "description", "image"}
            for capture in self.captures
        ):
            raise ValueError("metadata_only cannot contain transcript-like captures")
        return self


class ExternalSourceSpanV1(StrictContractModel):
    capture_id: StableId
    capture_sha256: Sha256Hex
    source_locator: str = Field(min_length=1, max_length=2048)
    exact_text: str = Field(min_length=1, max_length=10000)
    start_offset: FiniteFloat = Field(ge=0.0)
    end_offset: FiniteFloat = Field(gt=0.0)
    offset_unit: Literal["unicode_codepoints", "seconds"]

    @model_validator(mode="after")
    def validate_offsets(self) -> "ExternalSourceSpanV1":
        if self.end_offset <= self.start_offset:
            raise ValueError("end_offset must be greater than start_offset")
        if self.offset_unit == "unicode_codepoints" and (
            not self.start_offset.is_integer() or not self.end_offset.is_integer()
        ):
            raise ValueError("unicode_codepoints requires integer offsets")
        return self


class ExternalClaimV1(StrictContractModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:external-claim/v1"},
    )

    schema_version: Literal["external-claim/v1"]
    claim_id: StableId
    source_id: StableId
    claim_class: Literal[
        "astronomy_fact",
        "classical_quote",
        "historical_correspondence",
        "modern_inference",
        "disclaimer",
    ]
    source_span: ExternalSourceSpanV1
    review_status: ReviewStatus
    reviewer_id: StableId | None = None
    review_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_review_state(self) -> "ExternalClaimV1":
        _validate_review(self.review_status, self.reviewer_id)
        return self


class EvidenceLinkV1(StrictContractModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:evidence-link/v1"},
    )

    schema_version: Literal["evidence-link/v1"]
    evidence_link_id: StableId
    claim_id: StableId
    evidence_class: Literal[
        "classical_passage",
        "astronomy_calculation",
        "historical_record",
        "modern_authority",
    ]
    evidence_ref_id: StableId
    evidence_locator: str = Field(min_length=1, max_length=2048)
    evidence_sha256: Sha256Hex
    relationship: Literal["supports", "qualifies", "contradicts", "context_only"]
    mapping_note: str = Field(min_length=1, max_length=4000)
    review_status: ReviewStatus
    reviewer_id: StableId | None = None
    review_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_review_state(self) -> "EvidenceLinkV1":
        _validate_review(self.review_status, self.reviewer_id)
        return self


class ExternalClaimAssessmentV1(StrictContractModel):
    claim_id: StableId
    disposition: AuditDisposition
    evidence_link_ids: list[StableId] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="after")
    def validate_evidence_ids(self) -> "ExternalClaimAssessmentV1":
        ensure_unique(list(self.evidence_link_ids), "assessment evidence_link_ids")
        return self


class ExternalAuditV1(StrictContractModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        json_schema_extra={"$id": "urn:kaiyuan:external-audit/v1"},
    )

    schema_version: Literal["external-audit/v1"]
    audit_id: StableId
    source_id: StableId
    claim_ids: list[StableId] = Field(min_length=1)
    evidence_link_ids: list[StableId] = Field(default_factory=list)
    assessments: list[ExternalClaimAssessmentV1]
    overall_disposition: AuditDisposition
    research_only: Literal[True]
    grants_rule_authority: Literal[False]
    grants_classical_authority: Literal[False]
    review_status: ReviewStatus
    reviewer_id: StableId | None = None
    review_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_audit(self) -> "ExternalAuditV1":
        ensure_unique(list(self.claim_ids), "claim_ids")
        ensure_unique(list(self.evidence_link_ids), "evidence_link_ids")
        assessment_claim_ids = [item.claim_id for item in self.assessments]
        ensure_unique(assessment_claim_ids, "assessment claim_ids")
        if set(assessment_claim_ids) != set(self.claim_ids):
            raise ValueError("assessments must exactly cover claim_ids")
        allowed_evidence = set(self.evidence_link_ids)
        if any(
            evidence_link_id not in allowed_evidence
            for assessment in self.assessments
            for evidence_link_id in assessment.evidence_link_ids
        ):
            raise ValueError("assessment references missing audit evidence_link_ids")
        _validate_review(self.review_status, self.reviewer_id)
        return self


class ExternalAuditBundleV1(StrictContractModel):
    """Closed validation boundary; not an independently registered public schema."""

    schema_version: Literal["external-audit-bundle/v1"]
    source: ExternalMediaSourceV1
    claims: list[ExternalClaimV1] = Field(min_length=1)
    evidence_links: list[EvidenceLinkV1] = Field(default_factory=list)
    audit: ExternalAuditV1

    @model_validator(mode="after")
    def validate_bundle(self) -> "ExternalAuditBundleV1":
        claims_by_id = {claim.claim_id: claim for claim in self.claims}
        evidence_by_id = {
            link.evidence_link_id: link for link in self.evidence_links
        }
        ensure_unique([claim.claim_id for claim in self.claims], "bundle claims")
        ensure_unique(
            [link.evidence_link_id for link in self.evidence_links],
            "bundle evidence_links",
        )

        if any(claim.source_id != self.source.source_id for claim in self.claims):
            raise ValueError("claim source_id must equal bundle source_id")
        if self.audit.source_id != self.source.source_id:
            raise ValueError("audit source_id must equal bundle source_id")

        captures_by_id = {
            capture.capture_id: capture for capture in self.source.captures
        }
        for claim in self.claims:
            capture = captures_by_id.get(claim.source_span.capture_id)
            if capture is None or capture.content_sha256 != claim.source_span.capture_sha256:
                raise ValueError("claim span must bind to the same source capture")
            if capture.capture_type == "image":
                raise ValueError("text claim spans require a textual source capture")

        if any(link.claim_id not in claims_by_id for link in self.evidence_links):
            raise ValueError("evidence link references an unknown claim")
        if set(self.audit.claim_ids) != set(claims_by_id):
            raise ValueError("audit must exactly list bundle claims")
        if set(self.audit.evidence_link_ids) != set(evidence_by_id):
            raise ValueError("audit must exactly list bundle evidence links")

        matching_support_classes = {
            "astronomy_fact": {"astronomy_calculation"},
            "classical_quote": {"classical_passage"},
            "historical_correspondence": {
                "historical_record",
                "classical_passage",
            },
            "modern_inference": {"modern_authority"},
            "disclaimer": {"modern_authority"},
        }
        for assessment in self.audit.assessments:
            claim = claims_by_id[assessment.claim_id]
            links = [
                evidence_by_id[evidence_link_id]
                for evidence_link_id in assessment.evidence_link_ids
            ]
            relationships = {link.relationship for link in links}
            if assessment.disposition == "supported_exact":
                supports = [link for link in links if link.relationship == "supports"]
                if not supports:
                    raise ValueError("supported_exact requires a supporting link")
                if "contradicts" in relationships:
                    raise ValueError("supported_exact cannot include a contradicting link")
                if not any(
                    link.evidence_class in matching_support_classes[claim.claim_class]
                    for link in supports
                ):
                    raise ValueError("supported_exact requires a matching evidence class")
            elif assessment.disposition == "contradicted":
                if "contradicts" not in relationships:
                    raise ValueError("contradicted requires a contradicting link")
            elif assessment.disposition == "source_missing":
                if links:
                    raise ValueError("source_missing cannot reference evidence links")
            elif assessment.disposition == "modern_inference_only":
                if not links or any(
                    link.evidence_class != "modern_authority" for link in links
                ):
                    raise ValueError(
                        "modern_inference_only requires only modern-authority evidence"
                    )
            elif assessment.disposition == "partial":
                if not relationships & {"supports", "qualifies"}:
                    raise ValueError("partial requires supporting or qualifying evidence")

        dispositions = {item.disposition for item in self.audit.assessments}
        if len(dispositions) == 1 and self.audit.overall_disposition not in dispositions:
            raise ValueError(
                "overall_disposition must equal the single claim disposition"
            )
        if len(dispositions) > 1 and self.audit.overall_disposition not in {
            "partial",
            "ambiguous",
        }:
            raise ValueError("mixed claim dispositions require partial or ambiguous overall")
        return self
