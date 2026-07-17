from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "kb-search"))
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name)
    return importlib.import_module("app.retrieval_pools")


def _match_values(condition) -> list[str]:
    match = condition.match
    values = getattr(match, "any", None)
    if values is not None:
        return list(values)
    value = getattr(match, "value", None)
    return [value]


def test_evidence_intent_with_structured_stage_uses_structured_pool_only(monkeypatch):
    pools = _load_module(monkeypatch)

    effective, filters = pools.resolve_card_types(
        query_mode="evidence",
        retrieval_stage="structured_recall",
        card_types=["zhusu_card", "term_card", "extract_card"],
        filters={"kb_book_id": "kaiyuan_zhanjing"},
    )
    q_filter = pools.build_retrieval_filter(
        filters=filters,
        query_mode="evidence",
        retrieval_stage="structured_recall",
        card_types=effective,
    )

    assert effective == ["zhusu_card", "term_card", "extract_card"]
    card_conditions = [condition for condition in q_filter.must if condition.key == "card_type"]
    assert len(card_conditions) == 1
    assert _match_values(card_conditions[0]) == effective
    assert "fenjuan" not in _match_values(card_conditions[0])
    assert "fulltext" not in _match_values(card_conditions[0])


def test_primary_stage_defaults_to_fenjuan_and_fulltext(monkeypatch):
    pools = _load_module(monkeypatch)

    effective, filters = pools.resolve_card_types(
        query_mode="evidence",
        retrieval_stage="primary_evidence",
        card_types=None,
        filters={"book_id": "kaiyuan_zhanjing"},
    )

    assert effective == ["fenjuan", "fulltext"]
    assert filters == {"kb_book_id": "kaiyuan_zhanjing"}


def test_legacy_filter_card_type_is_lifted_out_of_generic_filters(monkeypatch):
    pools = _load_module(monkeypatch)

    effective, filters = pools.resolve_card_types(
        query_mode="evidence",
        retrieval_stage=None,
        card_types=None,
        filters={
            "book_id": "kaiyuan_zhanjing",
            "card_type": ["term_card", "extract_card"],
        },
    )

    assert effective == ["term_card", "extract_card"]
    assert filters == {"kb_book_id": "kaiyuan_zhanjing"}


def test_matching_explicit_and_legacy_card_types_are_accepted(monkeypatch):
    pools = _load_module(monkeypatch)

    effective, filters = pools.resolve_card_types(
        query_mode="knowledge",
        retrieval_stage="structured_recall",
        card_types=["term_card", "extract_card"],
        filters={"card_type": ["extract_card", "term_card"]},
    )

    assert effective == ["term_card", "extract_card"]
    assert filters == {}


def test_conflicting_explicit_and_legacy_card_types_are_rejected(monkeypatch):
    pools = _load_module(monkeypatch)

    with pytest.raises(ValueError, match="conflicting card type pools"):
        pools.resolve_card_types(
            query_mode="knowledge",
            retrieval_stage="structured_recall",
            card_types=["term_card"],
            filters={"card_type": ["fenjuan"]},
        )


def test_conflicting_book_id_aliases_are_rejected(monkeypatch):
    pools = _load_module(monkeypatch)

    with pytest.raises(ValueError, match="conflicting book identifiers"):
        pools.canonicalize_filters(
            {
                "book_id": "kaiyuan_zhanjing",
                "kb_book_id": "other_book",
            }
        )


def test_legacy_query_mode_pool_is_used_only_without_v2_stage_or_pool(monkeypatch):
    pools = _load_module(monkeypatch)

    evidence_types, _ = pools.resolve_card_types(
        query_mode="evidence",
        retrieval_stage=None,
        card_types=None,
        filters=None,
    )
    knowledge_types, _ = pools.resolve_card_types(
        query_mode="knowledge",
        retrieval_stage=None,
        card_types=None,
        filters=None,
    )

    assert evidence_types == ["fenjuan", "fulltext"]
    assert knowledge_types == [
        "xingguan_card",
        "zhusu_card",
        "term_card",
        "extract_card",
    ]


def test_invalid_stage_and_disallowed_prompt_assets_are_rejected(monkeypatch):
    pools = _load_module(monkeypatch)

    with pytest.raises(ValueError, match="retrieval_stage"):
        pools.resolve_card_types(
            query_mode="evidence",
            retrieval_stage="unknown",
            card_types=None,
            filters=None,
        )
    with pytest.raises(ValueError, match="not retrievable"):
        pools.resolve_card_types(
            query_mode="support",
            retrieval_stage=None,
            card_types=["prompt_asset"],
            filters=None,
        )
