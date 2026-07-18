from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from kb_text_core import (
    canonical_source_locator,
    normalize_search_text,
    source_volume_for_locator,
)

from src.config.settings import get_settings
from src.connectors.kb_contract import (
    can_be_final_fact,
    infer_metadata_from_path,
    resolve_evidence_level,
)
from src.connectors.primary_passage_cache import (
    PrimarySourceReadError,
    primary_passage_cache,
)

VALIDATION_VERSION = "citable-evidence/v2"
PRIMARY_CARD_TYPES = {"fenjuan", "fulltext"}
CHECK_NAMES = (
    "path",
    "card_type",
    "book",
    "locator",
    "page",
    "paragraph",
    "heading",
    "anchor",
    "hash",
)


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _checks() -> dict[str, bool]:
    return {name: False for name in CHECK_NAMES}


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _passage_trace(passage: Any) -> dict[str, Any]:
    return {
        "kb_book_id": passage.kb_book_id,
        "book_title": passage.book_title,
        "card_type": passage.card_type,
        "source_path": passage.source_path,
        "source_locator": passage.source_locator,
        "source_volume": passage.source_volume,
        "page_marker": passage.page_marker,
        "heading_path": list(passage.heading_path),
        "paragraph_index": passage.paragraph_index,
        "raw_start": passage.raw_start,
        "raw_end": passage.raw_end,
        "raw_text": passage.raw_text,
        "normalized_text": passage.normalized_text,
        "raw_content_hash": passage.raw_content_hash,
        "normalized_content_hash": passage.normalized_content_hash,
    }


def _finish(
    resolved: dict[str, Any],
    *,
    status: str,
    reason: str | None,
    checks: dict[str, bool],
    root_label: str,
    matched_passage: dict[str, Any] | None = None,
    anchor_match_type: str | None = None,
) -> dict[str, Any]:
    citable = status == "citable"
    resolved["status"] = status
    resolved["candidate_reason"] = reason
    resolved["final_citable"] = citable
    resolved["trace"] = {
        "resolver_version": "v2",
        "validation_version": VALIDATION_VERSION,
        "requires_primary_card_types": sorted(PRIMARY_CARD_TYPES),
        "primary_projection_ready": citable,
        "source_root_label": root_label,
        "checks": dict(checks),
        "matched_passage": matched_passage,
        "anchor_match_type": anchor_match_type,
    }
    return resolved


def _base_resolved(evidence: dict[str, Any], settings: Any) -> dict[str, Any]:
    card_type = str(evidence.get("card_type") or "")
    inferred_level = resolve_evidence_level(card_type) if card_type else None
    locator = evidence.get("locator")
    anchor_heading = evidence.get("anchor_heading")
    volume = evidence.get("source_volume") or evidence.get("volume")
    section = evidence.get("section")
    heading_path = evidence.get("heading_path")
    if not isinstance(heading_path, list):
        heading_path = [anchor_heading] if anchor_heading else []
    if not volume and isinstance(locator, str) and "/" in locator:
        volume = locator.split("/", 1)[0]
    if not volume and isinstance(locator, str):
        volume = locator
    if not section and isinstance(locator, str):
        section = locator.split("/")[-1]
    source_locator = evidence.get("source_locator") or locator
    anchor_text = evidence.get("anchor_text") or evidence.get("quote")
    return {
        "kb_book_id": evidence.get("kb_book_id") or evidence.get("book_id"),
        "book_title": evidence.get("book_title"),
        "note_id": evidence.get("note_id"),
        "relative_path": evidence.get("relative_path"),
        "card_type": card_type or None,
        "locator": locator,
        "anchor_heading": anchor_heading,
        "quote": evidence.get("quote"),
        "volume": volume,
        "source_volume": volume,
        "section": section,
        "source_locator": source_locator,
        "page_marker": evidence.get("page_marker"),
        "heading_path": heading_path,
        "anchor_text": anchor_text,
        "paragraph_index": evidence.get("paragraph_index"),
        "content_hash": evidence.get("content_hash"),
        "raw_content_hash": evidence.get("raw_content_hash"),
        "normalized_content_hash": evidence.get("normalized_content_hash"),
        "raw_start": evidence.get("raw_start"),
        "raw_end": evidence.get("raw_end"),
        "ingest_source": evidence.get(
            "ingest_source",
            settings.kb_obsidian_ingest_source_label,
        ),
        "source_type": evidence.get("source_type", "docs"),
        "evidence_level": evidence.get("evidence_level") or inferred_level,
        "resolved_path": None,
        "path_exists": None,
        "final_citable": False,
        "candidate_reason": None,
    }


def resolve_evidence(
    evidence: dict[str, Any],
    kb_root: str | Path | None = None,
) -> dict[str, Any]:
    """Resolve and verify a rule evidence reference against immutable raw text."""

    settings = get_settings()
    resolved = _base_resolved(evidence, settings)
    checks = _checks()
    root_label = settings.kb_obsidian_source_root_label
    card_type = str(resolved.get("card_type") or "")

    if card_type not in PRIMARY_CARD_TYPES:
        return _finish(
            resolved,
            status="candidate_only",
            reason="card_type_not_primary",
            checks=checks,
            root_label=root_label,
        )
    checks["card_type"] = can_be_final_fact(card_type)

    relative_path = resolved.get("relative_path")
    if not relative_path:
        return _finish(
            resolved,
            status="candidate_only",
            reason="missing_relative_path",
            checks=checks,
            root_label=root_label,
        )

    effective_root = Path(kb_root) if kb_root is not None else Path(settings.kb_sources_root)
    root = effective_root.expanduser().resolve()
    raw_relative = Path(str(relative_path)).expanduser()
    full_path = raw_relative.resolve() if raw_relative.is_absolute() else (root / raw_relative).resolve()
    resolved["resolved_path"] = str(full_path)
    resolved["path_exists"] = full_path.is_file()
    if not _is_within(full_path, root):
        return _finish(
            resolved,
            status="source_outside_root",
            reason="source_path_escapes_kb_root",
            checks=checks,
            root_label=root_label,
        )
    if not full_path.is_file():
        return _finish(
            resolved,
            status="missing_source",
            reason="source_file_not_found",
            checks=checks,
            root_label=root_label,
        )
    checks["path"] = True

    inferred = infer_metadata_from_path(str(full_path))
    inferred_book = inferred.get("kb_book_id") or inferred.get("book_id")
    requested_book = resolved.get("kb_book_id")
    if requested_book and inferred_book and str(requested_book) != str(inferred_book):
        return _finish(
            resolved,
            status="book_mismatch",
            reason="kb_book_id_does_not_match_source_path",
            checks=checks,
            root_label=root_label,
        )
    effective_book = str(requested_book or inferred_book or "")
    if not effective_book:
        return _finish(
            resolved,
            status="candidate_only",
            reason="missing_kb_book_id",
            checks=checks,
            root_label=root_label,
        )
    resolved["kb_book_id"] = effective_book
    resolved["book_title"] = resolved.get("book_title") or inferred.get("book_title")
    checks["book"] = True

    inferred_card = str(inferred.get("card_type") or "")
    if inferred_card and inferred_card != card_type:
        return _finish(
            resolved,
            status="card_type_mismatch",
            reason="card_type_does_not_match_source_path",
            checks=checks,
            root_label=root_label,
        )
    if not inferred_card:
        return _finish(
            resolved,
            status="candidate_only",
            reason="unrecognized_primary_source_path",
            checks=checks,
            root_label=root_label,
        )

    page_marker = str(resolved.get("page_marker") or "")
    if not page_marker:
        return _finish(
            resolved,
            status="candidate_only",
            reason="missing_page_marker",
            checks=checks,
            root_label=root_label,
        )

    canonical_locator = canonical_source_locator(str(full_path), page_marker)
    requested_locator = str(resolved.get("source_locator") or "")
    if requested_locator and requested_locator != canonical_locator:
        return _finish(
            resolved,
            status="locator_mismatch",
            reason="source_locator_does_not_match_path_or_page",
            checks=checks,
            root_label=root_label,
        )
    resolved["source_locator"] = canonical_locator
    resolved["source_volume"] = source_volume_for_locator(canonical_locator)
    resolved["volume"] = resolved["source_volume"]
    checks["locator"] = True

    try:
        snapshot = primary_passage_cache.load(
            full_path,
            card_type=card_type,
            kb_book_id=effective_book,
            book_title=str(resolved.get("book_title") or "唐開元占經"),
        )
    except PrimarySourceReadError as exc:
        return _finish(
            resolved,
            status="missing_source",
            reason=f"source_read_failed:{exc}",
            checks=checks,
            root_label=root_label,
        )

    passages = snapshot.passages
    page_passages = [
        passage
        for passage in passages
        if passage.page_marker == page_marker
        and passage.source_locator == canonical_locator
    ]
    if not page_passages:
        return _finish(
            resolved,
            status="page_mismatch",
            reason="page_marker_not_found_in_source_locator",
            checks=checks,
            root_label=root_label,
        )
    checks["page"] = True

    paragraph_index = resolved.get("paragraph_index")
    if paragraph_index is not None:
        if not isinstance(paragraph_index, int):
            return _finish(
                resolved,
                status="paragraph_mismatch",
                reason="paragraph_index_must_be_an_integer",
                checks=checks,
                root_label=root_label,
            )
        page_passages = [
            passage
            for passage in page_passages
            if passage.paragraph_index == paragraph_index
        ]
        if not page_passages:
            return _finish(
                resolved,
                status="paragraph_mismatch",
                reason="paragraph_index_not_found_on_page",
                checks=checks,
                root_label=root_label,
            )
    checks["paragraph"] = True

    anchor_text = str(resolved.get("anchor_text") or "")
    if not anchor_text:
        return _finish(
            resolved,
            status="candidate_only",
            reason="missing_anchor",
            checks=checks,
            root_label=root_label,
        )

    exact_matches = [
        passage for passage in page_passages if anchor_text in passage.raw_text
    ]
    anchor_match_type = "exact_raw"
    matching = exact_matches
    if not matching:
        normalized_anchor = normalize_search_text(anchor_text)
        matching = [
            passage
            for passage in page_passages
            if normalized_anchor
            and normalized_anchor in passage.normalized_text
        ]
        anchor_match_type = "normalized"
    if not matching:
        return _finish(
            resolved,
            status="anchor_mismatch",
            reason="anchor_text_not_found_in_selected_passage",
            checks=checks,
            root_label=root_label,
        )
    if len(matching) > 1:
        return _finish(
            resolved,
            status="paragraph_mismatch",
            reason="anchor_matches_multiple_passages",
            checks=checks,
            root_label=root_label,
        )
    passage = matching[0]
    resolved["paragraph_index"] = passage.paragraph_index
    resolved["raw_start"] = passage.raw_start
    resolved["raw_end"] = passage.raw_end
    checks["anchor"] = True

    expected_heading = resolved.get("heading_path")
    if expected_heading:
        if list(expected_heading) != list(passage.heading_path):
            return _finish(
                resolved,
                status="heading_mismatch",
                reason="heading_path_does_not_match_passage",
                checks=checks,
                root_label=root_label,
                matched_passage=_passage_trace(passage),
                anchor_match_type=anchor_match_type,
            )
    resolved["heading_path"] = list(passage.heading_path)
    checks["heading"] = True

    supplied_hashes = {
        key: str(resolved.get(key) or "")
        for key in (
            "content_hash",
            "raw_content_hash",
            "normalized_content_hash",
        )
        if resolved.get(key)
    }
    if not supplied_hashes:
        return _finish(
            resolved,
            status="candidate_only",
            reason="missing_hash",
            checks=checks,
            root_label=root_label,
            matched_passage=_passage_trace(passage),
            anchor_match_type=anchor_match_type,
        )

    anchor_hash = _sha256_text(anchor_text)
    hash_valid = True
    if "content_hash" in supplied_hashes:
        hash_valid = hash_valid and supplied_hashes["content_hash"] in {
            anchor_hash,
            passage.raw_content_hash,
        }
    if "raw_content_hash" in supplied_hashes:
        hash_valid = hash_valid and (
            supplied_hashes["raw_content_hash"] == passage.raw_content_hash
        )
    if "normalized_content_hash" in supplied_hashes:
        hash_valid = hash_valid and (
            supplied_hashes["normalized_content_hash"]
            == passage.normalized_content_hash
        )
    if not hash_valid:
        return _finish(
            resolved,
            status="hash_mismatch",
            reason="content_hash_does_not_match_anchor_or_passage",
            checks=checks,
            root_label=root_label,
            matched_passage=_passage_trace(passage),
            anchor_match_type=anchor_match_type,
        )
    checks["hash"] = True

    resolved["raw_content_hash"] = passage.raw_content_hash
    resolved["normalized_content_hash"] = passage.normalized_content_hash
    resolved["content_hash"] = supplied_hashes.get(
        "content_hash",
        passage.raw_content_hash,
    )
    return _finish(
        resolved,
        status="citable",
        reason=None,
        checks=checks,
        root_label=root_label,
        matched_passage=_passage_trace(passage),
        anchor_match_type=anchor_match_type,
    )
