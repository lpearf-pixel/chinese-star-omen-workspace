# GOV-T02 Legacy PR Disposition Audit

Date: 2026-08-02  
Stable baseline: `5571ddb34311f1601c8e084efa133be99655cd5a`  
Disposition: PR #1 and PR #7 are superseded; close only after this audit merges

## Row-level evidence

The authoritative machine-readable matrix is
`docs/development/gov-t02-legacy-pr-matrix.json` at Git blob
`9d61ed3daf5d1318e7c4e8d71d96afa7032fd952`. It contains exactly 70 rows. Every row records the legacy
PR/head/path/blob, stable path/blob, one of the four frozen classifications,
the preserved responsibility, concrete stable implementation/test evidence and
a verification note. Counts are recomputed from those rows:

- PR #1: exact 27, evolved_superset 24, retired_non_behavioral 7, unresolved 0;
- PR #7: exact 7, evolved_superset 5, retired_non_behavioral 0, unresolved 0.

Any future matrix row classified `unresolved` invalidates this disposition and
must block closure.

## PR #1 — candidate sync foundation

| Field | Value |
|---|---|
| Base | `codex/sync-contract-v1@98e0bb713a164a384d890b273af47d3b9b444682` |
| Head | `codex/implement-upstream-downstream-sync-contract-v1@0eaeffac6d875ce6834e2a5632708ba8933bf812` |
| Ancestry vs stable | diverged; stable ahead 79, legacy head has 8 unique commits |
| Changed paths | 58 |
| Stable path result | 51 behavior/data paths preserved; 27 exact blobs, 24 evolved |
| Retired paths | 7 obsolete task/plan documents |
| Comments / reviews / threads | 0 / 0 / 0 |

The retired paths are `CODEX_TASK.md`,
`apps/star-omen/docs/codex_plan_L1.md` through `codex_plan_L5.md`, and
`apps/star-omen/docs/codex_plan_index.md`. They contain no runtime behavior or
corpus data and are replaced by `AGENTS.md`, `TASKS.md`,
`PROJECT_MEMORY.md`, `WORK_LOG.md`, decisions, specs and plans.

Exact stable blobs include the corpus manifest, candidate sync documentation,
minimal KB app, corpus-manifest and candidate-import scripts, import tests,
downstream configuration/settings, KB contract and retriever tests, hashing,
manifest and normalization helpers, all three original candidate/corpus
schemas, and shared contract tests.

Evolved stable implementations preserve and strengthen the remaining
responsibilities:

- candidate generation and deterministic identity;
- transactional upstream sync with no partial manifest writes;
- `pending|merged|needs_review|stale` business states separated from run errors;
- optional candidate overlay without official-evidence promotion;
- approval-only upstream import and official source namespace;
- shared contract, downstream and upstream test entrypoints;
- locator-aware merge, citable evidence and structured transport errors added
  after the legacy head.

Unresolved behavior/data rows: **0**.

## PR #7 — corpus audit and evidence matching hardening

| Field | Value |
|---|---|
| Base | `dev-test@b42e2c66776dfcd24406cea78a34cabf6ef51b36` |
| Head | `codex/kaiyuan-pr-a-hardening@3cc654b92514223d069b56162c874b5a1a65e060` |
| Ancestry vs stable | diverged; stable ahead 74, legacy head has 1 unique commit |
| Changed paths | 12 |
| Stable path result | 12 present; 7 exact blobs, 5 evolved |
| Comments / reviews / threads | 0 / 0 / 0 |
| Historical head workflow | Kaiyuan PR A `29387666965`: success |

The exact stable blobs are the installable `kb-text-core` project,
`matching.py`, `ranking.py`, its regression test, corpus audit v2, volume
comparison and safe fulltext split script. The evolved files are the root
Makefile, retrieval documentation, package exports, anchors and parser.

Stable semantic checks confirm:

- `heading_only` is separate from exact primary evidence;
- `loose_window` preserves ordered query-term matching;
- duplicate source provenance is retained while fenjuan priority remains;
- audit reports duplicate/empty/page-structure failures;
- splitting is dry-run by default with explicit `--write` and overwrite
  `--force`;
- volume comparison CLI and installable package remain;
- later parser/anchor work adds stricter passage identity and source safety.

Unresolved behavior/data rows: **0**.

## Decision

Neither PR targets `stable/kaiyuan-v2`, and both histories have diverged. Their
behavior is already present on the stable line with later reviewed safety work.
Merging or cherry-picking either branch would be unsafe and redundant.

After this audit is merged:

1. add one comment to each PR linking the merged audit commit;
2. state the exact legacy head and stable replacement;
3. close without merge;
4. preserve branches and history;
5. publish a final closeout with observed GitHub states.

PR #54 and its two-human calibration gate are unrelated and remain untouched.
