# Scoped re-review of revised `audit_middle`

Scope: only the findings in `review_early_of_middle.md` (I1–I6, M1–M2), plus the requested checks for citation scope, C31/C41 entity taxonomy, C41 carrier/collated separation, C14 atom-level duplication, C43 boundary scope, and controlled enums. No new full-text research was performed.

## Verdict

**All original findings are ADDRESSED. Critical blockers: 0.** Within this scoped review, the revised `audit_middle.md/json` is **ready for integration**.

## Critical

None.

## Original findings

| Finding | Status | Revised evidence |
|---|---|---|
| I1 — scalar Citation decision and non-blanket atomic scope | **ADDRESSED** | Every case now has scalar `citation_eligible=YES` and `whole_passage_citation=NO`. All 52 atoms have an explicit `citation_scope`; no atom is missing scope. The previously challenged edges are correctly separated: C14-R01–R04 expanded, R05–R09 current; C31-R01–R03/R13 expanded, R04–R12 current; C33-R01–R10/R13 expanded, R11–R12 current; C41-R08 expanded; C43-R01/R09 expanded. |
| I2 — C31/C41 enclosures mislabeled as lunar mansions | **ADDRESSED** | C31 `celestial=[five_planets]` and C41 `celestial=[meteor]`; both add `target_entity_types=[enclosure, asterism]` and explicitly exclude `lunar_mansions`. C14 and C43 retain `lunar_mansions` for 心/房 and 虚/危. |
| I3 — unsupported C31 case conflict | **ADDRESSED** | C31 is now `Eligibility=eligible`, `special_tags=[]`. `出中華門間/東門` is confined to C31-R02 `textual_variant`; 殺/弑 is confined to C31-R04. Carrier reading and conjectural parallel are not merged. |
| I4 — C41 silently supplied `入` | **ADDRESSED** | Markdown quotes carrier `干太㣲紫宫` without adding `入`, then separately labels the *Han shu* reading. C41-R06 has distinct `carrier_text` and `collated_reading`; its relation says `入僅見校讀`. Risk is raised to `medium`. |
| I5 — C14 duplicate scope | **ADDRESSED** | C14 case `special_tags=[]` and remains `eligible`. Only C14-R08 carries `duplicate_of` and `parallel_same_book`; R01–R07/R09 have no duplicate marker. |
| I6 — inconsistent C43 boundary/atom inventory | **ADDRESSED** | C43 adopts the minimal right repair through the completed 甘氏 sentence at 079-8a. Atomic inventory is limited to R01–R09; R10/R11 are removed. Later 甘氏/郗萌/巫咸/黄帝 material is explicitly `context_only`. |
| M1 — flat source scopes | **ADDRESSED** | Every `ancient_books` entry now has `scope` such as `current_passage`, `boundary_repair`, `wider_context`, or `parallel`; C43’s later 巫咸/黄帝 entries additionally state `evidence_role=context_only`. |
| M2 — C41 risk too low | **ADDRESSED** | C41 is now `risk=medium`, with carrier/collated divergence stated as the reason. |

## Requested focused checks

### Citation scope — PASS

- Case decisions are scalar and consistent in Markdown/JSON: all five Formal candidate=YES, Citation eligible=YES, whole passage=NO, Eligibility=eligible.
- Atomic scopes are complete and match the supplied-versus-restored boundaries challenged in I1.
- No blanket `citation_eligible_atomic=YES` remains.

### C31/C41 entities — PASS

- 太微、紫宫 and associated gates/inner targets are represented through `target_entity_types`, not `lunar_mansions`.
- C31 still excludes Moon for 太陰門, excludes relation `合` for 《合誠圖》, and keeps the book title intact.
- C41 keeps `臣犯主` as an omen and excludes it from celestial relation values.

### C41 carrier/collated readings — PASS

`carrier_text` exactly preserves the cited carrier’s absence of `入`; `collated_reading` attributes `干太微，入紫宮` to *Han shu*. The narrative and rule table explicitly describe the separation.

### C14 duplicate atom — PASS

The duplicate is localized to C14-R08 and does not alter case-level Eligibility or Special tags.

### C43 boundary — PASS

The right edge is minimal, the expanded 甘氏 atom is marked `expanded_context`, and later rules are excluded from the case rather than selectively atomized.

### Enums — PASS

- All `recommendation.relation` values fall within `合 | 犯 | 入 | 守 | 掩 | 离 | 留 | 逆`.
- All five `special_tags` arrays are empty, therefore valid under `ambiguous | duplicate | conflict | []`.
- Final Complexity values match the stated rubric: C14/C31/C41=`compound`, C33/C43=`cross_passage`.

## Integration gate

**PASS.** No Critical or other blocking issue remains from the original review. The revised middle report can proceed to integration, subject only to any separate cross-case checks outside this scoped re-review.
