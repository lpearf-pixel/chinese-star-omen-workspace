# L5 read-only viewer

Goal: add a read-only Web UI for research cases, group reports, indexes, Markdown reports, JSON sidecars, evidence grades, timelines, and review status.

Do this only after L1 to L4 are stable.

Scope:
- UI is read-only.
- Do not edit source JSON from UI.
- Do not add backend database.
- Do not write Qdrant.
- Do not change upstream ingest.
- Do not break apps/star-omen CLI.

Preferred app location:
- apps/star-omen-viewer

Preferred stack:
- Vite
- React
- TypeScript

Avoid complex state management.

Tasks:

1. Add export CLI in apps/star-omen:

```bash
python -m src.cli export-research-viewer-data --research-root data/research --out-dir ../star-omen-viewer/public/research
```

Behavior:
- copy case_index.json;
- copy group_index.json;
- copy Markdown reports;
- copy JSON sidecars;
- output JSON summary;
- do not modify source data.

2. Viewer reads:
- /research/indexes/case_index.json
- /research/indexes/group_index.json
- /research/case_reports/*.md
- /research/case_reports/*.report.json

3. Add Case List page at /cases.

Show table fields:
- celestial event
- historical event
- dynasty
- rule_ids
- evidence_status
- omen_evidence_grade
- historical_evidence_grade
- confidence
- review_status
- case_type
- time_delta_days
- sample flag

Filters:
- dynasty
- celestial type
- evidence status
- confidence
- review status
- case type
- candidate-only
- needs-sources

4. Add Case Detail page at /cases/:caseId.

Read JSON sidecar and show:
- celestial event summary;
- historical event summary;
- matched rules;
- evidence grades;
- machine assessment;
- human judgment;
- time window;
- source refs;
- counterevidence and limitations;
- Markdown source view.

5. Add Group List page at /groups.

Read group_index.json and show:
- group_type
- group_key
- title
- correlation count
- rule IDs
- dynasty list
- evidence grade summary
- review status summary

6. Add Group Detail page at /groups/:groupId.

Show:
- overview table;
- timeline;
- per-case summaries;
- evidence grade statistics;
- counterevidence and limitations summary.

7. Add Review Board page at /review.

Group cases by review_status:
- draft
- needs_sources
- needs_date_check
- reviewed
- published
- rejected

8. Add Timeline component.

Display:
- celestial event date;
- historical event date;
- time window start and end;
- date_precision;
- uncertainty_days.

If date cannot be parsed, show date pending confirmation.

9. Add EvidenceBadge component.

Render badges for:
- primary_citable
- candidate_only
- missing
- A1/A2/B1/B2/C grades
- H1/H2/H3/H4/H5 grades
- confidence high/medium/low
- review status

10. Add apps/star-omen-viewer/README.md.

Include export command:

```bash
cd apps/star-omen
python -m src.cli export-research-viewer-data --research-root data/research --out-dir ../star-omen-viewer/public/research
```

Include startup commands:

```bash
cd apps/star-omen-viewer
npm install
npm run dev
```

State clearly that UI is read-only and does not write source files.

Tests and build:
- test export-research-viewer-data;
- apps/star-omen pytest -q passes;
- frontend npm run build passes;
- if frontend tests are configured, they pass.

Acceptance commands:

```bash
cd apps/star-omen
pytest -q
python -m src.cli export-research-viewer-data --research-root data/research --out-dir ../star-omen-viewer/public/research
cd ../star-omen-viewer
npm install
npm run build
npm run dev
```

Final report should include modified files, viewer structure, export CLI behavior, pages, startup commands, build/test results, and risks.
