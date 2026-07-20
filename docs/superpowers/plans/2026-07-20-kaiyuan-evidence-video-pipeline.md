# Kaiyuan Evidence-Backed Astronomical Short Video Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a review-first pipeline that converts verified celestial events and citable 《唐開元占經》 evidence into a claim-labelled short-video package, Stellarium scene script, subtitles, and optional local vertical MP4 preview.

**Architecture:** New focused modules under `apps/star-omen/src/video_pipeline/` own contracts, astronomy calculation, asterism mapping, evidence assembly, editorial compilation, Stellarium scene generation, subtitle/render manifests, and human review. Existing retrieval, evidence resolver, and rule-engine APIs remain authoritative; Stellarium and FFmpeg are optional local adapters invoked only after a deterministic package passes validation.

**Tech Stack:** Python 3.12, Pydantic 2, Skyfield, existing KB Search/retrieval/evidence/rule modules, Stellarium 26.x scripting/Remote Control, FFmpeg, pytest, Typer, YAML/JSON.

## Global Constraints

- Target only `stable/kaiyuan-v2` through a feature pull request; never merge B9 into `main`.
- Never delete, recreate, migrate, or write to `local_kb_default`.
- `apps/star-omen` remains read-only with respect to official Qdrant data and official ingest.
- Pending, rejected, stale, ambiguous, or candidate-only evidence is not a final classical quotation.
- Every narration segment must be exactly one of `astronomy_fact`, `classical_quote`, `historical_context`, `modern_interpretation`, or `production_instruction`.
- “开口破局” is `modern_interpretation`; it must never be presented as 《开元占经》原文或古代占断。
- Raw corpus bytes, `<pb:...>` markers, original glyphs, and `&KRxxxx;` entities remain immutable.
- Missing astronomy values, non-finite values, ambiguous asterism mapping, unavailable retrieval, or failed citation validation fails closed.
- Generated frames, audio, and MP4 files stay outside Git; only small deterministic fixtures and manifests may be committed.
- No automatic Douyin upload or publication is in B9.

---

### Task 0: Activate B9 governance before code

**Files:**
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: `docs/development/DECISIONS.md`

**Interfaces:**
- Consumes: this design and implementation plan, current stable head, and draft PR metadata.
- Produces: an active `B9` section with `B9-T01` through `B9-T10`, current feature/PR metadata, a decision recording the evidence-package-first boundary, and an initial work-log entry.

- [ ] **Step 1: Update the stale current-release metadata.** Set the stable base to the exact current `stable/kaiyuan-v2` head, current feature to `codex/kaiyuan-evidence-video-pipeline-v1`, current PR to the B9 draft PR, forbidden target to `main`, protected collection to `local_kb_default`, and v2 collection policy unchanged.
- [ ] **Step 2: Add B9 tasks and mark only `B9-T01` `IN_PROGRESS`.** Record the design path, plan path, goal, acceptance criteria, review-first boundary, and that no subsequent task may begin until its predecessor is `DONE` or explicitly recorded as independently executable.
- [ ] **Step 3: Add an accepted architecture decision.** Record that modern astronomy, classical evidence, modern interpretation, and rendering are separate claim/provenance layers; Stellarium is a renderer, not the astronomy authority; no automatic Douyin publication is allowed.
- [ ] **Step 4: Add a work-log start entry with exact base/head/PR, files changed, and the next RED test.**
- [ ] **Step 5: Run `python scripts/check_development_governance.py --base stable/kaiyuan-v2 --head HEAD` and `python -m unittest discover -s scripts/tests -p 'test_*.py' -v`; require pass.**
- [ ] **Step 6: Commit with `git commit -m "docs(video): activate B9 evidence video pipeline"`.**

### Task 1: Versioned video-package contracts

**Files:**
- Create: `apps/star-omen/src/video_pipeline/__init__.py`
- Create: `apps/star-omen/src/video_pipeline/models.py`
- Create: `apps/star-omen/tests/video_pipeline/test_models_v1.py`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Produces: `ClaimClass`, `EvidenceStatus`, `ReviewStatus`, `ObserverLocation`, `AstronomyMeasurement`, `AsterismMapping`, `EvidenceReference`, `NarrationSegment`, `Shot`, `RenderManifest`, `ReviewRecord`, and `VideoPackage` Pydantic models.
- Produces: `VideoPackage.model_json_schema()` with `schema_version="video-package/v1"`.
- Consumes: no production dependency beyond Pydantic and standard library.

- [ ] **Step 1: Write failing contract tests.** Assert that a minimal valid package serializes with stable field names; duplicate segment IDs, non-finite coordinates, negative durations, unknown claim classes, and a `classical_quote` without citable evidence fail validation.
- [ ] **Step 2: Run `cd apps/star-omen && pytest -q tests/video_pipeline/test_models_v1.py`; expect collection/import failure because `src.video_pipeline.models` does not exist.**
- [ ] **Step 3: Implement strict models.** Use `ConfigDict(extra="forbid")`, finite-number validators, UTC-aware datetimes, positive durations, stable IDs, and model-level checks linking every classical quotation to at least one `EvidenceReference(status="citable")`.
- [ ] **Step 4: Rerun the focused test; expect all contract cases pass.**
- [ ] **Step 5: Move `B9-T01` to `VERIFYING`, record RED/GREEN evidence, run the relevant governance gate, then mark `DONE` only with commit evidence.**
- [ ] **Step 6: Commit with `git commit -m "feat(video): add evidence video package contracts"`.**

### Task 2: Deterministic Skyfield astronomy provider

**Files:**
- Create: `apps/star-omen/src/video_pipeline/astronomy.py`
- Create: `apps/star-omen/tests/video_pipeline/test_astronomy_provider_v1.py`
- Modify: `apps/star-omen/src/config/settings.py`
- Modify: `.env.workspace.example`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Consumes: `src.interfaces.astronomy.EphemerisPoint` and `EphemerisProvider`.
- Produces: `SkyfieldEphemerisProvider.get_points(*, bodies: list[str], at: list[datetime]) -> list[EphemerisPoint]`.
- Produces: `calculate_observer_measurement(*, body: str, at_utc: datetime, observer: ObserverLocation) -> AstronomyMeasurement`.
- Configuration: `ASTRO_EPHEMERIS_PATH`, `ASTRO_TIMESCALE_DIR`, and existing observer defaults; no network download during normal execution or tests.

- [ ] **Step 1: Mark `B9-T02` `IN_PROGRESS` before editing code.**
- [ ] **Step 2: Write failing tests using an injected fake timescale/ephemeris.** Cover UTC normalization, right ascension/declination/ecliptic coordinates, observer altitude/azimuth, angular separation, finite-value rejection, unknown bodies, and deterministic provenance hashes.
- [ ] **Step 3: Run the focused module and require RED from missing provider.**
- [ ] **Step 4: Implement dependency-injected Skyfield calculation.** Runtime loads only the configured local ephemeris file; errors are classified as `missing_ephemeris`, `unknown_body`, `invalid_time`, or `calculation_error`, never empty success.
- [ ] **Step 5: Rerun focused tests; expect pass without internet access.**
- [ ] **Step 6: Run `cd apps/star-omen && pytest -q tests/test_config_settings.py tests/video_pipeline/test_astronomy_provider_v1.py`.**
- [ ] **Step 7: Record verification and commit with `git commit -m "feat(video): add deterministic astronomy provider"`.**

### Task 3: Chinese asterism mapping and event detection

**Files:**
- Create: `apps/star-omen/src/video_pipeline/asterism.py`
- Create: `apps/star-omen/src/video_pipeline/events.py`
- Create: `apps/star-omen/data/video_pipeline/asterism_aliases_v1.yaml`
- Create: `apps/star-omen/tests/video_pipeline/test_asterism_event_v1.py`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Consumes: existing asterism catalog records and `EphemerisPoint` values.
- Produces: `CatalogAsterismMatcher.match(*, points, asterisms) -> list[MatchResult]`.
- Produces: `detect_video_event(*, measurements, mappings, thresholds) -> CelestialVideoEvent`.
- Alias file maps modern object IDs to Chinese names without rewriting the underlying catalog.

- [ ] **Step 1: Mark `B9-T03` `IN_PROGRESS` before editing code.**
- [ ] **Step 2: Add failing tests for exact object mapping, nearest-star angular mapping, ambiguous equal-distance candidates, low-confidence mapping, and unresolved aliases.**
- [ ] **Step 3: Add failing event tests for conjunction/near-passage, lunar phase marker, visibility-required failure, missing angular separation, and `insufficient_data`.**
- [ ] **Step 4: Implement the minimum matcher and detector with deterministic tie-breaking and explicit confidence/method metadata.**
- [ ] **Step 5: Run `cd apps/star-omen && pytest -q tests/video_pipeline/test_asterism_event_v1.py`; expect pass.**
- [ ] **Step 6: Record verification and commit with `git commit -m "feat(video): map astronomy events to Chinese asterisms"`.**

### Task 4: Evidence and rule-result assembly

**Files:**
- Create: `apps/star-omen/src/video_pipeline/evidence.py`
- Create: `apps/star-omen/tests/video_pipeline/test_evidence_builder_v1.py`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Consumes: `KBSearchRetriever`, official two-stage retrieval, `resolve_evidence`, `is_citable_evidence`, and `run_match_rule`/existing rule executor.
- Produces: `build_video_evidence(*, event, queries, rules_path, kb_root=None, retriever=None) -> VideoEvidenceBundle`.
- Produces ordered fields for official structured hits, official primary hits, filesystem fallback, candidate leads, resolved citations, match status, conflicts, and corpus/collection provenance.

- [ ] **Step 1: Mark `B9-T04` `IN_PROGRESS` before editing code.**
- [ ] **Step 2: Write failing tests with fakes proving official structured retrieval runs before official primary retrieval and filesystem fallback runs only when official primary is empty.**
- [ ] **Step 3: Add tests proving pending overlays never become `classical_quote`, generic transport/contract errors are not converted into no-hit, and citable references require source/locator/page/paragraph/heading/anchor/hash.**
- [ ] **Step 4: Add rule tests proving `insufficient_data`, `candidate_only`, conflict suppression, and primary-evidence preference remain visible in the video evidence bundle.**
- [ ] **Step 5: Implement the evidence builder by composing existing modules without duplicating retrieval or citation logic.**
- [ ] **Step 6: Run `cd apps/star-omen && pytest -q tests/video_pipeline/test_evidence_builder_v1.py tests/test_cli_evidence_audit_v2.py tests/test_rule_matcher.py`.**
- [ ] **Step 7: Record verification and commit with `git commit -m "feat(video): assemble citable astronomy evidence"`.**

### Task 5: Claim-labelled editorial compiler

**Files:**
- Create: `apps/star-omen/src/video_pipeline/editorial.py`
- Create: `apps/star-omen/data/video_pipeline/templates/zh_cn_75s_v1.yaml`
- Create: `apps/star-omen/tests/video_pipeline/test_editorial_compiler_v1.py`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Consumes: `CelestialVideoEvent`, `VideoEvidenceBundle`, and the versioned YAML template.
- Produces: `compile_editorial(*, event, evidence, template_id, modern_interpretation=None) -> EditorialPackage`.
- Produces: narration segments, disclosure text, hook, title candidates, source card text, and bounded action suggestion.

- [ ] **Step 1: Mark `B9-T05` `IN_PROGRESS` before editing code.**
- [ ] **Step 2: Write failing tests for the fixed 60–90 second structure, deterministic segment ordering, exact claim classes, and required source disclosure.**
- [ ] **Step 3: Add rejection tests for unsourced classical quotation, candidate-only quotation, unclassified text, deterministic/fatalistic promises, and wording that attributes modern interpretation to the ancient source.**
- [ ] **Step 4: Implement a template-only compiler; do not add a free-form LLM dependency in B9.**
- [ ] **Step 5: Verify the phrase `开口破局` appears only in a `modern_interpretation` segment and disclosure identifies it as contemporary cultural translation.**
- [ ] **Step 6: Run the focused tests; expect pass.**
- [ ] **Step 7: Record verification and commit with `git commit -m "feat(video): compile claim-labelled short video scripts"`.**

### Task 6: Shot list and Stellarium script generation

**Files:**
- Create: `apps/star-omen/src/video_pipeline/stellarium.py`
- Create: `apps/star-omen/tests/video_pipeline/test_stellarium_script_v1.py`
- Create: `apps/star-omen/data/video_pipeline/stellarium_defaults_v1.yaml`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Consumes: observer location, UTC event times, selected objects, asterism labels, and editorial timing.
- Produces: `build_shot_list(editorial, event) -> list[Shot]`.
- Produces: `render_stellarium_script(*, shots, output_dir, config) -> str`.
- Local runtime contract: generated `.ssc` may be launched with Stellarium `--startup-script` or posted to the Remote Control script endpoint; CI does not start Stellarium.

- [ ] **Step 1: Mark `B9-T06` `IN_PROGRESS` before editing code.**
- [ ] **Step 2: Write snapshot tests for date, location, sky culture, projection, atmosphere/landscape state, object selection, camera movement, field of view, pauses, screenshot names, and safe relative output paths.**
- [ ] **Step 3: Add failure tests for absolute output paths, path traversal, unsupported object IDs, negative shot duration, and scene/event time mismatch.**
- [ ] **Step 4: Implement deterministic `.ssc` generation using only allowlisted commands and caller-selected relative screenshot names.**
- [ ] **Step 5: Add a parser-level smoke assertion that every generated screenshot is represented in the render manifest.**
- [ ] **Step 6: Run `cd apps/star-omen && pytest -q tests/video_pipeline/test_stellarium_script_v1.py`; expect pass.**
- [ ] **Step 7: Record verification and commit with `git commit -m "feat(video): generate Stellarium scene scripts"`.**

### Task 7: Subtitles, media manifest, and local FFmpeg adapter

**Files:**
- Create: `apps/star-omen/src/video_pipeline/subtitles.py`
- Create: `apps/star-omen/src/video_pipeline/media.py`
- Create: `apps/star-omen/tests/video_pipeline/test_media_pipeline_v1.py`
- Modify: `.gitignore`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Produces: `render_srt(segments) -> str` with monotonic, non-overlapping timestamps.
- Produces: `build_render_manifest(*, shots, frames, subtitle_path, audio_path=None) -> RenderManifest`.
- Produces: `build_ffmpeg_command(*, manifest, output_path, mode) -> list[str]` for `preview` or `final`.
- `preview` may be subtitle-only; `final` requires approved narration audio.

- [ ] **Step 1: Mark `B9-T07` `IN_PROGRESS` before editing code.**
- [ ] **Step 2: Write failing tests for SRT numbering, millisecond formatting, no overlap, exact total duration, frame hash inventory, 1080x1920 output, and shell-safe argv construction.**
- [ ] **Step 3: Add rejection tests for missing frames, hash mismatch, audio shorter than the narration timeline, output outside package root, and `final` mode without audio.**
- [ ] **Step 4: Implement pure manifest and command construction; isolate `subprocess.run` behind `run_ffmpeg(...)` and do not execute it in unit tests.**
- [ ] **Step 5: Add `.gitignore` entries for `video_packages/`, frame sequences, WAV/M4A files, and MP4 files while preserving committed JSON/YAML fixtures.**
- [ ] **Step 6: Run focused tests; expect pass.**
- [ ] **Step 7: Record verification and commit with `git commit -m "feat(video): add subtitles and local media rendering"`.**

### Task 8: Atomic package builder and human review gate

**Files:**
- Create: `apps/star-omen/src/video_pipeline/package.py`
- Create: `apps/star-omen/src/video_pipeline/review.py`
- Create: `apps/star-omen/tests/video_pipeline/test_package_review_v1.py`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Produces: `build_video_package(*, event, evidence, editorial, shots, stellarium_script, output_dir) -> VideoPackage`.
- Produces: `write_video_package_atomic(package, output_dir) -> Path`.
- Produces: `evaluate_publish_gate(package, review) -> PublishGateResult`.

- [ ] **Step 1: Mark `B9-T08` `IN_PROGRESS` before editing code.**
- [ ] **Step 2: Write RED tests proving the builder writes no partial directory when validation or serialization fails and refuses to overwrite an existing package.**
- [ ] **Step 3: Write gate tests requiring separate astronomy, classical evidence, editorial, and render approvals; reviewer identity and UTC timestamp are mandatory.**
- [ ] **Step 4: Add tests proving `partial_metadata_only`, `candidate_only`, ambiguous asterism, missing audio, or changed asset hashes block `publishable`.**
- [ ] **Step 5: Implement atomic staging-directory write followed by same-filesystem rename; use strict canonical JSON and SHA-256 inventory.**
- [ ] **Step 6: Run focused tests; expect pass.**
- [ ] **Step 7: Record verification and commit with `git commit -m "feat(video): add atomic packages and review gate"`.**

### Task 9: CLI commands and 2026-07-21 reference candidate

**Files:**
- Modify: `apps/star-omen/src/cli.py`
- Create: `apps/star-omen/data/examples/video/2026-07-21-special-event-input.json`
- Create: `apps/star-omen/data/examples/video/2026-07-21-modern-interpretation.json`
- Create: `apps/star-omen/tests/video_pipeline/test_video_cli_v1.py`
- Modify: `Makefile`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- Adds: `python -m src.cli video-plan --input <json> --out <dir>`.
- Adds: `python -m src.cli video-review --package <dir> --review <json>`.
- Adds: `python -m src.cli video-render --package <dir> --mode preview|final --execute` where execution is explicit.
- Adds: `make video-pipeline-test` and `make video-plan-2026-07-21`.

- [ ] **Step 1: Mark `B9-T09` `IN_PROGRESS` before editing code.**
- [ ] **Step 2: Write CLI tests for successful dry package generation, strict JSON output, explicit non-zero exits, and absence of external process execution without `--execute`.**
- [ ] **Step 3: Create the July 21 input as a candidate with configurable observer coordinates and explicit `source_video_status="partial_metadata_only"`; do not hardcode an unverified Spica/角宿一 conclusion as verified.**
- [ ] **Step 4: Create the modern interpretation fixture with `phrase="开口破局"`, `claim_class="modern_interpretation"`, and `classical_quote=false`.**
- [ ] **Step 5: Implement Typer and fallback argparse commands using shared implementation functions.**
- [ ] **Step 6: Run `make video-pipeline-test`; then run `make video-plan-2026-07-21` against fake/offline fixtures and inspect every generated file.**
- [ ] **Step 7: Record verification and commit with `git commit -m "feat(video): expose evidence video pipeline CLI"`.**

### Task 10: Hermetic end-to-end gate, documentation, and release evidence

**Files:**
- Create: `apps/star-omen/tests/video_pipeline/test_video_pipeline_e2e_v1.py`
- Modify: `.github/workflows/kaiyuan-stable-core.yml`
- Modify: `README.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: `docs/development/DECISIONS.md`
- Create: `docs/development/B9_VIDEO_PIPELINE_RUNBOOK.md`

**Interfaces:**
- Hermetic E2E consumes fake Skyfield data, fake official retrieval, real citation/rule/editorial/package code, and pure Stellarium/FFmpeg command generators.
- Produces a deterministic package summary and proves no network, Stellarium process, FFmpeg process, Qdrant mutation, ingest, or Douyin publishing occurs in CI.

- [ ] **Step 1: Mark `B9-T10` `IN_PROGRESS` before editing code.**
- [ ] **Step 2: Add an end-to-end RED test that builds the July 21 candidate package and asserts exact claim counts, citable-reference requirements, disclosure text, shot inventory, `.ssc`, SRT, and blocked publish status before human/audio approval.**
- [ ] **Step 3: Add failure injection for tampered evidence hash, missing angular separation, candidate-only quotation, path traversal, and changed frame hash; each must fail before publishable output.**
- [ ] **Step 4: Register a named `Evidence-backed video pipeline gate` in `kaiyuan-stable-core.yml`.**
- [ ] **Step 5: Document local prerequisites and exact commands in the B9 runbook, including Stellarium user permissions for external screenshot directories and FFmpeg availability checks.**
- [ ] **Step 6: Move B9 to `VERIFYING`, update decisions and work log with exact RED/GREEN evidence, and keep media outside Git.**
- [ ] **Step 7: Run focused tests, `make contracts-test`, `make text-core-test`, `make downstream-test`, `make upstream-test`, governance checks, and the new E2E gate.**
- [ ] **Step 8: Perform one manual local rendering smoke with Stellarium and FFmpeg into an ignored package directory; record versions, commands, output hashes, and remaining visual defects without committing media.**
- [ ] **Step 9: Keep the implementation PR draft until exact-head workflows pass and independent review has no unresolved Critical or Important findings.**
- [ ] **Step 10: After merge, record final head, workflow run IDs, squash merge SHA, and change B9 status to `DONE` in a docs-only closeout PR.**

## Completion definition

B9 is complete only when the deterministic package and review gate are merged, the July 21 reference remains correctly classified according to its verified evidence, CI proves the fail-closed boundaries, and a local Stellarium/FFmpeg smoke produces a reviewable vertical preview. A publish-ready `final.mp4` additionally requires approved narration audio and human approval; automated Douyin publication remains out of scope.