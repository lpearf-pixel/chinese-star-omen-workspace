from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

import src.video_pipeline.feedback_loop.readonly_adapter_v1 as adapter_module
from src.connectors.evidence_resolver import EvidenceResolverContext, resolve_evidence
from src.connectors.primary_passage_cache import build_primary_source_snapshot
from src.video_pipeline.feedback_loop.readonly_adapter_v1 import (
    REJECTION_STATUSES,
    CanonicalExactHitV1,
    ValidatedTwoStageResultV1,
    project_citable_references,
    validate_two_stage_response,
)
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalEvidenceQueryPlanV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
)


COLLECTION = "test_vfl_ephemeral_task4"
CORPUS_VERSION = "20260903T010203Z"
BOOK_ID = "kaiyuan_zhanjing"
PROVENANCE = "c" * 64
RELATIVE_PATH = "古籍/唐開元占經/分卷/KR3g0018_031.md"
RAW_TEXT = "石氏曰熒惑守心。"
RAW_HASH = "sha256:491ab466667efbd8746a1feafcbb25e0baae29d1e40e49f3b958c081737f074f"
NORMALIZED_HASH = "sha256:267c1200d1f1830640b44eee66d177d06e5fd178639eff629e74cfb2ab987b46"
PAGE = "KR3g0018_WYG_031-17a"
LOCATOR = "KR3g0018_031"
CONTEXT = EvidenceResolverContext(
    source_root_label="task4-snapshot",
    ingest_source_label="task4-test",
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _plan() -> LocalEvidenceQueryPlanV1:
    return LocalEvidenceQueryPlanV1.model_validate(
        {
            "schema_version": "local-evidence-query-plan/v1",
            "plan_id": "plan:task4",
            "policy_version": "vfl-readonly-probe/1.0.0",
            "source_id": "source:task4",
            "audit_id": "audit:task4",
            "execution_scope": "hermetic_test",
            "collection": COLLECTION,
            "kb_book_id": BOOK_ID,
            "expected_corpus_version": CORPUS_VERSION,
            "requests": [
                {
                    "request_id": "request:one",
                    "source_id": "source:task4",
                    "audit_id": "audit:task4",
                    "claim_id": "claim:one",
                    "query": "熒惑守心",
                    "kb_book_id": BOOK_ID,
                    "query_mode": "evidence",
                    "top_k": 4,
                }
            ],
        }
    )


def _hit(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "chunk_id": "passage-31",
        "score": 0.98,
        "path": RELATIVE_PATH,
        "title": "KR3g0018_031.md",
        "snippet": "never-an-anchor",
        "card_type": "fenjuan",
        "kb_book_id": BOOK_ID,
        "book_title": "唐開元占經",
        "evidence_level": "primary",
        "status": "official",
        "match_type": "exact_raw",
        "source_locator": LOCATOR,
        "page_marker": PAGE,
        "heading_path": ["唐開元占經"],
        "paragraph_index": 0,
        "raw_start": 34,
        "raw_end": 42,
        "anchor_text": RAW_TEXT,
        "raw_content_hash": RAW_HASH,
        "normalized_content_hash": NORMALIZED_HASH,
    }
    value.update(changes)
    return value


def _stage_observability(
    stage: str,
    card_types: list[str],
    *,
    returned: int,
) -> dict[str, object]:
    return {
        "schema_version": "kb-observability/v1",
        "operation": "retrieve",
        "stage": stage,
        "latency_ms": 1.25,
        "upstream_latency_ms": 1.0,
        "requested_top_k": 4,
        "raw_pool_size": returned,
        "returned_pool_size": returned,
        "card_types": card_types,
        "collection": COLLECTION,
        "corpus_version": CORPUS_VERSION,
        "upstream_provenance_sha256": PROVENANCE,
        "corpus_provenance": "upstream_meta",
    }


def _response(
    *,
    hit: dict[str, object] | None = None,
    fallback: bool = False,
) -> dict[str, object]:
    primary_hit = _hit() if hit is None else hit
    structured_pool = ["zhusu_card", "term_card", "extract_card"]
    primary_pool = ["fenjuan", "fulltext"]
    official_hits: list[dict[str, object]] = [] if fallback else [primary_hit]
    stage2_hits = [primary_hit]
    official = {
        "schema_version": "kb-retrieve/v2",
        "query_mode": "evidence",
        "retrieval_stage": "primary_evidence",
        "card_types": primary_pool,
        "collection": COLLECTION,
        "filters": {"kb_book_id": BOOK_ID},
        "hits": official_hits,
        "exact_hits": official_hits,
        "related_hits": [],
        "raw_hits": official_hits,
        "inferred_hits": official_hits,
        "retrieved_count": len(official_hits),
        "latency_ms": 1,
        "observability": _stage_observability(
            "primary_evidence", primary_pool, returned=len(official_hits)
        ),
    }
    stage1 = {
        "schema_version": "kb-retrieve/v2",
        "query_mode": "evidence",
        "retrieval_stage": "structured_recall",
        "card_types": structured_pool,
        "collection": COLLECTION,
        "filters": {"kb_book_id": BOOK_ID},
        "hits": [],
        "exact_hits": [],
        "related_hits": [],
        "raw_hits": [],
        "inferred_hits": [],
        "retrieved_count": 0,
        "latency_ms": 1,
        "observability": _stage_observability(
            "structured_recall", structured_pool, returned=0
        ),
    }
    stage2 = {
        "schema_version": "kb-two-stage/v2",
        "source": "filesystem" if fallback else "official_qdrant",
        "official_result": official,
        "raw_hits": official_hits,
        "inferred_hits": stage2_hits,
        "query_mode": "evidence",
        "retrieval_stage": "primary_evidence",
        "card_types": primary_pool,
        "normalized_query": "熒惑守心",
        "query_variants": ["熒惑守心", "荧惑守心"],
        "exact_hits": stage2_hits,
        "related_hits": [],
        "hits": stage2_hits,
        "primary_candidates": stage2_hits,
        "candidate_overlay_hits": [],
        "structured_fallbacks": [],
        "official_primary_used": not fallback,
        "official_primary_empty": fallback,
        "fallback_used": fallback,
        "fallback_reason": "official_primary_empty" if fallback else None,
        "files_scanned": 1 if fallback else 0,
        "matched_files": [RELATIVE_PATH] if fallback else [],
        "matched_headings": ["唐開元占經"] if fallback else [],
        "matched_quotes": [RAW_TEXT] if fallback else [],
        "only_structured_no_primary": False,
    }
    outer_stages = [
        {**stage1["observability"], "source": "official_qdrant"},
        {**official["observability"], "source": "official_qdrant"},
    ]
    if fallback:
        outer_stages.append(
            {
                "schema_version": "kb-observability/v1",
                "operation": "filesystem_fallback",
                "stage": "primary_evidence",
                "source": "filesystem",
                "latency_ms": 0.75,
                "upstream_latency_ms": None,
                "requested_top_k": 4,
                "raw_pool_size": 1,
                "returned_pool_size": 1,
                "card_types": primary_pool,
                "collection": COLLECTION,
                "corpus_version": None,
                "fallback_reason": "official_primary_empty",
            }
        )
    return {
        "stage1": stage1,
        "stage2": stage2,
        "observability": {
            "schema_version": "kb-observability/v1",
            "operation": "two_stage_retrieve",
            "total_latency_ms": 3.0,
            "collection": COLLECTION,
            "corpus_version": CORPUS_VERSION,
            "upstream_provenance_sha256": PROVENANCE,
            "corpus_provenance": "upstream_meta",
            "provenance_conflicts": [],
            "fallback_reason": "official_primary_empty" if fallback else None,
            "stages": outer_stages,
        },
    }


def _set_path(value: dict[str, object], path: str, replacement: object) -> None:
    parts = path.split(".")
    target: dict[str, object] = value
    for part in parts[:-1]:
        target = target[part]  # type: ignore[assignment]
    if replacement is _DELETE:
        del target[parts[-1]]
    else:
        target[parts[-1]] = replacement


_DELETE = object()


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        ("stage1", _DELETE),
        ("stage2", _DELETE),
        ("observability", _DELETE),
        ("stage1.schema_version", _DELETE),
        ("stage1.schema_version", "kb-retrieve/v1"),
        ("stage1.query_mode", "knowledge"),
        ("stage1.retrieval_stage", "primary_evidence"),
        ("stage1.collection", "wrong"),
        ("stage1.filters", {"kb_book_id": "wrong"}),
        ("stage2.schema_version", "kb-two-stage/v1"),
        ("stage2.query_mode", "support"),
        ("stage2.retrieval_stage", "structured_recall"),
        ("stage2.official_result.schema_version", "kb-retrieve/v1"),
        ("stage2.official_result.query_mode", "knowledge"),
        ("stage2.official_result.retrieval_stage", "structured_recall"),
        ("stage2.official_result.collection", "wrong"),
        ("stage2.official_result.filters", {}),
        ("observability.schema_version", "kb-observability/v2"),
        ("observability.operation", "retrieve"),
        ("observability.provenance_conflicts", ["collection"]),
    ],
)
def test_envelope_rejects_each_missing_or_wrong_identity_field(
    path: str,
    replacement: object,
) -> None:
    """Catches accepting an incomplete or mismatched two-stage identity layer."""

    response = _response()
    _set_path(response, path, replacement)
    with pytest.raises(ReadOnlyAdapterError) as caught:
        validate_two_stage_response(response, request=_plan().requests[0], plan=_plan())
    assert caught.value.code is ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED
    assert caught.value.__cause__ is None


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        ("stage1.card_types", ["term_card", "zhusu_card", "extract_card"]),
        ("stage1.card_types", ["zhusu_card", "term_card"]),
        ("stage2.card_types", ["fulltext", "fenjuan"]),
        ("stage2.official_result.card_types", ["fenjuan", "fulltext", "term_card"]),
        ("stage2.candidate_overlay_hits", [{"status": "candidate_only"}]),
        ("stage2.official_primary_used", 1),
        ("stage2.fallback_used", 0),
        ("stage1.retrieved_count", True),
        ("stage1.latency_ms", float("nan")),
        ("observability.total_latency_ms", float("inf")),
    ],
)
def test_envelope_rejects_pool_status_count_and_finite_json_adversaries(
    path: str,
    replacement: object,
) -> None:
    """Catches card reordering, boolean coercion, overlay promotion, and NaN."""

    response = _response()
    _set_path(response, path, replacement)
    with pytest.raises(ReadOnlyAdapterError):
        validate_two_stage_response(response, request=_plan().requests[0], plan=_plan())


@pytest.mark.parametrize(
    "path",
    [
        "stage1.observability.upstream_latency_ms",
        "stage2.official_result.observability.upstream_latency_ms",
        "observability.fallback_reason",
    ],
)
def test_envelope_rejects_missing_nullable_observability_fields(path: str) -> None:
    """Catches treating an omitted contract-owned nullable field as explicit null."""

    response = _response()
    _set_path(response, path, _DELETE)
    with pytest.raises(ReadOnlyAdapterError):
        validate_two_stage_response(response, request=_plan().requests[0], plan=_plan())


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        ("stage2.raw_hits", []),
        ("stage2.inferred_hits", []),
        ("stage2.source", "none"),
        ("stage2.only_structured_no_primary", True),
    ],
)
def test_envelope_rejects_inconsistent_stage2_derived_fields(
    path: str,
    replacement: object,
) -> None:
    """Catches stage-2 pools and flags disagreeing with their validated owners."""

    response = _response()
    _set_path(response, path, replacement)
    with pytest.raises(ReadOnlyAdapterError):
        validate_two_stage_response(response, request=_plan().requests[0], plan=_plan())


@pytest.mark.parametrize(
    "path",
    [
        "stage1.observability.upstream_provenance_sha256",
        "stage2.official_result.observability.upstream_provenance_sha256",
        "observability.upstream_provenance_sha256",
        "stage1.observability.corpus_provenance",
        "stage2.official_result.observability.corpus_provenance",
        "observability.corpus_provenance",
        "stage1.observability.corpus_version",
        "stage2.official_result.observability.corpus_version",
        "observability.corpus_version",
    ],
)
def test_envelope_requires_exact_verified_provenance_at_every_layer(path: str) -> None:
    """Catches a stage using response-native/default or disagreeing provenance."""

    response = _response()
    replacement = "response_native" if path.endswith("corpus_provenance") else "d" * 64
    if path.endswith("corpus_version"):
        replacement = "20260903T010204Z"
    _set_path(response, path, replacement)
    with pytest.raises(ReadOnlyAdapterError):
        validate_two_stage_response(response, request=_plan().requests[0], plan=_plan())


@pytest.mark.parametrize(
    "path",
    [
        "stage1.observability",
        "stage2.official_result.observability",
        "observability",
    ],
)
@pytest.mark.parametrize("shape", ["alias_only", "both", "missing"])
def test_envelope_requires_only_the_mandated_upstream_provenance_key(
    path: str,
    shape: str,
) -> None:
    """Catches accepting a legacy alias or treating it as an additive field."""

    response = _response()
    target: dict[str, object] = response
    for part in path.split("."):
        target = target[part]  # type: ignore[assignment]
    value = target.pop("upstream_provenance_sha256")
    if shape in {"alias_only", "both"}:
        target["provenance_sha256"] = value
    if shape == "both":
        target["upstream_provenance_sha256"] = value
    with pytest.raises(ReadOnlyAdapterError):
        validate_two_stage_response(response, request=_plan().requests[0], plan=_plan())


@pytest.mark.parametrize("mutation", ["empty", "junk", "reordered", "mismatch"])
def test_outer_observability_stages_are_an_exact_ordered_transcript(
    mutation: str,
) -> None:
    """Catches accepting stages unrelated to the validated retrieval components."""

    response = _response()
    stages = response["observability"]["stages"]  # type: ignore[index]
    if mutation == "empty":
        response["observability"]["stages"] = []  # type: ignore[index]
    elif mutation == "junk":
        response["observability"]["stages"] = [{"junk": True}]  # type: ignore[index]
    elif mutation == "reordered":
        response["observability"]["stages"] = list(  # type: ignore[index, arg-type]
            reversed(stages)
        )
    else:
        stages[0]["latency_ms"] = 99.0  # type: ignore[index]
    with pytest.raises(ReadOnlyAdapterError):
        validate_two_stage_response(response, request=_plan().requests[0], plan=_plan())


@pytest.mark.parametrize("mutation", ["missing", "extra", "mismatch"])
def test_fallback_observability_stage_is_closed_and_mandatory(mutation: str) -> None:
    """Catches fallback execution without its exact ordered observability stage."""

    response = _response(fallback=True)
    stages = response["observability"]["stages"]  # type: ignore[index]
    if mutation == "missing":
        stages.pop()  # type: ignore[union-attr]
    elif mutation == "extra":
        stages[-1]["unexpected"] = "field"  # type: ignore[index]
    else:
        stages[-1]["returned_pool_size"] = 0  # type: ignore[index]
    with pytest.raises(ReadOnlyAdapterError):
        validate_two_stage_response(response, request=_plan().requests[0], plan=_plan())


@pytest.mark.parametrize(("left", "right"), [(True, 1), (1, 1.0)])
def test_missing_match_type_uses_canonical_bytes_not_python_equality(
    left: object,
    right: object,
) -> None:
    """Catches True==1 and 1==1.0 promoting a non-identical official hit."""

    response = _response()
    official_hit = response["stage2"]["official_result"]["exact_hits"][0]  # type: ignore[index]
    official_hit.pop("match_type")  # type: ignore[union-attr]
    official_hit["strict_value"] = left  # type: ignore[index]
    stage_hit = deepcopy(official_hit)
    stage_hit["strict_value"] = right
    response["stage2"]["exact_hits"] = [stage_hit]  # type: ignore[index]
    response["stage2"]["hits"] = [stage_hit]  # type: ignore[index]
    response["stage2"]["primary_candidates"] = [stage_hit]  # type: ignore[index]
    response["stage2"]["inferred_hits"] = [stage_hit]  # type: ignore[index]
    with pytest.raises(ReadOnlyAdapterError):
        validate_two_stage_response(response, request=_plan().requests[0], plan=_plan())


def test_official_missing_match_type_requires_exact_membership_and_no_fallback() -> None:
    """Catches inferring a missing match type outside the official exact pool."""

    response = _response()
    for pool in (
        response["stage2"]["official_result"]["hits"],  # type: ignore[index]
        response["stage2"]["official_result"]["exact_hits"],  # type: ignore[index]
        response["stage2"]["official_result"]["raw_hits"],  # type: ignore[index]
        response["stage2"]["official_result"]["inferred_hits"],  # type: ignore[index]
        response["stage2"]["hits"],  # type: ignore[index]
        response["stage2"]["exact_hits"],  # type: ignore[index]
        response["stage2"]["primary_candidates"],  # type: ignore[index]
        response["stage2"]["inferred_hits"],  # type: ignore[index]
    ):
        pool[0].pop("match_type", None)  # type: ignore[index, union-attr]
    validated = validate_two_stage_response(
        response, request=_plan().requests[0], plan=_plan()
    )
    assert validated.exact_candidate_count == 1

    fallback = _response(hit=_hit(match_type=None), fallback=True)
    with pytest.raises(ReadOnlyAdapterError):
        validate_two_stage_response(fallback, request=_plan().requests[0], plan=_plan())


def test_validator_bounds_every_list_and_canonicalizes_immutable_exact_hits() -> None:
    """Catches input order, duplicate mappings, and caller aliases entering state."""

    one = _hit(chunk_id="one")
    two = _hit(chunk_id="two", score=0.7)
    response = _response(hit=one)
    for key in ("hits", "exact_hits", "primary_candidates", "inferred_hits"):
        response["stage2"][key] = [two, deepcopy(one), deepcopy(two), one]  # type: ignore[index]
    official = response["stage2"]["official_result"]  # type: ignore[index]
    for key in ("hits", "exact_hits", "raw_hits", "inferred_hits"):
        official[key] = [one, two]
    response["stage2"]["raw_hits"] = [one, two]  # type: ignore[index]
    official["retrieved_count"] = 2
    official["observability"]["raw_pool_size"] = 2
    official["observability"]["returned_pool_size"] = 2
    response["observability"]["stages"][1] = {  # type: ignore[index]
        **official["observability"],
        "source": "official_qdrant",
    }

    validated = validate_two_stage_response(
        response, request=_plan().requests[0], plan=_plan()
    )
    before = validated.exact_hits
    assert isinstance(before, tuple)
    assert validated.exact_candidate_count == 2
    assert tuple(item.canonical_bytes for item in before) == tuple(
        sorted({_canonical(one), _canonical(two)})
    )
    response.clear()
    one.clear()
    two["chunk_id"] = "mutated"
    assert validated.exact_hits == before

    over = _response()
    over["stage2"]["related_hits"] = [  # type: ignore[index]
        _hit(chunk_id=str(i)) for i in range(5)
    ]
    with pytest.raises(ReadOnlyAdapterError):
        validate_two_stage_response(over, request=_plan().requests[0], plan=_plan())


class _MemoryLoader:
    def __init__(self, root: Path) -> None:
        path = root / RELATIVE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = f"# 唐開元占經\n<pb:{PAGE}>\n{RAW_TEXT}\n".encode("utf-8")
        path.write_bytes(raw)
        self.snapshot = build_primary_source_snapshot(
            raw,
            path=path,
            mtime_ns=1,
            card_type="fenjuan",
            kb_book_id=BOOK_ID,
            book_title="唐開元占經",
        )
        self.calls: list[tuple[object, dict[str, object]]] = []

    def load(self, path: str | Path, **kwargs: object):
        self.calls.append((path, kwargs))
        assert str(path) == RELATIVE_PATH
        return self.snapshot

    def relative_paths(self) -> tuple[str, ...]:
        return (RELATIVE_PATH,)


class _TwoPassageLoader:
    def __init__(self, root: Path) -> None:
        path = root / RELATIVE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (
            "# 唐開元占經\n"
            f"<pb:{PAGE}>\n{RAW_TEXT}\n"
            "<pb:KR3g0018_WYG_031-17b>\n太白犯東井。\n"
        ).encode("utf-8")
        path.write_bytes(raw)
        self.snapshot = build_primary_source_snapshot(
            raw,
            path=path,
            mtime_ns=1,
            card_type="fenjuan",
            kb_book_id=BOOK_ID,
            book_title="唐開元占經",
        )

    def load(self, path: str | Path, **kwargs: object):
        assert str(path) == RELATIVE_PATH
        return self.snapshot

    def relative_paths(self) -> tuple[str, ...]:
        return (RELATIVE_PATH,)


def _validated(hit: dict[str, object]) -> ValidatedTwoStageResultV1:
    return ValidatedTwoStageResultV1(
        observed_corpus_version=CORPUS_VERSION,
        upstream_provenance_sha256=PROVENANCE,
        corpus_provenance="upstream_meta",
        response_schema_versions=("kb-retrieve/v2", "kb-two-stage/v2", "kb-retrieve/v2"),
        exact_hits=(CanonicalExactHitV1(_canonical(hit)),),
        exact_candidate_count=1,
    )


def test_projector_uses_allowlisted_fields_and_real_snapshot_resolver(tmp_path: Path) -> None:
    """Catches copying candidate fields instead of revalidating the exact passage."""

    loader = _MemoryLoader(tmp_path)
    anchor_hash = "sha256:" + hashlib.sha256(RAW_TEXT.encode("utf-8")).hexdigest()
    hit = _hit(
        content_hash=anchor_hash,
        raw_content_hash=RAW_HASH,
        normalized_content_hash=NORMALIZED_HASH,
        unrelated_anchor="must be ignored",
    )
    result = project_citable_references(
        validated=_validated(hit),
        request=_plan().requests[0],
        kb_root=tmp_path,
        passage_loader=loader,
        resolver_context=CONTEXT,
        resolver=resolve_evidence,
    )
    assert result.rejection_counts == tuple((status, 0) for status in REJECTION_STATUSES)
    assert len(result.references) == 1
    reference = result.references[0]
    assert reference.evidence_class == "citable_passage"
    assert reference.relationship == "context_only"
    assert reference.note == "Semantic support or contradiction remains unreviewed."
    assert reference.evidence_locator == (
        "kaiyuan-passage:v1:KR3g0018_031:KR3g0018_WYG_031-17a:p0"
    )
    assert reference.evidence_sha256 == RAW_HASH.removeprefix("sha256:")


def test_absolute_and_relative_path_aliases_agree_after_confinement(tmp_path: Path) -> None:
    """Catches comparing deployed absolute and canonical relative aliases as raw strings."""

    loader = _MemoryLoader(tmp_path)
    hit = _hit(path=str((tmp_path / RELATIVE_PATH).resolve()), relative_path=RELATIVE_PATH)
    result = project_citable_references(
        validated=_validated(hit),
        request=_plan().requests[0],
        kb_root=tmp_path,
        passage_loader=loader,
        resolver_context=CONTEXT,
        resolver=resolve_evidence,
    )
    assert len(result.references) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"path": "../escape.md"},
        {"relative_path": RELATIVE_PATH, "source_path": "古籍/other/分卷/x.md"},
        {"source_locator": LOCATOR, "locator": "different"},
        {"anchor_text": RAW_TEXT, "quote": "different"},
        {"anchor_text": 7},
        {"raw_content_hash": "a" * 64},
        {"raw_content_hash": "sha256:" + "A" * 64},
        {"raw_content_hash": None, "normalized_content_hash": None},
        {"page_marker": ""},
        {"heading_path": ["ok", 7]},
        {"paragraph_index": True},
    ],
)
def test_candidate_local_projection_defects_omit_without_resolver_diagnostic(
    tmp_path: Path,
    changes: dict[str, object],
) -> None:
    """Catches unsafe hit-local aliases being promoted or persisted as diagnostics."""

    loader = _MemoryLoader(tmp_path)
    hit = _hit(**changes)
    calls = 0

    def forbidden(*args: object, **kwargs: object):
        nonlocal calls
        calls += 1
        raise AssertionError("candidate must be omitted before resolver")

    result = project_citable_references(
        validated=_validated(hit),
        request=_plan().requests[0],
        kb_root=tmp_path,
        passage_loader=loader,
        resolver_context=CONTEXT,
        resolver=forbidden,
    )
    assert calls == 0
    assert result.references == ()
    assert result.rejection_counts == tuple((status, 0) for status in REJECTION_STATUSES)


def test_missing_candidate_book_id_is_omitted_without_synthesis(tmp_path: Path) -> None:
    """Catches silently filling a missing candidate identity from the request."""

    loader = _MemoryLoader(tmp_path)
    hit = _hit()
    hit.pop("kb_book_id")
    result = project_citable_references(
        validated=_validated(hit),
        request=_plan().requests[0],
        kb_root=tmp_path,
        passage_loader=loader,
        resolver_context=CONTEXT,
        resolver=lambda *args, **kwargs: pytest.fail(
            "missing candidate identity reached resolver"
        ),
    )
    assert result.references == ()
    assert loader.calls == []


@pytest.mark.parametrize("status", REJECTION_STATUSES)
def test_known_non_citable_status_increments_only_its_aggregate(
    tmp_path: Path,
    status: str,
) -> None:
    """Catches a known resolver omission aborting or incrementing another bucket."""

    loader = _MemoryLoader(tmp_path)

    def resolver(*args: object, **kwargs: object) -> dict[str, object]:
        return {"status": status}

    result = project_citable_references(
        validated=_validated(_hit()),
        request=_plan().requests[0],
        kb_root=tmp_path,
        passage_loader=loader,
        resolver_context=CONTEXT,
        resolver=resolver,
    )
    assert result.references == ()
    assert dict(result.rejection_counts)[status] == 1
    assert sum(dict(result.rejection_counts).values()) == 1


@pytest.mark.parametrize("status", ["unknown", 7, None])
def test_unknown_or_malformed_resolver_status_aborts(tmp_path: Path, status: object) -> None:
    """Catches fail-open handling of a new or wrongly typed resolver status."""

    loader = _MemoryLoader(tmp_path)
    with pytest.raises(ReadOnlyAdapterError) as caught:
        project_citable_references(
            validated=_validated(_hit()),
            request=_plan().requests[0],
            kb_root=tmp_path,
            passage_loader=loader,
            resolver_context=CONTEXT,
            resolver=lambda *args, **kwargs: {"status": status},
        )
    assert caught.value.code is ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED


def test_snippet_only_official_hit_rehydrates_exact_unique_passage_boundary(
    tmp_path: Path,
) -> None:
    """Catches snippet promotion and verifies snapshot-only offset rehydration."""

    loader = _MemoryLoader(tmp_path)
    hit = _hit()
    hit.pop("anchor_text")
    hit.pop("match_type")
    seen: list[dict[str, object]] = []

    def recording_resolver(evidence: dict[str, object], *args: object, **kwargs: object):
        seen.append(deepcopy(evidence))
        return resolve_evidence(evidence, *args, **kwargs)

    result = project_citable_references(
        validated=_validated(hit),
        request=_plan().requests[0],
        kb_root=tmp_path,
        passage_loader=loader,
        resolver_context=CONTEXT,
        resolver=recording_resolver,
    )
    assert len(result.references) == 1
    assert seen[0]["anchor_text"] == RAW_TEXT
    assert "snippet" not in seen[0]
    assert "never-an-anchor" not in json.dumps(
        [item.model_dump(mode="json") for item in result.references],
        ensure_ascii=False,
    )


@pytest.mark.parametrize(
    ("raw_start", "raw_end"),
    [(None, 42), (34, None), (True, 42), (34, False), (-1, 42), (34, 34), (35, 42)],
)
def test_invalid_or_nonboundary_offsets_omit_candidate(
    tmp_path: Path,
    raw_start: object,
    raw_end: object,
) -> None:
    """Catches partial, boolean, negative, empty, or non-passage offset rehydration."""

    loader = _MemoryLoader(tmp_path)
    hit = _hit(raw_start=raw_start, raw_end=raw_end)
    hit.pop("anchor_text")
    hit.pop("match_type")
    result = project_citable_references(
        validated=_validated(hit),
        request=_plan().requests[0],
        kb_root=tmp_path,
        passage_loader=loader,
        resolver_context=CONTEXT,
        resolver=lambda *args, **kwargs: pytest.fail("invalid offset reached resolver"),
    )
    assert result.references == ()


def test_offset_rehydration_normalizes_loader_failure_to_integrity_error(
    tmp_path: Path,
) -> None:
    """Catches a source accessor failure escaping the typed adapter boundary."""

    loader = _MemoryLoader(tmp_path)

    def broken_load(*args: object, **kwargs: object):
        raise RuntimeError("private source detail")

    loader.load = broken_load  # type: ignore[method-assign]
    hit = _hit()
    hit.pop("anchor_text")
    hit.pop("match_type")
    with pytest.raises(ReadOnlyAdapterError) as caught:
        project_citable_references(
            validated=_validated(hit),
            request=_plan().requests[0],
            kb_root=tmp_path,
            passage_loader=loader,
            resolver_context=CONTEXT,
        )
    assert caught.value.code is ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_locator", None),
        ("page_marker", ""),
        ("paragraph_index", True),
        ("heading_path", ["ok", 7]),
        ("raw_content_hash", RAW_HASH.removeprefix("sha256:")),
        ("raw_content_hash", "hash:" + "a" * 64),
        ("raw_content_hash", "sha256:" + "A" * 64),
        ("source_locator", "wrong"),
        ("page_marker", "wrong"),
        ("paragraph_index", 1),
        ("heading_path", ["wrong"]),
        ("raw_content_hash", "sha256:" + "0" * 64),
    ],
)
def test_malformed_or_snapshot_inconsistent_citable_fields_abort_batch(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    """Catches trusting a fake citable resolver passage instead of the snapshot."""

    loader = _MemoryLoader(tmp_path)
    resolved: dict[str, object] = {
        "status": "citable",
        "source_locator": LOCATOR,
        "page_marker": PAGE,
        "paragraph_index": 0,
        "heading_path": ["唐開元占經"],
        "raw_content_hash": RAW_HASH,
    }
    resolved[field] = value
    with pytest.raises(ReadOnlyAdapterError):
        project_citable_references(
            validated=_validated(_hit()),
            request=_plan().requests[0],
            kb_root=tmp_path,
            passage_loader=loader,
            resolver_context=CONTEXT,
            resolver=lambda *args, **kwargs: resolved,
        )


def test_citable_replay_rejects_cross_passage_substitution(tmp_path: Path) -> None:
    """Catches replay accepting a real passage unrelated to projected evidence."""

    loader = _TwoPassageLoader(tmp_path)
    first, second = loader.snapshot.passages
    hit = _hit(
        source_locator=first.source_locator,
        page_marker=first.page_marker,
        paragraph_index=first.paragraph_index,
        heading_path=list(first.heading_path),
        anchor_text=first.raw_text,
        raw_content_hash=first.raw_content_hash,
        normalized_content_hash=first.normalized_content_hash,
    )
    substituted = {
        "status": "citable",
        "source_locator": second.source_locator,
        "page_marker": second.page_marker,
        "paragraph_index": second.paragraph_index,
        "heading_path": list(second.heading_path),
        "raw_content_hash": second.raw_content_hash,
    }
    with pytest.raises(ReadOnlyAdapterError) as caught:
        project_citable_references(
            validated=_validated(hit),
            request=_plan().requests[0],
            kb_root=tmp_path,
            passage_loader=loader,
            resolver_context=CONTEXT,
            resolver=lambda *args, **kwargs: substituted,
        )
    assert caught.value.code is ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED


def test_distinct_hits_resolving_to_same_passage_deduplicate_reference(
    tmp_path: Path,
) -> None:
    """Catches conflating exact candidate count with deduplicated citable count."""

    loader = _MemoryLoader(tmp_path)
    hits = (_hit(chunk_id="one"), _hit(chunk_id="two", score=0.7))
    validated = ValidatedTwoStageResultV1(
        observed_corpus_version=CORPUS_VERSION,
        upstream_provenance_sha256=PROVENANCE,
        corpus_provenance="upstream_meta",
        response_schema_versions=("kb-retrieve/v2", "kb-two-stage/v2", "kb-retrieve/v2"),
        exact_hits=tuple(CanonicalExactHitV1(_canonical(hit)) for hit in hits),
        exact_candidate_count=2,
    )
    result = project_citable_references(
        validated=validated,
        request=_plan().requests[0],
        kb_root=tmp_path,
        passage_loader=loader,
        resolver_context=CONTEXT,
        resolver=resolve_evidence,
    )
    assert validated.exact_candidate_count == 2
    assert len(result.references) == 1


def test_reference_id_collision_aborts_instead_of_deduplicating(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Catches one derived ID being reused for distinct passage tuples."""

    loader = _MemoryLoader(tmp_path)
    hit_one = _hit(chunk_id="one")
    hit_two = _hit(chunk_id="two", score=0.7)
    validated = ValidatedTwoStageResultV1(
        observed_corpus_version=CORPUS_VERSION,
        upstream_provenance_sha256=PROVENANCE,
        corpus_provenance="upstream_meta",
        response_schema_versions=("kb-retrieve/v2", "kb-two-stage/v2", "kb-retrieve/v2"),
        exact_hits=(
            CanonicalExactHitV1(_canonical(hit_one)),
            CanonicalExactHitV1(_canonical(hit_two)),
        ),
        exact_candidate_count=2,
    )
    monkeypatch.setattr(
        adapter_module,
        "_reference_id",
        lambda *args, **kwargs: "evidence:vfl:s1:collision",
    )

    calls = 0

    def resolver(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {
            "status": "citable",
            "source_locator": LOCATOR,
            "page_marker": PAGE,
            "paragraph_index": 0,
            "heading_path": ["唐開元占經"],
            "raw_content_hash": RAW_HASH,
        }

    replay_calls = 0

    def replay(*args: object, **kwargs: object):
        nonlocal replay_calls
        replay_calls += 1
        return (
            LOCATOR,
            PAGE,
            replay_calls - 1,
            ("唐開元占經",),
            RAW_HASH,
        )

    monkeypatch.setattr(adapter_module, "_validated_citable_tuple", replay)
    with pytest.raises(ReadOnlyAdapterError) as caught:
        project_citable_references(
            validated=validated,
            request=_plan().requests[0],
            kb_root=tmp_path,
            passage_loader=loader,
            resolver_context=CONTEXT,
            resolver=resolver,
        )
    assert caught.value.code is ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED
    assert calls == 2
    assert replay_calls == 2
