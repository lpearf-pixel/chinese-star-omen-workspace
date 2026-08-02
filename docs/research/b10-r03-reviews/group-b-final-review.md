# Targeted re-review — Group B

## Verdict

**Spec: PASS**

**Quality: APPROVED**

Findings: **Critical 0; Important 0; Minor 0.**

No new Critical or Important finding was introduced by the remediation.

## Closure of the three prior Important findings

1. **Song treatise boundary — CLOSED.** Fixed raw accessions now cover `宋書/卷23` through `宋書/卷26`. Their headers form a continuous boundary: 天文一 → 天文二 → 天文三 → 天文四, with volume 23 preceded by 樂四 and volume 26 followed by 符瑞上. The report and accession identity notes now correctly describe volumes 23–26 as the complete separable `宋書·天文志` run and warn that they are one Wikisource family.
2. **C09 direct locus — CLOSED.** `宋書/卷25` oldid 1748426, raw line 83 contains the direct passage beginning `義熙七年四月辛丑` and including `七月丁卯，歲星犯填星，在參……一曰：「益州戰不勝，亡地。」`, followed by the 朱齡石/蜀 sequel. The report and accession designate this as C09; volume-24 moon–Jupiter passages are explicitly limited to context.
3. **Song compiler provenance — CLOSED.** The report and all four Song accessions now say that 沈約 is the historical compiler while the fixed raw `author` fields are blank. They no longer claim that the volume headers display his name.

## Fixed-revision replay

On 2026-08-02, all eight `action=raw&oldid=` endpoints were reacquired from Wikisource. Every download matched both its local raw file and its declared SHA-256 and byte count. The Wikisource revision API also matched all eight declared page titles, oldids, and revision timestamps. `accessions.json` parses as an eight-entry array with unique oldids and valid raw manifest fields.
