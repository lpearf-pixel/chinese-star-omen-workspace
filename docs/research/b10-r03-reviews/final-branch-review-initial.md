# B10-R03 final independent branch review — PR #57

Review date: 2026-08-02  
Repository: `lpearf-pixel/chinese-star-omen-workspace`  
Base: `6cffa1e4adf428f068149a31e7f2572dce4a2069`  
Reviewed head: `e7be9bbf323f95a849b410d3d46218a8b809fc80`

## Verdict

**Ready: NO.** The source package and mappings pass the substantive integrity checks, but two repository-governance acceptance defects remain at the reviewed head.

Final finding counts:

- Critical: **0**
- Important: **2**
- Minor: **1**

PR state re-resolved through the GitHub connector: open, Draft, mergeable, base `stable/kaiyuan-v2` at the expected base SHA, and head at the expected reviewed SHA. The base/head comparison is `ahead_by=47`, `behind_by=0`. All three head workflows are completed successfully: Development Governance, Kaiyuan Upstream Runtime, and Kaiyuan Stable Core.

## Strengths

1. **The live repository scope is narrow and auditable.** GitHub's paginated changed-file list and base/head comparison agree on exactly 42 files: 34 files under `corpus/research_sources/related-wikisource/` and eight task-specific governance/report/plan files. The corpus package consists of four top-level package files, seven accession JSONs, seven notes, and 16 raw snapshots. The only pre-existing files modified are `PROJECT_MEMORY.md`, `TASKS.md`, and `WORK_LOG.md`; no application, production contract/schema, threshold-freeze, canonical Reviewer A/B, ingest, Qdrant, or collection file is touched.

2. **All committed and upstream raw objects replay exactly.** I fetched all 16 raw files from the reviewed GitHub head and independently recomputed UTF-8 byte counts and SHA-256 values. Every file matches its family accession JSON and `accession-manifest.json`; the total is exactly 645,044 bytes. I then freshly reacquired all 16 fixed Wikisource objects with `action=raw`, streaming each response through `sha256sum` and `wc -c`; all 16 remote hashes and byte counts match the committed snapshots. A batched MediaWiki revision API query also matched page title, oldid, and revision timestamp for all 16 objects.

3. **The structured package is internally consistent.** All ten changed JSON files parse. The declared and observed counts are 7 families, 16 accessions, 16 unique raw paths, and 20 unique mappings. There are no duplicate family IDs, accession IDs, mapping IDs, or raw-path collisions. Every accession contains every field required by `accession-working-contract.json`; oldids, dates, timestamps, fixed URLs, repository-relative paths, SHA-256 syntax, byte counts, sorted unique Core14 scopes, and the `complete | unavailable | partial_with_reason` enum all validate. All 16 captures are `complete`.

4. **Provenance and witness limits are explicit.** Each accession has a fixed oldid URL, floating supplemental URL, source identity, locator, access and revision dates, version-family description, author/compiler treatment, CC BY-SA attribution note, and independent-witness limitation. The family notes consistently warn that same-family Wikisource pages or mirrors are not independent witnesses. The package keeps raw snapshots, accession metadata, research mappings, and notes separate.

5. **The 20 directional mappings agree with the merged Core14 audits.** I parsed the merged `audit-early.json`, `audit-middle.json`, and `audit-late.json` from the reviewed base and checked every non-empty `target_atom_ids` value against the atom set of its stated case. Every target exists with exact case and ID spelling, including `B10-C13-E-PAR`, `C47-R3`, `C47-R7`, `B10-C09-HIST`, `C41-R06/R07`, and `C45-H2`. All source accession IDs exist, each target case is within the source accession's declared scope, relation values belong to the four declared relation types, mapping direction is consistently `localized_source_to_core14`, and every `target_whole_row_citation_eligible` value is `NO`, matching the merged Core14 whole-row decisions.

6. **The named content corrections and boundaries are supported by raw evidence.** C13 is correctly assigned to `乙巳占/5` line 11 (`火逆行氐，失地，一曰多火災`) rather than 卷二. C47 is correctly assigned to 卷八, chapter 48, with `大臣誅` and the 30/50/70-day sequence preserved. The direct C09 locus is `宋書/卷25` line 83, including `歲星犯填星` and `益州戰不勝，亡地`; volume 24 is not mislabeled as the direct locus. Song volumes 23–26 form the complete separable `天文一` through `天文四` run, bounded by `樂四` before volume 23 and `符瑞上` after volume 26. Jin volumes 11–13 identify `天文上`, `天文中`, and `天文下` and link consecutively through their headers/footers.

7. **Safety boundaries remain unfrozen and inactive.** The working contract and mapping are explicitly `UNFROZEN`; manifest and contract forbidden-side-effect fields are `NOT_RUN`, including production schema freeze, official ingest, Qdrant, `local_kb_default`, and Reviewer A/B modification. A scan of newly added content and the actual modified hunks found no machine-local path, secret, private key, token, or file URI. Historical `/Users/...` strings elsewhere in full governance files predate this PR and are not added by its hunks.

8. **Group C's process-only Minor is closed for the submitted repository scope.** The original reviewer could not prove historical no-outside-scope writes from its non-Git workspace. The live GitHub base/head comparison now establishes the complete submitted repository delta, and connector readback verifies every changed file at the reviewed head. That closes the release-relevant repository-scope concern without rewriting Group C's historical report. It does not retroactively prove facts about an ephemeral pre-integration workspace, but no such proof is needed to establish the PR's actual repository diff.

## Critical findings

None.

## Important findings

### 1. Current repository memory records stale and malformed live facts

`docs/development/PROJECT_MEMORY.md:14` newly states that the live open PRs are only `#1, #7, #54`, omitting the current PR #57 even though the same snapshot names its branch and task. `docs/development/PROJECT_MEMORY.md:44` also stores literal `\\n` characters between phase entries and leaves B10-R03 at `IN_PROGRESS`, while the execution plan and `TASKS.md` say `VERIFYING`.

This violates the root governance requirement to resolve all open PRs and update stale memory facts before relying on them (`AGENTS.md:11`) and weakens the file's role as the cross-session recovery entrypoint (`AGENTS.md:21`). `TASKS.md:16` already contains the correct open-PR set, so the repository currently has conflicting current-state sources.

**Required correction:** update the current memory snapshot to include #57, use real line breaks, and align the B10-R03 phase with the final intended state at the new head. Re-resolve live PR/base/head facts again after the correction.

### 2. Task 5's required final verification evidence is absent from the work log

`docs/development/WORK_LOG.md:5-14` adds only a “localization started” entry. It records the Runner policy, PR #56 preconditions, task startup, and scope boundaries, but it does not record PR #57's final validation commands/results, exact reviewed head, 16-object remote replay results, manifest/hash/byte totals, JSON/mapping checks, workflow results, or final review disposition.

The implementation plan explicitly requires re-fetch/hash/parse/replay/scope review (`docs/superpowers/plans/2026-08-01-b10-related-wikisource-localization.md:75-77`) and makes “work log records commands/results and Runner policy” an acceptance condition (`:84`). Runner policy alone satisfies only half of that condition.

**Required correction:** add a B10-R03 verification/closeout work-log entry at the next exact head. Record the actual commands or auditable methods and results, remote fixed-object replay totals, revision-identity totals, JSON/count/duplicate/mapping checks, changed-file scope, workflow status, Runner `NOT RUN` rationale, and the final review counts. Update task/memory state only after that head is re-reviewed.

## Minor findings

### 1. Mapping M17 labels a prose summary as an evidence excerpt

`corpus/research_sources/related-wikisource/core14-mapping.json:246-254` uses `evidence_excerpt: "星孛、彗星、掃、蓬星 historical sequences."`. This is a mixed-language research summary rather than a verbatim source excerpt, unlike the other mapping records and despite the field name. The cited raw range does support the contextual terminology, including the exact `有蓬星如粉絮` passage at raw line 142, so the mapping conclusion is not invalid.

**Suggested correction:** replace the value with one or more short exact source strings from the cited range and keep the English characterization in `research_note`.

## Final ruling

The B10-R03 research corpus, provenance, source identities, raw bytes, mappings, corrections, citation boundary, and safety scope are technically sound at `e7be9bbf323f95a849b410d3d46218a8b809fc80`. The PR is nevertheless **not ready** because its current-memory facts and mandatory work-log closeout evidence do not meet repository governance. Correct the two Important findings, optionally clean up M17, then re-resolve and re-review the new head before changing the Draft/merge disposition.
