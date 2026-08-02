# Independent review — Group C

## Verdicts

- **Spec: PASS**
- **Quality: APPROVED**

Finding count: Critical 0; Important 0; Minor 1.

## Evidence reviewed

- Brief: `group-c-brief.md`.
- Deliverables: `group-c/report.md`, `group-c/accessions.json`, and the three named `.wikitext` snapshots.
- Fresh primary-source replay on 2026-08-02: Chinese Wikisource `action=raw` for each stated `title`/`oldid`, plus the MediaWiki revisions API (`prop=revisions`, `rvprop=ids|timestamp|user|comment`).

| Accession | Fixed revision replay | Stored raw verification | Chapter/work and excerpt verification |
|---|---|---|---|
| GC-01 | `後漢紀 (四庫全書本)/卷16`, revid 597512, timestamp `2016-10-05T07:07:29Z` | 16,006 bytes; SHA-256 `91a228d8d7d0a6889d03844dd4ec6a3719b68632b1487f4dfe62355bf8955612`; exact byte match | Raw header gives `晉　袁宏　撰` and `孝安皇帝紀第十六`; it contains `五月戊寅熒惑逆行守心本志以為後周章謀廢帝之應也`. |
| GC-02 | `後漢書/卷83`, revid 1458140, timestamp `2018-05-20T01:46:31Z` | 30,373 bytes; SHA-256 `fd064cf6b7cd2fa55b3e0aeff9c16b952805a65f611788d475218b607076b32a`; exact byte match | Raw header identifies `卷八十三·逸民列傳第七十三`, author field `范曄、司馬彪等`; the 嚴光 passage has `客星犯御坐甚急` exactly as reported. |
| GC-03 | `後漢書/卷100`, revid 1753568, timestamp `2019-12-08T08:44:18Z` | 28,124 bytes; SHA-256 `115fadb6aa7d09f1413bbc90cee0968abee6b21238dd9c365065b2e178945e41`; exact byte match | Raw header identifies `《志》第十` / `天文上`; its `古今注` note contains `又案嚴光傳，光與帝臥，足加帝腹上，太史奏客星犯帝坐甚急。` exactly as reported. |

The fixed URLs carry explicit `oldid` values, and the recorded timestamps equal the source API response. The JSON parses and has exactly the Group A field contract. Its stored SHA-256 values and byte counts agree with local recomputation and the fresh primary-source responses. The raw files are complete returned wikitext objects, preserving the source markup (including each page's `onlyinclude` structures and the 四庫 page's `SKQS`/`PD-old` markup); no unrecorded normalization was found.

The report correctly distinguishes 袁宏's annal from the `後漢書` biography and astronomy-treatise contexts. It accurately limits GC-03 to contextual cross-reference rather than replacing GC-02's narrative, warns that GC-02/GC-03 are same-family rather than independent witnesses, and avoids asserting an unobserved print imprint or external collation. License/attribution and limitations are stated at the right level: historical text public-domain by age, with Wikisource transcription/markup attribution and CC BY-SA qualification. No claim of a completed external collation or otherwise unsupported research result was found.

Within `group-c`, the only files present are the required report, accessions JSON, and three raw snapshots. The requested review itself is outside that directory only because the reviewer instruction explicitly requires `group-c-review.md`. This workspace has no readable Git repository or change baseline, so historical modifications elsewhere cannot be attributed or disproved from filesystem state alone.

## Findings

### Minor

1. **Repository-level no-outside-scope verification is not independently auditable.** The current workspace is not a Git worktree (`git status` reports no repository), so the review can confirm the Group C directory contents but cannot prove that the implementer made no prior write outside it. This does not contradict any visible deliverable and is not a Group C content defect.

   **Remediation:** For future runs, create the task from a repository baseline or save a before/after file manifest (with hashes) for the permitted scope and its parent directory. No change to these Group C deliverables is required.

## Verification commands

```bash
jq empty coordination/b10-r03/group-c/accessions.json
sha256sum coordination/b10-r03/group-c/*.wikitext
wc -c coordination/b10-r03/group-c/*.wikitext
# For each accession, replay the exact source object:
curl --fail --location --get 'https://zh.wikisource.org/w/index.php' \
  --data-urlencode 'title=…' --data-urlencode 'oldid=…' \
  --data-urlencode 'action=raw' --data-urlencode 'ctype=text/plain'
```
