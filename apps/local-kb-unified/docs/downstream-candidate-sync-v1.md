# Downstream Candidate Sync v1

`apps/local-kb-unified` is the source of truth for the official knowledge base. Downstream projects may discover text spans, but they must submit them as candidate artifacts for upstream validation and promotion.

## Flow

1. Downstream `apps/star-omen` generates `candidate-card/v1` markdown files and `candidate_manifest.json` under `apps/star-omen/data/generated_candidates/`.
2. A human or automation copies those files into `apps/local-kb-unified/incoming/downstream_candidates/<submitter>/`.
3. Upstream validates the inbox:

   ```bash
   python scripts/import_candidate_cards.py --inbox incoming/downstream_candidates/codex-ready --book-id kaiyuan_zhanjing --mode validate
   ```

4. A reviewer changes acceptable cards from `review_status: pending` to `review_status: approved`.
5. Upstream promotes approved cards only:

   ```bash
   python scripts/import_candidate_cards.py --inbox incoming/downstream_candidates/codex-ready --book-id kaiyuan_zhanjing --mode promote
   ```

6. Promotion writes official extract cards to `data/generated/extract_cards/{book_id}/` and writes `promoted_manifest.json`.
7. Upstream runs the official `make ingest` after promotion.
8. Downstream runs `sync-upstream-status` to reconcile local candidate status with the new upstream corpus version.

## Invariants

- Pending, rejected, stale, or otherwise unapproved candidates never participate in official ingest.
- `incoming/downstream_candidates` is an inbox only and is excluded from ingest scanning.
- Downstream must not run upstream ingest, write to Qdrant, or present pending candidates as official evidence.
- Pending candidates may be shown only as runtime `primary_candidates` when downstream candidate overlay is explicitly enabled.
- `packages/kb-contracts` is the shared source for schemas, status enums, hashing, manifest merge, and stable candidate ids.
