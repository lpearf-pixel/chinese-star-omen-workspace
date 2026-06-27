from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ModernIdentification(BaseModel):
    star_name: str
    catalog: str
    catalog_id: str | int | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    notes: str | None = None


class Asterism(BaseModel):
    id: str
    name_cn: str
    system_version: Literal["pre_qin", "han", "jin", "tang", "song", "ming", "qing", "modern_reconstruction"]
    region: Literal["san_yuan", "er_shi_ba_xiu", "other"]
    modern_identifications: list[ModernIdentification]
    source_refs: list[str]
    aliases: list[str] = []
    parent_region: str | None = None
    anchor_star: str | None = None
    notes: str | None = None


class Evidence(BaseModel):
    kb_book_id: str | None = None
    note_id: str | None = None
    relative_path: str | None = None
    card_type: str | None = None
    locator: str | None = None
    anchor_heading: str | None = None
    quote: str | None = None
    manifest_ref: str | None = None
    evidence_level: str | None = None


class Trigger(BaseModel):
    body: str
    event_type: str
    target: str | None = None
    qualifiers: list[str] = []


class OmenRule(BaseModel):
    id: str
    source_text: str
    source_book: str
    trigger: Trigger
    effect_domain: list[Literal["politics", "leadership", "military", "agriculture", "climate", "economy", "public_health", "ritual", "border", "general_omen"]]
    validation_status: Literal["unverified", "partially_verified", "historically_attested", "disputed"]
    source_chapter: str | None = None
    evidence: Evidence | None = None
    severity: Literal["low", "medium", "high", "critical"] | None = None
    time_window: str | None = None
    interpretation: str | None = None
    modern_translation: str | None = None
    linked_cases: list[str] = []
    notes: str | None = None


class CelestialEvent(BaseModel):
    id: str
    datetime_utc: str
    body: str
    event_type: str
    epoch: str


class BacktestRecord(BaseModel):
    id: str
    event_id: str
    matched_rules: list[str]
    review_status: Literal["auto_generated", "manual_reviewed", "rejected", "needs_more_evidence"]


class SourceRef(BaseModel):
    title: str | None = None
    citation: str | None = None
    url: str | None = None
    note: str | None = None


class HistoricalEvent(BaseModel):
    id: str
    title: str
    date_start: str | None = None
    date_end: str | None = None
    date_precision: Literal["day", "month", "year", "range", "unknown"]
    calendar_system: Literal["gregorian", "julian", "chinese_lunisolar", "unknown"]
    source_date_text: str | None = None
    calendar_note: str | None = None
    dynasty: str | None = None
    reign_period: str | None = None
    location: str | None = None
    domains: list[str] = Field(default_factory=list)
    summary: str
    details: str | None = None
    source_refs: list[SourceRef] = Field(default_factory=list)
    certainty: Literal["high", "medium", "low"]
    notes: str | None = None


class CelestialHistoricalCorrelation(BaseModel):
    id: str
    celestial_event_id: str
    historical_event_id: str
    matched_rule_ids: list[str] = Field(default_factory=list)
    time_delta_days: int | None = None
    relation_type: Literal["within_rule_window", "same_record", "later_interpretation", "manual_hypothesis", "rejected"]
    confidence: Literal["high", "medium", "low"]
    status: Literal["draft", "reviewed", "published", "rejected"]
    evidence_status: Literal["primary_citable", "candidate_only", "missing"]
    caveats: list[str] = Field(default_factory=list)
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CaseReport(BaseModel):
    id: str
    title: str
    celestial_event: dict
    historical_events: list[dict]
    correlations: list[dict]
    matched_rules: list[dict]
    evidence_summary: dict
    machine_assessment: dict
    human_assessment: dict
    conclusion: str
    limitations: list[str]
    generated_at: str
    report_version: str
