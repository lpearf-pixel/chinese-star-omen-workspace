"""Map query modes to Qdrant card-type filters."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from qdrant_client.http import models as qmodels

NEVER_WHEN_QUERY_MODE = ("prompt_asset", "qa_example")
EVIDENCE_CARD_TYPES = ("fenjuan", "fulltext")
KNOWLEDGE_CARD_TYPES = ("xingguan_card", "zhusu_card", "term_card", "extract_card")
SUPPORT_CARD_TYPES = ("topic_index", "chapter_summary", "nav")

_POOL_BY_MODE: Dict[str, tuple[str, ...]] = {
    "evidence": EVIDENCE_CARD_TYPES,
    "knowledge": KNOWLEDGE_CARD_TYPES,
    "support": SUPPORT_CARD_TYPES,
}


def build_retrieval_filter(
    user_filters: Optional[Dict[str, Any]],
    query_mode: Optional[str],
) -> Optional[qmodels.Filter]:
    must: List[qmodels.FieldCondition] = []
    must_not: List[qmodels.FieldCondition] = []

    if user_filters:
        for key, value in user_filters.items():
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

    mode = (query_mode or "").strip().lower()
    if mode:
        pool = _POOL_BY_MODE.get(mode)
        if not pool:
            raise ValueError(
                f"invalid query_mode={query_mode!r}; expected evidence|knowledge|support"
            )
        must.append(
            qmodels.FieldCondition(
                key="card_type",
                match=qmodels.MatchAny(any=list(pool)),
            )
        )
        must_not.append(
            qmodels.FieldCondition(
                key="card_type",
                match=qmodels.MatchAny(any=list(NEVER_WHEN_QUERY_MODE)),
            )
        )

    if not must and not must_not:
        return None
    return qmodels.Filter(
        must=must if must else None,
        must_not=must_not if must_not else None,
    )
