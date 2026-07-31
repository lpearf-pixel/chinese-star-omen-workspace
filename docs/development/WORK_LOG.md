# 开发工作日志

按时间倒序记录实际开发批次、任务编号、改动、验证证据和遗留风险。任务只有在这里记录最新验证后才能在 `TASKS.md` 标记 `DONE`。

## 2026-07-30 — B10-PR-A contract work started

PR #51 final exact head
`909b24c3738f0d300c3c66be296d07095b2b4e10` passed Development Governance
`30599537056`, Kaiyuan Stable Core `30599537037` and Kaiyuan Upstream Runtime
`30599537036`. It had five expected documentation files, zero reviews, zero
review threads and matching local/remote blob SHA values. GitHub squash merged
it as `0df8c70551c1746d073a390e3fcd9371a5de8e5d`.

B10-PR-A started from that exact commit on
`codex/kaiyuan-b10-omen-rule-v2`. Scope is limited to strict
`OmenRule/v2`/`RuleCandidate/v2` contracts, identity and immutable history,
explicit v1 migration reports, an annotation guide and frozen reviewed
fixtures. Passage inventory, extraction, model use, review queues, Qdrant,
official ingest, B11/B12 and corpus mutation remain out of scope. Tests must
fail first before implementation.

TDD RED was observed when the focused test could not import the absent
`kb_contracts.omen_rule_v2` module. The implemented checkpoint now includes:

```text
RuleCandidate/v2 deterministic identity and canonical JSON
proposal-hash-bound append-only candidate history
model/extractor approval rejection
OmenRule/v2 human approval and complete citable evidence
immutable rule versions and content hashes
explicit fail-closed v1 migration reports
annotation guide plus 6 manually inspected hash-frozen cases
canonical candidate/rule contract fixtures
```

Compatibility review removed eager v2 imports from `kb_contracts.__init__`, so
existing lightweight sync/index consumers do not gain an undeclared Pydantic
dependency. Preliminary verification:

```text
shared contract tests: 23 passed
downstream tests: 487 passed
upstream tests: 188 passed, 3 skipped by existing integration flags
compileall: passed
git diff --check: passed
```

The fresh final local pass repeated all three suites with the same results.
Additional checks passed: v2 JSON schema `$id` and
`additionalProperties=false`, governance unit tests `5/5`, development
governance `changed_files=18 code_files=5`, canonical fixture/annotation hash
bindings, legacy `kb_contracts` import without site packages, external
I/O/mutation scan and exact changed-path audit.

B10-PR-A is now `VERIFYING`. Remaining work is commit, Draft PR, exact-head
hosted gates, review/thread audit and merge. No corpus, Qdrant, collection,
ingest, model call, B11/B12, `local_kb_default` or `main` operation occurred.

Draft PR #52 targets only `stable/kaiyuan-v2`. Its initial exact head
`cbb2fc7c82e7b73404089bca0fd4ecae2915b422` is one commit ahead of the exact
base, and its remote tree
`aa317a5da706bb53ac896815ecb620db0561de8a` exactly matches the locally
verified tree. All 18 remote blob SHA values were checked during publication.

```text
Development Governance 30600436677: success
Kaiyuan Stable Core 30600436719: success
Kaiyuan Upstream Runtime 30600436650: success
changed files: 18 expected
submitted reviews: 0
review threads: 0
mergeable: true
```

B10-PR-A is `DONE` in the PR #52 merge candidate. This evidence-only status
update creates a new exact head; it must repeat all required workflows and the
review/thread/diff audit before expected-head squash merge. PR-B cannot start
from the feature branch.

## 2026-07-30 — B10-T00 program charter started

PR #50 was rechecked as merged into `stable/kaiyuan-v2`. Independent fetch
resolved the stable ref to
`a10e33118c2e34f947a099492bb01e13a07a98a8`; the merged closeout file is
present. The only open pull requests remain legacy #1 and #7, neither of which
targets the stable release line.

B10 now starts on the independent branch
`docs/kaiyuan-b10-planning-v1`. Task B10-T00 freezes governance before
`OmenRule/v2` implementation:

```text
whole-book denominators: 6 explicit terminal-coverage conditions
implementation sequence: B10-PR-A through B10-PR-H
citable evidence false-positive gate: 0
deterministic formal-candidate precision target before pilot: >= 0.90
threshold authority: canonical threshold-freeze.json after B10-PR-C pilot
long jobs: stable batch ID, checkpoint/resume, idempotent no-overwrite outputs
model extraction: optional and disabled by default
B11 input: approved/citable engine-gap-report only
```

No contract, extractor, corpus, candidate, review queue, model, Qdrant,
collection, B11 or B12 behavior changes in B10-T00. `main` and
`local_kb_default` remain outside scope.

Local verification completed before publication:

```text
charter acceptance scan: PASS
governance unit tests: 5/5 PASS
development governance checker: PASS (changed_files=5, code_files=0)
compileall: PASS
git diff --check: PASS
```

B10-T00 is now `VERIFYING`. It remains incomplete until the final feature head
passes hosted exact-head gates, changed-file/review/thread audit and merges into
`stable/kaiyuan-v2`.

Draft PR #51 targets only `stable/kaiyuan-v2`. Its initial exact head
`fb7fb012a98a7d6d75d37354da3b9ca73d743e76` contains exactly five expected
documentation files, with remote blob SHA values identical to the locally
verified files. The first exact-head workflows completed successfully:

```text
Development Governance 30599473112: success
Kaiyuan Stable Core 30599473165: success
Kaiyuan Upstream Runtime 30599473127: success
```

B10-T00 is `DONE` in the PR #51 merge candidate. This evidence-only status
update creates a new head, so the same workflows, changed-file audit,
review/thread audit and mergeability check must pass again before merge. PR-A
must start from the resulting stable squash SHA, not from this feature branch.

## 2026-07-30 — B9 final closeout started after corrected G6 acceptance

Remote `stable/kaiyuan-v2` was independently fetched as
`e5a5315fcea72ea878bf62968170d4f262fabc5d`, the squash merge of PR #49.
The only open pull requests remain legacy #1 and #7; neither targets
`stable/kaiyuan-v2`. The closeout branch is
`docs/kaiyuan-b9-final-closeout-v1`.

PR #49 exact-head evidence at
`69faf14ee60c43bd65b36d67b1f23ab4f779d298`:

```text
Development Governance 30566529753: success
Kaiyuan Stable Core 30566529828: success
Kaiyuan Upstream Runtime 30566529785: success
Changed files: 8 expected
Review threads: 0
Submitted reviews: 0
Squash merge: e5a5315fcea72ea878bf62968170d4f262fabc5d
```

The uploaded corrected archive
`b9-local-g6-evidence-20260730T121805Z-corrected-v1.tar.gz` has SHA-256
`8a4af09210961fada5cb6e8ac1a3344d4055307bb7d8c48920c90f71c4020214`.
Fresh independent verification against the exact merged stable models proved:

```text
archive members: 19 fixed members
unsafe paths, links or devices: 0
absolute machine paths: 0
AppleDouble members: 0
screenshot inventory: 5 relative entries, all hashes matched
stable modeled artifacts: 8/8 canonical
renderer hard gate: passed, 0 issues
AI visual review: needs_human_review
human experience checks: all true
resolved assisted review: approved
Stellarium: 26.1.0, matching the visible Stellarium 26.1 window
FFmpeg: 8.1.2
preview: 1080x1920, H.264, 80000 ms, 1 video, 0 audio
preview SHA-256: eaf290ef84630c5a8bc80cf675c7279c61da76f360c19f58b557e71c6b9c9bd3
screenshots: 5, all capability/review/OCR hashes byte-bound
visual contact-sheet review: no clipping, internal field leakage or path leakage
disposition: accepted for B9-G6
```

The earlier archives with SHA-256
`fc49031dc98083e46aad912b3cfaa43cea611ec80934c37352ba9691cf9eff52`
and
`0271e15b99151811123ff47f25e5254dec42703001e6bc8079344e6f66916918`
remain rejected and immutable.

B9-G6-E4 and B9-G6-E6 are now `DONE`. Draft PR #50 targets only
`stable/kaiyuan-v2`. Its initial exact head
`a2f2c9c668f5a9b0da4ee13a424b9eea93fa1093` had four expected documentation
files, no submitted reviews or review threads, was mergeable, and passed:

```text
Development Governance 30598928710: success
Kaiyuan Stable Core 30598928837: success
Kaiyuan Upstream Runtime 30598928873: success
```

B9-FINAL-CLOSEOUT and B9 overall are `DONE` in the PR #50 merge candidate.
The final status-only documentation head must rerun the same required
workflows. B10 remains `BLOCKED` until PR #50 is actually merged and the
resulting stable head is independently reverified.

## 2026-07-30 — B9-G6-E6 evidence handoff integrity started

Remote `stable/kaiyuan-v2` was resolved as
`c2be80c2adbf307178c353a6769ab98c170d1930`, the merge commit of PR #48.
The only open pull requests remain legacy #1 and #7; neither targets the stable
release line.

The uploaded archive
`b9-local-g6-evidence-20260730T121805Z.tar.gz` has SHA-256
`0271e15b99151811123ff47f25e5254dec42703001e6bc8079344e6f66916918`.
Safe extraction and exact stable-model verification proved:

```text
unsafe archive paths or links: 0
canonical renderer review input/report: passed
renderer hard gate: passed, 0 issues
AI visual review: needs_human_review
human experience checks: all true
resolved assisted review: approved
preview: 1080x1920, H.264, 80000 ms, 1 video, 0 audio
preview SHA-256: eaf290ef84630c5a8bc80cf675c7279c61da76f360c19f58b557e71c6b9c9bd3
screenshots: 5, all review/capability/OCR hashes bound
```

The handoff itself failed closed for three independently reproduced reasons:

1. the capability JSON records Stellarium `26.2.0`, while the bound overview
   window title shows Stellarium `26.1`;
2. all five lines in `screenshot-sha256.txt` contain a private `/Users/...`
   absolute path;
3. macOS tar added sixteen AppleDouble `._*` members, including five entries
   that become extra `screenshots/*.png` files after Linux extraction.

The core evidence bytes remain preserved. B9-G6-E6 will replace manual version
entry and platform tar behavior with a tested, dependency-free handoff
packager. B9 remains `VERIFYING`; run `20260730T121805Z` is not accepted and
B10 remains blocked until a corrected archive passes independent verification
and final B9 closeout merges.

TDD and pressure verification:

```text
RED: real CLI invocation failed because scripts/b9_g6_handoff.py did not exist
Initial GREEN: 8 handoff behaviors passed
Version-only RED: argparse required archive inputs
Version-only GREEN: 9 behaviors passed
Identity-binding RED: capability validation and archived bytes used separate file snapshots
Final handoff GREEN: 10 behaviors passed
Preview/collector related regressions: 10 passed
Combined direct plain-assert harness: 20 passed
compileall: passed
collector bash -n: passed
CLI help: passed
git diff --check: passed
```

The current execution environment does not provide pytest and cannot reach the
package index, so the same pytest-compatible functions were invoked directly
with isolated temporary directories. Exact-head pytest, full repository gates
and remote workflows remain required before merge.

The new packager then pressure-tested the actual extracted evidence:

```text
Claimed 26.2.0 with synthetic actual app 26.1:
  rejected; no output created
Canonical capability rebuilt as 26.1.0:
  archive members: 19
  relative screenshot inventory entries: 5
  AppleDouble members: 0
```

The command reads `CFBundleShortVersionString`, normalizes `26.1` to `26.1.0`,
requires capability equality, enumerates only fixed regular non-symlink
members, derives the inventory in memory, normalizes tar/gzip metadata and
publishes with exclusive no-overwrite semantics. Post-review hardening also
archives the exact bounded capability bytes used for version validation,
preventing a changed capability file from crossing the validation-to-archive
boundary. B9-G6-E6 is `VERIFYING`.

## 2026-07-30 — B9-G6-E5 FFmpeg runtime preflight started

The first source-backed preview later reached the hash-bound AI visual gate and
was correctly rejected: the historical subtitle exposed the internal
`catalog_context` value and English catalog title. The rejected run
`20260730T073457Z` remains immutable and must never enter the collector.

The root cause was `_prepare_historical_assets()` concatenating
`source_type/source_title` into audience copy. TDD changed the existing
consumer-level regression first:

```text
Audience-copy RED: expected `历史背景：...`, received the subtitle containing
`catalog_context` and `Chinese sky-culture catalog context`
Audience-copy GREEN: 1 passed
Editorial regression: 41 passed
Astronomy/editorial/package-review/runner/collector regression: 170 passed
```

The minimal implementation now emits only `历史背景：{approved text}` while
retaining the original structured source fields and exact `historical_source`
asset reference. D-024 records the separation between audience copy and
provenance. Full exact-head gates and a new-run macOS evidence chain remain
required.

Remote `stable/kaiyuan-v2` was independently resolved as
`23e9d0fce3c5f2609456430f9829234afe2e704b`. PR #45, #46 and #47 are merged;
legacy PR #1 and #7 remain unrelated to the stable release line.

The fresh macOS package reached `manifest verification: PASS`, then the selected
FFmpeg failed before writing `preview.mp4`:

```text
No option name near 'subtitles.srt'
Error parsing filterchain 'subtitles=subtitles.srt'
subprocess.CalledProcessError: exit status 234
```

The earlier diagnosis was too narrow: this output proves FFmpeg started and the
filtergraph failed, but does not alone prove a missing file, a PATH defect or
one specific package formula. B9-G6-E5 therefore uses a real bounded subtitle
smoke against the selected executables rather than trusting PATH, package
labels or advertised feature lists alone.

Accepted design: keep `PreviewCommand/v1` and package bytes machine-independent;
resolve runtime binaries through optional `B9_FFMPEG_BIN` /
`B9_FFPROBE_BIN` overrides or PATH; fail early on missing features or failed
smoke; then execute the exact frozen argv with only argv zero replaced by the
verified executable. No Qdrant, corpus, candidate, collection or publishing
scope is added.

TDD and verification:

```text
Runtime runner RED: scripts/b9_preview.py missing; 4 failed as expected
Runtime runner GREEN: 4 passed
Make entrypoint RED: no rule to make target b9-preview
Runner plus Make GREEN: 5 passed
B9 package-review plus collector/runner: 100 passed
Runtime/collector/governance focused: 13 passed
Shared contracts: 6 passed
Text core: 22 passed
Full downstream: 487 passed
Governance diff gate: passed (11 changed files, 2 code files)
compileall: passed
Runbook embedded Python: 5 blocks parsed
```

The first final diff check correctly rejected one trailing blank line in each
new spec/plan. Those two documentation-only defects were removed. Because this
evidence update creates a new docs head, the complete gates are rerun before
remote publication. B9-G6-E5 is `VERIFYING`; hosted tests do not prove the real
macOS FFmpeg/Stellarium evidence run.

Independent review then found three Important execution-boundary defects:

1. a failed preview command could create `preview.mp4`, after which cleanup
   unconditionally deleted that path and could race with another process;
2. preview validation accepted any argv beginning with `ffmpeg` and ending in
   `preview.mp4`, including network inputs, `-y` or extra outputs;
3. missing-feature diagnostics did not identify the actual PATH-selected
   executables.

Three regressions first failed. The runner now never unlinks an output created
during execution, requires the complete fixed B9 command and metadata shape,
and includes resolved FFmpeg/ffprobe identities plus both override names in
every post-resolution preflight failure. Focused package-review, collector and
runner result after the review fix: `102 passed`.

## 2026-07-30 — B9-G6-E4 lightweight human confirmation started

PR #45 was rechecked at exact remote head `944a55458aa06916f6751a462659e9f8a5826494`: it was mergeable, had no reviews or unresolved threads, and all five applicable workflows concluded `success`. It was marked ready and merged into `stable/kaiyuan-v2` as `f937c60c76f5e450279e05b3c04de67e296fa687`.

B9-G6-E4 starts on `codex/kaiyuan-b9-light-human-confirmation-v1`. The accepted scope is exactly three layperson checks plus a pure final resolver. No human input may alter scientific, evidence, media or AI fields, and no approval control is available after machine or AI rejection.

PR #46 was later rechecked at exact remote head `b719add4ce0cb664624fb09cd92a9fa31c5d7042`: it was mergeable, had no reviews or unresolved threads, and Development Governance, B9 Assisted Renderer Review, B9 Package Review Preview, Kaiyuan Stable Core and Kaiyuan Upstream Runtime all concluded `success`. It was marked ready and merged into `stable/kaiyuan-v2` as `939c5272a84a1bf3dd2e9c72037ea180f76e8adf`.

Implementation is merged. E4 and B9 remain `VERIFYING`; the next action is a fresh macOS run, normalized AI visual report, three-check native confirmation and independent archive verification.

TDD progress:

```text
Final decision contract RED: HumanExperienceConfirmationV1 missing
Final decision contract GREEN: 8 passed
macOS collector RED: repository script missing, 3 failed
macOS collector GREEN: 3 passed; bash -n passed
```

The collector re-verifies the hard gate, normalized AI report, preview and ordered screenshot bytes before opening QuickTime, Preview or any native dialog. It contains no terminal stdin approval and writes canonical human/final reports with exclusive creation.

E4 implementation is `VERIFYING`. Real G6 evidence remains blocked until the implementation is merged and the repository collector runs on macOS with a fresh run ID. Hosted or Linux verification must not mark the real-evidence plan steps complete.

Self-review found that callers could construct a final-report reason without the report hashes that reason logically requires. Four regression cases first failed; the strict model now requires AI and/or human hashes for `ai_rejected`, `human_rejected`, `human_confirmation_missing`, `binding_mismatch` and `approved`, and forbids later hashes when the AI report is missing. Review-fix focused result: `12 passed`.

Fresh local verification on implementation head `8e403e8a42fc3a07164810e152d3bea5853532ab`:

```text
B9 assisted renderer focused: 160 passed
macOS collector static tests: 3 passed
bash -n collector: passed
Shared contracts: 6 passed
Text core: 22 passed
Full downstream: 487 passed
Governance unit tests: 5 passed
Development governance diff gate: passed (9 changed files, 3 code files)
compileall: passed
Runbook embedded Python: 6 blocks parsed
git diff --check: passed
Working tree: clean before this verification-evidence update
```

The evidence update creates a docs-only head; every listed local gate is rerun on that exact head before remote publication.

## 2026-07-30 — B9-G6-E3 AI visual review started

PR #44 was rechecked at exact head `6304f88b0a42d3ded9a5c67276495177fc7fd579`: it was mergeable, had no reviews or unresolved threads, and all seven pull-request workflows concluded `success`. It was marked ready and merged into `stable/kaiyuan-v2` as `d6f2f862d7cf45c1008925f6d4286aabb4e43077`.

The only open repository pull requests remain legacy PR #1 and #7; neither targets `stable/kaiyuan-v2`. B9-G6-E3 starts on `codex/kaiyuan-b9-ai-visual-review-v1` under the approved provider-neutral AI visual review plan. The core accepts normalized JSON only, requires exact hard-gate/media/screenshot hash binding, and gives AI no scientific, classical-evidence or publication authority.

TDD progress:

```text
AI report contract RED: AIAssistedVisualCheckV1/AIAssistedVisualReviewV1 missing
AI report contract GREEN: 9 passed
AI binding verifier RED: verify_ai_visual_review missing
AI contract plus binding verifier GREEN: 16 passed
```

The provider-neutral handoff records the exact request/response JSON, requires real provider/model/prompt-policy identifiers, and excludes secrets, machine paths and raw provider responses. Core code has no mandatory provider SDK and performs no network call.

Self-review found that the initial verifier proved the AI report matched observed media but did not prove the passed hard-gate report had checked those same bytes. New regressions first failed `3` cases, then the verifier required exact `preview.mp4` and ordered `screenshots/*` bindings in the hard-gate artifact set. The runbook now adds screenshot bindings to `RendererReviewInputV1`. Evidence-frame order is also canonicalized against the screenshot inventory. Review-fix focused result: `18 passed`.

B9-G6-E3 is now `VERIFYING`. No completion or merge claim is valid until the exact implementation head passes focused, shared-contract, text-core, downstream, governance, compile and runbook syntax gates and the resulting remote PR head passes its workflows.

Fresh local verification on implementation head `6b34494918989b6262b3614a1753ef95056b7808`:

```text
B9 assisted renderer focused: 148 passed
Package review: 80 passed
Shared contracts: 6 passed
Text core: 22 passed
Full downstream: 475 passed
Governance unit tests: 5 passed
Development governance diff gate: passed (10 changed files, 3 code files)
compileall: passed
Runbook embedded Python: 6 blocks parsed
git diff --check: passed
Working tree: clean before this verification-evidence update
```

This evidence update creates a new docs-only head; the same gates are rerun on that exact head before remote publication.

## 2026-07-30 — B9-G6-E2 scientific hard gate verifying

PR #43 was confirmed merged into `stable/kaiyuan-v2`; independent `git ls-remote` resolved the actual stable ref as `28f3b2a1ce5a9e324b6fc03060423bbacf1b917a`. The isolated branch is `codex/kaiyuan-b9-assisted-review-gate-v1`.

The first real macOS G6 archive `b9-local-g6-evidence-20260730T040856Z.tar.gz` passed archive SHA-256, safe member paths, media properties, screenshot hashes, scene hash and capture timing. Content review rejected it because the fixture and narration asserted `3.25°` while verified offline Skyfield 1.51 with `de421.bsp` computes `5.40412185407934°` for the exact 2026-07-21 11:00 UTC Shanghai topocentric observation. The old fixture also contained a placeholder ephemeris hash and incorrect `icrs` measurement frame.

TDD evidence:

```text
Renderer hard-gate contract RED: assisted_review module missing
Renderer hard-gate contract GREEN: 4 passed
Scientific verifier RED: verify_recomputed_astronomy missing
Scientific verifier GREEN with hard-gate regressions: 8 passed
Local sample RED 1: local_sample module missing
Local sample RED 2: source-backed fixture differed from hand-authored fixture
Astronomy/editorial/package-review after fixture migration: 126 passed
Artifact/OCR gate RED: OCRObservationV1 missing
Artifact/OCR plus hard/scientific gates GREEN: 11 passed
Post-review RED: unordered review artifacts and event/calculation identity drift were accepted
Post-review GREEN: canonical artifact ordering and event/calculation identity are enforced
Final focused astronomy/editorial/package-review: 130 passed
Workflow YAML, all five runbook Python blocks and compileall: PASS
Contracts: 6 passed
Text core: 22 passed
Downstream first run: 455 passed / 1 failed because fixture manifest retained the old event SHA-256
Downstream after canonical manifest migration: 456 passed
Final exact-workspace downstream after review fixes: 457 passed
```

Delivered locally:

- canonical path-free `RendererReviewInputV1` and `RendererHardGateReportV1`;
- stable hard issue codes and non-overridable derived status;
- placeholder provenance, exact event identity and `0.01°` recomputation checks;
- provider-built July event with `de421.bsp` SHA-256 `a20a7139da04cbc462454634918e9a9ca69127044e2cc9d4f9c16e238d2deedc`;
- artifact, preview, screenshot inventory and normalized caller-supplied OCR checks;
- hermetic focused workflow and runbook hard-gate stage before visual approval.

The task is `VERIFYING`, not `DONE`. Remaining: independent code review, exact-head local rerun, explicit user authorization to publish the committed branch contents, remote PR workflows and merge. No corpus, candidate, ingest, Qdrant, collection, `local_kb_default`, `main`, publishing or B10–B12 behavior changed.

## 2026-07-18 — B8-T02 merged

```text
PR: #28
Final head: 8e4e1e704d19559bb2bf213a5d7143cd16f04e8a
Development Governance: 29674325255 — success
Kaiyuan Stable Core: 29674325256 — success
Kaiyuan Upstream Runtime: 29674325263 — success
Squash merge: 9945fc4c76cdc3521cd9ab6dbe7a068580582bbf
```

Immediately before merge PR #28 was base `stable/kaiyuan-v2`, non-draft, mergeable, scoped to the seven expected workflow/test/governance files, and had no submitted review or unresolved review thread. GitHub merged the expected exact head, and independent `git ls-remote` resolved the stable ref to the same actual squash SHA. The hermetic gate composes the real capture, assembly, bundle, and offline verification contracts, audits protected fake inspection once per phase, and proves tampering fails before bundle creation. It performs no live service/Qdrant/corpus/candidate/ingest/routing or collection mutation and does not treat synthetic CI as production evidence. B8-T02 is DONE; only this docs-only closeout PR remains.

## 2026-07-18 — B8-T01 merged

```text
PR: #26
Final head: d58e7ff91adf54a35b9d9d49c54a3a2fa5a12ad0
Development Governance: 29673734249 — success
Kaiyuan Stable Core: 29673734284 — success
Kaiyuan Upstream Runtime: 29673734259 — success
Squash merge: c6af74a5875d3df55e56bbea251ede63b56c427c
```

GitHub returned `merged=true` for the exact reviewed head, and independent `git ls-remote` plus fetch resolved `refs/heads/stable/kaiyuan-v2` to the actual squash SHA. Immediately before merge PR #26 was base `stable/kaiyuan-v2`, non-draft and mergeable; changed-file audit contained only the offline archive module/CLIs/tests, CI, runbook, and development/design/plan evidence. Review threads and submitted reviews were empty, and independent review had no remaining Critical/Important finding.

The implementation verifies every B7-T03 bundle, emits a path-free deterministic archive index, and classifies only `retain|cold_archive_eligible`; it never moves or deletes evidence. It does not target `main`, access corpus/candidates/ingest/runtime retrieval/Qdrant data, or read/write `local_kb_default`. B8-T01 is DONE. Closeout exact-head gates remain before the next task starts.

## 2026-07-18 — B8-T01 evidence archive index started

- Actual base: `stable/kaiyuan-v2` at `dfefb73daf001af051a50a461c63a4e7ab308fe8` (B7-T03 closeout PR #25).
- Branch: `codex/kaiyuan-release-evidence-archive-v2`; PR will target only `stable/kaiyuan-v2`.
- Task moved to `IN_PROGRESS` before behavior implementation.
- Selected design: explicit logical-name/path bundle map, full B7-T03 verification, deterministic content-free archive index, and classification-only retention. Automatic scan and any move/delete behavior are excluded.
- Design: `docs/superpowers/specs/2026-07-18-kaiyuan-release-evidence-archive-design.md`; decision D-020.
- Plan: `docs/superpowers/plans/2026-07-18-kaiyuan-release-evidence-archive.md`; self-review found no placeholder, uncovered spec requirement, or interface mismatch.
- Draft PR: #26, base `stable/kaiyuan-v2`; initial published design/plan head `fb4cb4c1e6360a2c3498ca801340e426da095c0d`.
- Baseline: B7-T03 focused bundle suite → `21 passed in 0.17s`.
- TDD RED: focused archive test failed during collection with `ModuleNotFoundError: release_evidence_archive`.
- TDD GREEN: the same focused test passed after the minimal pure builder implemented full B7 verification, safe provenance projection, deterministic per-target latest/pin classification, and stable final ordering.
- TDD RED 2: the expanded archive suite failed during collection because `canonical_index_bytes` and `verify_archive_index` did not exist.
- TDD GREEN 2: policy/name/pin/bundle validation plus strict canonical rebuild verifier passed `24 passed`.
- TDD RED 3: four CLI tests failed because `create_release_evidence_archive.py` and `verify_release_evidence_archive.py` did not exist.
- TDD GREEN 3: atomic create/verify CLI, safe binding parsing and no-path serialization passed the full archive suite, `28 passed`.
- Related regression after Make/CI/runbook integration: archive, bundle, artifact, observation and release-drill suites → `132 passed in 3.42s`.
- Initial Make missing-argument contract exited `2`, but independent review later showed that a Make whitespace list cannot preserve bundle paths containing spaces; archive Make targets were removed and the runbook now uses separately quoted repeated CLI arguments.
- Implementation includes pure deterministic classification, strict index verifier, bounded reads, atomic hard-link no-overwrite output, create/verify CLIs, named CI coverage, and classification-only runbook instructions. Production scan found no network/Qdrant/ingest/routing integration; the only deletion-like call is same-directory temporary-file cleanup after atomic publication, never an evidence bundle or completed index.
- B8-T01 is now `VERIFYING`, not `DONE`. Remaining: full local gates, independent review, latest-head PR #26 workflows, merge and closeout evidence.

### Independent review fixes

Independent review found no Critical and three Important issues. Each was reproduced before the fix:

1. Input files were fully read before size checks. RED proved no bounded reader existed. The shared reader now requests at most `limit + 1` bytes for bundles and indexes, then fails `input_too_large` without loading the remainder.
2. Latest sorting converted datetimes to float Unix timestamps, collapsing valid year-9999 microseconds. RED selected the older `.000001Z` bundle over `.000002Z`. Stable two-pass ordering now compares exact `datetime` values and preserves release-head/hash tie-breakers.
3. Make `foreach` split `NAME=PATH` bindings on whitespace. RED confirmed unsafe archive Make targets existed. They were removed; runbook commands pass every repeated `--bundle` as a separately quoted CLI argument and explicitly support paths with spaces.

A separate fail-closed RED also found non-string/unhashable pin values could raise raw `TypeError`; validation now checks pin type/format before duplicate-set construction. Focused post-fix verification is required before full gates are considered current.

### Post-review local verification

```text
focused review regressions: 3 passed
archive plus B6/B7 related regression: 136 passed
make contracts-test: 6 passed
make text-core-test: 22 passed
make downstream-test: 220 passed
make upstream-test: 185 passed, 3 environment skips
make release-drill: passed, all 13 checks true
governance --base dfefb73d... --head 501b15a1...: passed, changed_files=11, code_files=4
git diff --check: passed
forbidden component diff scan: empty
machine-path/private-key/embedded-key scan: no match
```

Verified implementation head before this evidence-only commit: `501b15a1f0335d0c83db773f11019721daa8c863`. Independent review has no remaining Critical/Important finding after the three review-fix RED/GREEN cycles. PR #26 remains draft; this evidence commit changes the head, so all three workflows must succeed on the newly published exact head before ready/merge.

## 2026-07-18 — B7-T03 merged

```text
PR: #24
Final head: 71cc8d9e299154d877b7600d2e042c4541312339
Development Governance: 29672619531 — success
Kaiyuan Stable Core: 29672619536 — success
Kaiyuan Upstream Runtime: 29672619530 — success
Squash merge: bf56df0a1f396d1e2db40f72c6b52e809dd7ab9c
```

GitHub returned `merged=true` for the exact reviewed head, and independent `git ls-remote` plus fetch resolved `refs/heads/stable/kaiyuan-v2` to the actual squash SHA above. PR metadata was base `stable/kaiyuan-v2`, non-draft and mergeable immediately before merge; all three workflows belonged to the actual final head, review threads and submitted reviews were empty, and independent safety review had no remaining Critical/Important finding.

The merged 13-file diff is limited to the offline deterministic evidence bundle module/CLIs/tests, Make/CI entry points, runbook, design/plan/decision/task/work-log. It does not target `main`, change corpus/candidates/ingest/runtime retrieval/Qdrant schema or data, or access/write `local_kb_default`. B7-T03 is DONE. The closeout PR and its exact-head gates remain before starting the next task.

## 2026-07-18 — B7-T03 release evidence bundle started

- Actual base: `stable/kaiyuan-v2` at `d3aaea12f0a033703e91ee1f715441761444d563` (B7-T02 closeout PR #23).
- Branch: `codex/kaiyuan-release-evidence-bundle-v2`; PR will target only `stable/kaiyuan-v2`.
- Task moved to `IN_PROGRESS` before behavior implementation.
- Selected design: deterministic stored ZIP with strict internal inventory, atomic hard-link publication, no extraction, and offline byte plus semantic revalidation. Directory and external-reference alternatives were rejected because they cannot preserve the same atomic/no-overwrite or portability guarantees.
- Design: `docs/superpowers/specs/2026-07-18-kaiyuan-release-evidence-bundle-design.md`; decision D-019.
- Baseline: `PYTHONPATH=. /tmp/kaiyuan-b5/bin/pytest -q tests/test_release_drill_v1.py tests/test_release_observation_v1.py tests/test_release_artifact_v1.py` from `apps/local-kb-unified` → `83 passed in 2.31s`.
- Environment note: bare `pytest` was unavailable; this was a shell environment issue, not a test failure. The existing isolated venv `/tmp/kaiyuan-b5` ran the baseline without dependency or assertion changes.
- Plan: `docs/superpowers/plans/2026-07-18-kaiyuan-release-evidence-bundle.md`; self-review found no uncovered spec requirement, placeholder, or interface mismatch.
- Draft PR: #24, base `stable/kaiyuan-v2`, head `codex/kaiyuan-release-evidence-bundle-v2`; initial published design/plan head `fff4c4a320db6dfef73b0c06f77d289c7611dc1f`.

### TDD and implementation evidence

```text
RED 1:
PYTHONPATH=. /tmp/kaiyuan-b5/bin/pytest -q tests/test_release_evidence_bundle_v1.py::test_create_and_verify_deterministic_bundle
result: collection error, ModuleNotFoundError: release_evidence_bundle

GREEN 1:
same command
result: 1 passed

RED 2:
PYTHONPATH=. /tmp/kaiyuan-b5/bin/pytest -q tests/test_release_evidence_bundle_v1.py
result: 4 failed, 11 passed
root causes: verifier accepted ZIP member comment/extra/compression metadata and leaked a lower-level ReleaseArtifactError for semantic tampering.

GREEN 2:
same command after fixed metadata checks and stable exception normalization
result: 15 passed

RED 3:
PYTHONPATH=. /tmp/kaiyuan-b5/bin/pytest -q tests/test_release_evidence_bundle_v1.py::test_create_and_verify_clis_publish_once_without_temp_residue
result: 1 failed because create_release_evidence_bundle.py did not exist

GREEN 3:
PYTHONPATH=. /tmp/kaiyuan-b5/bin/pytest -q tests/test_release_evidence_bundle_v1.py
result: 18 passed in 0.16s
```

Implemented deterministic stored ZIP creation, exact internal inventory, explicit release-head/time provenance, strict finite/unique/bounded JSON, bounded no-extraction verification, byte hash/size checks, semantic reassembly and B6 validation, atomic hard-link publication, create/verify CLIs, Make targets, CI coverage, and runbook operations. No network/Qdrant/ingest/routing/corpus/candidate integration was added.

Related regression: bundle plus B6/B7 drill/observation/artifact tests → `101 passed in 2.38s`. Make missing-argument contract exited `2` with the exact required-variable list. Production forbidden-import/mutation scan returned no match. B7-T03 is now `VERIFYING`, not `DONE`.

Remaining: run full local gates, perform independent review, publish implementation head to PR #24, require exact-head CI, then merge only if every safety/review condition remains satisfied.

### Independent review fixes

Independent safety review found no Critical and two Important issues:

1. Python `ZipFile` accepted arbitrary trailing bytes, so member-level checks alone did not prove exact deterministic archive bytes. RED: `verify_bundle_bytes(valid_bundle + b"SECRET")` returned healthy success. Fix: after byte and semantic validation, deterministically rebuild the complete archive and require exact byte equality, covering trailing data and noncanonical local/central metadata.
2. Creator allowed reused `ReleaseArtifactError` to escape, producing a traceback and unstable exit semantics for strict-JSON but contract-invalid observation/manifest input; verifier also collapsed drill failure into assembly mismatch. RED: the two focused review tests failed, including a full traceback from `observation_contract_error`. Fix: translate all assembler exceptions at the pure boundary using content-free stable fields and preserve `drill_validation_failed` distinctly.

Review-fix GREEN: the two focused regressions passed, then the full bundle suite passed `21 passed in 0.17s`. A separate TDD RED/GREEN also made canonical JSON bytes mandatory even when a tamperer recomputed inventory hashes. Full gates must be rerun on the resulting head.

### Final local verification after review fixes

```text
make contracts-test: 6 passed
make text-core-test: 22 passed
make downstream-test: 220 passed
make upstream-test: 153 passed, 3 environment skips
make release-drill: passed, all 13 checks true
python scripts/check_development_governance.py --base d3aaea12... --head a80e76b7...: passed, changed_files=13, code_files=6
git diff --check: passed
forbidden component diff scan: empty for corpus, star-omen, contracts, text-core, index-jobs and upstream data
machine-path/private-key/embedded-key scan: no match
```

Verified implementation head before this evidence-only commit: `a80e76b76f0f4e94e35c38a02d5635a6df8463e2`. Scope is limited to the offline bundle pure module/CLIs/tests, Make/CI entry points, runbook, design/plan/decision/task/work-log. No raw corpus, candidate, ingest, runtime retrieval, Qdrant schema/data, `main`, or `local_kb_default` operation changed. The evidence commit creates a new head, so GitHub workflows on that exact published head remain mandatory before completion.

## 2026-07-18 — B7-T02 merged

```text
PR: #22
Final head: 23168954f809f046dedee7d1ce107be8dd0332d4
Development Governance: 29670048368 — success
Kaiyuan Stable Core: 29670048362 — success
Kaiyuan Upstream Runtime: 29670048361 — success
Squash merge: 4abd11d5f5c30991656cbf525f9f3be0ff3fbf38
```

GitHub returned `merged=true`, and independent `git ls-remote` resolved `refs/heads/stable/kaiyuan-v2` to the same squash SHA. Final PR metadata was base `stable/kaiyuan-v2`, non-draft, mergeable, with zero review threads/submitted reviews. Independent review found no Critical; every Important finding was reproduced with RED tests and fixed before the final exact-head workflows. Final local evidence: 37 focused, 6 contracts, 22 text-core, 220 downstream, and 132 upstream tests passed (3 environment skips), plus the passing 13-check release drill and governance check.

The merged 12-file scope is limited to the offline pure assembler/CLI, tests, Make/CI entry points, runbook, design/plan/decision, and task evidence. It contains no network/Qdrant client, routing, ingest, corpus/candidate, collection schema/data, `main`, or `local_kb_default` mutation. B7-T02 is DONE. No later READY task is registered.

## 2026-07-18 — B7-T02 started

### Implementation verifying

Implemented the pure offline assembler and strict atomic CLI, Make entry points, a named synthetic CI step, and runbook assembly instructions. The implementation imports the existing B6 constants/validator, binds exact B7 observation envelopes and phase slots, requires strictly increasing canonical UTC capture times, projects only approved manifest identity, and creates output only after the B6 report passes. It contains no HTTP/Qdrant/ingest integration and performs no routing, corpus, candidate, collection, or `local_kb_default` mutation.

Observed TDD evidence:

```text
RED 1  ModuleNotFoundError: release_artifact
GREEN  pure happy path 1 passed
RED 2  3 failures: timezone offset, invalid date, non-increasing chronology accepted
GREEN  pure contract suite 15 passed
RED 3  4 failures: assemble_release_artifact.py absent
GREEN  focused assembler suite 22 passed, including strict JSON/UTF-8, exact artifact hash, and no-live/mutation source assertions
```

B7-T02 is `VERIFYING`, not `DONE`. Remaining: add final source/strict-parser safety assertions, run full gates and governance, publish exact head, latest-head workflows, independent review, squash merge to `stable/kaiyuan-v2`, and closeout evidence.

Fresh pre-publication local verification:

```text
focused assembler  22 passed
release drill       passed, 13 checks true
contracts            6 passed
text-core           22 passed
downstream         220 passed
upstream           117 passed, 3 skipped
git diff --check     passed
```

Remaining exact action: commit the implementation evidence, run governance/base-scope scans, publish the resulting remote head, then use only that SHA's workflows and review as merge evidence.

Independent review of remote head `522b102a5cbc3968b1bcade4278d36f0d2588d51` found one Important content-boundary issue: the assembler validated the four observation envelope keys but copied the nested `phase` mapping verbatim, while B6 intentionally ignores unknown fields. Four injected raw-body/hit/meta/fingerprint payload cases were observed RED (`4 failed`) and could have entered a passing artifact. The fix recursively requires exact allowlisted keys for phase, health/checks, meta, smoke stages/results, collection set, and fingerprints before copying. Focused post-fix result is 27 passed. The prior workflow run IDs are stale; full gates and workflows must rerun on the fixed head.

Review of that first fix found two further Important gaps. Exact keys still allowed object/content values in B6-ignored fields, and mkdir/UTF-8/argparse failures could bypass stable content-free diagnostics. Six counterexamples were observed RED: three allowed-value payloads, output parent as a file, lone-surrogate identity, and unknown argument sentinel. The fix validates every phase scalar/constant/count/collection/hash and safe manifest text, moves all output preparation inside structured error handling, distinguishes link races from parent failures, and uses a parser whose errors never echo untrusted arguments. Focused post-fix result: 33 passed. No prior CI is final evidence.

Final re-review found two additional Important type/value holes: `card_types=1|null` raised an uncaught `TypeError`, and symbolic strings such as `sha256:SECRET_SOURCE_CONTENT` satisfied the permissive hash pattern. Three counterexamples were observed RED. The fix requires JSON list card pools exactly equal to official stage pools and exact lowercase 64-hex SHA-256 values for source/config fingerprints. Focused post-fix result: 36 passed. A final independent assessment and all full/exact-head gates remain required.

The final assessment found no Critical and one last Important parser-boundary risk: excessive JSON nesting/`RecursionError` could bypass stable input errors. A 2,000-level input was observed RED because it reached later validation instead of being rejected as `invalid_json`. Strict parsing now uses iterative depth/node bounds and explicitly maps `RecursionError`; focused result is 37 passed. All independent Critical/Important findings are addressed; final full and exact-head gates remain.

Started `codex/kaiyuan-release-artifact-assembly-v2` from the independently verified stable head `549143c396d1566096e26797161d8d9b25ccf2dd`. No READY task existed after B7-T01, so B7-T02 was registered as the smallest adjacent release-safety increment: offline assembly of the three already captured phase observations into the existing B6 input contract. Selected a separate pure assembler over extending the verifier CLI or documenting shell/jq assembly. It will perform no network, routing, ingest, corpus/candidate, Qdrant, or collection operation. Design, D-018, implementation plan, and draft PR #22 are now the durable sources; next action is observed import RED for the pure assembler.

## 2026-07-18 — B7-T01 merged

```text
PR: #20
Final head: 57f43bcc1778b2e79926ca625a08ac4f4de49016
Development Governance: 29666701659 — success
Kaiyuan Stable Core: 29666701666 — success
Kaiyuan Upstream Runtime: 29666701658 — success
Squash merge: eef5f2c2afd64312bedf7c33cc07fe7ca6f5f41f
```

GitHub returned `merged=true`, and an independent `git ls-remote` resolved `refs/heads/stable/kaiyuan-v2` to the same squash SHA. Final PR metadata was base `stable/kaiyuan-v2`, non-draft, mergeable, with zero review threads and zero submitted reviews. Independent safety review found no Critical; all three Important findings and one race taxonomy finding were reproduced with RED tests and fixed before the final exact-head workflows. Final local evidence was 20 focused, 6 contracts, 22 text-core, 220 downstream, and 95 upstream tests passed (3 environment skips), plus the passing 13-check release drill and governance check.

The merged 13-file scope contains only read-only observation building/adapters, an atomic CLI, synthetic tests/CI, Make entry points, runbook, design/plan, decision, and task evidence. It does not change `main`, corpus, candidates, ingest behavior, Qdrant schema/data, routing, or write `local_kb_default`. B7-T01 is DONE. No later READY task is currently registered; the next development task must first be entered in TASKS on a new feature branch.

## 2026-07-18 — B7-T01 started

### Implementation verifying

Implemented the content-free pure observation builder, exact KB Search HTTP adapter, allowlisted Qdrant metadata reader, and atomic caller-selected CLI. The CLI performs no routing change or Qdrant/corpus/candidate/ingest mutation, refuses overwrite, and never persists API keys, raw bodies, hits, snippets, paths, anchors, payloads, or source content. Added Make entry points, an explicit synthetic CI contract step, and three-phase operator instructions in the B6 runbook.

Observed TDD evidence includes missing-module RED, allowlist-hash RED, missing live-adapter RED, count/hit mismatch RED, generic-404 taxonomy RED, and a final four-failure RED proving missing vector schema, invalid input preflight, and HTTP redirect acceptance. After minimal fixes:

```text
cd apps/local-kb-unified
PYTHONPATH=. /tmp/kaiyuan-b5/bin/python -m pytest -q tests/test_release_observation_v1.py
17 passed
```

The focused suite also proves a captured phase passes the existing B6 verifier, timeout errors omit upstream text, source modules contain no Qdrant/ingest mutation calls, and exclusive atomic creation preserves an existing file without temp residue. B7-T01 is now `VERIFYING`, not `DONE`. Remaining: full local gates, governance/diff/secret checks, publish the resulting exact head, latest-head workflows, independent safety review, ready transition, squash merge to `stable/kaiyuan-v2`, and merge evidence.

Full local regression (using the existing `/tmp/kaiyuan-b5/bin` environment because bare `make` could not locate pytest) passed without changing assertions:

```text
PATH=/tmp/kaiyuan-b5/bin:$PATH make contracts-test   6 passed
PATH=/tmp/kaiyuan-b5/bin:$PATH make text-core-test   22 passed
PATH=/tmp/kaiyuan-b5/bin:$PATH make downstream-test  220 passed
PATH=/tmp/kaiyuan-b5/bin:$PATH make upstream-test    92 passed, 3 skipped
make release-drill                                   passed, 13 checks true
git diff --check                                     passed
```

Independent safety review of remote head `902f59be8609c9f47df1c2314d973111e0382fbd` found no Critical and three Important issues: live Requests redirects could bypass the fake 302 test, the runbook named the verifier report schema instead of its input schema, and Qdrant timeouts were collapsed into `upstream_unavailable`. It also noted a race-only `output_exists` taxonomy gap. All were reproduced before fixes: redirect request kwargs RED, then two focused failures for Qdrant timeout/runbook schema, then an atomic-race error-code RED. Minimal fixes disable redirects, preserve `httpx`/Requests timeout taxonomy without exception text, document `kaiyuan-release-drill-input/v1`, and classify an exclusive-create race as `output_exists`.

Post-review local evidence (prior workflow runs are stale after these fixes):

```text
focused       20 passed
contracts      6 passed
text-core     22 passed
downstream   220 passed
upstream      95 passed, 3 skipped
```

Remaining: publish a new exact head, rerun governance and all three workflows for that SHA, recheck PR metadata/threads, mark ready, and squash merge only to `stable/kaiyuan-v2`.

Started `codex/kaiyuan-release-observation-capture-v2` from the independently verified stable head `627b3dc086966fec0c527500e4a7e5fac6a8f987`. B7-T01 is limited to a read-only phase-observation collector feeding the existing B6 verifier. It will not switch routing, ingest, upsert/delete Qdrant, write `local_kb_default`, or copy raw response bodies/source content into artifacts. Next action: inventory current health/meta/retrieve clients and Qdrant read metadata, then write the design and implementation plan before code.

Selected a local direct-read CLI over a new inspection endpoint or operator-supplied fingerprints. Health/meta and exact-stage smoke use existing KB Search contracts; active/protected fingerprints use Qdrant read-only collection metadata and exact counts. Secrets, hits, raw bodies, payloads, and source content are excluded. Design and D-017 are now the durable source; next action is the detailed TDD plan and draft PR.

Draft PR #20 targets only `stable/kaiyuan-v2`. Task 1 TDD began with an observed import RED (`ModuleNotFoundError: release_observation`), followed by a minimal content-free builder GREEN (`1 passed`). A second RED proved whole-config hashing changed when non-allowlisted simulated payload/status secrets changed; projecting to the explicit schema allowlist restored GREEN (`2 passed`). No live adapter, network call, output write, Qdrant mutation, corpus, candidate, or collection change has occurred. Next action: add fail-closed builder cases, then HTTP/Qdrant read-adapter RED tests.

## 2026-07-18 — B6-T03 merged and release line complete

```text
PR: #18
Final head: 4f403682d8d39860b383d9483446704d82a85029
Development Governance: 29647775680 — success
Kaiyuan Stable Core: 29647775679 — success
Kaiyuan Upstream Runtime: 29647775710 — success
Squash merge: 1378f2790b52c5f08ddf235223fcf128928fc911
```

GitHub returned `merged=true`, and an independent `ls-remote` resolved `refs/heads/stable/kaiyuan-v2` to the same squash SHA. Final metadata was base `stable/kaiyuan-v2`, non-draft, mergeable, with zero review threads and zero submitted reviews. The 13-file diff contained only the non-mutating validator, strict CLI, synthetic fixture, Make/CI gate, runbook, tests, and governance documents. It did not change `main`, raw corpus, candidate content, ingest implementation, Qdrant schema/data, or `local_kb_default`.

Independent review found six Important and one Minor issue; all were reproduced and resolved before the final head. Final local evidence was 26 focused, 6 contracts, 22 text-core, 220 downstream, and 75 upstream tests passed (3 environment skips), plus a passing 13-check synthetic drill. B6-T03 and the currently registered B4–B6 release sequence are complete. No further READY task is registered; future work must first be added to TASKS on a new feature branch.

## 2026-07-18 — B6-T02 merged; B6-T03 started

```text
PR: #17
Final head: 534723d0828c8f438900e203d96e981daf77218d
Development Governance: 29646657185 — success
Kaiyuan Stable Core: 29646657169 — success
Kaiyuan Upstream Runtime: 29646657195 — success
Squash merge: af3f80d8b415f98825a0516fbbce7890e134a90c
```

GitHub returned `merged=true`, and `refs/heads/stable/kaiyuan-v2` independently resolved to the same squash SHA. No corpus, candidate content, ingest, Qdrant schema/collection, `main`, or `local_kb_default` change.

B6-T03 started from the actual merge SHA on `codex/kaiyuan-stable-release-rollback-v2`. Task moved to `IN_PROGRESS` before design. Next action: inventory release scripts, manifest/meta health checks, collection configuration, and existing B4 runbook; define a non-destructive ephemeral rollback drill that proves `local_kb_default` protection.

### B6-T03 design

Selected a pure three-phase snapshot verifier over a live mutating switch script or documentation-only checklist. The design records exact release and rollback manifest identities, healthy structured/primary smoke results, the prior read route, and an invariant fingerprint for `local_kb_default`. It explicitly permits restoring read routing to a previously active legacy collection while never authorizing writes, ingest, recreation, deletion, or migration. Decision `D-016` and the design spec are the durable source of truth. Next action: write the implementation plan, publish the design checkpoint, and open a draft PR targeting only `stable/kaiyuan-v2`.

### B6-T03 implementation verifying

Draft PR #18 targets only `stable/kaiyuan-v2`; first implementation head is `0d4ba53a02a86eaf85ea6eaddc398b5ee9c08bb5`. Added the pure `kaiyuan-release-drill/v1` verifier, strict CLI exit semantics, synthetic fixture, Make/CI gate, operator runbook, design, plan, and decision D-016. No command connects to Qdrant or changes routing; no corpus, candidate, ingest, Qdrant schema/data, `main`, or `local_kb_default` change.

TDD evidence:

```text
RED  PYTHONPATH=. pytest -q tests/test_release_drill_v1.py
     ModuleNotFoundError: release_drill
GREEN 2 passed, then 14 passed

RED  PYTHONPATH=. pytest -q tests/test_release_drill_v1.py -k cli
     3 failed because CLI and fixture were absent
GREEN 17 passed

RED  test_release_target_must_exist_in_observed_collection_snapshot
     expected failed, got passed
GREEN 18 passed
```

Related regression on the same local implementation tree:

```text
make release-drill   passed, status=passed, all 12 checks true
make contracts-test  6 passed
make text-core-test  22 passed
make downstream-test 220 passed
make upstream-test   67 passed, 3 skipped
git diff --check     passed
```

B6-T03 is `VERIFYING`, not `DONE`. Remaining: publish this evidence update, run governance and all required workflows for the resulting exact head, inspect the complete PR diff and unresolved review threads, perform independent review, resolve findings with RED/GREEN evidence, mark ready, and squash merge only to `stable/kaiyuan-v2`.

Independent review of `a5271684d3e629b119402ba3dccfda97d7633773` found six Important fail-closed/proof-boundary defects and one Minor report-safety issue. All five validator/CLI counterexamples were reproduced together as RED (`5 failed`): missing `meta_status`, bool/int manifest equality, invalid protected fingerprint, non-finite JSON, and a no-op transition. A sixth RED proved arbitrary HTTP/stage/pool smoke data passed. Fixes require observed `meta_status=ok`, non-empty string manifest identities, typed existing protected fingerprints, strict finite/unique-key JSON, a distinct safe previous collection, HTTP 200 plus exact official stage pools, and redaction of unsafe rollback names. The runbook now labels B4 citable resolution as separate manual release evidence rather than executable drill proof. Focused result after fixes: `26 passed`. Required full regressions and exact-head CI must be rerun after publishing; prior run IDs `29647515047`, `29647515058`, and `29647515057` are stale evidence for the superseded head.

Review fixes were published as head `714280b90cd7dd2c68de14f0a0a3570278f494b3`. Fresh post-fix verification:

```text
PYTHONPATH=. pytest -q tests/test_release_drill_v1.py  26 passed
make release-drill                                      passed, 13 checks true
make contracts-test                                     6 passed
make text-core-test                                     22 passed
make downstream-test                                    220 passed
make upstream-test                                      75 passed, 3 skipped
governance af3f80d..714280b                             passed, 13 changed / 6 code files
git diff --check af3f80d..714280b                       passed
Development Governance 29647704022                     success
Kaiyuan Stable Core 29647704011                        success
Kaiyuan Upstream Runtime 29647703977                    success (all 5 jobs)
```

The GitHub thread-aware API returned zero review threads and zero submitted reviews; the independent review findings above were all resolved and independently covered by focused tests. PR #18 remained draft, mergeable, and targeted only `stable/kaiyuan-v2`; its 13-file diff contains no raw corpus, candidate content, ingest implementation, Qdrant schema/data, `main`, or `local_kb_default` mutation. This evidence update changes the head, so these run IDs are an intermediate reviewed checkpoint, not final merge evidence. Next operation: publish this log-only commit, wait for every required workflow on the resulting exact head, mark ready, verify metadata/threads/diff once more, and squash merge.

## 2026-07-18 — B6-T02 implementation verifying

### TDD evidence

```text
RED 1: ModuleNotFoundError: src.observability
GREEN 1: helper contract 16 passed

RED 2: retrieval modules had no monotonic timing seam or observability envelope
GREEN 2: official/fallback/error two-stage tests 7 passed

RED 3: candidate_sync had no monotonic seam or returned observability
GREEN 3: candidate sync v1/v2 20 passed

RED 4: nested NaN/Infinity remained in an observability error copy
GREEN focused: observability/retrieval/transport/sync 47 passed
```

### Implementation

- Added additive `kb-observability/v1` envelopes with monotonic, finite, non-negative latency.
- Official retrieval records requested/raw/returned pools, collection, optional upstream latency and corpus version.
- Two-stage retrieval records ordered structured, official-primary, and filesystem fallback stages plus explicit fallback reason.
- Official errors still raise `KBSearchError`; safe trace is attached only under `details.observability`, and errors never trigger fallback.
- Candidate sync reports total latency, collection/corpus provenance, checked/lookups/hits and structured `run_error`; failed manifests remain byte-identical and latency is not persisted into manifests.
- Nested non-finite values are converted to null only in the copied trace, preserving caller/error inputs.

### Local verification

```text
focused: 47 passed
contracts: 6 passed
text-core: 22 passed
downstream: 217 passed
upstream: 49 passed, 3 skipped
```

B6-T02 is `VERIFYING`, not `DONE`. Draft PR #17 targets only `stable/kaiyuan-v2`. Remaining: publish, exact-head governance and three workflows, independent review, review-fix RED/GREEN if needed, ready and squash merge. No corpus, candidate content, ingest, Qdrant, collection, `main`, or `local_kb_default` change.

### Independent review fixes

Review reported no Critical, two Important, and one Minor issue. Four new/updated assertions reproduced all failures:

- top-level two-stage collection ignored effective response collection;
- conflicting stage collection/corpus versions were silently guessed;
- sync telemetry duplicated upstream message/details containing simulated secret/raw content;
- injected non-official hit providers increased `official_hit_count`.

Fixes now promote collection/corpus provenance only on official-stage consensus, expose deterministic `provenance_conflicts`, allowlist sync telemetry errors to code/status/retryable, and count official hits only on the official retriever path. The authoritative top-level sync error and atomic manifest behavior remain unchanged. Fresh focused/full gates and a new exact-head CI run are required.

## 2026-07-18 — B6-T02 observability design and plan

- Inventory confirmed upstream retrieve already returns some `latency_ms`, collection, and optional corpus metadata, but downstream two-stage results have no uniform stage trace and candidate sync reports expose errors without timing/count provenance.
- Selected an additive `kb-observability/v1` envelope using client monotonic timing. Upstream timing is retained separately and invalid/missing values become null.
- Retrieval errors still raise; sync errors remain run-level reports and preserve all manifest bytes. No error becomes healthy empty results or candidate status.
- Design: `docs/superpowers/specs/2026-07-18-kaiyuan-retrieval-sync-observability-design.md`.
- Plan: `docs/superpowers/plans/2026-07-18-kaiyuan-retrieval-sync-observability.md`.
- Decision: D-015.
- No implementation claim. Next exact action: create draft PR, add observability helper tests, observe import RED, then implement only the pure helper.

## 2026-07-18 — B6-T01 merged; B6-T02 started

```text
PR: #16
Final head: 9a395ac8bacb1ab0464b584a8e9ef31f5f5d42cb
Development Governance: 29644669300 — success
Kaiyuan Stable Core: 29644669317 — success
Kaiyuan Upstream Runtime: 29644669313 — success
Squash merge: 0632c0a87515b4b6d33ea2476630d62e2b3321d7
```

GitHub returned `merged=true`, and `refs/heads/stable/kaiyuan-v2` independently resolved to the same squash SHA. PR #16 targeted only `stable/kaiyuan-v2`; no corpus, candidate, ingest, Qdrant, collection, `main`, or `local_kb_default` change.

B6-T02 started from the actual merge SHA on `codex/kaiyuan-retrieval-observability-v2`. Task moved to `IN_PROGRESS` before design. Next action: inventory retrieval/sync result schemas and error boundaries, then define additive JSON-safe observability fields for stage latency, pool size, fallback reason, sync run error, corpus version, and collection.

## 2026-07-18 — B6-T01 implementation verifying

### TDD evidence

```text
RED 1: test_primary_passage_cache_v2.py collection failed with
ModuleNotFoundError: src.connectors.primary_passage_cache
GREEN 1: 9 passed

RED 2: scanner integration failed because primary_file_scanner had no
primary_passage_cache injection point
GREEN 2: cache + filesystem retrieval 16 passed

RED 3: resolver and migration integration failed because both modules had no
primary_passage_cache injection point
GREEN 3: cache + retrieval + resolver + migration 37 passed
```

### Implementation

- Added a bounded, thread-safe process-local LRU of immutable strict-UTF-8 source snapshots and `kb-text-core` passages.
- Each load reads and hashes exact bytes; a content change invalidates parsing even when mtime and byte length are preserved.
- Missing, invalid UTF-8, or unstable sources never return a stale snapshot. Parser errors propagate.
- Filesystem fallback, citable resolver, and rule-evidence migration reuse snapshots. Resolver still performs every B4 validation on every call; migration fingerprint keeps its exact raw-byte algorithm.
- Draft PR #16 targets only `stable/kaiyuan-v2`.

### Local verification

```text
PATH=/tmp/kaiyuan-b5/bin:$PATH make contracts-test
6 passed

PATH=/tmp/kaiyuan-b5/bin:$PATH make text-core-test
22 passed

PATH=/tmp/kaiyuan-b5/bin:$PATH make downstream-test
195 passed

PATH=/tmp/kaiyuan-b5/bin:$PATH make upstream-test
49 passed, 3 skipped
```

B6-T01 is `VERIFYING`, not `DONE`. Remaining: publish implementation, run governance and all three exact-head GitHub workflows, independent review, fix any Critical/Important finding with RED tests, then ready/squash merge. No raw corpus, candidate, ingest, Qdrant, collection, `main`, or `local_kb_default` change.

### Independent review fix

Review found one Important issue and no Critical issues: `KaiyuanPassage` is frozen but its `heading_path` was a mutable list, so returning the cached parser object allowed a consumer to poison later resolver/migration loads without changing source bytes.

```text
RED: cached heading_path was ['唐開元占經', '熒惑占'] rather than an immutable tuple
GREEN focused: 38 passed
GREEN downstream: 196 passed
GREEN contracts: 6 passed
GREEN text-core: 22 passed
GREEN upstream: 49 passed, 3 skipped
```

The cache now defensively converts every cached passage heading path to a tuple. The regression attempts mutation and proves a later unchanged-byte load remains source-derived. Publishing this fix creates a new head and requires all exact-head CI again.

## 2026-07-18 — B6-T01 design and implementation plan

- Hot paths confirmed in `primary_file_scanner`, `evidence_resolver`, and rule-evidence migration: unchanged primary Markdown was decoded and/or parsed repeatedly.
- Selected a bounded process-local cache of exact-byte source snapshots and immutable `kb-text-core` passages. Each load hashes strict UTF-8 bytes, so preserved mtime/size cannot hide content changes.
- Design: `docs/superpowers/specs/2026-07-18-kaiyuan-primary-passage-cache-design.md`.
- Plan: `docs/superpowers/plans/2026-07-18-kaiyuan-primary-passage-cache.md`.
- Decision: D-014.
- No implementation or completion claim yet. Next exact action: create draft PR, add `tests/test_primary_passage_cache_v2.py`, run focused pytest, and record the expected RED before implementing the cache module.

## 2026-07-18 — B5-T03 merged; B6-T01 started

```text
PR: #15
Final head: dcea5ac9b58cb9621307104b18ea49c4caa2f10b
Governance: 29640418519 — success
Stable Core: 29640418556 — success
Upstream Runtime: 29640418531 — success
Squash merge: 6dd0910a2d6b825904ae8e0dcc7d3f1a75557775
```

B5-T03 merged only to `stable/kaiyuan-v2`. Repository audit kept the legacy primary reference ambiguous and created no migrated evidence or raw-corpus change.

B6-T01 started on `codex/kaiyuan-primary-passage-cache-v2`. Task moved to `IN_PROGRESS` before design. Next action: inventory filesystem parse hot paths and define path/mtime/hash invalidation semantics.

## 2026-07-18 — B5-T03 evidence migration implementation verifying

### TDD and implementation

```text
RED: ModuleNotFoundError: src.rule_engine.rule_evidence_migration
focused GREEN: 4 passed
CLI/audit related: 7 passed
```

- Added a read-only bulk planner using `kb-text-core` primary passages.
- Only a unique exact raw/normalized match can become `migratable`.
- Every proposal is revalidated by the B4 resolver as `citable`.
- Apply writes a separate atomic output and refuses input overwrite.
- Added Typer and argparse `audit-rule-evidence-migration` command.

### Repository audit

```text
source_fingerprint: sha256:f2e01f0cb17d77f9aa441d7e1481ebdae7ad9f340bd1bf7b9c2dd2b0a12ccbdc
total_rules: 4
ambiguous: 1
missing_evidence: 3
migratable: 0
```

The legacy `荧惑守心` anchor occurs in multiple primary passages and remains ambiguous/candidate-only. No migrated fixture or source change was created.

### Local gates

```text
contracts: 6 passed
text-core: 22 passed
downstream: 181 passed
upstream: 49 passed, 3 skipped
```

B5-T03 is `VERIFYING`, not `DONE`. Draft PR #15 targets `stable/kaiyuan-v2`. Remaining work is exact-head CI, independent review, ready and squash merge. No `main`, raw corpus, candidate, ingest, retrieval, Qdrant, or `local_kb_default` change.

### Independent review fixes

Review found one Critical and three Important issues. New tests first reproduced three failures, then fixes:

- apply now binds every plan detail to current index/rule id/before evidence, verifies source fingerprint, rejects duplicate/out-of-range indices, and re-runs the resolver before any write;
- plan/apply output must differ from input and remain outside `kb_root`; plan output is atomic too;
- malformed evidence is `invalid_rule`, while only absent evidence is `missing_evidence`;
- missing/empty primary `kb_root` fails clearly instead of returning healthy unresolved;
- restored candidate-generation CLI message to its original command.

Post-review verification: focused 6 passed; downstream 183 passed; contracts 6 passed; text-core 22 passed; upstream 49 passed, 3 skipped. A new exact-head CI run is required after publishing these fixes.

## 2026-07-18 — B5-T02 merged; B5-T03 started

### B5-T02 final evidence

```text
PR: #14
Final feature head: 05cdf6271b73284e943e357df754292ebc31ade1
Development Governance: 29631008326 — success
Kaiyuan Stable Core: 29631008308 — success
Kaiyuan Upstream Runtime: 29631008338 — success
Squash merge commit: 57da1a8b9afb994b3f3ef0ac1714d14fd4a3d37b
Base: stable/kaiyuan-v2
```

GitHub returned `merged=true` for the expected head after independent review fixes and fresh final-head gates. PR #14 did not target `main` and did not change corpus, candidate, ingest, retrieval, Qdrant schema, or `local_kb_default`.

### B5-T03 start

- Branch: `codex/kaiyuan-rule-evidence-migration-v2` from the actual B5-T02 stable merge commit.
- Task moved to `IN_PROGRESS` before design or implementation.
- Next: inventory legacy rule evidence states, define fail-closed audit/migration design, write implementation plan, and open a draft PR to `stable/kaiyuan-v2` before behavior changes.

## 2026-07-18 — B5-T01 merged; B5-T02 started

### B5-T01 merge evidence

```text
PR: #13
Final feature head: 5e4ef05a3e4c4bfa02334676ef877f1bf1eccc8d
Development Governance: 29625533123 — success
Kaiyuan Stable Core: 29625533107 — success
Kaiyuan Upstream Runtime: 29625533117 — success
Squash merge commit: e4e25ba39d43270b1d2ac54ae3057eb741161b38
Base: stable/kaiyuan-v2
```

GitHub returned `merged=true` for the expected feature head. PR #13 did not target `main`; its changed-file audit contained only rule engine, related tests, and development/spec/plan documents. It did not change raw corpus, candidate flow, ingest, retrieval, Qdrant schema, or `local_kb_default`.

### B5-T02 start

- Branch: `codex/kaiyuan-conflict-resolution-v2` from the actual merged stable commit above.
- Task moved to `IN_PROGRESS` before behavior implementation.
- Selected design: a pure conflict resolver module with deterministic policy keys, explicit manual-review withholding, retained suppressed rows, and group trace.
- Design: `docs/superpowers/specs/2026-07-18-kaiyuan-conflict-resolution-policy-design.md`.
- Plan: `docs/superpowers/plans/2026-07-18-kaiyuan-conflict-resolution-policy.md`.
- Decision: D-012.
- Remaining risk: no B5-T02 behavior has been implemented or verified yet; TDD RED is the next gate.

## 2026-07-18 — B5-T02 conflict resolution implementation verifying

### TDD evidence

```text
RED 1:
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python /tmp/kaiyuan-b5/bin/pytest -q tests/test_conflict_resolution_policy_v2.py
result: collection error, ModuleNotFoundError: src.rule_engine.conflict_resolution

GREEN 1:
same command
result: 14 passed

RED 2:
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python /tmp/kaiyuan-b5/bin/pytest -q tests/test_rule_matcher.py
result: 2 failed, 4 passed
failures: recommendation_status absent; manual_review still returned a formal recommended_rule_id

GREEN 2:
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python /tmp/kaiyuan-b5/bin/pytest -q tests/test_conflict_resolution_policy_v2.py tests/test_rule_matcher.py
result: 20 passed

RED 3 (compatibility self-review):
minimal legacy row without explicit score/priority/evidence raised KeyError: rule_priority

GREEN 3:
normalized compatible defaults onto the copied row before ordering
focused result: 21 passed
```

### Implementation

- Added pure `resolve_rule_conflicts()` with fail-closed row validation.
- Executed `highest_score`, `highest_priority`, `prefer_primary_evidence`, and `manual_review`.
- Added stable rule-id tie-breaking, group-policy consistency checks, suppression metadata, formal/provisional recommendation separation, and group trace.
- Replaced the matcher's report-only conflict block with resolver output while preserving all eligible rows.

### Local regression evidence

```text
downstream: 174 passed
contracts: 6 passed
text-core: 22 passed
upstream: 49 passed, 3 skipped
```

The initial upstream collection failure was environmental: the fresh isolated venv lacked declared upstream dependencies (`qdrant_client`, `requests`, `fastapi`). Installing both repository requirements files resolved collection without code or assertion changes.

### Pre-merge review fixes

Independent review found three Important issues. Each received an observed failing regression test before the fix:

1. `minimal_matcher` coerced `rule_priority` with `int()`, allowing bool/string/float configuration to bypass resolver validation. The matcher now passes the raw value and the resolver alone validates it.
2. The resolver stripped `conflict_group`, incorrectly merging distinct exact strings such as `group-a` and ` group-a`. It now only uses whitespace to recognize an empty group and otherwise preserves the exact string.
3. The matcher attached all conflict reasons to every grouped row. It now maps each multi-row trace to only that exact group, so singleton groups and their top-level recommendation remain clean.

Review-fix RED: 3 failed. Review-fix GREEN: focused 24 passed; downstream 177 passed; contracts 6 passed; text-core 22 passed; upstream 49 passed, 3 skipped.

### Status

- Task is `VERIFYING`, not `DONE`.
- Draft PR: #14, base `stable/kaiyuan-v2`.
- Previous verified implementation head: `fbc114b6ec7841918f8ca041cd6372d429e3fce6`; its three workflows passed before review fixes.
- Changed-file audit is limited to rule engine, focused tests, conflict documentation, task/decision/work log, design and plan. Review threads: 0.
- Remaining: publish review fixes and require fresh final-head workflows; after they pass, re-check threads/diff, mark ready and squash merge.
- No corpus, CText, candidate, ingest, retrieval, Qdrant schema, `main`, or `local_kb_default` change.

## 2026-07-18 — B5-T01 three-valued rule semantics implementation verified

### Scope

- 把规则条件从隐式布尔值升级为 `pass | fail | unknown`。
- 缺失角距、持续时间和必需可见性不再自动视为通过。
- 新增 `insufficient_data`，不改变 B4 citable evidence、candidate、语料或 Qdrant 行为。

### TDD RED evidence

```text
Initial failing-test head: c85e32d704b5bfb42ac75c52aa77e720da259141
Kaiyuan Stable Core run: 29624857624
Observed failure: ModuleNotFoundError: src.rule_engine.conditions
```

新测试先定义了 condition contract、numeric/visibility unknown 语义、聚合状态和输出字段；在实现模块不存在时 downstream job 明确失败。

第二轮回归发现两个旧 fixture 仍编码“缺失测量不影响完整匹配”的旧语义：

```text
Intermediate head: f452aee538bc7c2b07c7a82c377c396328c6c43e
Result: 2 failed, 149 passed
```

根因与处理：

1. page mismatch 规则事件没有 angle/duration。证据仍保持 `page_mismatch`，但 trigger 正确改为 `insufficient_data`。
2. `structured_only_demo` 缺少 angle/duration/visibility。旧 `candidate_only/partial` 期望改为 `insufficient_data`，并断言 unknown condition 列表。

没有降低 B4 evidence mismatch 断言。

### Implementation

- 新增 `src/rule_engine/conditions.py`：
  - `ConditionState`；
  - `ConditionEvaluation`；
  - exact、max numeric、min numeric、required visibility evaluator；
  - missing/empty/bool/nonnumeric/NaN/infinity 的明确 unknown reason；
  - invalid configured threshold 的 deterministic ValueError；
  - 非有限 actual 转为严格 JSON-safe 字符串。
- 扩展 `RuleMatchResult`：
  - `condition_states`；
  - `unknown_conditions`；
  - `failed_conditions`；
  - `trigger_ratio`。
- 重构 `minimal_matcher.py`：
  - 核心 identity fail → `not_matched`；
  - 已知非核心 fail → `partial_match`；
  - 无已知 fail 但存在 unknown → `insufficient_data`；
  - 全部适用条件 pass 后依据 B4 citable evidence 判定 `matched` 或 `candidate_only`；
  - 未配置 target/visibility/threshold 不进入条件集合与分母；
  - unknown 进入分母但不进入 pass 分子；
  - rule trigger body/event_type 必须是非空字符串；
  - malformed related asterism data 不产生未分类异常。

### Implementation verification

```text
Verified implementation head: da007704c7b11a0ed90241f57a4e02062f57a191

Development Governance
run 29625394299
conclusion: success

Kaiyuan Stable Core
run 29625394306
conclusion: success

Kaiyuan Upstream Runtime
run 29625394314
conclusion: success
```

覆盖：

- focused three-valued condition tests；
- strict JSON-safe condition trace；
- invalid trigger/threshold/visibility configuration；
- optional target and `visibility_required=false` omission；
- full downstream regression；
- Python 3.9/3.12 text-core；
- shared contracts；
- strict CText spot checks；
- upstream unit and safety gates；
- Qdrant incremental/retrieval contract；
- B4 candidate roundtrip regression。

### Review status

- D-011 已记录三值聚合决策。
- B5-T01 进入 `VERIFYING`。
- PR #13 仍为 draft。
- 本日志和任务状态提交后必须重新运行 final-head 门禁，才能标记 ready 或合并。
- `main`、raw corpus、candidate flow、Qdrant schema 和 `local_kb_default` 未修改。

## 2026-07-18 — B4-R01 pre-merge integrity review verified

### Verified head

```text
767e107d7ccaf34a6dbfc7881dd2860ca0bd1369
```

### Workflow evidence

```text
Development Governance
run 29624529981
conclusion: success

Kaiyuan Stable Core
run 29624530036
conclusion: success

Kaiyuan Upstream Runtime
run 29624529987
conclusion: success
```

### Review findings and fixes

1. **真实 CLI sync 绕过 canonical book filter**
   - Finding: `candidate_cards.sync_upstream_status()` 为每个 item 调用 legacy helper，新建 retriever且未传 `kb_book_id`。
   - Fix: 真实入口只创建一个结构化 `KBSearchRetriever`，直接交给 `sync_candidate_manifests()`；official lookup 统一传 `filters={"kb_book_id": book_id}`、`structured_recall` 和 `extract_card`。
   - Test: legacy CLI sync test 改为拦截 canonical `retrieve()`，验证 filter/stage/card pool。

2. **Candidate card 完整性字段可缺失**
   - Finding: manifest 有 anchor/hash 时，card frontmatter 缺少对应字段仍可能通过本地校验。
   - Fix: card 的 `anchor_text` 和 `content_hash` 都成为本地 current 的必要字段；缺失时标为 `stale`，不访问上游。

3. **相同引文跨卷误合并风险**
   - Finding: official hit 只要 content hash 相同就会标记 `merged`，没有验证 source locator。
   - Fix: `merged` 现在要求 content hash 与 canonical source locator 同时一致；有正式卡但 locator 缺失或不一致时为 `needs_review`。

4. **Generic 404 被误报为 collection missing**
   - Finding: 任意 HTTP 404 都被分类为 `collection_not_found`，旧服务缺少 `/v1/meta` 时会产生错误诊断。
   - Fix: 只有上游显式返回 `COLLECTION_NOT_FOUND` 才使用该错误码；generic 404 为非重试 `contract_error`。

### Gate coverage

- governance checker；
- Python 3.9/3.12 text core；
- shared contracts；
- strict CText spot checks；
- full downstream regression including new sync/transport tests；
- upstream unit and compose/security checks；
- Qdrant incremental and retrieval-contract integration；
- candidate promote/ingest/retrieve/sync/citation roundtrip。

### Status

- B4-R01: `DONE`
- B4-T09: remains `VERIFYING` until the documentation status commit receives a fresh final-head gate.
- No change to `main` or `local_kb_default`.

## 2026-07-18 — GOV-T01 / B4-T01–T08 verified

### Verified head

```text
6152acc6bd9e3dbb07af97b10df42577ff87af54
```

### Workflow evidence

```text
Development Governance
run 29623960771
conclusion: success

Kaiyuan Stable Core
run 29623960806
conclusion: success

Kaiyuan Upstream Runtime
run 29623960814
conclusion: success
```

### Gates covered

- governance checker unit tests and task/work-log PR policy；
- shared contracts；
- text-core Python 3.9 and Python 3.12；
- strict local CText spot checks；
- downstream full regression；
- upstream unit tests；
- Docker Compose validation；
- machine-local path and secret artifact scan；
- Qdrant incremental reconciliation；
- Qdrant retrieval contract；
- candidate generate/approve/promote/ingest/retrieve/sync/citation roundtrip。

### Root-cause fixes in this batch

1. **Legacy audit expectation**
   - Failure: an absent `docs/a.md` was expected to be citable merely because it declared `card_type=fenjuan`.
   - Fix: build a real `KR3g0018_031` passage fixture with locator, page, heading, paragraph, anchor and raw hash.
   - Safety: resolver fail-closed requirements were preserved; no assertion was weakened.

2. **Canonical book filter and limit compatibility**
   - Failure: old CLI tests expected `filters.book_id`; v2 wire contract requires `kb_book_id`.
   - Fix: tests now require canonical `kb_book_id`; retrieval client accepts transitional `limit` while using `top_k` internally.

3. **CText Mars-heart spot check**
   - Failure: the manually recorded excerpt omitted the character `來` before `三月`, so strict comparison correctly reported mismatch.
   - Fix: corrected the reference record to `其來三月彗星如房后百二十日名山崩熒惑守心`.
   - Safety: local raw corpus was not changed.

4. **Candidate roundtrip configuration**
   - Failure: the integration job ran from workspace root while the downstream config lives at `apps/star-omen/config/config.yaml`.
   - Fix: test explicitly sets `APP_CONFIG_PATH` to the repository config.

5. **Structured-card indexing cardinality**
   - Failure: the roundtrip assumed one Qdrant point per Markdown candidate, but heading-based structured indexing correctly emitted several retrieval records from one approved card.
   - Fix: validate shared official approval/provenance and matching candidate hash across one or more records; do not force an artificial one-point invariant.

### Delivered governance and operations documentation

- `AGENTS.md`
- `docs/development/DEVELOPMENT_MANUAL.md`
- `docs/development/TASKS.md`
- `docs/development/WORK_LOG.md`
- `docs/development/DECISIONS.md`
- `docs/development/B4_RELEASE_RUNBOOK.md`
- `scripts/check_development_governance.py`
- `.github/workflows/development-governance.yml`

### Status after verification

- GOV-T01: `DONE`
- B4-T01 through B4-T08: `DONE`
- B4-T09: `VERIFYING`
- B5-T01: `READY` after B4 merge

### Remaining release work

- Run all required workflows on the final documentation/status head.
- Update PR #12 body with final evidence.
- Mark PR ready only when the latest head is green.
- Squash merge only into `stable/kaiyuan-v2`.
- Confirm `main` and `local_kb_default` were not modified.

## 2026-07-18 — GOV-T01 / B4 continuation

### Scope

- 用户选择三层治理方案：长期手册、任务台账、工作记录，并增加决策记录和根目录入口。
- 所有后续任务必须先进入文件，开发前必须阅读手册。
- 继续 B4，不修改 `main`，目标仍为 `stable/kaiyuan-v2`。

### Changes

- 新增根目录 `AGENTS.md`，定义开发前强制阅读顺序和不可违反边界。
- 新增 `docs/development/DEVELOPMENT_MANUAL.md`。
- 新增 `docs/development/TASKS.md`，登记 GOV、B4、B5、B6 任务。
- 新增 `docs/development/DECISIONS.md`，记录 release、Qdrant、语料、CText、检索、sync 和 citation 决策。
- 新增 governance checker、单元测试和 PR gate。

### Current B4 diagnosis

最初 downstream CI 的明确失败根因：

1. `tests/test_cli_audit.py` 仍假设一个不存在的 `docs/a.md` 只要声明 `card_type=fenjuan` 就可以 `citable`。这与 B4 fail-closed 设计冲突。
2. 早期 candidate sync fixture 把 manifest hash 改成任意占位值，导致新本地 hash 验证把所有 item 正确标为 stale。
3. legacy `candidate_cards.sync_upstream_status` 测试仍依赖旧裸请求 seam，需要保持命令兼容但统一到结构化 retriever。

### Verification evidence before governance batch

- PR: `#12 Harden Kaiyuan candidate sync and citable evidence`
- Base: `stable/kaiyuan-v2`
- Head before governance batch: `23f95fbfd020c039a6a08138df3e9acb4ff85256`
- Text-core Python 3.9/3.12 jobs: passing on the inspected run.
- Upstream unit, Qdrant incremental and retrieval-contract jobs: passing on the inspected run.
- Downstream: failing on stale legacy expectations; no completion claim was made at that point.
# 2026-07-18 — B8-T02 hermetic release evidence gate started

B8-T01 closeout PR #27 was confirmed base `stable/kaiyuan-v2`, ready, mergeable, docs-only, and free of reviews or unresolved threads at exact head `d60e3daa5e0c9e8934184ac43faca3b721182b2c`. Its exact-head workflows Governance `29673783672`, Stable Core `29673783647`, and Upstream Runtime `29673783671` all succeeded. PR #27 squash merged, and independent `git ls-remote` confirmed the actual stable ref as `bae59e0b636588c5600916ce992c642746f002da`.

B8-T02 started from that exact stable SHA on `codex/kaiyuan-ephemeral-release-gate-v2`. TASKS moved to `IN_PROGRESS` before code. Design selects one hermetic pytest composing the real read-only observation, assembly, bundle, and offline verification pure APIs with an explicit operation audit. D-021 records that synthetic CI does not prove a production release and must never access `local_kb_default`. Next exact action: commit the reviewed spec/plan, create a draft PR targeting only `stable/kaiyuan-v2`, then observe TDD RED for the missing end-to-end gate helper.

TDD environment diagnosis: the first command could not import global pytest and was not counted as RED. After installing the repository-declared test dependencies into an isolated temporary target and prepending that target to `PYTHONPATH`, `python -m pytest -q tests/test_release_evidence_e2e_v1.py` produced the valid expected RED: `NameError: _run_release_evidence_gate`, `1 failed`. Reading `capture_phase_observation` then exposed that the established B6 contract always requests the protected collection fingerprint. The spec was corrected before implementation: the hermetic fake may receive that read-only inspection request, but no live client/service is instantiated and no mutation is allowed. This preserves rather than weakens the protected invariant.

TDD GREEN and regression evidence: the minimum hermetic phase builder composed actual `capture_phase_observation`, `assemble_release_artifact`, `create_bundle_bytes`, and `verify_bundle_bytes`; focused result was `1 passed`. The second RED was `TypeError: _run_release_evidence_gate() got an unexpected keyword argument 'tamper_after_switch'`; the minimum tamper injection then produced the established fail-closed `drill_validation_failed:document` before bundle creation, and focused result became `2 passed`. A stale test expectation for the report schema was corrected to the actual `kaiyuan-release-drill/v1` contract after inspecting the full diff; no production semantic changed. The combined release regression command using isolated declared dependencies passed `138 passed in 3.39s`. B8-T02 is now `VERIFYING`, not DONE. Next exact action: commit the implementation head, run all full local gates and independent review, publish to draft PR #28, then wait for that actual remote head's workflows.

Independent review of `087d500` found no Critical or Important issues and two Minor issues. The aggregate protected-inspection count could not prove one inspection per phase; a new test first failed with `ValueError: not enough values to unpack`, then the audit records gained `phase_name` and now assert the exact ordered three-phase protected inspections. The work log's transient dependency path was replaced by the portable isolated-target setup description. Post-review focused result: `3 passed`; combined release regressions: `139 passed in 4.56s`. Full gates on the resulting workspace: contracts `6 passed`; text-core `22 passed`; downstream `220 passed`; upstream `188 passed, 3 skipped` (the established environment-only Qdrant integrations); release drill passed all 13 checks. Remaining: commit this review fix, run exact-head governance/diff scans, publish the new remote head, and require its PR workflows before ready/merge.

PR #28 remained draft, base `stable/kaiyuan-v2`, mergeable, and scoped to exactly seven B8-T02 workflow/test/governance files. Remote implementation head `c9dcb7f5ef970ed16c8d51c10cc0a71c81816e18` passed Development Governance run `29674290728`, Kaiyuan Stable Core run `29674290738`, and Kaiyuan Upstream Runtime run `29674290722`. This evidence is intentionally recorded in a docs-only follow-up commit, so those runs become historical rather than final-head merge evidence. Next exact action: publish this work-log commit, require all workflows on the resulting actual remote head, recheck reviews/threads/diff, then ready and squash merge only to `stable/kaiyuan-v2`.
