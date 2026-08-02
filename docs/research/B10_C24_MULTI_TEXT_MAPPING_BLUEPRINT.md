# B10 C24 multi-text mapping blueprint

## 1. Mission and non-goals

The outcome is a reversible, evidence-linked map from an atomic omen passage to
all carrier witnesses, quoted ancient sources, parallel formulas and review
decisions. Success means a reviewer can move from a proposed rule back to exact
page markers, original glyphs and hashes, while alternative readings remain
visible.

Non-goals for this pilot: no full-book extraction, no automatic emendation, no
model approval, no official KB promotion, no `local_kb_default` mutation, and
no final schema freeze before the planned structure discussion.

## 2. Boundary and stakeholders

| Actor/system | Role | Input | Output/constraint |
|---|---|---|---|
| Research reviewer | decides boundaries and readings | witnesses and hypotheses | explicit decision with rationale |
| Source accession | preserves evidence | revision/commit/blob | immutable bytes, locator and hash |
| Passage mapper | relates text units | exact excerpts | candidate edges, never silent merges |
| B10 calibration | measures extraction/review | approved pilot data | cannot use AI notes as human labels |
| Official KB | downstream consumer | only approved citable release | out of scope in this pilot |

Observed facts, inferred emendations and approved decisions are separate
records.

## 3. Minimum closed loop

`C24 locator → source snapshot → section split → parallel search → variant
hypotheses → human review → revised split/reading → recheck against source`.

The pilot is complete only when a person can reject or approve each proposed
edge without losing the original text.

## 4. Subsystems and interface contracts

| Subsystem | Responsibility | Failure behavior |
|---|---|---|
| Accession | bind URL/revision/commit/blob/content hash | fail if bytes or locator drift |
| Boundary record | mark headings and atomic passage spans | retain unresolved overlap |
| Source register | distinguish witness label, normalized title, person and book | never replace original label |
| Parallel mapper | propose repeated-formula links | candidate only |
| Variant ledger | store supporting/contrary evidence and confidence | no auto-emendation |
| Review ledger | capture human decisions and reversals | AI output cannot fill human slots |

## 5. Knowledge layers

- **Observation:** exact characters, page markers, headings, revision and hash.
- **Hypothesis:** segmentation, title normalization, formula ancestry.
- **Decision:** reviewer-approved boundary/reading with evidence IDs.
- **Outcome:** downstream rule split, citation eligibility and later reversals.

## 6. Current pilot status

| Gate | State | Evidence/exit condition |
|---|---|---|
| G0 source identity | complete in branch | revision, commit, blob and SHA-256 recorded |
| G1 section boundary | supported | sections eight and nine separated by explicit heading |
| G2 parallel discovery | supported | exact matches from volumes 23, 30 and 38 recorded |
| G3 reading decision | blocked | independent witness or qualified human collation required |
| G4 mapping schema | deferred | discuss node/edge structure with user after evidence review |
| G5 B10 use | forbidden now | PR #54 human calibration and threshold gates remain independent |

## 7. Metrics

- 100% of stored excerpts have source identity, locator and SHA-256.
- 0 silent glyph normalizations.
- 0 hypotheses promoted as facts.
- 100% of candidate mappings expose supporting and contrary evidence.
- Citable evidence false-positive count remains 0.
- Reviewer effort and reversals are logged for later schema design.

## 8. Risks and reversible decisions

| Risk | Evidence today | Reversible response |
|---|---|---|
| `客環守` over-interpreted | three planetary formulas disagree | retain H1–H3 and block citation |
| Wikisource mistaken for independent edition | same WYG-derived wording | label it comparison transcription |
| Lost titles treated as extant books | only quotations located | cite the extant carrier |
| shape descriptions forced into numeric rules | no angular/duration threshold | keep qualitative observation |
| normalized title erases glyph evidence | both 雒書 and 洛書 occur | store label and normalized title separately |

## 9. Next discussion points

The later structure discussion should decide only after the evidence pilot:
node identity (passage, witness, source label, work, person, relation), edge
types, variant directionality, confidence ownership, and how a reviewer
reverses an earlier mapping. No production schema is frozen by this document.
