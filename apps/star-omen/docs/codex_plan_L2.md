# L2 research credibility

Goal: improve credibility of research reports with evidence grades, richer source references, counterevidence, score breakdowns, and review metadata.

Scope:
- Continue after L1 is complete.
- Do not change upstream ingest.
- Do not write Qdrant.
- Do not add a database.
- Do not build Web UI.
- Do not add large real historical data.

Tasks:

1. Keep evidence_status, but add omen_evidence_grade:
- A1_original_fulltext
- A2_structured_from_primary
- B1_structured_only
- B2_candidate_card
- C_missing

2. Add historical_evidence_grade:
- H1_official_history_primary
- H2_secondary_classical
- H3_modern_research
- H4_manual_note
- H5_missing

3. Enrich ResearchSourceRef with:
- id
- source_type
- title
- author
- dynasty_or_period
- juan
- chapter
- section
- locator
- original_date_text
- quote
- translation
- url
- citation
- reliability
- notes

source_type enum:
- official_history
- chronicle
- classical_text
- local_gazetteer
- modern_research
- database
- manual_note
- unknown

4. Add source rules:
- missing quote should warn;
- manual_note cannot grade higher than H4_manual_note;
- official_history or chronicle with quote or citation can conservatively grade higher.

5. Extend correlation with:
- case_type: positive, negative, ambiguous, control;
- counter_evidence_refs;
- alternative_explanations.

6. Add correlation_score_breakdown:
- temporal_score
- semantic_score
- source_score
- rule_match_score
- counter_evidence_score
- final_confidence

Do not automatically override human confidence.

7. Add review/version fields:
- review_status: draft, needs_sources, needs_date_check, reviewed, published, rejected;
- review_notes;
- reviewed_by;
- report_version;
- data_version;
- generated_at;
- source_hashes.

8. Update Markdown reports with:
- evidence grade overview;
- machine assessment;
- human research judgment;
- counterevidence and limitations;
- source refs.

9. Update case_index.json with:
- case_type
- omen_evidence_grade
- historical_evidence_grade
- review_status
- temporal_score
- semantic_score
- source_score
- rule_match_score
- counter_evidence_score
- has_counter_evidence
- has_alternative_explanations
- is_sample

Tests:
- manual note cannot grade above H4;
- candidate_only cannot silently become published;
- missing source refs warns or errors;
- illegal case_type errors;
- Markdown contains evidence grade overview, machine assessment, and counterevidence sections;
- index includes new fields.

Acceptance commands:

```bash
cd apps/star-omen
pytest -q
python -m src.cli validate-research-data --research-root data/research --rules-path data/processed/corpus/sample_rules.json
python -m src.cli generate-case-report --correlation-id corr_mars_xin_leadership_change_001 --research-root data/research --rules-path data/processed/corpus/sample_rules.json --out-dir data/research/case_reports
python -m src.cli build-research-index --research-root data/research
```

Final report should include modified files, new fields, grading rules, report sections, tests, acceptance results, and risks.
