"""Resolve the v2 retrieval intent, stage and explicit card-type pool."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Dict, List, Optional

from qdrant_client.http import models as qmodels

NEVER_RETRIEVABLE = ("prompt_asset", "qa_example")
PRIMARY_CARD_TYPES = ("fenjuan", "fulltext")
KNOWLEDGE_CARD_TYPES = (
    "xingguan_card",
    "zhusu_card",
    "term_card",
    "extract_card",
)
STRUCTURED_RECALL_CARD_TYPES = (
    "xingguan_card",
    "zhusu_card",
    "term_card",
    "extract_card",
    "topic_index",
    "chapter_summary",
)
SUPPORT_CARD_TYPES = ("topic_index", "chapter_summary", "nav")

STAGE_POOLS: Dict[str, tuple[str, ...]] = {
    "structured_recall": STRUCTURED_RECALL_CARD_TYPES,
    "primary_evidence": PRIMARY_CARD_TYPES,
    "support_context": SUPPORT_CARD_TYPES,
}

# Backward compatibility is used only when a v2 stage/pool is absent.
LEGACY_MODE_POOLS: Dict[str, tuple[str, ...]] = {
    "evidence": PRIMARY_CARD_TYPES,
    "knowledge": KNOWLEDGE_CARD_TYPES,
    "support": SUPPORT_CARD_TYPES,
}

KNOWN_CARD_TYPES = set(
    (*STRUCTURED_RECALL_CARD_TYPES, *PRIMARY_CARD_TYPES, *SUPPORT_CARD_TYPES)
)
VALID_QUERY_MODES = set(LEGACY_MODE_POOLS)
VALID_RETRIEVAL_STAGES = {"auto", *STAGE_POOLS}


def _normalize_card_types(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        values: Iterable[Any] = [value]
    elif isinstance(value, Iterable):
        values = value
    else:
        raise ValueError("card_types must be a string or list of strings")

    output: list[str] = []
    for raw in values:
        card_type = str(raw).strip()
        if card_type and card_type not in output:
            output.append(card_type)
    return output or None


def canonicalize_filters(
    filters: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Canonicalize compatibility aliases without mutating the caller."""

    canonical = dict(filters or {})
    legacy_book_id = canonical.get("book_id")
    canonical_book_id = canonical.get("kb_book_id")
    if (
        legacy_book_id is not None
        and canonical_book_id is not None
        and str(legacy_book_id) != str(canonical_book_id)
    ):
        raise ValueError("conflicting book identifiers: book_id and kb_book_id")
    if canonical_book_id is None and legacy_book_id is not None:
        canonical["kb_book_id"] = legacy_book_id
    canonical.pop("book_id", None)
    return canonical


def _validate_card_types(card_types: list[str] | None) -> list[str] | None:
    if card_types is None:
        return None
    disallowed = [value for value in card_types if value in NEVER_RETRIEVABLE]
    if disallowed:
        raise ValueError(f"card types are not retrievable: {disallowed}")
    unknown = [value for value in card_types if value not in KNOWN_CARD_TYPES]
    if unknown:
        raise ValueError(f"unknown card types: {unknown}")
    return card_types


def resolve_card_types(
    *,
    query_mode: Optional[str],
    retrieval_stage: Optional[str],
    card_types: Optional[List[str]],
    filters: Optional[Dict[str, Any]],
) -> tuple[list[str] | None, Dict[str, Any]]:
    """Return one effective card pool plus canonical non-card filters.

    Precedence is explicit ``card_types``, legacy ``filters.card_type``, v2
    ``retrieval_stage``, then legacy ``query_mode`` fallback.  Only one pool is
    materialized into Qdrant, avoiding accidental AND-ed card-type conditions.
    """

    mode = (query_mode or "").strip().lower() or None
    if mode is not None and mode not in VALID_QUERY_MODES:
        raise ValueError(
            f"invalid query_mode={query_mode!r}; expected evidence|knowledge|support"
        )

    stage = (retrieval_stage or "").strip().lower() or None
    if stage is not None and stage not in VALID_RETRIEVAL_STAGES:
        raise ValueError(
            "invalid retrieval_stage={!r}; expected auto|structured_recall|"
            "primary_evidence|support_context".format(retrieval_stage)
        )

    canonical_filters = canonicalize_filters(filters)
    legacy_pool = _normalize_card_types(canonical_filters.pop("card_type", None))
    explicit_pool = _normalize_card_types(card_types)

    if (
        explicit_pool is not None
        and legacy_pool is not None
        and set(explicit_pool) != set(legacy_pool)
    ):
        raise ValueError(
            "conflicting card type pools: card_types and filters.card_type"
        )

    effective = explicit_pool or legacy_pool
    if effective is None and stage and stage != "auto":
        effective = list(STAGE_POOLS[stage])
    if effective is None and mode:
        effective = list(LEGACY_MODE_POOLS[mode])

    return _validate_card_types(effective), canonical_filters


def build_retrieval_filter(
    *,
    filters: Optional[Dict[str, Any]],
    query_mode: Optional[str],
    retrieval_stage: Optional[str] = None,
    card_types: Optional[List[str]] = None,
) -> Optional[qmodels.Filter]:
    effective_card_types, canonical_filters = resolve_card_types(
        query_mode=query_mode,
        retrieval_stage=retrieval_stage,
        card_types=card_types,
        filters=filters,
    )

    must: List[qmodels.FieldCondition] = []
    for key, value in canonical_filters.items():
        if isinstance(value, list):
            must.append(
                qmodels.FieldCondition(
                    key=key,
                    match=qmodels.MatchAny(any=list(value)),
                )
            )
        else:
            must.append(
                qmodels.FieldCondition(
                    key=key,
                    match=qmodels.MatchValue(value=value),
                )
            )

    if effective_card_types:
        must.append(
            qmodels.FieldCondition(
                key="card_type",
                match=qmodels.MatchAny(any=list(effective_card_types)),
            )
        )

    must_not = [
        qmodels.FieldCondition(
            key="card_type",
            match=qmodels.MatchAny(any=list(NEVER_RETRIEVABLE)),
        )
    ]
    if not must and not must_not:
        return None
    return qmodels.Filter(
        must=must or None,
        must_not=must_not,
    )
