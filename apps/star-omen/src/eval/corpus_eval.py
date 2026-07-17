from __future__ import annotations

from pathlib import Path
from typing import Any

from src.connectors.kb_search_retriever import KBSearchRetriever

PRIMARY_TYPES = {"fenjuan", "fulltext"}
DEFAULT_POLLUTION_TYPES = {"prompt_asset", "nav", "qa_example"}
CITABLE_FIELDS = {
    "source_locator",
    "source_volume",
    "page_marker",
    "heading_path",
    "paragraph_index",
    "raw_start",
    "raw_end",
    "content_hash",
    "raw_content_hash",
    "normalized_content_hash",
    "managed_by",
    "collection_schema",
}


def _parse_scalar(raw: str) -> Any:
    value = raw.strip().strip('"')
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        return [item.strip().strip('"') for item in body.split(",")]
    return value


def load_eval_cases(path: Path) -> list[dict[str, Any]]:
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        cases = parsed.get("cases", []) if isinstance(parsed, dict) else []
        return [case for case in cases if isinstance(case, dict)]
    except Exception:
        cases: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line == "cases:":
                continue
            if line.startswith("- "):
                if current:
                    cases.append(current)
                current = {}
                line = line[2:]
            if ":" in line and current is not None:
                key, value = line.split(":", 1)
                current[key.strip()] = _parse_scalar(value)
        if current:
            cases.append(current)
        return cases


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _primary_hits(stage2: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key in ("hits", "primary_candidates", "exact_hits", "related_hits"):
        rows = stage2.get(key) or []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict) or row.get("card_type") not in PRIMARY_TYPES:
                continue
            identity = str(
                row.get("chunk_id")
                or row.get("source_locator")
                or row.get("path")
                or id(row)
            )
            if identity in seen:
                continue
            seen.add(identity)
            output.append(row)
    return output


def _all_outputs(stage1: dict[str, Any], stage2: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for stage in (stage1, stage2):
        for key in (
            "hits",
            "primary_candidates",
            "structured_fallbacks",
            "candidate_overlay_hits",
            "exact_hits",
            "related_hits",
        ):
            rows = stage.get(key) or []
            if isinstance(rows, list):
                output.extend(row for row in rows if isinstance(row, dict))
    return output


def _heading_contains(hit: dict[str, Any], expected: str) -> bool:
    if not expected:
        return True
    heading_path = hit.get("heading_path")
    if isinstance(heading_path, list):
        return any(expected in str(value) for value in heading_path)
    return expected in str(heading_path or "")


def _citable_fields_present(hit: dict[str, Any]) -> bool:
    if hit.get("final_citable") is not True:
        return False
    if not all(field in hit and hit.get(field) is not None for field in CITABLE_FIELDS):
        return False
    return (
        hit.get("managed_by") == "local-kb-unified/v2"
        and hit.get("collection_schema") == "passage-v2"
        and isinstance(hit.get("heading_path"), list)
    )


def run_corpus_eval(
    *,
    eval_path: Path = Path("eval/corpus_eval_cases.yaml"),
    retriever: KBSearchRetriever | None = None,
    collection: str | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    client = retriever or KBSearchRetriever()
    cases = load_eval_cases(eval_path)
    rows: list[dict[str, Any]] = []

    for case in cases:
        query = str(case.get("query") or "")
        expected_mode = str(
            case.get("expected_query_mode")
            or case.get("query_mode")
            or ""
        )
        legacy_case = not any(
            key in case
            for key in (
                "expected_query_mode",
                "expected_stage1_card_types",
                "expected_stage2_card_types",
                "must_use_official_primary",
                "expected_source_locator",
                "expected_page_marker",
                "expected_heading_contains",
                "require_final_citable",
            )
        )

        stage = client.two_stage_retrieve(
            query,
            collection=collection,
            top_k=top_k,
        )
        stage1 = stage.get("stage1", {}) if isinstance(stage, dict) else {}
        stage2 = stage.get("stage2", {}) if isinstance(stage, dict) else {}
        if not isinstance(stage1, dict):
            stage1 = {}
        if not isinstance(stage2, dict):
            stage2 = {}

        query_mode = str(stage1.get("query_mode") or "")
        mode_match = not expected_mode or query_mode == expected_mode

        expected_stage1 = _string_list(case.get("expected_stage1_card_types"))
        expected_stage2 = _string_list(case.get("expected_stage2_card_types"))
        actual_stage1 = _string_list(stage1.get("card_types"))
        actual_stage2 = _string_list(stage2.get("card_types"))
        stage1_pool_match = not expected_stage1 or actual_stage1 == expected_stage1
        stage2_pool_match = not expected_stage2 or actual_stage2 == expected_stage2

        primary_hits = _primary_hits(stage2)
        primary_hit = primary_hits[0] if primary_hits else {}
        has_primary = bool(primary_hits)
        expected_primary_type = str(case.get("expected_primary_card_type") or "")
        primary_card_type_match = (
            not expected_primary_type
            or primary_hit.get("card_type") == expected_primary_type
        )

        expected_path_contains = str(case.get("expected_top1_path_contains") or "")
        actual_top1_path = str(primary_hit.get("path") or "")
        if not actual_top1_path:
            top1 = (stage2.get("hits") or stage1.get("hits") or [None])[0] or {}
            if isinstance(top1, dict):
                actual_top1_path = str(top1.get("path") or "")
        top1_match = (
            expected_path_contains in actual_top1_path
            if expected_path_contains
            else True
        )

        official_primary_used = bool(stage2.get("official_primary_used"))
        fallback_used = bool(stage2.get("fallback_used"))
        must_use_official = bool(case.get("must_use_official_primary", False))
        allow_fallback = bool(case.get("allow_filesystem_fallback", True))
        must_hit_primary = bool(case.get("must_hit_primary", False))

        expected_locator = str(case.get("expected_source_locator") or "")
        expected_page = str(case.get("expected_page_marker") or "")
        expected_heading = str(case.get("expected_heading_contains") or "")
        source_locator_match = (
            not expected_locator
            or str(primary_hit.get("source_locator") or "") == expected_locator
        )
        page_marker_match = (
            not expected_page
            or str(primary_hit.get("page_marker") or "") == expected_page
        )
        heading_match = _heading_contains(primary_hit, expected_heading)

        require_citable = bool(case.get("require_final_citable", False))
        citable_fields_present = (
            _citable_fields_present(primary_hit)
            if require_citable
            else True
        )

        forbidden_types = set(
            _string_list(case.get("forbidden_card_types"))
            or DEFAULT_POLLUTION_TYPES
        )
        pollution_detected = any(
            str(hit.get("card_type") or "") in forbidden_types
            for hit in _all_outputs(stage1, stage2)
        )

        failure_reasons: list[str] = []
        if not mode_match:
            failure_reasons.append("query_mode_mismatch")
        if not stage1_pool_match:
            failure_reasons.append("stage1_pool_mismatch")
        if not stage2_pool_match:
            failure_reasons.append("stage2_pool_mismatch")
        if (must_hit_primary or expected_primary_type or expected_locator or expected_page) and not has_primary:
            failure_reasons.append("primary_evidence_missing")
        if must_use_official and not official_primary_used:
            failure_reasons.append("official_primary_required")
        if fallback_used and not allow_fallback:
            failure_reasons.append("filesystem_fallback_disallowed")
        if not primary_card_type_match:
            failure_reasons.append("primary_card_type_mismatch")
        if not source_locator_match:
            failure_reasons.append("source_locator_mismatch")
        if not page_marker_match:
            failure_reasons.append("page_marker_mismatch")
        if not heading_match:
            failure_reasons.append("heading_mismatch")
        if not citable_fields_present:
            failure_reasons.append("citable_fields_missing")
        if not top1_match:
            failure_reasons.append("top1_path_mismatch")
        if pollution_detected:
            failure_reasons.append("forbidden_card_type_pollution")

        rows.append(
            {
                "query": query,
                "legacy_case": legacy_case,
                "query_mode": query_mode,
                "expected_query_mode": expected_mode,
                "mode_match": mode_match,
                "expected_stage1_card_types": expected_stage1,
                "actual_stage1_card_types": actual_stage1,
                "stage1_pool_match": stage1_pool_match,
                "expected_stage2_card_types": expected_stage2,
                "actual_stage2_card_types": actual_stage2,
                "stage2_pool_match": stage2_pool_match,
                "must_use_official_primary": must_use_official,
                "official_primary_used": official_primary_used,
                "allow_filesystem_fallback": allow_fallback,
                "fallback_used": fallback_used,
                "expected_primary_card_type": expected_primary_type,
                "actual_primary_card_type": primary_hit.get("card_type"),
                "primary_card_type_match": primary_card_type_match,
                "must_hit_primary": must_hit_primary,
                "primary_hit": has_primary,
                "expected_source_locator": expected_locator,
                "actual_source_locator": primary_hit.get("source_locator"),
                "source_locator_match": source_locator_match,
                "expected_page_marker": expected_page,
                "actual_page_marker": primary_hit.get("page_marker"),
                "page_marker_match": page_marker_match,
                "expected_heading_contains": expected_heading,
                "actual_heading_path": primary_hit.get("heading_path"),
                "heading_match": heading_match,
                "require_final_citable": require_citable,
                "citable_fields_present": citable_fields_present,
                "expected_top1_path_contains": expected_path_contains,
                "actual_top1_path": actual_top1_path,
                "top1_match": top1_match,
                "pollution_detected": pollution_detected,
                "failure_reasons": failure_reasons,
                "pass": not failure_reasons,
            }
        )

    passed = sum(1 for row in rows if row["pass"])
    return {
        "schema_version": "corpus-eval/v2",
        "eval_path": str(eval_path),
        "total": len(rows),
        "passed": passed,
        "failed": len(rows) - passed,
        "all_passed": passed == len(rows),
        "rows": rows,
    }
