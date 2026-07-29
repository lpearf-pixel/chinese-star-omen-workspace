from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.video_pipeline.contracts import AstronomyEventV1, RuleAssessmentV1

from . import rule_assessment_impl as _base

AssessmentBuildResultV1 = _base.AssessmentBuildResultV1
TwoStageRetriever = _base.TwoStageRetriever
event_to_matcher_input = _base.event_to_matcher_input
project_matcher_result = _base.project_matcher_result

_ALLOWED_EXPLICIT_HIT_STATUSES = {None, "official", "citable", "primary"}


class _ValidatedTwoStageRetriever:
    def __init__(self, inner: TwoStageRetriever):
        self.inner = inner

    def two_stage_retrieve(self, query: str, **kwargs: Any) -> dict[str, Any]:
        result = self.inner.two_stage_retrieve(query, **kwargs)
        if not isinstance(result, dict):
            raise ValueError("two-stage retrieval result must be a mapping")
        stage2 = result.get("stage2")
        if not isinstance(stage2, dict):
            raise ValueError("two-stage retrieval stage2 must be a mapping")
        exact_hits = stage2.get("exact_hits", [])
        primary_candidates = stage2.get("primary_candidates", [])
        if not isinstance(exact_hits, list):
            raise ValueError("stage2 exact_hits must be a list")
        if not isinstance(primary_candidates, list):
            raise ValueError("stage2 primary_candidates must be a list")

        official_used = stage2.get("official_primary_used") is True
        fallback_used = stage2.get("fallback_used") is True
        if official_used and fallback_used:
            raise ValueError("conflicting official/fallback retrieval provenance")

        primary_rows = [item for item in primary_candidates if isinstance(item, dict)]
        filtered: list[dict[str, Any]] = []
        for raw in exact_hits:
            if not isinstance(raw, dict):
                continue
            if raw.get("card_type") not in _base._PRIMARY_CARD_TYPES:
                continue
            match_type = raw.get("match_type")
            if match_type is not None and match_type not in _base._EXACT_MATCH_TYPES:
                continue
            if raw.get("status") not in _ALLOWED_EXPLICIT_HIT_STATUSES:
                continue
            if not any(raw == candidate for candidate in primary_rows):
                raise ValueError("exact hit is not present in primary candidate set")
            filtered.append(copy.deepcopy(raw))

        if filtered and not (official_used or fallback_used):
            raise ValueError(
                "exact primary retrieval hit lacks official/fallback provenance"
            )

        normalized = copy.deepcopy(result)
        normalized_stage2 = dict(normalized["stage2"])
        normalized_stage2["exact_hits"] = filtered
        normalized["stage2"] = normalized_stage2
        return normalized


def _prepare_candidate_rules(
    *,
    prepared_rules: list[dict[str, Any]],
    candidate_rows: Sequence[Mapping[str, Any]],
    kb_root: str | Path | None,
    retriever: TwoStageRetriever | None,
    default_kb_book_id: str,
) -> tuple[
    list[_base.RuleRetrievalReportV1],
    dict[str, _base.EvidenceProjectionRecordV1],
]:
    validated_retriever = (
        _ValidatedTwoStageRetriever(retriever) if retriever is not None else None
    )
    reports: list[_base.RuleRetrievalReportV1] = []
    overrides: dict[str, _base.EvidenceProjectionRecordV1] = {}
    for row in candidate_rows:
        rule_id = str(row["rule_id"])
        external = (
            validated_retriever
            if row.get("match_status") == "candidate_only"
            else None
        )
        row_reports, row_overrides = _base._prepare_candidate_rules(
            prepared_rules=prepared_rules,
            candidate_rule_ids=[rule_id],
            kb_root=kb_root,
            retriever=external,
            default_kb_book_id=default_kb_book_id,
        )
        reports.extend(row_reports)
        overrides.update(row_overrides)
    return reports, overrides


def build_rule_assessment_result(
    *,
    event: AstronomyEventV1,
    rules: Sequence[Mapping[str, Any]],
    rule_set_version: str,
    kb_root: str | Path | None = None,
    retriever: TwoStageRetriever | None = None,
    default_kb_book_id: str = "kaiyuan_zhanjing",
) -> AssessmentBuildResultV1:
    rule_set_version = _base._require_stable_id(
        rule_set_version,
        field_name="rule set version",
    )
    default_kb_book_id = _base._require_stable_id(
        default_kb_book_id,
        field_name="kb book id",
    )
    prepared = _base._validate_rules(rules)
    matcher_input = _base.event_to_matcher_input(event)
    initial_matcher = _base.match_event_to_rules(
        event=matcher_input,
        rules=prepared,
        kb_root=kb_root,
    )
    candidate_rows = _base._validate_match_rows(initial_matcher)
    candidate_ids = [row["rule_id"] for row in candidate_rows]
    reports, overrides = _prepare_candidate_rules(
        prepared_rules=prepared,
        candidate_rows=candidate_rows,
        kb_root=kb_root,
        retriever=retriever,
        default_kb_book_id=default_kb_book_id,
    )
    final_matcher = _base.match_event_to_rules(
        event=matcher_input,
        rules=prepared,
        kb_root=kb_root,
    )
    final_ids = _base._candidate_rule_ids(final_matcher)
    if set(final_ids) != set(candidate_ids):
        raise ValueError("evidence hydration changed the candidate rule set")

    reports_by_rule = {report.rule_id: report for report in reports}
    if set(reports_by_rule) != set(final_ids):
        raise ValueError("retrieval reports do not cover final candidate rules")
    prepared_by_rule = {str(rule["id"]): rule for rule in prepared}
    records = [
        _base._record_for_rule(
            rule=prepared_by_rule[rule_id],
            kb_root=kb_root,
            report=reports_by_rule[rule_id],
            override=overrides.get(rule_id),
        )
        for rule_id in final_ids
    ]
    ordered_reports = [reports_by_rule[rule_id] for rule_id in final_ids]
    return _base.project_matcher_result(
        event=event,
        rule_set_version=rule_set_version,
        matcher_result=final_matcher,
        evidence_records=records,
        retrieval_reports=ordered_reports,
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
