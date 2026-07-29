from __future__ import annotations

import copy
import math
import re
from pathlib import Path
from typing import Any, Literal, Mapping, Protocol, Sequence

from pydantic import Field

from src.connectors.evidence_resolver import resolve_evidence
from src.connectors.kb_contract import is_citable_evidence
from src.rule_engine.minimal_matcher import match_event_to_rules
from src.video_pipeline.contracts import (
    AstronomyEventV1,
    EvidenceReferenceV1,
    RuleAssessmentV1,
    RuleMatchV1,
)
from src.video_pipeline.contracts._common import StrictContractModel
from src.video_pipeline.evidence_bundle import (
    EvidenceBundleV1,
    EvidenceProjectionRecordV1,
    RuleRetrievalReportV1,
    build_evidence_bundle,
    stable_lineage_id,
)

_ALLOWED_MATCH_STATUSES = {
    "matched",
    "candidate_only",
    "insufficient_data",
    "partial_match",
    "not_matched",
}
_PRIMARY_CARD_TYPES = {"fenjuan", "fulltext"}
_EXACT_MATCH_TYPES = {"exact_raw", "exact_normalized"}
_STABLE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:/-]{0,159}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class TwoStageRetriever(Protocol):
    def two_stage_retrieve(self, query: str, **kwargs: Any) -> dict[str, Any]: ...


class AssessmentBuildResultV1(StrictContractModel):
    schema_version: Literal["rule-assessment-build-result/v1"] = (
        "rule-assessment-build-result/v1"
    )
    assessment: RuleAssessmentV1
    evidence_bundle: EvidenceBundleV1
    matcher_result: dict[str, Any] = Field(exclude=True, repr=False)
    evidence_records: list[EvidenceProjectionRecordV1]
    retrieval_reports: list[RuleRetrievalReportV1]


def _require_stable_id(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not _STABLE_ID_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a stable identifier")
    return normalized


def _utc_z(value: Any) -> str:
    text = value.isoformat()
    return text[:-6] + "Z" if text.endswith("+00:00") else text


def _measurement_value(event: AstronomyEventV1, kinds: set[str]) -> float | None:
    values = [item.value for item in event.measurements if item.kind in kinds]
    if len(values) > 1:
        raise ValueError(f"event has multiple measurements for {sorted(kinds)!r}")
    return values[0] if values else None


def event_to_matcher_input(event: AstronomyEventV1) -> dict[str, Any]:
    visibility = {
        "visible": True,
        "not_visible": False,
        "unknown": None,
    }[event.visibility.status]
    projected: dict[str, Any] = {
        "id": event.event_id,
        "datetime_utc": _utc_z(event.peak_utc),
        "body": event.primary_body,
        "event_type": event.event_type,
        "target_asterism": event.target_body_or_region,
        "related_asterisms": [event.target_body_or_region],
        "visibility": {"is_visible": visibility},
    }
    angular_distance = _measurement_value(
        event,
        {
            "angular-distance-deg",
            "angular-separation-deg",
            "angular_distance_deg",
        },
    )
    duration = _measurement_value(event, {"duration-days", "duration_days"})
    if angular_distance is not None:
        projected["angular_distance_deg"] = angular_distance
    if duration is not None:
        projected["duration_days"] = duration
    return projected


def _normalize_hash(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip().lower()
    if candidate.startswith("sha256:"):
        candidate = candidate[7:]
    return candidate if _HEX64_RE.fullmatch(candidate) else None


def _public_evidence_status(
    resolver_status: str,
    candidate_reason: str | None = None,
) -> str:
    if resolver_status == "citable":
        return "citable"
    if resolver_status == "candidate_only":
        return "candidate_only"
    if resolver_status in {"missing", "missing_evidence", "missing_source"}:
        return "missing_evidence"
    if candidate_reason in {"source_file_not_found", "missing_rule_evidence"}:
        return "missing_evidence"
    return "ambiguous"


def _retrieval_source(stage2: Mapping[str, Any]) -> str:
    if stage2.get("official_primary_used") is True:
        return "official_primary"
    if stage2.get("fallback_used") is True:
        return "filesystem_fallback"
    return "none"


def _stable_evidence_id(
    *,
    rule_id: str,
    status: str,
    source_locator: str | None,
    content_hash: str | None,
    resolver_status: str,
) -> str:
    return stable_lineage_id(
        "evidence",
        rule_id,
        status,
        source_locator or "",
        content_hash or "",
        resolver_status,
    )


def _record_from_resolved(
    *,
    rule_id: str,
    resolved: Mapping[str, Any],
    retrieval_source: str,
    forced_status: str | None = None,
) -> EvidenceProjectionRecordV1:
    resolver_status = str(resolved.get("status") or "missing_evidence")
    candidate_reason = (
        str(resolved.get("candidate_reason"))
        if resolved.get("candidate_reason") is not None
        else None
    )
    public_status = forced_status or _public_evidence_status(
        resolver_status,
        candidate_reason,
    )
    locator_value = resolved.get("source_locator")
    source_locator = (
        str(locator_value).strip()
        if isinstance(locator_value, str) and locator_value.strip()
        else None
    )
    content_hash = _normalize_hash(
        resolved.get("content_hash") or resolved.get("raw_content_hash")
    )
    if public_status == "missing_evidence":
        source_locator = None
        content_hash = None
    trace = resolved.get("trace") if isinstance(resolved.get("trace"), dict) else {}
    return EvidenceProjectionRecordV1(
        evidence_id=_stable_evidence_id(
            rule_id=rule_id,
            status=public_status,
            source_locator=source_locator,
            content_hash=content_hash,
            resolver_status=resolver_status,
        ),
        rule_id=rule_id,
        status=public_status,
        source_locator=source_locator,
        content_hash=content_hash,
        resolver_status=resolver_status,
        resolver_version=(
            str(trace.get("resolver_version"))
            if trace.get("resolver_version") is not None
            else None
        ),
        validation_version=(
            str(trace.get("validation_version"))
            if trace.get("validation_version") is not None
            else None
        ),
        retrieval_source=retrieval_source,
        blocking_reasons=[] if public_status == "citable" else [public_status],
    )


def _missing_record(
    rule_id: str,
    *,
    status: str = "missing_evidence",
    resolver_status: str = "missing_evidence",
    retrieval_source: str = "none",
) -> EvidenceProjectionRecordV1:
    return EvidenceProjectionRecordV1(
        evidence_id=_stable_evidence_id(
            rule_id=rule_id,
            status=status,
            source_locator=None,
            content_hash=None,
            resolver_status=resolver_status,
        ),
        rule_id=rule_id,
        status=status,
        source_locator=None,
        content_hash=None,
        resolver_status=resolver_status,
        retrieval_source=retrieval_source,
        blocking_reasons=[status],
    )


def _validate_rules(rules: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for rule in rules:
        if not isinstance(rule, Mapping):
            raise ValueError("each rule must be a mapping")
        row = copy.deepcopy(dict(rule))
        rule_id = _require_stable_id(row.get("id"), field_name="rule id")
        if rule_id in seen:
            raise ValueError(f"duplicate rule id {rule_id!r}")
        seen.add(rule_id)
        row["id"] = rule_id
        if not isinstance(row.get("trigger"), dict):
            raise ValueError(f"rule {rule_id!r} requires a trigger mapping")
        normalized.append(row)
    return normalized


def _candidate_rule_ids(matcher_result: Mapping[str, Any]) -> list[str]:
    rows = _validate_match_rows(matcher_result)
    return [row["rule_id"] for row in rows]


def _hit_to_evidence(hit: Mapping[str, Any], *, kb_book_id: str) -> dict[str, Any]:
    return {
        "kb_book_id": hit.get("kb_book_id") or hit.get("book_id") or kb_book_id,
        "book_title": hit.get("book_title"),
        "card_type": hit.get("card_type"),
        "evidence_level": "primary",
        "relative_path": hit.get("relative_path") or hit.get("source_path"),
        "source_locator": hit.get("source_locator") or hit.get("locator"),
        "source_volume": hit.get("source_volume") or hit.get("volume"),
        "page_marker": hit.get("page_marker"),
        "heading_path": hit.get("heading_path"),
        "paragraph_index": hit.get("paragraph_index"),
        "anchor_text": (
            hit.get("anchor_text")
            or hit.get("raw_text")
            or hit.get("quote")
            or hit.get("excerpt")
        ),
        "content_hash": hit.get("content_hash") or hit.get("raw_content_hash"),
        "raw_content_hash": hit.get("raw_content_hash"),
        "normalized_content_hash": hit.get("normalized_content_hash"),
    }


def _retrieve_rule_evidence(
    *,
    rule: dict[str, Any],
    retriever: TwoStageRetriever,
    kb_root: str | Path | None,
    default_kb_book_id: str,
) -> tuple[dict[str, Any] | None, RuleRetrievalReportV1, EvidenceProjectionRecordV1 | None]:
    rule_id = str(rule["id"])
    source_text = rule.get("source_text")
    if not isinstance(source_text, str) or not source_text.strip():
        report = RuleRetrievalReportV1(
            rule_id=rule_id,
            status="missing_evidence",
            exact_primary_count=0,
            candidate_overlay_count=0,
            official_primary_used=False,
            fallback_used=False,
            retrieval_source="none",
            resolver_status="missing_evidence",
        )
        return None, report, _missing_record(rule_id)
    embedded = rule.get("evidence") if isinstance(rule.get("evidence"), dict) else {}
    kb_book_id = _require_stable_id(
        embedded.get("kb_book_id")
        or embedded.get("book_id")
        or default_kb_book_id,
        field_name="kb book id",
    )
    result = retriever.two_stage_retrieve(
        source_text.strip(),
        top_k=8,
        filters={"kb_book_id": kb_book_id},
        query_mode="evidence",
        literal_first=True,
    )
    if not isinstance(result, dict):
        raise ValueError("two-stage retrieval result must be a mapping")
    stage2 = result.get("stage2")
    if not isinstance(stage2, dict):
        raise ValueError("two-stage retrieval stage2 must be a mapping")
    exact_hits = stage2.get("exact_hits", [])
    overlays = stage2.get("candidate_overlay_hits", [])
    if not isinstance(exact_hits, list):
        raise ValueError("stage2 exact_hits must be a list")
    if not isinstance(overlays, list):
        raise ValueError("stage2 candidate_overlay_hits must be a list")
    exact_primary = []
    for hit in exact_hits:
        if not isinstance(hit, dict) or hit.get("card_type") not in _PRIMARY_CARD_TYPES:
            continue
        match_type = hit.get("match_type")
        if match_type is not None and match_type not in _EXACT_MATCH_TYPES:
            continue
        exact_primary.append(dict(hit))
    source = _retrieval_source(stage2)
    common = {
        "rule_id": rule_id,
        "exact_primary_count": len(exact_primary),
        "candidate_overlay_count": len(overlays),
        "official_primary_used": stage2.get("official_primary_used") is True,
        "fallback_used": stage2.get("fallback_used") is True,
        "retrieval_source": source,
    }
    if len(exact_primary) > 1:
        report = RuleRetrievalReportV1(
            status="ambiguous_exact_primary",
            resolver_status="ambiguous_exact_primary",
            **common,
        )
        return None, report, _missing_record(
            rule_id,
            status="ambiguous",
            resolver_status="ambiguous_exact_primary",
            retrieval_source=source,
        )
    if not exact_primary:
        status = "candidate_overlay_only" if overlays else "no_exact_primary"
        report = RuleRetrievalReportV1(
            status=status,
            resolver_status="candidate_only",
            **common,
        )
        return None, report, _missing_record(
            rule_id,
            status="candidate_only",
            resolver_status=status,
            retrieval_source=source,
        )
    candidate = _hit_to_evidence(exact_primary[0], kb_book_id=kb_book_id)
    resolved = resolve_evidence(candidate, kb_root=kb_root)
    if is_citable_evidence(resolved):
        report = RuleRetrievalReportV1(
            status="hydrated_citable",
            resolver_status="citable",
            **common,
        )
        return candidate, report, None
    resolver_status = str(resolved.get("status") or "candidate_only")
    report = RuleRetrievalReportV1(
        status="resolver_rejected",
        resolver_status=resolver_status,
        **common,
    )
    return None, report, _record_from_resolved(
        rule_id=rule_id,
        resolved=resolved,
        retrieval_source=source,
        forced_status=_public_evidence_status(
            resolver_status,
            str(resolved.get("candidate_reason") or "") or None,
        ),
    )


def _prepare_candidate_rules(
    *,
    prepared_rules: list[dict[str, Any]],
    candidate_rule_ids: Sequence[str],
    kb_root: str | Path | None,
    retriever: TwoStageRetriever | None,
    default_kb_book_id: str,
) -> tuple[
    list[RuleRetrievalReportV1],
    dict[str, EvidenceProjectionRecordV1],
]:
    rules_by_id = {str(rule["id"]): rule for rule in prepared_rules}
    reports: list[RuleRetrievalReportV1] = []
    overrides: dict[str, EvidenceProjectionRecordV1] = {}
    for rule_id in candidate_rule_ids:
        rule = rules_by_id.get(rule_id)
        if rule is None:
            raise ValueError("initial matcher returned an unknown rule id")
        evidence = rule.get("evidence") if isinstance(rule.get("evidence"), dict) else None
        resolved = resolve_evidence(evidence, kb_root=kb_root) if evidence is not None else None
        if resolved is not None and is_citable_evidence(resolved):
            reports.append(
                RuleRetrievalReportV1(
                    rule_id=rule_id,
                    status="embedded_citable",
                    exact_primary_count=0,
                    candidate_overlay_count=0,
                    official_primary_used=False,
                    fallback_used=False,
                    retrieval_source="embedded_rule",
                    resolver_status="citable",
                )
            )
            continue
        if retriever is None:
            if resolved is None:
                reports.append(
                    RuleRetrievalReportV1(
                        rule_id=rule_id,
                        status="missing_evidence",
                        exact_primary_count=0,
                        candidate_overlay_count=0,
                        official_primary_used=False,
                        fallback_used=False,
                        retrieval_source="none",
                        resolver_status="missing_evidence",
                    )
                )
                overrides[rule_id] = _missing_record(rule_id)
            else:
                reports.append(
                    RuleRetrievalReportV1(
                        rule_id=rule_id,
                        status="embedded_non_citable",
                        exact_primary_count=0,
                        candidate_overlay_count=0,
                        official_primary_used=False,
                        fallback_used=False,
                        retrieval_source="embedded_rule",
                        resolver_status=str(resolved.get("status") or "candidate_only"),
                    )
                )
            continue
        hydrated, report, override = _retrieve_rule_evidence(
            rule=rule,
            retriever=retriever,
            kb_root=kb_root,
            default_kb_book_id=default_kb_book_id,
        )
        reports.append(report)
        if hydrated is not None:
            rule["evidence"] = hydrated
        elif override is not None:
            overrides[rule_id] = override
    return reports, overrides


def _record_for_rule(
    *,
    rule: Mapping[str, Any],
    kb_root: str | Path | None,
    report: RuleRetrievalReportV1,
    override: EvidenceProjectionRecordV1 | None,
) -> EvidenceProjectionRecordV1:
    if override is not None:
        return override
    rule_id = str(rule["id"])
    evidence = rule.get("evidence")
    if not isinstance(evidence, dict):
        return _missing_record(rule_id)
    return _record_from_resolved(
        rule_id=rule_id,
        resolved=resolve_evidence(evidence, kb_root=kb_root),
        retrieval_source=report.retrieval_source,
    )


def _condition_states(row: Mapping[str, Any] | None) -> dict[str, str]:
    if row is None:
        return {}
    raw = row.get("condition_states", {})
    if not isinstance(raw, dict):
        raise ValueError("matcher condition_states must be a mapping")
    states: dict[str, str] = {}
    for name, value in raw.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("matcher condition name must be a non-empty string")
        state = value.get("state") if isinstance(value, dict) else value
        if state not in {"pass", "fail", "unknown"}:
            raise ValueError(f"invalid condition state for {name!r}")
        states[name] = str(state)
    return dict(sorted(states.items()))


def _validate_match_rows(matcher_result: Mapping[str, Any]) -> list[dict[str, Any]]:
    if matcher_result.get("match_status", "not_matched") not in _ALLOWED_MATCH_STATUSES:
        raise ValueError("matcher top-level match_status is invalid")
    raw_rows = matcher_result.get("matches", [])
    if not isinstance(raw_rows, list):
        raise ValueError("matcher matches must be a list")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_rows:
        if not isinstance(raw, dict):
            raise ValueError("matcher rows must be mappings")
        row = dict(raw)
        rule_id = _require_stable_id(row.get("rule_id"), field_name="matcher rule id")
        if rule_id in seen:
            raise ValueError(f"duplicate matcher rule_id {rule_id!r}")
        seen.add(rule_id)
        status = row.get("match_status")
        if status not in _ALLOWED_MATCH_STATUSES:
            raise ValueError(f"matcher row {rule_id!r} has invalid status")
        score = row.get("match_score")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError(f"matcher row {rule_id!r} score must be numeric")
        score = float(score)
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            raise ValueError(f"matcher row {rule_id!r} score must be in [0,1]")
        row["rule_id"] = rule_id
        row["match_score"] = score
        rows.append(row)
    declared = matcher_result.get("matched_rule_ids")
    if declared is not None and (
        not isinstance(declared, list)
        or declared != [row["rule_id"] for row in rows]
    ):
        raise ValueError("matcher matched_rule_ids do not match rows")
    return rows


def _conflict_summary(
    matcher_result: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    reasons = matcher_result.get("conflict_reasons", [])
    if not isinstance(reasons, list):
        raise ValueError("matcher conflict_reasons must be a list")
    items = [str(reason) for reason in reasons]
    trace = matcher_result.get("conflict_trace", [])
    if not isinstance(trace, list):
        raise ValueError("matcher conflict_trace must be a list")
    for item in trace:
        if not isinstance(item, dict):
            raise ValueError("matcher conflict trace entries must be mappings")
        if item.get("status") == "manual_review":
            items.append(
                "manual_review:"
                + str(item.get("conflict_group") or "unknown")
                + ":"
                + str(item.get("provisional_rule_id") or "none")
            )
    for row in rows:
        if row.get("suppressed") is True:
            items.append(
                f"suppressed:{row['rule_id']}:{row.get('suppression_reason') or 'conflict'}"
            )
    return list(dict.fromkeys(items))


def project_matcher_result(
    *,
    event: AstronomyEventV1,
    rule_set_version: str,
    matcher_result: Mapping[str, Any],
    evidence_records: Sequence[EvidenceProjectionRecordV1],
    retrieval_reports: Sequence[RuleRetrievalReportV1],
) -> AssessmentBuildResultV1:
    rule_set_version = _require_stable_id(
        rule_set_version,
        field_name="rule set version",
    )
    if not isinstance(matcher_result, Mapping):
        raise ValueError("matcher result must be a mapping")
    if matcher_result.get("event_id") != event.event_id:
        raise ValueError("matcher event_id does not match AstronomyEvent")
    rows = _validate_match_rows(matcher_result)
    records_by_rule = {record.rule_id: record for record in evidence_records}
    if len(records_by_rule) != len(evidence_records):
        raise ValueError("evidence records must have unique rule IDs")
    if set(records_by_rule) != {row["rule_id"] for row in rows}:
        raise ValueError("evidence records must cover matcher rows exactly")
    report_rule_ids = [report.rule_id for report in retrieval_reports]
    if len(report_rule_ids) != len(set(report_rule_ids)):
        raise ValueError("retrieval reports must have unique rule IDs")
    if set(report_rule_ids) != set(records_by_rule):
        raise ValueError("retrieval reports must cover matcher rows exactly")

    public_matches = [
        RuleMatchV1(
            rule_id=row["rule_id"],
            status=row["match_status"],
            score=row["match_score"],
        )
        for row in rows
    ]
    row_by_id = {row["rule_id"]: row for row in rows}
    internal_recommended = matcher_result.get("recommended_rule_id")
    internal_provisional = matcher_result.get("provisional_recommended_rule_id")
    if internal_recommended is not None and internal_recommended not in row_by_id:
        raise ValueError("matcher recommended_rule_id is not in rows")
    if internal_provisional is not None and internal_provisional not in row_by_id:
        raise ValueError("matcher provisional recommendation is not in rows")
    focus = (
        row_by_id.get(str(internal_recommended))
        if internal_recommended is not None
        else row_by_id.get(str(internal_provisional))
        if internal_provisional is not None
        else rows[0]
        if rows
        else None
    )
    match_status = str(focus.get("match_status")) if focus else "not_matched"
    recommendation_status = str(
        matcher_result.get("recommendation_status") or "not_matched"
    )
    formal_rule_id: str | None = None
    if internal_recommended is not None:
        recommended_row = row_by_id[str(internal_recommended)]
        recommended_evidence = records_by_rule[str(internal_recommended)]
        if (
            recommendation_status == "selected"
            and recommended_row.get("match_status") == "matched"
            and recommended_row.get("suppressed") is not True
            and recommended_evidence.status == "citable"
        ):
            formal_rule_id = str(internal_recommended)
    provisional_rule_id: str | None = None
    if formal_rule_id is None:
        if internal_provisional is not None:
            provisional_rule_id = str(internal_provisional)
        elif internal_recommended is not None:
            provisional_rule_id = str(internal_recommended)

    evidence_references = [
        EvidenceReferenceV1(
            evidence_id=records_by_rule[row["rule_id"]].evidence_id,
            status=records_by_rule[row["rule_id"]].status,
            source_locator=records_by_rule[row["rule_id"]].source_locator,
            content_hash=records_by_rule[row["rule_id"]].content_hash,
        )
        for row in rows
    ]
    uncertainties: list[str] = []
    if not rows:
        uncertainties.append("no_matching_rule")
    uncertainties.extend(f"astronomy:{reason}" for reason in event.uncertainty_reasons)
    for name, state in _condition_states(focus).items():
        if state != "pass":
            uncertainties.append(f"condition:{name}:{state}")
    for record in evidence_records:
        if record.status != "citable":
            uncertainties.append(f"evidence:{record.status}")
    for report in retrieval_reports:
        if report.status not in {"embedded_citable", "hydrated_citable"}:
            uncertainties.append(f"retrieval:{report.status}")
    if recommendation_status == "manual_review":
        uncertainties.append("conflict:manual_review")
    if rows and formal_rule_id is None:
        uncertainties.append("formal_recommendation_unavailable")

    assessment_id = stable_lineage_id(
        "assessment",
        event.event_id,
        rule_set_version,
    )
    assessment = RuleAssessmentV1(
        schema_version="rule-assessment/v1",
        assessment_id=assessment_id,
        event_id=event.event_id,
        rule_set_version=rule_set_version,
        matched_rules=public_matches,
        condition_states=_condition_states(focus),
        match_status=match_status,
        conflict_summary=_conflict_summary(matcher_result, rows),
        recommended_rule_id=formal_rule_id,
        provisional_rule_id=provisional_rule_id,
        evidence_references=evidence_references,
        narration_eligibility="eligible" if formal_rule_id else "blocked",
        uncertainty_reasons=sorted(set(uncertainties)),
    )
    return AssessmentBuildResultV1(
        assessment=assessment,
        evidence_bundle=build_evidence_bundle(assessment, evidence_records),
        matcher_result=copy.deepcopy(dict(matcher_result)),
        evidence_records=list(evidence_records),
        retrieval_reports=list(retrieval_reports),
    )


def build_rule_assessment_result(
    *,
    event: AstronomyEventV1,
    rules: Sequence[Mapping[str, Any]],
    rule_set_version: str,
    kb_root: str | Path | None = None,
    retriever: TwoStageRetriever | None = None,
    default_kb_book_id: str = "kaiyuan_zhanjing",
) -> AssessmentBuildResultV1:
    prepared = _validate_rules(rules)
    matcher_input = event_to_matcher_input(event)
    initial_matcher = match_event_to_rules(
        event=matcher_input,
        rules=prepared,
        kb_root=kb_root,
    )
    candidate_ids = _candidate_rule_ids(initial_matcher)
    reports, overrides = _prepare_candidate_rules(
        prepared_rules=prepared,
        candidate_rule_ids=candidate_ids,
        kb_root=kb_root,
        retriever=retriever,
        default_kb_book_id=default_kb_book_id,
    )
    final_matcher = match_event_to_rules(
        event=matcher_input,
        rules=prepared,
        kb_root=kb_root,
    )
    final_ids = _candidate_rule_ids(final_matcher)
    if final_ids != candidate_ids:
        raise ValueError("evidence hydration changed the candidate rule set")

    reports_by_rule = {report.rule_id: report for report in reports}
    prepared_by_rule = {str(rule["id"]): rule for rule in prepared}
    records = [
        _record_for_rule(
            rule=prepared_by_rule[rule_id],
            kb_root=kb_root,
            report=reports_by_rule[rule_id],
            override=overrides.get(rule_id),
        )
        for rule_id in final_ids
    ]
    return project_matcher_result(
        event=event,
        rule_set_version=rule_set_version,
        matcher_result=final_matcher,
        evidence_records=records,
        retrieval_reports=reports,
    )


def build_rule_assessment(
    *,
    event: AstronomyEventV1,
    rules: Sequence[Mapping[str, Any]],
    rule_set_version: str,
    kb_root: str | Path | None = None,
    retriever: TwoStageRetriever | None = None,
    default_kb_book_id: str = "kaiyuan_zhanjing",
) -> RuleAssessmentV1:
    return build_rule_assessment_result(
        event=event,
        rules=rules,
        rule_set_version=rule_set_version,
        kb_root=kb_root,
        retriever=retriever,
        default_kb_book_id=default_kb_book_id,
    ).assessment


__all__ = [
    "AssessmentBuildResultV1",
    "TwoStageRetriever",
    "build_rule_assessment",
    "build_rule_assessment_result",
    "event_to_matcher_input",
    "project_matcher_result",
]
