# L3 group reports

Goal: support multi-correlation and group reports without breaking single-correlation reports.

Use cases:
- one celestial event linked to multiple historical events;
- one historical event linked to multiple celestial events;
- correlations grouped by rule, dynasty, or custom selection.

Scope:
- Continue after L1 and L2 are complete.
- Do not change upstream ingest.
- Do not write Qdrant.
- Do not add a database.
- Do not build Web UI in this stage.

Tasks:

1. Add GroupReport model with:
- id
- title
- group_type
- group_key
- correlation_ids
- celestial_events
- historical_events
- correlations
- matched_rules
- summary
- machine_assessment_summary
- human_assessment_summary
- evidence_grade_summary
- timeline_items
- limitations
- generated_at
- report_version

group_type enum:
- by_celestial_event
- by_historical_event
- by_rule
- by_dynasty
- custom

2. Add CLI generate-group-report with arguments:
- --group-type
- --group-key
- repeatable --correlation-id for custom mode
- --research-root
- --rules-path
- --out-dir
- optional --title

3. generate-group-report behavior:
- scan data/research/correlations;
- find matching correlations;
- load linked celestial and historical events;
- reuse single-report matching and evidence logic where possible;
- write group Markdown;
- write group JSON sidecar;
- do not overwrite single-correlation reports.

Suggested output names:
- group_by_celestial_event_<celestial_event_id>.md
- group_by_historical_event_<historical_event_id>.md
- group_by_rule_<rule_id>.md
- group_custom_<hash>.md

4. Group Markdown should include:
- title;
- group metadata;
- overview table;
- timeline;
- per-case summary;
- evidence grade statistics;
- counterevidence and limitations summary;
- missing evidence or TODO section.

Overview table columns:
- correlation_id
- celestial_event
- historical_event
- rule_ids
- time_delta_days
- evidence_status
- omen_evidence_grade
- historical_evidence_grade
- confidence
- review_status
- case_type

5. Add timeline_items:
- item_id
- item_type: celestial_event, historical_event, window_start, window_end
- title
- date_start
- date_end
- date_precision
- source_id
- correlation_id
- notes

Unparseable dates should not fail; add limitation instead.

6. Add group_index.json under data/research/indexes.

Fields:
- group_id
- group_type
- group_key
- title
- correlation_count
- celestial_event_count
- historical_event_count
- rule_ids
- dynasty_list
- evidence_grade_summary
- review_status_summary
- report_path
- json_report_path
- updated_at

7. Add CLI build-group-index.

Tests:
- group by celestial event;
- group by historical event;
- custom group with multiple correlation ids;
- group Markdown contains overview, timeline, and evidence stats;
- group JSON sidecar contains timeline_items;
- group_index.json generation;
- single-correlation report unchanged.

Acceptance commands:

```bash
cd apps/star-omen
pytest -q
python -m src.cli generate-group-report --group-type by_celestial_event --group-key mars_guarding_xin_001 --research-root data/research --rules-path data/processed/corpus/sample_rules.json --out-dir data/research/case_reports
python -m src.cli build-group-index --research-root data/research
python -m src.cli build-research-index --research-root data/research
```

Final report should include modified files, GroupReport model, new CLI commands, group report structure, group index fields, tests, acceptance results, and risks.
