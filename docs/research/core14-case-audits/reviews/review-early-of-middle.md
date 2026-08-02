# Cross-review of `audit_middle` (C14/C31/C33/C41/C43)

Review target: `agent-reports/audit_middle.md` and `agent-reports/audit_middle.json` (read-only).  No GitHub or source-report modification was made.

Evidence basis: the five Wikisource revision IDs were checked through the MediaWiki revision API; the Kanripo commit `eb17a11a6a8a40922ccff01f727e2b5df7f3e734` was resolved locally and the cited page markers and parallel passages were checked against that commit.  Severity counts: **Critical 0 / Important 6 / Minor 2**.  The report is **not yet ready for integration** until the Important findings are corrected.

## Critical

None.  All five cases resolve to the stated volumes and page markers, and the ancient carrier/source distinction is not fatally confused.

## Important

### I1. The final `Citation eligible` value is not a valid scalar decision, and `citation_eligible_atomic=YES` overstates atom-level support

**Evidence.** The annotation contract accepts one case-level `YES` or `NO`, but the final table reports `NO（整段）；YES（原子局部）`, while JSON replaces the scalar with `citation_eligible_whole=NO` and a blanket `citation_eligible_atomic=YES`.  The blanket atomic value is demonstrably too broad:

- C14-R01–R04 inherit `郗萌曰熒…` from 031-17b; only R05–R09 have sufficiently local, source-identifiable wording in the supplied passage.
- C31-R01 and R02–R03 inherit the subject/source from 043-12a, and R13 ends after the supplied passage; R04–R12 contain usable local atoms.
- C33-R01–R04 are reconstructed from 045-8a, while R13 crosses the right edge; the locally self-contained `荆州占曰` atoms R11–R12 suffice for a case-level YES.  R05–R10 are syntactically present but inherit `甘氏曰` and the subject from the preceding page.
- C41-R08 is truncated at `水旱不`; R01–R05 and R07 are locally usable (R06 also needs the textual correction in I4).
- C43-R01 lacks `石氏曰客星` at the left edge, R09 lacks its continuation at the right edge, and R10–R11 are outside the supplied passage.

**Recommendation.** Preserve three distinct fields: `citation_eligible=YES` for all five cases under the project convention “at least one complete local atom”; `whole_passage_citation=NO`; and a per-atom `citation_scope` of `current_passage`, `expanded_context`, or `not_yet_citable`.  Do not use one blanket atomic boolean.  The final three decisions must contain a scalar case-level Citation value.

### I2. C31 and C41 incorrectly classify fixed enclosures as `lunar_mansions`

**Evidence.** C31’s target is 太微 and its named gate gaps; vol. 66 defines the west/east walls and 太陽/中華/太陰 gates (`KR3g0018_066.txt`, especially lines 303–308).  C41’s target is 紫宫.  Neither 太微 nor 紫宫 is one of the twenty-eight lunar mansions.  The report’s statement that the schema uses `lunar_mansions` to “承接固定星官” changes the meaning of the published enumeration without authority.  By contrast, C14 legitimately includes 心/房, and C43 legitimately includes 虚/危, all lunar mansions.  C43’s 離宫 is an asterism associated with 營室, not itself the reason for the lunar-mansion tag.

**Recommendation.** For C31 use `five_planets` plus a new/explicit `celestial_enclosure` or `asterism` target category; for C41 use `meteor` plus `celestial_enclosure`.  If the current closed enumeration cannot be extended, retain only `five_planets` or `meteor` at case level and preserve the target in the atomic target field; do not encode an enclosure as `lunar_mansions`.  Retain `lunar_mansions` for C14 and C43.

### I3. C31 does not meet the report’s own threshold for case-level `conflict`

**Evidence.** The three same-book parallels actually converge on `入中華西門出中華東門`: vol. 28 lines 252–254, vol. 36 lines 119–123, and vol. 58 lines 206–210.  This makes `出中華門間` in vol. 43 a strong local corruption/uncertain reading, not an unresolved pair of equally supported incompatible readings.  The `殺/弑` variants occur in separately attributed formulae and do not force two incompatible outcomes for one normalized atom.  Most of C31-R04–R12 is unaffected and citable.

**Recommendation.** Set case-level `Eligibility=eligible`; attach `textual_variant`/`needs_collation` only to R02 and keep the carrier reading verbatim with `[東]` solely as an explicitly sourced conjecture.  Use `conflict` only if the project decides that separately witnessed, irreconcilable readings attach to the same normalized rule—not merely because a passage contains a likely typo or different-source omen wording.

### I4. C41 silently inserts an `入` that is absent from the cited carrier

**Evidence.** The fixed carrier reads `流星出翼軫東北干太㣲紫宫始出小旦入大有光入有聲如雷` (`KR3g0018_074.txt`, lines 165–167).  The proposed quotation prints `干太㣲，入紫宫` without brackets.  The transmitted *Han shu* does support `干太微，入紫宮`, and also reads `且入大` and `入有頃，聲如雷`; that makes it valuable collation evidence, but not license to present `入` as a character in the Kanripo/Wikisource carrier.  The report records the latter two variants but misses this more consequential omission.

**Recommendation.** Quote the carrier as-is, or write `干太㣲，[入]紫宫` with a note “據《漢書·天文志》補”.  In C41-R06 distinguish `carrier_text` from `collated_reading`; do not assert the `入紫宫` observation as unmarked carrier text.  This correction does not undermine the independent omen atoms R01–R05 and R07.

### I5. C14’s duplicate evidence is valid only for R08, not for the case

**Evidence.** Vol. 88 lines 33–36 repeats `陳卓占曰熒惑守心期三十日彗星出`, directly supporting the C14-R08 core and the `comet=outcome_only` interpretation.  It does not duplicate C14-R01–R07 or R09.  The JSON nevertheless gives the whole case `special_tags=["duplicate"]`; the report’s own eligibility remains `eligible`, showing the scope mismatch.

**Recommendation.** Attach `duplicate_of/parallel_same_book` to C14-R08 only and keep case-level `Eligibility=eligible`.  Remove the case-level `duplicate` tag unless the Special-tags contract explicitly means “one or more atoms has this property”; if retained under that convention, state `duplicate_scope=C14-R08` in both Markdown and JSON.  Do not classify the entire candidate as duplicate.

### I6. C43’s restored right boundary and atomic inventory use inconsistent scopes

**Evidence.** The supplied passage ends at 079-7b with `甘氏曰客星出危大臣被刑`; the minimal completion is 079-8a lines 133–134 through `期不出年`.  The boundary section then expands to the entire `客星犯危五` section through 079-8b, and C43-R10/R11 use material from lines 136–140, but the table omits several intervening rules (`赤星出危`, `客星出危中大水`, `巫咸曰客星入守危`, the 荆州/黄帝 rules, etc.).  Thus it is neither a minimal-boundary atomization nor a complete-section atomization.

**Recommendation.** Prefer the minimal restored scope and keep C43-R01–R09, marking R01 and R09 `expanded_context`; treat R10/R11 and later rules as context-only and remove them from this case.  Alternatively, if the whole section is intentionally audited, atomize every rule through 079-8b and label all of them as outside the supplied passage.  The first option is cleaner for this pilot.

## Minor

### M1. `ancient_books` mixes current evidence, restored-edge evidence, and unrelated following context

**Evidence.** C33 lists `班固天文志` and `天官書` only because they occur later in the next section; C41 includes the preceding 司馬彪/宋史 notes and following 韋昭 note; C43 includes 巫咸/黄帝 from beyond the minimal right-edge repair.  Their identities are not wrong, but their evidence role is unclear in a flat list.

**Recommendation.** Add `scope=current_passage | boundary_repair | wider_context | parallel` to each source and keep `ancient_books` for sources actually used by the audited atoms.  This will prevent a later consumer from attributing a rule to a merely adjacent source.

### M2. C41’s `risk=low` is too optimistic before collation

**Evidence.** The carrier/transmitted-history differences include the missing `入` after 太微, `旦/且`, and `入有聲/入有頃聲`; the first changes the explicit path relation in R06.  Entity and omen parsing are otherwise clear, but the textual state is not low-risk.

**Recommendation.** Use `risk=medium` until R06 has carrier/collated readings separated.  Risk can remain low for the independent 石氏 and `占曰` atoms.

## Approved

### A1. Version identity and locators

The five Wikisource IDs resolve to the claimed titles and timestamps: C14 `2506688` (2024-12-18T02:43:48Z), C31 `772363` (2016-10-25T18:37:22Z), C33 `655964` (2016-10-15T10:46:13Z), C41 `656022` (2016-10-15T10:46:23Z), and C43 `656032` (2016-10-15T10:46:25Z).  The Kanripo commit exists, is the checked revision, and every cited line range contains its stated page marker.  No locator correction is needed.

### A2. Boundary restoration, subject to I6’s scope correction

C14 correctly restores `郗萌曰熒惑` and closes the 袁宏 note at 031-18b; C31 correctly restores the 石氏 sentence and the truncated 郗萌 sentence at 043-13a; C33 correctly detects a section break inside the supplied passage and completes `山崩…脩邊地`; C41 correctly completes `水旱不調`; C43 correctly restores `石氏曰客星` on the left and the 甘氏 sentence on the right.

### A3. Entity disambiguation

The report correctly rejects Moon for `太陰西門/東門`, rejects relation `合` in the title 《春秋緯合誠圖》, treats `臣犯主` as a human omen rather than the celestial relation `犯`, and treats `離宫` as an asterism rather than relation `离`.  These decisions are directly supported by vols. 66, 84, 61, and 106 respectively.

### A4. Parallel-evidence use

C14’s vol. 88 parallel genuinely supports both the R08 duplicate link and `彗星出` as a predicted outcome.  C31’s vols. 28/36/58 parallels genuinely support the conjectural `東` (with the scope correction in I3).  C41’s vol. 84 parallel supports the omen reading of `臣犯主`, while *Han shu* supplies a useful collated historical text (with I4’s bracket requirement).  C43’s vol. 61/106 evidence securely identifies 離宫, and the vol. 32/95 formulae are correctly described as a family rather than a duplicate.  C33 correctly treats *Qianxiang tongjian* as a later corroborating parallel, not an independent early witness.

### A5. Trigger/outcome/history separation

The report correctly marks C14’s comet and C33’s meteor as `outcome_only`; it does not turn the historical notes or their later political events into trigger conditions.  C41’s `臣犯主` and C43’s emperor-death narrative are likewise kept on the omen/history side.  The proposed exclusions of `moon`, `合`, `犯/守` in C41, and `离` in C43 are sound.

### A6. Final decisions apart from the corrections above

`Formal candidate=YES` is supported for all five cases.  `Eligibility=eligible` is supported for C14, C33, C41, and C43.  After I3, C31 should also be `eligible`.  Under the case-level local-atom policy, `Citation eligible=YES` is supported for all five, with `whole_passage_citation=NO` and the per-atom exceptions in I1.

## Integration gate

Not ready for integration.  Required before merge: normalize the scalar Citation decisions and atom scopes (I1), correct C31/C41 taxonomy (I2), change C31 from `conflict` to `eligible` or document a stricter conflict rule (I3), mark C41’s supplied `入` as an emendation (I4), scope C14 duplication to R08 (I5), and choose one consistent C43 boundary/atomization scope (I6).  The two Minor items may be fixed in the same pass but do not independently block integration.
