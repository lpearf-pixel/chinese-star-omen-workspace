# Codex Task

Repository: lpearf-pixel/chinese-star-omen-workspace

Branch: codex/implement-upstream-downstream-sync-contract-v1

Working directory: apps/star-omen

Current task: execute apps/star-omen/docs/codex_plan_L1.md only.

Do not execute L2, L3, L4, or L5.

Do not work on other projects.

Do not modify apps/local-kb-unified.

Do not write Qdrant.

Do not add a database.

Do not build Web UI.

Do not add large real historical data.

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

Final response must include:

1. Modified files
2. Model changes
3. CLI changes
4. Test results
5. Acceptance command results
6. Remaining risks or TODOs
