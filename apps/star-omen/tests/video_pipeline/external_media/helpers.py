from __future__ import annotations


def valid_source_payload() -> dict:
    return {
        "schema_version": "external-media-source/v1",
        "source_id": "media:fixture:work-001",
        "platform": "other",
        "creator_id": "creator:fixture:001",
        "creator_display_name": "Fixture Creator",
        "creator_account_locator": "fixture-account",
        "platform_work_id": "fixture-work-001",
        "fixed_url": "https://example.invalid/media/work-001",
        "published_at_utc": "2026-08-12T01:00:00Z",
        "capture_status": "captured",
        "captures": [
            {
                "capture_id": "capture:fixture:description",
                "capture_type": "description",
                "content_sha256": "a" * 64,
                "content_locator": "https://example.invalid/media/work-001#description",
                "captured_at_utc": "2026-08-12T02:00:00Z",
                "rights_status": "quotation_for_research",
                "rights_note": "Synthetic fixture text; not a real creator capture.",
            }
        ],
        "capture_notes": ["Synthetic contract fixture only."],
    }


def valid_claim_payload() -> dict:
    return {
        "schema_version": "external-claim/v1",
        "claim_id": "claim:fixture:001",
        "source_id": "media:fixture:work-001",
        "claim_class": "modern_inference",
        "source_span": {
            "capture_id": "capture:fixture:description",
            "capture_sha256": "a" * 64,
            "source_locator": "description#chars=0-18",
            "exact_text": "Synthetic inference",
            "start_offset": 0.0,
            "end_offset": 18.0,
            "offset_unit": "unicode_codepoints",
        },
        "review_status": "candidate",
        "reviewer_id": None,
        "review_notes": [],
    }


def valid_evidence_link_payload() -> dict:
    return {
        "schema_version": "evidence-link/v1",
        "evidence_link_id": "evidence-link:fixture:001",
        "claim_id": "claim:fixture:001",
        "evidence_class": "modern_authority",
        "evidence_ref_id": "authority:fixture:001",
        "evidence_locator": "https://example.invalid/authority/001",
        "evidence_sha256": "b" * 64,
        "relationship": "supports",
        "mapping_note": "Synthetic support used only to exercise the contract.",
        "review_status": "candidate",
        "reviewer_id": None,
        "review_notes": [],
    }


def valid_audit_payload() -> dict:
    return {
        "schema_version": "external-audit/v1",
        "audit_id": "audit:fixture:001",
        "source_id": "media:fixture:work-001",
        "claim_ids": ["claim:fixture:001"],
        "evidence_link_ids": ["evidence-link:fixture:001"],
        "assessments": [
            {
                "claim_id": "claim:fixture:001",
                "disposition": "modern_inference_only",
                "evidence_link_ids": ["evidence-link:fixture:001"],
                "rationale": "Only a synthetic modern-authority link is present.",
            }
        ],
        "overall_disposition": "modern_inference_only",
        "research_only": True,
        "grants_rule_authority": False,
        "grants_classical_authority": False,
        "review_status": "candidate",
        "reviewer_id": None,
        "review_notes": [],
    }


def valid_bundle_payload() -> dict:
    return {
        "schema_version": "external-audit-bundle/v1",
        "source": valid_source_payload(),
        "claims": [valid_claim_payload()],
        "evidence_links": [valid_evidence_link_payload()],
        "audit": valid_audit_payload(),
    }
