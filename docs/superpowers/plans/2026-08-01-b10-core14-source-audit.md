# B10 Core14 source audit and multi-text mapping preparation

**Date:** 2026-08-01  
**Task:** B10-R02  
**Branch:** `codex/kaiyuan-b10-c24-source-mapping-v1`  
**Target:** `stable/kaiyuan-v2`  
**Status:** VERIFYING

## Objective

Audit the frozen fourteen-case pilot as research evidence before the two-human
calibration gate. For every case, extend the frozen passage to real source
boundaries, bind public carriers to immutable identities, register quoted
ancient works, compare relevant parallel formulae, propose atomic splits, and
separate formal-candidate value from present citation eligibility.

This task does not choose the future production schema. It prepares reversible,
queryable evidence so that schema and mapping structure can be discussed after
the philological findings are visible.

## Frozen case set

`C02`, `C03`, `C09`, `C11`, `C13`, `C14`, `C24`, `C31`,
`C33`, `C41`, `C43`, `C44`, `C45`, `C47`.

## Evidence layers

1. **Frozen sample** — exact passage, sample split and workbook identity.
2. **Carrier witness** — Wikisource permanent revision and Kanripo pinned
   commit/blob, with page markers and hashes.
3. **Context unit** — previous page, target page and following page or explicit
   section boundaries.
4. **Diplomatic text** — source glyphs and page markers preserved; no silent
   normalization.
5. **Editorial hypotheses** — punctuation, subject recovery, emendation and
   segmentation are named alternatives, never replacements for the witness.
6. **Atomic rule proposals** — observation, relation, condition, omen, time
   term, quoted authority and citation status.
7. **Normalized astronomy mapping** — deferred proposal that requires a
   versioned relation glossary, asterism identities and unit policy.
8. **Review/release decision** — remains outside this task and cannot be
   supplied by AI pre-review.

## Work plan and live state

| Stage | Deliverable | State |
|---|---|---|
| 0 | Recover and verify the repaired AI-prefill workbook; freeze fourteen IDs | DONE |
| 1 | Pin thirteen Wikisource revisions and Kanripo carrier commit | DONE |
| 2A | Audit C02, C03, C09, C11 and C13 | DONE |
| 2B | Audit C14, C31, C33, C41 and C43 | DONE |
| 2C | Audit C24, C44, C45 and C47 | DONE |
| 3 | Cross-review boundary, source, relation and citation findings | DONE |
| 4 | Merge case JSON, ancient-source register and cross-case report | DONE |
| 5 | Verify hashes, JSON, links, raw glyph preservation and branch scope | DONE |
| 6 | Mark B10-R02 VERIFYING/DONE and open a Draft PR | VERIFYING |

## Per-case acceptance contract

Each case must record:

- frozen locator and exact carrier page marker;
- left and right boundary status and recovered heading/subject;
- source-preserving transcription plus proposed punctuation and plain-language
  explanation;
- observation, omen and historical verification note as separate fields;
- all quoted books and authorities, with witness label separate from normalized
  catalog title;
- Wikisource revision URL and Kanripo pinned commit/blob;
- relevant internal or external parallel text and explicit variants;
- atomic rule proposals and all unresolved readings;
- current and recommended celestial/relation/complexity/computability/risk
  labels;
- `Formal candidate`, whole-passage citation eligibility, post-split citation
  eligibility and final eligibility;
- operational-threshold gaps for distance, duration, color, shape, brightness
  or direction.

## Gates

- A page that merely adds modern punctuation is not an independent witness.
- A quoted lost book is not represented as an independently downloaded complete
  text; the extant carrier remains 《唐開元占經》 unless another witness is found.
- Witness strings retain page markers and glyph variants such as `雒書/洛書`.
- No conjectural emendation can overwrite diplomatic text.
- Astronomical event computability is separate from the computability or truth
  of the omen outcome.
- AI results cannot populate Reviewer A/B or freeze thresholds.
- No official ingest, Qdrant access, `local_kb_default` mutation, B11/B12 work
  or `main` target.

## Exit evidence

The task exits only when all fourteen case records validate, the public carrier
accession manifest is hash-bound, the cross-case report is independently
reviewed, `TASKS.md` is moved through VERIFYING to DONE, and the resulting
Draft PR still targets `stable/kaiyuan-v2`.
