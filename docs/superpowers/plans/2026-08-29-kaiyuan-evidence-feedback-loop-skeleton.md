# Kaiyuan Evidence-to-video Feedback-loop Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:executing-plans` to implement this plan task-by-task. Every
> behavior task follows RED → verify RED → minimal GREEN → verify GREEN →
> commit. Do not combine implementation tasks before their focused tests pass.

**Goal:** Deliver one deterministic offline S0 control-plane run from the
canonical 祖山觀 episode 22 external audit to local-evidence comparison,
non-applying improvement candidates, a safe B9 production request, a blocked
manual-publication handoff and an optional non-applying learning proposal.

**Architecture:** Add an isolated `video_pipeline.feedback_loop` package. Its
strict v1 models preserve observation/hypothesis/decision/outcome boundaries;
pure comparison and planning modules contain policy; an orchestration module
builds canonical members and delegates no-replace atomic publication to the
existing B9 package primitive. A local CLI loads strict JSON and has no network
or account adapter.

**Tech stack:** Python 3.12, Pydantic v2, canonical JSON, pytest, existing
`ExternalAuditBundleV1` and B9 package primitives.

**Execution status (2026-08-31):** Tasks 1–6 are complete for the approved S0
scope. Local implementation/review closed at
`f36b146ddb08809b6b23a8db5e5fc94393165a21`, tree
`fe4babc7c34328a4b18f22bbea998882ae38b2dc`, and that exact closeout was later
non-force pushed to `codex/kaiyuan-evidence-feedback-loop-skeleton-v1`.
Runner remains `NOT RUN`; no VFL PR, merge, render, upload or publication is
claimed. S1 and every later adapter remain outside this plan and require a new
task and decision.

## Global constraints

- Base is
  `stable/kaiyuan-v2@99c0a85c1f944add8d013aedbae830fe022b7c3b`.
- Target only a feature PR to `stable/kaiyuan-v2`; never `main` or a direct
  stable push.
- Treat external media and modern authority as research-only. Never generate
  a missing classical quotation or a weather equivalence.
- All `ImprovementCandidateV1` and `LearningUpdateProposalV1` objects must have
  `apply_allowed=false` by schema, not caller convention.
- All `ManualPublicationHandoffV1` objects must have
  `auto_publish_allowed=false` by schema.
- Do not add live scraping, network retrieval, model calls, media rendering,
  account credentials, uploads, corpus changes, official ingest, Qdrant access,
  `local_kb_default` access, PR #54 changes or Reviewer A/B behavior.
- Do not modify frozen B9 contract semantics. VFL code may import and name
  their versions only.
- Canonical inputs and a fixed policy version determine the run ID; wall-clock
  time, random IDs and machine paths cannot enter output.

## Working commands

Run Python tests from `apps/star-omen` with:

```bash
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  ../../.venv/bin/python -m pytest -q <paths>
```

The worktree-local `.venv` is ignored and contains the declared project
dependencies. It is not a repository artifact.

---

### Task 1: Freeze strict lifecycle contracts

**Files:**

- Create: `apps/star-omen/src/video_pipeline/feedback_loop/__init__.py`
- Create: `apps/star-omen/src/video_pipeline/feedback_loop/contracts_v1.py`
- Create: `apps/star-omen/tests/video_pipeline/feedback_loop/__init__.py`
- Create: `apps/star-omen/tests/video_pipeline/feedback_loop/helpers.py`
- Create: `apps/star-omen/tests/video_pipeline/feedback_loop/test_contracts_v1.py`

- [ ] **Step 1: Write RED contract tests**

  Cover strict/frozen models, unknown fields, invalid IDs, non-finite confidence,
  duplicate references, probe-state/evidence contradictions, broken lifecycle
  references, optional outcome/proposal pairing and the literal false authority
  flags. Include mutation cases proving callers cannot set either apply flag or
  auto-publish flag to true.

- [ ] **Step 2: Run the focused file and record RED**

  ```bash
  cd apps/star-omen
  PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
    ../../.venv/bin/python -m pytest -q \
    tests/video_pipeline/feedback_loop/test_contracts_v1.py
  ```

  Expected: collection/import failure because
  `src.video_pipeline.feedback_loop.contracts_v1` does not exist.

- [ ] **Step 3: Implement the minimal models**

  Define and export:

  ```python
  LocalEvidenceReferenceV1
  LocalEvidenceProbeV1
  FeedbackObservationV1
  ImprovementCandidateV1
  VideoClaimCandidateV1
  VideoProductionRequestV1
  ManualPublicationHandoffV1
  FeedbackMetricV1
  FeedbackOutcomeV1
  LearningUpdateProposalV1
  FeedbackLoopRunV1
  ```

  Reuse `StrictContractModel`, `StableId`, `Sha256Hex`, `FiniteFloat` and
  `ensure_unique`. `FeedbackLoopRunV1` must validate all stable-ID references,
  exact source/audit identity, outcome/proposal pairing and stage-state
  consistency. Keep observations, candidates, decision, outcome and proposal as
  separate nested records.

- [ ] **Step 4: Run GREEN and commit**

  Expected: the focused contract file passes. Commit only the contracts and
  their focused tests.

---

### Task 2: Compare external audit to read-only local probes

**Files:**

- Create: `apps/star-omen/src/video_pipeline/feedback_loop/comparison.py`
- Create: `apps/star-omen/tests/video_pipeline/feedback_loop/test_comparison_v1.py`

- [ ] **Step 1: Write RED policy tests**

  Load the real episode 22 `ExternalAuditBundleV1` through the test helper.
  Require a deterministic observation for every claim and test these cases:

  - external `source_missing` + local `unresolved` stays `source_missing`;
  - a `modern_authority/context_only` link stays `modern_context_only`;
  - `not_searched` remains unknown rather than contradiction;
  - explicit local corroboration/contradiction is preserved with its references;
  - duplicate probes, unknown claim IDs, source mismatch and incomplete probe
    coverage fail closed;
  - reversed input order yields identical canonical observations.

- [ ] **Step 2: Run RED**

  Expected: import failure for the absent comparison function.

- [ ] **Step 3: Implement one pure comparison entry point**

  ```python
  def compare_external_audit(
      *,
      audit_bundle: ExternalAuditBundleV1,
      local_probes: Sequence[LocalEvidenceProbeV1],
  ) -> tuple[FeedbackObservationV1, ...]: ...
  ```

  Validate defensive copies, join by claim ID, use audit assessment order only
  after canonical sorting, carry explicit external/local evidence IDs, and do
  not perform I/O.

- [ ] **Step 4: Run comparison plus external-media regression and commit**

  ```bash
  ... pytest -q \
    tests/video_pipeline/feedback_loop/test_comparison_v1.py \
    tests/video_pipeline/external_media
  ```

---

### Task 3: Plan bounded improvements and a safe B9 request

**Files:**

- Create: `apps/star-omen/src/video_pipeline/feedback_loop/planner.py`
- Create: `apps/star-omen/tests/video_pipeline/feedback_loop/test_planner_v1.py`

- [ ] **Step 1: Write RED planning tests**

  For episode 22 require deterministic candidates only where an observation
  justifies them, stable sorted IDs, supporting/contradicting observation refs,
  confidence, owner subsystem, verification and rollback. Assert every
  candidate is non-applying.

  Require one `source_audit_explainer` request naming `video-package/v1`. Its
  candidate claims may state captured metadata, missing source and modern
  context, but its allowed claim classes exclude `classical_quote`; its explicit
  forbidden statements include the absent quotation and any 烈风/storm-system
  equivalence. Require human review and `auto_publish_allowed=false`.

- [ ] **Step 2: Run RED**

  Expected: import failure for absent planner functions.

- [ ] **Step 3: Implement deterministic policy tables**

  Provide separate pure functions for improvement candidates, production
  request and initial handoff. Key them by typed dispositions, not creator-name
  string matching. The handoff initially uses `awaiting_video_package` and
  enumerates the B9 artifact and human-review requirements.

- [ ] **Step 4: Run planner, comparison and B9 contract regression; commit**

  ```bash
  ... pytest -q \
    tests/video_pipeline/feedback_loop/test_planner_v1.py \
    tests/video_pipeline/feedback_loop/test_comparison_v1.py \
    tests/video_pipeline/contracts
  ```

---

### Task 4: Assemble and atomically publish a deterministic run

**Files:**

- Create: `apps/star-omen/src/video_pipeline/feedback_loop/orchestrator.py`
- Create: `apps/star-omen/tests/video_pipeline/feedback_loop/test_orchestrator_v1.py`

- [ ] **Step 1: Write RED orchestration tests**

  Require:

  - canonical input bytes + `vfl-policy/1.0.0` derive a stable hash-bound run ID;
  - two builds from reordered probes are byte-identical;
  - members include the validated audit snapshot, probes, observations,
    candidates, production request, handoff and run record;
  - each member is canonical JSON and the existing manifest verifies every hash;
  - optional outcome yields one linked proposal and a distinct deterministic run;
  - no outcome means no proposal member;
  - existing destination, symlink destination and invalid input leave no partial
    package or staging directory.

- [ ] **Step 2: Run RED**

  Expected: import failure for absent orchestrator API.

- [ ] **Step 3: Implement build/publish APIs**

  ```python
  @dataclass(frozen=True, slots=True)
  class FeedbackLoopBuild:
      run: FeedbackLoopRunV1
      manifest: PackageManifestV1
      members: Mapping[str, bytes]

  def build_feedback_loop_run(...) -> FeedbackLoopBuild: ...
  def publish_feedback_loop_run(*, output_dir: Path, build: FeedbackLoopBuild) -> Path: ...
  ```

  Hash canonical audit, sorted probes, optional validated outcome and policy
  version. Generate proposals through a pure function. Use
  `build_package_manifest`, `verify_package_members` and
  `write_package_atomic`; do not duplicate atomic filesystem logic.

- [ ] **Step 4: Run orchestration and package regression; commit**

  ```bash
  ... pytest -q \
    tests/video_pipeline/feedback_loop/test_orchestrator_v1.py \
    tests/video_pipeline/package_review/test_package_atomic_v1.py \
    tests/video_pipeline/package_review/test_vertical_package_e2e_v1.py
  ```

---

### Task 5: Add the episode 22 gold fixture and offline CLI

**Files:**

- Create: `tests/fixtures/video-feedback-loop/v1/episode-22-probes.json`
- Create: `tests/fixtures/video-feedback-loop/v1/synthetic-human-outcome.json`
- Create: `tests/fixtures/video-feedback-loop/v1/manifest.json`
- Create: `apps/star-omen/scripts/run_video_feedback_loop.py`
- Create: `apps/star-omen/tests/video_pipeline/feedback_loop/test_fixture_assets_v1.py`
- Create: `apps/star-omen/tests/video_pipeline/feedback_loop/test_cli_v1.py`
- Modify: `Makefile`

- [ ] **Step 1: Write RED fixture and CLI tests**

  Require canonical fixture bytes and hash manifest. The probe fixture must bind
  exactly the two episode 22 claim IDs and contain no citable classical evidence.
  The synthetic outcome must be plainly labelled test-only and must identify a
  human decision without claiming a platform publication.

  Invoke the CLI in a subprocess with explicit `--audit`, `--probes` and
  `--output`; inspect the complete package. Cover optional `--outcome`, duplicate
  JSON keys, `NaN`, malformed model data, absent parent and destination
  collision. Assert stderr contains a useful failure and no partial output.

- [ ] **Step 2: Run RED**

  Expected: missing fixture/CLI failures.

- [ ] **Step 3: Implement fixtures, strict loader and CLI**

  The strict loader must reject duplicate keys and non-finite constants before
  Pydantic validation. The CLI uses only local paths and returns non-zero on
  validation/publication failure. Add one discoverable root target:

  ```text
  vfl-s0-run
  ```

  It requires explicit `VFL_AUDIT`, `VFL_PROBES` and `VFL_OUTPUT`; optional
  `VFL_OUTCOME` is passed only when non-empty. It does not embed a platform URL,
  credential or network command.

- [ ] **Step 4: Run the full feedback-loop suite and commit**

  ```bash
  ... pytest -q tests/video_pipeline/feedback_loop
  ```

---

### Task 6: Reconcile governance and verify the complete candidate

**Files:**

- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/DECISIONS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: `summary.md`

- [ ] **Step 1: Run focused and related regression**

  ```bash
  cd apps/star-omen
  PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
    ../../.venv/bin/python -m pytest -q \
    tests/video_pipeline/feedback_loop \
    tests/video_pipeline/external_media \
    tests/video_pipeline/package_review/test_package_atomic_v1.py \
    tests/video_pipeline/package_review/test_vertical_package_e2e_v1.py
  ```

- [ ] **Step 2: Run full downstream and compile checks**

  ```bash
  cd apps/star-omen
  PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
    ../../.venv/bin/python -m pytest -q
  ../../.venv/bin/python -m compileall -q src scripts tests
  ```

- [ ] **Step 3: Run governance and scope gates from repository root**

  ```bash
  .venv/bin/python -m unittest discover -s scripts/tests -p 'test_*.py' -v
  .venv/bin/python scripts/check_development_governance.py \
    --base 99c0a85c1f944add8d013aedbae830fe022b7c3b \
    --head HEAD
  git diff --check 99c0a85c1f944add8d013aedbae830fe022b7c3b..HEAD
  git diff --name-only 99c0a85c1f944add8d013aedbae830fe022b7c3b..HEAD
  ```

  Inspect changed paths explicitly. Confirm zero changes under raw corpus,
  `apps/local-kb-unified`, Qdrant/collection configuration, workflows, B10 rule
  fixtures, Reviewer workbooks and account/publisher code. Scan changed text for
  `local_kb_default`, secrets, absolute machine paths and any claim of automatic
  application/publication; documented prohibitions are allowed.

- [ ] **Step 4: Run the canonical episode 22 CLI twice**

  Publish to two fresh temporary parent directories, compare their complete file
  hashes, then deliberately rerun against one occupied output and prove its tree
  is unchanged. Remove only the validated temporary directories after evidence
  is recorded.

- [ ] **Step 5: Request independent review and resolve findings**

  Review the exact candidate diff against the blueprint, task contract and
  safety boundaries. Fix every Critical or Important finding with its own RED
  test when behavioral, then replay affected and final gates.

- [ ] **Step 6: Record exact-head evidence and mark status accurately**

  Update the work log with command results, run/package hashes, changed-path
  audit, review findings, exact commit/tree and Runner `NOT RUN`. Use
  `VERIFYING` until all local and independent-review gates pass. Do not mark the
  task `DONE` merely because the CLI produced a package.

## Plan self-review

- The plan has no unresolved `TODO` or `TBD`; later stages are explicit gates,
  not unfinished S0 steps.
- Every behavior appears first in a RED test task.
- External, local, model, media and publication adapters are absent from S0;
  callers supply audited/probed/outcome data.
- Episode 22 safety assertions are both contract-level and end-to-end.
- Atomic/no-replace behavior is reused from B9 and regression-tested.
- A successful run cannot grant classical/rule authority, apply an improvement,
  mutate another module or publish an account.
