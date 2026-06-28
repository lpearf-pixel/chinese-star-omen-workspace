# L1 stabilize research MVP

Goal: stabilize the existing research case-report MVP in apps/star-omen.

Scope:
- Work only in apps/star-omen unless a small doc reference is needed.
- Do not change apps/local-kb-unified ingest.
- Do not write Qdrant.
- Do not add a database.
- Do not build Web UI.
- Do not add large real historical data.

Tasks:

1. Add a focused Research case reports section to apps/star-omen/README.md.

2. Add src/research_models.py with Pydantic models:
- ResearchSourceRef
- HistoricalEvent
- CelestialHistoricalCorrelation
- CaseReport
- ResearchValidationSummary
- CaseIndexItem

3. Use the models in validate-research-data, generate-case-report, and build-research-index while keeping current fixtures compatible.

4. Strengthen validate-research-data:
- correlation id should match filename, mismatch is warning;
- celestial_event_id must exist;
- historical_event_id must exist;
- matched_rule_ids must exist in rules-path when provided;
- historical event should include title, summary, source_refs;
- each source ref should include at least one of title, citation, locator;
- celestial event should include body and event_type;
- correlation should include confidence, status, relation_type, evidence_status;
- date_precision=day with unparseable date_start is error;
- other date parsing issues are warnings;
- null time_delta_days is warning.

5. Fix computed evidence status:
- primary_citable only from primary_evidence_found true;
- candidate_only only from candidate evidence flags/status;
- otherwise missing;
- do not classify candidate_only only because matched_rule_ids exists.

6. Clearly mark sample/demo research data or move samples to tests/fixtures/research.

7. Add CLI-level tests for validate-research-data, generate-case-report, and build-research-index.

Acceptance commands:

```bash
cd apps/star-omen
pytest -q
python -m src.cli validate-data
python -m src.cli match-rule --event data/examples/events/mars_guarding_xin_demo.json
python -m src.cli validate-research-data --research-root data/research --rules-path data/processed/corpus/sample_rules.json
python -m src.cli generate-case-report --correlation-id corr_mars_xin_leadership_change_001 --research-root data/research --rules-path data/processed/corpus/sample_rules.json --out-dir data/research/case_reports
python -m src.cli build-research-index --research-root data/research
```

Final report should include modified files, model changes, CLI changes, test results, acceptance command results, and remaining risks.
