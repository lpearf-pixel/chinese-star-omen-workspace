from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Literal, Mapping
from urllib.parse import quote

from kb_text_core import normalize_search_text

from src.connectors.evidence_resolver import EvidenceResolverContext, resolve_evidence
from src.connectors.primary_passage_cache import (
    PrimarySourceByteLoader,
    PrimarySourceSnapshot,
)
from src.video_pipeline.feedback_loop.contracts_v1 import LocalEvidenceReferenceV1
from src.video_pipeline.feedback_loop.readonly_contracts_v1 import (
    LocalEvidenceProbeRequestV1,
    LocalEvidenceQueryPlanV1,
    ReadOnlyAdapterError,
    ReadOnlyErrorCode,
)


STRUCTURED_CARD_TYPES = ("zhusu_card", "term_card", "extract_card")
PRIMARY_CARD_TYPES = ("fenjuan", "fulltext")
REJECTION_STATUSES = (
    "candidate_only",
    "source_outside_root",
    "missing_source",
    "book_mismatch",
    "card_type_mismatch",
    "locator_mismatch",
    "page_mismatch",
    "paragraph_mismatch",
    "heading_mismatch",
    "anchor_mismatch",
    "hash_mismatch",
)
_ALLOWED_EXACT_STATUSES = frozenset(("official", "citable", "primary"))
_EXACT_MATCH_TYPES = frozenset(("exact_raw", "exact_normalized"))
_PATH_ALIASES = ("relative_path", "source_path", "path")
_LOCATOR_ALIASES = ("source_locator", "locator")
_ANCHOR_ALIASES = ("anchor_text", "raw_text", "quote", "excerpt")
_HASH_FIELDS = ("content_hash", "raw_content_hash", "normalized_content_hash")
_SHA256_PREFIXED = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")
_NOTE = "Semantic support or contradiction remains unreviewed."
_SCHEMA_VERSIONS = ("kb-retrieve/v2", "kb-two-stage/v2", "kb-retrieve/v2")


@dataclass(frozen=True, slots=True)
class CanonicalExactHitV1:
    canonical_bytes: bytes

    def __post_init__(self) -> None:
        if type(self.canonical_bytes) is not bytes:
            raise TypeError("canonical_bytes must be bytes")


@dataclass(frozen=True, slots=True)
class ValidatedTwoStageResultV1:
    observed_corpus_version: str
    upstream_provenance_sha256: str
    corpus_provenance: Literal["upstream_meta"]
    response_schema_versions: tuple[str, ...]
    exact_hits: tuple[CanonicalExactHitV1, ...]
    exact_candidate_count: int

    def __post_init__(self) -> None:
        if (
            type(self.observed_corpus_version) is not str
            or not self.observed_corpus_version
            or not _SHA256_HEX.fullmatch(self.upstream_provenance_sha256)
            or self.corpus_provenance != "upstream_meta"
            or self.response_schema_versions != _SCHEMA_VERSIONS
            or type(self.exact_hits) is not tuple
            or any(type(item) is not CanonicalExactHitV1 for item in self.exact_hits)
            or type(self.exact_candidate_count) is not int
            or self.exact_candidate_count != len(self.exact_hits)
        ):
            raise ValueError("invalid validated two-stage result")


@dataclass(frozen=True, slots=True)
class ProjectionResultV1:
    references: tuple[LocalEvidenceReferenceV1, ...]
    rejection_counts: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        if (
            type(self.references) is not tuple
            or any(type(item) is not LocalEvidenceReferenceV1 for item in self.references)
            or self.rejection_counts
            != tuple(
                (status, dict(self.rejection_counts).get(status, -1))
                for status in REJECTION_STATUSES
            )
            or any(type(count) is not int or count < 0 for _, count in self.rejection_counts)
        ):
            raise ValueError("invalid projection result")


def _fail(code: ReadOnlyErrorCode) -> None:
    raise ReadOnlyAdapterError(code) from None


def _strict_json_copy(value: object) -> object:
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError
        return value
    if isinstance(value, Mapping):
        copied: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str or key in copied:
                raise ValueError
            copied[key] = _strict_json_copy(item)
        return copied
    if type(value) is list:
        return [_strict_json_copy(item) for item in value]
    raise ValueError


def _canonical_bytes(value: object) -> bytes:
    copied = _strict_json_copy(value)
    return json.dumps(
        copied,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError
    _strict_json_copy(value)
    return value


def _list(value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError
    return value


def _strict_nonnegative_int(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError
    return value


def _strict_nonnegative_number(value: object) -> int | float:
    if type(value) not in (int, float) or value < 0:
        raise ValueError
    if type(value) is float and not math.isfinite(value):
        raise ValueError
    return value


def _provenance_sha(observability: Mapping[str, object]) -> str:
    value = observability.get("upstream_provenance_sha256")
    if (
        "provenance_sha256" in observability
        or type(value) is not str
        or not _SHA256_HEX.fullmatch(value)
    ):
        raise ValueError
    return value


def _validate_observability(
    value: object,
    *,
    operation: str,
    collection: str,
    corpus_version: str,
    card_types: tuple[str, ...] | None = None,
    stage: str | None = None,
    top_k: int | None = None,
    raw_count: int | None = None,
    returned_count: int | None = None,
) -> str:
    observed = _mapping(value)
    if (
        observed.get("schema_version") != "kb-observability/v1"
        or observed.get("operation") != operation
        or observed.get("collection") != collection
        or observed.get("corpus_version") != corpus_version
        or observed.get("corpus_provenance") != "upstream_meta"
    ):
        raise ValueError
    if operation == "retrieve":
        if (
            observed.get("stage") != stage
            or observed.get("card_types") != list(card_types or ())
            or _strict_nonnegative_int(observed.get("requested_top_k")) != top_k
            or _strict_nonnegative_int(observed.get("raw_pool_size")) != raw_count
            or _strict_nonnegative_int(observed.get("returned_pool_size")) != returned_count
            or "upstream_latency_ms" not in observed
        ):
            raise ValueError
        _strict_nonnegative_number(observed.get("latency_ms"))
        upstream_latency = observed.get("upstream_latency_ms")
        if upstream_latency is not None:
            _strict_nonnegative_number(upstream_latency)
    else:
        _strict_nonnegative_number(observed.get("total_latency_ms"))
        if (
            observed.get("provenance_conflicts") != []
            or "fallback_reason" not in observed
            or (
                observed.get("fallback_reason") is not None
                and type(observed.get("fallback_reason")) is not str
            )
        ):
            raise ValueError
        stages = _list(observed.get("stages"))
        if any(not isinstance(item, Mapping) for item in stages):
            raise ValueError
    return _provenance_sha(observed)


def _hit_arrays(
    owner: Mapping[str, object],
    *,
    keys: tuple[str, ...],
    top_k: int,
    bounded: frozenset[str],
) -> dict[str, list[Mapping[str, object]]]:
    result: dict[str, list[Mapping[str, object]]] = {}
    for key in keys:
        values = _list(owner.get(key))
        if key in bounded and len(values) > top_k:
            raise ValueError
        rows = []
        for value in values:
            rows.append(_mapping(value))
        result[key] = rows
    return result


def _validate_card_types(rows: list[Mapping[str, object]], allowed: tuple[str, ...]) -> None:
    if any(row.get("card_type") not in allowed for row in rows):
        raise ValueError


def _validate_retrieve_stage(
    value: object,
    *,
    request: LocalEvidenceProbeRequestV1,
    plan: LocalEvidenceQueryPlanV1,
    retrieval_stage: str,
    card_types: tuple[str, ...],
) -> tuple[Mapping[str, object], dict[str, list[Mapping[str, object]]], str]:
    stage = _mapping(value)
    if (
        stage.get("schema_version") != "kb-retrieve/v2"
        or stage.get("query_mode") != "evidence"
        or stage.get("retrieval_stage") != retrieval_stage
        or stage.get("card_types") != list(card_types)
        or stage.get("collection") != plan.collection
        or _canonical_bytes(stage.get("filters"))
        != _canonical_bytes({"kb_book_id": request.kb_book_id})
    ):
        raise ValueError
    arrays = _hit_arrays(
        stage,
        keys=("hits", "exact_hits", "related_hits", "raw_hits", "inferred_hits"),
        top_k=request.top_k,
        bounded=frozenset(("hits", "exact_hits", "related_hits")),
    )
    for rows in arrays.values():
        _validate_card_types(rows, card_types)
    if (
        _strict_nonnegative_int(stage.get("retrieved_count")) != len(arrays["raw_hits"])
        or _strict_nonnegative_number(stage.get("latency_ms")) is None
    ):
        raise ValueError
    provenance = _validate_observability(
        stage.get("observability"),
        operation="retrieve",
        collection=plan.collection,
        corpus_version=plan.expected_corpus_version,
        card_types=card_types,
        stage=retrieval_stage,
        top_k=request.top_k,
        raw_count=len(arrays["raw_hits"]),
        returned_count=len(arrays["hits"]),
    )
    return stage, arrays, provenance


def _contains_bytes(pool: list[Mapping[str, object]], target: bytes) -> bool:
    return any(_canonical_bytes(item) == target for item in pool)


def _validate_outer_stages(
    outer: Mapping[str, object],
    *,
    stage1: Mapping[str, object],
    official: Mapping[str, object],
    fallback_used: bool,
    request: LocalEvidenceProbeRequestV1,
    plan: LocalEvidenceQueryPlanV1,
    files_scanned: int,
    returned_count: int,
) -> None:
    stage1_observability = _mapping(stage1.get("observability"))
    official_observability = _mapping(official.get("observability"))
    expected: list[Mapping[str, object]] = [
        {**stage1_observability, "source": "official_qdrant"},
        {**official_observability, "source": "official_qdrant"},
    ]
    stages = _list(outer.get("stages"))
    if fallback_used:
        if len(stages) != 3:
            raise ValueError
        fallback = _mapping(stages[2])
        if set(fallback) != {
            "schema_version",
            "operation",
            "stage",
            "source",
            "latency_ms",
            "upstream_latency_ms",
            "requested_top_k",
            "raw_pool_size",
            "returned_pool_size",
            "card_types",
            "collection",
            "corpus_version",
            "fallback_reason",
        }:
            raise ValueError
        if (
            fallback.get("schema_version") != "kb-observability/v1"
            or fallback.get("operation") != "filesystem_fallback"
            or fallback.get("stage") != "primary_evidence"
            or fallback.get("source") != "filesystem"
            or fallback.get("upstream_latency_ms") is not None
            or _strict_nonnegative_int(fallback.get("requested_top_k"))
            != request.top_k
            or _strict_nonnegative_int(fallback.get("raw_pool_size"))
            != files_scanned
            or _strict_nonnegative_int(fallback.get("returned_pool_size"))
            != returned_count
            or fallback.get("card_types") != list(PRIMARY_CARD_TYPES)
            or fallback.get("collection") != plan.collection
            or fallback.get("corpus_version") is not None
            or fallback.get("fallback_reason") != "official_primary_empty"
        ):
            raise ValueError
        _strict_nonnegative_number(fallback.get("latency_ms"))
        expected.append(fallback)
    if _canonical_bytes(stages) != _canonical_bytes(expected):
        raise ValueError


def _validate_response(
    response: Mapping[str, object],
    *,
    request: LocalEvidenceProbeRequestV1,
    plan: LocalEvidenceQueryPlanV1,
) -> ValidatedTwoStageResultV1:
    top = _mapping(response)
    stage1, stage1_arrays, stage1_provenance = _validate_retrieve_stage(
        top.get("stage1"),
        request=request,
        plan=plan,
        retrieval_stage="structured_recall",
        card_types=STRUCTURED_CARD_TYPES,
    )
    stage2 = _mapping(top.get("stage2"))
    if (
        stage2.get("schema_version") != "kb-two-stage/v2"
        or stage2.get("query_mode") != "evidence"
        or stage2.get("retrieval_stage") != "primary_evidence"
        or stage2.get("card_types") != list(PRIMARY_CARD_TYPES)
    ):
        raise ValueError
    official, official_arrays, official_provenance = _validate_retrieve_stage(
        stage2.get("official_result"),
        request=request,
        plan=plan,
        retrieval_stage="primary_evidence",
        card_types=PRIMARY_CARD_TYPES,
    )
    stage2_arrays = _hit_arrays(
        stage2,
        keys=(
            "hits",
            "exact_hits",
            "related_hits",
            "primary_candidates",
            "candidate_overlay_hits",
            "structured_fallbacks",
            "raw_hits",
            "inferred_hits",
        ),
        top_k=request.top_k,
        bounded=frozenset(
            (
                "hits",
                "exact_hits",
                "related_hits",
                "primary_candidates",
                "candidate_overlay_hits",
                "structured_fallbacks",
            )
        ),
    )
    for key in (
        "hits",
        "exact_hits",
        "related_hits",
        "primary_candidates",
        "raw_hits",
        "inferred_hits",
    ):
        _validate_card_types(stage2_arrays[key], PRIMARY_CARD_TYPES)
    if stage2_arrays["candidate_overlay_hits"]:
        raise ValueError
    for fallback in stage2_arrays["structured_fallbacks"]:
        if (
            fallback.get("card_type") not in STRUCTURED_CARD_TYPES
            or fallback.get("status") != "candidate_only"
        ):
            raise ValueError
    if [_canonical_bytes(item) for item in stage2_arrays["hits"]] != [
        _canonical_bytes(item) for item in stage2_arrays["primary_candidates"]
    ]:
        raise ValueError
    if [_canonical_bytes(item) for item in stage2_arrays["raw_hits"]] != [
        _canonical_bytes(item) for item in official_arrays["raw_hits"]
    ]:
        raise ValueError
    if [_canonical_bytes(item) for item in stage2_arrays["inferred_hits"]] != [
        _canonical_bytes(item) for item in stage2_arrays["primary_candidates"]
    ]:
        raise ValueError
    exact_bytes = [_canonical_bytes(item) for item in stage2_arrays["exact_hits"]]
    if any(not _contains_bytes(stage2_arrays["primary_candidates"], item) for item in exact_bytes):
        raise ValueError

    official_used = stage2.get("official_primary_used")
    official_empty = stage2.get("official_primary_empty")
    fallback_used = stage2.get("fallback_used")
    fallback_reason = stage2.get("fallback_reason")
    if (
        type(official_used) is not bool
        or type(official_empty) is not bool
        or type(fallback_used) is not bool
    ):
        raise ValueError
    if official_used:
        if (
            official_empty
            or fallback_used
            or fallback_reason is not None
            or stage2.get("source") != "official_qdrant"
            or not official_arrays["hits"]
            or {_canonical_bytes(item) for item in official_arrays["hits"]}
            != {_canonical_bytes(item) for item in stage2_arrays["primary_candidates"]}
        ):
            raise ValueError
    else:
        expected_source = (
            "filesystem" if stage2_arrays["primary_candidates"] else "none"
        )
        if (
            not official_empty
            or not fallback_used
            or fallback_reason != "official_primary_empty"
            or official_arrays["hits"]
            or official_arrays["exact_hits"]
            or stage2.get("source") != expected_source
        ):
            raise ValueError

    for hit, canonical in zip(stage2_arrays["exact_hits"], exact_bytes):
        if "status" in hit and hit.get("status") not in _ALLOWED_EXACT_STATUSES:
            raise ValueError
        if "match_type" in hit:
            if hit.get("match_type") not in _EXACT_MATCH_TYPES:
                raise ValueError
        elif not (
            official_used
            and not fallback_used
            and _contains_bytes(official_arrays["exact_hits"], canonical)
            and _contains_bytes(stage2_arrays["primary_candidates"], canonical)
        ):
            raise ValueError

    files_scanned = _strict_nonnegative_int(stage2.get("files_scanned"))
    for key in ("matched_files", "matched_headings", "matched_quotes", "query_variants"):
        values = _list(stage2.get(key))
        if any(type(item) is not str for item in values):
            raise ValueError
    expected_only_structured = bool(stage1_arrays["hits"]) and not bool(
        stage2_arrays["primary_candidates"]
    )
    if (
        type(stage2.get("normalized_query")) is not str
        or type(stage2.get("only_structured_no_primary")) is not bool
        or stage2.get("only_structured_no_primary") != expected_only_structured
    ):
        raise ValueError

    outer_provenance = _validate_observability(
        top.get("observability"),
        operation="two_stage_retrieve",
        collection=plan.collection,
        corpus_version=plan.expected_corpus_version,
    )
    outer = _mapping(top.get("observability"))
    if outer.get("fallback_reason") != fallback_reason:
        raise ValueError
    if len({stage1_provenance, official_provenance, outer_provenance}) != 1:
        raise ValueError
    _validate_outer_stages(
        outer,
        stage1=stage1,
        official=official,
        fallback_used=fallback_used,
        request=request,
        plan=plan,
        files_scanned=files_scanned,
        returned_count=len(stage2_arrays["primary_candidates"]),
    )
    canonical_hits = tuple(
        CanonicalExactHitV1(value)
        for value in sorted(set(exact_bytes))
    )
    return ValidatedTwoStageResultV1(
        observed_corpus_version=plan.expected_corpus_version,
        upstream_provenance_sha256=outer_provenance,
        corpus_provenance="upstream_meta",
        response_schema_versions=_SCHEMA_VERSIONS,
        exact_hits=canonical_hits,
        exact_candidate_count=len(canonical_hits),
    )


def validate_two_stage_response(
    response: Mapping[str, object],
    *,
    request: LocalEvidenceProbeRequestV1,
    plan: LocalEvidenceQueryPlanV1,
) -> ValidatedTwoStageResultV1:
    """Validate and freeze one complete S1 two-stage response."""

    result: ValidatedTwoStageResultV1 | None = None
    try:
        result = _validate_response(response, request=request, plan=plan)
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError):
        pass
    if result is None:
        _fail(ReadOnlyErrorCode.RESPONSE_CONTRACT_REJECTED)
    return result


def _canonical_relative_path(raw: str, *, root: Path) -> str | None:
    if not raw or raw.startswith("~") or "\\" in raw:
        return None
    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            resolved = candidate.resolve(strict=True)
            relative = resolved.relative_to(root)
        except (OSError, RuntimeError, ValueError):
            return None
        value = relative.as_posix()
    else:
        value = raw
    pure = PurePosixPath(value)
    if (
        not value
        or value.startswith("/")
        or "//" in value
        or pure.as_posix() != value
        or any(part in ("", ".", "..") for part in pure.parts)
    ):
        return None
    return value


def _agreed_alias(
    hit: Mapping[str, object],
    names: tuple[str, ...],
) -> str | None:
    values: list[str] = []
    for name in names:
        if name not in hit:
            continue
        value = hit[name]
        if type(value) is not str or not value:
            return None
        values.append(value)
    if not values or any(value != values[0] for value in values[1:]):
        return None
    return values[0]


def _projected_hit(
    hit: Mapping[str, object],
    *,
    request: LocalEvidenceProbeRequestV1,
    root: Path,
    passage_loader: PrimarySourceByteLoader,
) -> tuple[dict[str, object], object | None] | None:
    if hit.get("card_type") not in PRIMARY_CARD_TYPES:
        _fail(ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED)
    if "status" in hit and hit.get("status") not in _ALLOWED_EXACT_STATUSES:
        _fail(ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED)
    if "match_type" in hit and hit.get("match_type") not in _EXACT_MATCH_TYPES:
        _fail(ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED)
    if (
        type(hit.get("kb_book_id")) is not str
        or hit.get("kb_book_id") != request.kb_book_id
    ):
        return None

    paths: list[str] = []
    for name in _PATH_ALIASES:
        if name not in hit:
            continue
        raw = hit[name]
        if type(raw) is not str:
            return None
        normalized = _canonical_relative_path(raw, root=root)
        if normalized is None:
            return None
        paths.append(normalized)
    if not paths or any(value != paths[0] for value in paths[1:]):
        return None
    relative_path = paths[0]

    locator = None
    if any(name in hit for name in _LOCATOR_ALIASES):
        locator = _agreed_alias(hit, _LOCATOR_ALIASES)
        if locator is None:
            return None
    anchor = None
    if any(name in hit for name in _ANCHOR_ALIASES):
        anchor = _agreed_alias(hit, _ANCHOR_ALIASES)
        if anchor is None:
            return None

    hashes: dict[str, str] = {}
    for name in _HASH_FIELDS:
        if name not in hit:
            continue
        value = hit[name]
        if type(value) is not str or not _SHA256_PREFIXED.fullmatch(value):
            return None
        hashes[name] = value
    if not hashes:
        return None

    page = hit.get("page_marker")
    if page is not None and (type(page) is not str or not page):
        return None
    heading = hit.get("heading_path")
    if heading is not None and (
        type(heading) is not list or any(type(item) is not str for item in heading)
    ):
        return None
    paragraph = hit.get("paragraph_index")
    if paragraph is not None and (type(paragraph) is not int or paragraph < 0):
        return None

    loaded = None
    if anchor is None:
        if "match_type" in hit:
            return None
        raw_start = hit.get("raw_start")
        raw_end = hit.get("raw_end")
        if (
            type(raw_start) is not int
            or type(raw_end) is not int
            or raw_start < 0
            or raw_start >= raw_end
        ):
            return None
        loaded = _load_source_snapshot(
            passage_loader,
            relative_path,
            card_type=str(hit["card_type"]),
            kb_book_id=request.kb_book_id,
            book_title="唐開元占經",
        )
        passages = [
            item
            for item in loaded.passages
            if item.raw_start == raw_start and item.raw_end == raw_end
        ]
        if len(passages) != 1:
            return None
        passage = passages[0]
        if (
            (locator is not None and locator != passage.source_locator)
            or (page is not None and page != passage.page_marker)
            or (paragraph is not None and paragraph != passage.paragraph_index)
            or (heading is not None and heading != list(passage.heading_path))
        ):
            return None
        anchor = passage.raw_text
        anchor_hash = "sha256:" + hashlib.sha256(anchor.encode("utf-8")).hexdigest()
        if (
            (
                "content_hash" in hashes
                and hashes["content_hash"]
                not in (anchor_hash, passage.raw_content_hash)
            )
            or (
                "raw_content_hash" in hashes
                and hashes["raw_content_hash"] != passage.raw_content_hash
            )
            or (
                "normalized_content_hash" in hashes
                and hashes["normalized_content_hash"] != passage.normalized_content_hash
            )
        ):
            return None
        locator = passage.source_locator
        page = passage.page_marker
        paragraph = passage.paragraph_index
        heading = list(passage.heading_path)
    elif page is None:
        return None

    projected: dict[str, object] = {
        "relative_path": relative_path,
        "card_type": hit["card_type"],
        "kb_book_id": request.kb_book_id,
        "anchor_text": anchor,
        **hashes,
    }
    if locator is not None:
        projected["source_locator"] = locator
    if page is not None:
        projected["page_marker"] = page
    if paragraph is not None:
        projected["paragraph_index"] = paragraph
    if heading is not None:
        projected["heading_path"] = list(heading)
    if loaded is not None:
        projected["raw_start"] = passage.raw_start
        projected["raw_end"] = passage.raw_end
    return projected, loaded


def _load_source_snapshot(
    passage_loader: PrimarySourceByteLoader,
    path: str,
    *,
    card_type: str,
    kb_book_id: str,
    book_title: str,
) -> PrimarySourceSnapshot:
    loaded: PrimarySourceSnapshot | None = None
    failure_code: ReadOnlyErrorCode | None = None
    try:
        value = passage_loader.load(
            path,
            card_type=card_type,
            kb_book_id=kb_book_id,
            book_title=book_title,
        )
        if not isinstance(value, PrimarySourceSnapshot):
            raise TypeError
        loaded = value
    except ReadOnlyAdapterError as exc:
        failure_code = exc.code
    except Exception:
        failure_code = ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED
    if failure_code is not None:
        _fail(failure_code)
    if loaded is None:
        _fail(ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED)
    return loaded


def _call_resolver(
    resolver: Callable[..., Mapping[str, object]],
    evidence: dict[str, object],
    *,
    kb_root: Path,
    passage_loader: PrimarySourceByteLoader,
    resolver_context: EvidenceResolverContext,
) -> Mapping[str, object]:
    result: Mapping[str, object] | None = None
    failure_code: ReadOnlyErrorCode | None = None
    try:
        value = resolver(
            evidence,
            kb_root,
            passage_loader=passage_loader,
            resolver_context=resolver_context,
        )
        result = _mapping(value)
    except ReadOnlyAdapterError as exc:
        failure_code = exc.code
    except (Exception,):
        failure_code = ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED
    if failure_code is not None:
        _fail(failure_code)
    if result is None:
        _fail(ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED)
    return result


def _validated_citable_tuple(
    resolved: Mapping[str, object],
    *,
    projected: Mapping[str, object],
    passage_loader: PrimarySourceByteLoader,
) -> tuple[str, str, int, tuple[str, ...], str]:
    locator = resolved.get("source_locator")
    page = resolved.get("page_marker")
    paragraph = resolved.get("paragraph_index")
    heading = resolved.get("heading_path")
    raw_hash = resolved.get("raw_content_hash")
    if (
        type(locator) is not str
        or not locator
        or type(page) is not str
        or not page
        or type(paragraph) is not int
        or paragraph < 0
        or type(heading) is not list
        or any(type(item) is not str for item in heading)
        or type(raw_hash) is not str
        or not _SHA256_PREFIXED.fullmatch(raw_hash)
    ):
        _fail(ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED)
    loaded = _load_source_snapshot(
        passage_loader,
        str(projected["relative_path"]),
        card_type=str(projected["card_type"]),
        kb_book_id=str(projected["kb_book_id"]),
        book_title="唐開元占經",
    )
    projected_locator = projected.get("source_locator")
    projected_page = projected.get("page_marker")
    projected_paragraph = projected.get("paragraph_index")
    projected_heading = projected.get("heading_path")
    projected_anchor = projected.get("anchor_text")
    raw_start = projected.get("raw_start")
    raw_end = projected.get("raw_end")
    try:
        candidates = list(loaded.passages)
        if projected_locator is not None:
            candidates = [
                item
                for item in candidates
                if item.source_locator == projected_locator
            ]
        if projected_page is not None:
            candidates = [
                item for item in candidates if item.page_marker == projected_page
            ]
        if projected_paragraph is not None:
            candidates = [
                item
                for item in candidates
                if item.paragraph_index == projected_paragraph
            ]
        if projected_heading is not None:
            candidates = [
                item
                for item in candidates
                if tuple(item.heading_path) == tuple(projected_heading)
            ]
        if raw_start is not None or raw_end is not None:
            candidates = [
                item
                for item in candidates
                if item.raw_start == raw_start and item.raw_end == raw_end
            ]
        if type(projected_anchor) is not str or not projected_anchor:
            raise ValueError
        raw_anchor_matches = [
            item for item in candidates if projected_anchor in item.raw_text
        ]
        if raw_anchor_matches:
            candidates = raw_anchor_matches
        else:
            normalized_anchor = normalize_search_text(projected_anchor)
            candidates = [
                item
                for item in candidates
                if normalized_anchor
                and normalized_anchor in item.normalized_text
            ]
        anchor_hash = (
            "sha256:"
            + hashlib.sha256(projected_anchor.encode("utf-8")).hexdigest()
        )
        content_hash = projected.get("content_hash")
        projected_raw_hash = projected.get("raw_content_hash")
        projected_normalized_hash = projected.get("normalized_content_hash")
        candidates = [
            item
            for item in candidates
            if (
                content_hash is None
                or content_hash in (anchor_hash, item.raw_content_hash)
            )
            and (
                projected_raw_hash is None
                or projected_raw_hash == item.raw_content_hash
            )
            and (
                projected_normalized_hash is None
                or projected_normalized_hash == item.normalized_content_hash
            )
        ]
    except (AttributeError, TypeError, ValueError):
        _fail(ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED)
    if len(candidates) != 1:
        _fail(ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED)
    selected = candidates[0]
    if (
        selected.source_locator != locator
        or selected.page_marker != page
        or selected.paragraph_index != paragraph
        or tuple(selected.heading_path) != tuple(heading)
        or selected.raw_content_hash != raw_hash
    ):
        _fail(ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED)
    return locator, page, paragraph, tuple(heading), raw_hash


def _reference_id(
    *,
    claim_id: str,
    evidence_locator: str,
    evidence_sha256: str,
) -> str:
    digest = hashlib.sha256(
        _canonical_bytes(
            {
                "claim_id": claim_id,
                "evidence_locator": evidence_locator,
                "evidence_sha256": evidence_sha256,
            }
        )
    ).hexdigest()
    return f"evidence:vfl:s1:{digest}"


def project_citable_references(
    *,
    validated: ValidatedTwoStageResultV1,
    request: LocalEvidenceProbeRequestV1,
    kb_root: Path,
    passage_loader: PrimarySourceByteLoader,
    resolver_context: EvidenceResolverContext,
    resolver: Callable[..., Mapping[str, object]] = resolve_evidence,
) -> ProjectionResultV1:
    """Project immutable exact hits through the citable resolver."""

    try:
        root = Path(kb_root).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise ValueError
    except (OSError, RuntimeError, ValueError):
        _fail(ReadOnlyErrorCode.SOURCE_INTEGRITY_FAILED)
    counts = {status: 0 for status in REJECTION_STATUSES}
    references: dict[tuple[str, str, str], LocalEvidenceReferenceV1] = {}
    id_registry: dict[str, tuple[str, str, str]] = {}
    for wrapper in validated.exact_hits:
        decoded: object | None = None
        try:
            decoded = json.loads(wrapper.canonical_bytes.decode("utf-8"))
            hit = _mapping(decoded)
            if _canonical_bytes(hit) != wrapper.canonical_bytes:
                raise ValueError
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            _fail(ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED)
        projection = _projected_hit(
            hit,
            request=request,
            root=root,
            passage_loader=passage_loader,
        )
        if projection is None:
            continue
        evidence, _loaded = projection
        resolved = _call_resolver(
            resolver,
            evidence,
            kb_root=root,
            passage_loader=passage_loader,
            resolver_context=resolver_context,
        )
        status = resolved.get("status")
        if status in counts:
            counts[str(status)] += 1
            continue
        if status != "citable":
            _fail(ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED)
        locator, page, paragraph, _heading, raw_hash = _validated_citable_tuple(
            resolved,
            projected=evidence,
            passage_loader=passage_loader,
        )
        encoded_locator = (
            "kaiyuan-passage:v1:"
            f"{quote(locator, safe='-._~')}:"
            f"{quote(page, safe='-._~')}:p{paragraph}"
        )
        evidence_sha256 = raw_hash.removeprefix("sha256:")
        identity = (request.claim_id, encoded_locator, evidence_sha256)
        if identity in references:
            continue
        reference_id = _reference_id(
            claim_id=request.claim_id,
            evidence_locator=encoded_locator,
            evidence_sha256=evidence_sha256,
        )
        existing = id_registry.get(reference_id)
        if existing is not None and existing != identity:
            _fail(ReadOnlyErrorCode.EVIDENCE_PROJECTION_REJECTED)
        id_registry[reference_id] = identity
        references[identity] = LocalEvidenceReferenceV1(
            evidence_ref_id=reference_id,
            evidence_class="citable_passage",
            evidence_locator=encoded_locator,
            evidence_sha256=evidence_sha256,
            relationship="context_only",
            note=_NOTE,
        )
    ordered = tuple(
        sorted(
            references.values(),
            key=lambda item: (
                item.evidence_locator,
                item.evidence_sha256,
                item.evidence_ref_id,
            ),
        )
    )
    return ProjectionResultV1(
        references=ordered,
        rejection_counts=tuple((status, counts[status]) for status in REJECTION_STATUSES),
    )
