# B10-R03 Related Wikisource localization execution plan

Date: 2026-08-01
Status: IN_PROGRESS
Base: `stable/kaiyuan-v2` at `6cffa1e4adf428f068149a31e7f2572dce4a2069`
Target branch: `codex/kaiyuan-b10-related-wikisource-localization-v1`

## Goal

Preserve the P0 related works used by the Core14 audit with provenance treatment equivalent to 《唐開元占經》: revision-bound Wikisource source, replayable permanent URL, source title, work/volume/section locator, access date, UTF-8 source snapshot, SHA-256, version-family identity, license note, collation limits and case-scoped mapping.

This is a raw-source and research-evidence task. It does not freeze the future multi-text database schema.

## Global constraints

- Target only `stable/kaiyuan-v2`; never modify `main`.
- No official KB ingest, Qdrant access, or `local_kb_default` read/write.
- Preserve source characters and source page boundaries; do not overwrite raw snapshots with normalized punctuation.
- A fixed oldid/permanent URL is mandatory; a floating current-page URL is supplemental only.
- Wikisource and a same-family mirror do not become independent witnesses merely because they agree.
- Lost works and carrier-only quotations are excerpts, never fabricated complete books.
- Keep source observation, suggested punctuation, translation and collation hypotheses separate.
- Formal cross-text schema, duplicate domain and production rule mapping remain unfrozen.

## Task 1 — Accession policy and reversible directory layout

Create a source-package README and machine-checkable working manifest contract for revision-bound page snapshots. The layout must be additive and reversible: one source object per Wikisource title/revision, raw snapshot separate from notes and case mapping.

Acceptance:
- required provenance fields documented;
- license and attribution recorded;
- no production schema claim;
- no machine-local path;
- no normalized text substituted for raw source.

## Task 2 — P0 astronomy works

Localize the directly relevant Wikisource source objects for:
- 《乙巳占》 — C09, C13, C47;
- 《史記·天官書》 — C03;
- 《漢書·天文志》 — C41;
- 《宋書·天文志》 — C09, C14, C43;
- 《晉書·天文志》 — C03, C11, C14, C47.

For each object, capture the relevant volume/section pages first, then expand all pages that belong to the named astronomy chapter when Wikisource exposes stable separable pages.

Acceptance:
- fixed oldid and permanent URL;
- exact raw source snapshot;
- replayable title/locator;
- SHA-256 and byte count;
- version-family and independent-witness warning;
- explicit Core14 scope.

## Task 3 — P0 historical works

Localize the directly relevant Wikisource source objects for:
- 袁宏《後漢紀》 — C14;
- 《後漢書》 — C45.

Capture the directly relevant chapter/volume pages first. Expand only pages belonging to the identified work/section without guessing absent pages or conflating different editions.

Acceptance: same provenance and integrity fields as Task 2, plus compiler/author and chapter identity disambiguation.

## Task 4 — Cross-source research mapping

Produce reversible research mapping from localized source objects to Core14 cases and atomic proposals. Record relation as citation-source, historical-note parallel, material variant, or locator support. Do not declare logical conflict solely from outcome diversity.

Acceptance:
- every mapping has direction, scope and evidence locator;
- whole-row and atomic citation eligibility remain distinct;
- disputed readings stay unresolved;
- no Reviewer A/B modification.

## Task 5 — QA, review and closeout

Re-fetch every committed source object, recompute hashes and byte counts, parse all JSON, replay permanent URLs, scan for machine paths and forbidden side effects, and run independent task and branch review.

Acceptance:
- all manifest hashes and byte counts match;
- no duplicate accession IDs or source path collisions;
- every P0 family has at least one fixed accession object;
- reviews have no unresolved Critical/Important finding;
- work log records commands/results and Runner policy;
- Draft PR targets only `stable/kaiyuan-v2`.
