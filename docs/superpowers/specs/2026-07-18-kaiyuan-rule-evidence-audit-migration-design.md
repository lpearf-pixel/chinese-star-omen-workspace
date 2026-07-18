# Kaiyuan Rule Evidence Audit and Migration v2 Design

## Goal

Audit legacy rule evidence in bulk and produce fail-closed migration proposals that add canonical locator, page, paragraph, heading, anchor and hashes only when one immutable primary passage can be proven.

## Safety boundary

- Base: `stable/kaiyuan-v2@57da1a8b9afb994b3f3ef0ac1714d14fd4a3d37b`.
- Branch: `codex/kaiyuan-rule-evidence-migration-v2`.
- Never target `main`, mutate raw corpus, access `local_kb_default`, ingest, or write Qdrant.
- Audit is read-only. Apply writes only a caller-specified output JSON file; it never overwrites the input rule file.
- Existing evidence is never silently replaced. A proposal contains `before`, `after`, match trace, and status.

## Inventory result

The current formal sample set contains one legacy primary reference missing page, canonical locator, paragraph, heading and hashes. Other rules either have no evidence or intentionally use non-primary structured cards. Missing and non-primary evidence are reported, not promoted.

## Selected approach

Add a pure downstream module `rule_evidence_migration.py` that loads primary passages through `kb-text-core`, indexes them in memory, audits every rule, and returns a deterministic plan. This reuses the shared parser and hash semantics without calling retrieval, ingest, candidate, or external services.

Alternatives rejected:

- Reusing the strict resolver alone cannot discover a missing page/locator.
- Mutating rules in place makes partial failure and accidental promotion difficult to audit.
- Loose/heading search is useful for clues but is insufficient for automatic migration.

## Classification

Each rule receives exactly one status:

- `already_citable`: existing evidence passes the B4 resolver unchanged.
- `migratable`: exactly one primary passage contains the anchor by exact raw or exact normalized match.
- `ambiguous`: more than one passage matches at the best exact level.
- `unresolved`: no exact raw/normalized primary passage matches.
- `candidate_only`: evidence is non-primary or lacks a usable anchor.
- `missing_evidence`: the rule has no evidence object.
- `invalid_rule`: rule/id/evidence shape is malformed.

Only `migratable` produces `after`. The proposed evidence preserves unrelated legacy fields and sets canonical `kb_book_id`, `relative_path`, `card_type`, `source_locator`, `page_marker`, `paragraph_index`, `heading_path`, `anchor_text`, `raw_content_hash`, and `normalized_content_hash`. The proposal is re-run through `resolve_evidence`; if it is not `citable`, planning fails closed with `migration_validation_failed` and no output apply.

## Determinism and atomicity

- Source files and rules are processed in lexical order while report details preserve rule input order.
- Candidate matches sort by primary ranking and stable source/offset identity.
- Duplicate/non-empty rule IDs are required.
- Any source read/parse error aborts the run; it is not converted to unresolved.
- Apply first validates the entire plan and then writes one complete output file through temp-file plus atomic replace.
- Output refuses to equal input after resolved-path comparison.

## CLI and report

Add `audit-rule-evidence-migration` with `--rules`, `--kb-root`, optional `--plan-out`, and optional `--apply-out`. JSON includes counts, source fingerprint, details, and `applied=false|true`. The existing `audit-rules` remains compatible.

## Tests

TDD covers unique raw and normalized migration, ambiguity, unresolved, non-primary, missing evidence, already-citable, duplicate IDs, validation failure, input/output alias refusal, atomic write, strict JSON, and proof that raw sources remain byte-identical.
