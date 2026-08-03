# GOV-T04 Major-Version Unified Runner Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace eight automatic PR/push workflows with eight exact-SHA reusable gates composed by one explicit major-version Runner entrypoint.

**Architecture:** A standard-library validator makes workflow topology a repository contract. Existing job bodies remain in focused reusable workflows and receive the candidate SHA as a required input. A tag-filtered orchestrator runs from the candidate commit, proves lightweight tag/event/object/checkout identity and current-stable ancestry, fans out to all reusable workflows, then emits a fail-closed SHA-bound result artifact.

**Tech Stack:** GitHub Actions YAML, Python 3.12 standard library, `unittest`, Git, existing Make/pytest gates.

## Global Constraints

- Release target is `stable/kaiyuan-v2`; `main` is forbidden.
- No `pull_request`, ordinary branch `push`, `workflow_dispatch` or `schedule` event may trigger a migrated Runner workflow.
- The only entry is a lightweight `kaiyuan-runner/v2/<40-hex-sha>` tag; its suffix equals `github.sha`, the object is a commit and checkout `HEAD` is identical.
- Current remote `stable/kaiyuan-v2` is the exact merge base; the candidate is strictly ahead.
- All eight reusable workflows checkout `inputs.candidate_sha` and must succeed.
- Missing, skipped, cancelled or failed work is a failed unified result.
- Nightly and real-device/scientific/corpus/human/migration/security evidence remain separate.
- No product code, corpus, schema, Qdrant, `local_kb_default`, PR #54, B10-PR-D/E/F, B11/B12, publishing or `main` change.

---

### Task 1: Define the workflow topology contract

**Files:**
- Create: `scripts/tests/test_validate_runner_workflows.py`
- Create: `scripts/validate_runner_workflows.py`

**Interfaces:**
- Produces: `validate_repository(root: Path) -> list[str]` and CLI exit `0` only when the complete GOV-T04 topology is valid.
- Consumes: the nine expected files under `.github/workflows/`.

- [x] **Step 1: Write the failing tests**

Add tests that import the validator, require the real repository to validate,
and copy fixture workflows into a temporary root to prove rejection of:

```python
self.assertTrue(any("automatic trigger" in error for error in errors))
self.assertTrue(any("candidate_sha checkout" in error for error in errors))
self.assertTrue(any("missing reusable workflow" in error for error in errors))
self.assertTrue(any("default-branch-only workflow_dispatch" in error for error in errors))
```

- [x] **Step 2: Run RED for the missing validator**

Run:

```bash
python3 -m unittest scripts.tests.test_validate_runner_workflows -v
```

Expected: import failure because `scripts.validate_runner_workflows` does not exist.

- [x] **Step 3: Implement the standard-library validator**

The validator must inspect top-level `on:` event keys without a YAML dependency,
require `workflow_call` plus typed required SHA inputs in each reusable file,
count every checkout/ref binding, reject the default-branch-only
`workflow_dispatch` design, require the exact candidate tag filter, require all
eight `uses: ./.github/workflows/<name>` calls, and require the
preflight/finalizer tag identity, ancestry, fan-in and evidence markers.

- [x] **Step 4: Run RED against the transitional baseline**

Run the same unittest command. Expected: fixture rejection tests pass, while
the real-repository test fails because automatic PR/branch-push triggers remain
and the unified workflow is missing.

- [x] **Step 5: Commit the executable contract**

```bash
git add scripts/tests/test_validate_runner_workflows.py scripts/validate_runner_workflows.py
git commit -m "test: define unified Runner topology"
```

### Task 2: Convert all eight existing workflows to reusable exact-SHA gates

**Files:**
- Modify: `.github/workflows/b9-assisted-renderer-review.yml`
- Modify: `.github/workflows/b9-editorial-stellarium.yml`
- Modify: `.github/workflows/b9-package-review-preview.yml`
- Modify: `.github/workflows/b9-rule-assessment.yml`
- Modify: `.github/workflows/b9-scientific-provider.yml`
- Modify: `.github/workflows/development-governance.yml`
- Modify: `.github/workflows/kaiyuan-pr-a.yml`
- Modify: `.github/workflows/kaiyuan-upstream-runtime.yml`

**Interfaces:**
- Consumes: `inputs.candidate_sha`; Development Governance also consumes `inputs.base_sha`.
- Produces: unchanged job bodies operating only on the exact candidate checkout.

- [x] **Step 1: Replace automatic events**

Each reusable workflow uses this shape:

```yaml
on:
  workflow_call:
    inputs:
      candidate_sha:
        description: Exact major-version candidate commit SHA
        required: true
        type: string
```

Development Governance adds the same required string contract for `base_sha`.
Delete all existing `pull_request`, branch `push`, branch and path event filters.

- [x] **Step 2: Bind every checkout to the candidate**

Every `actions/checkout@v4` step gains:

```yaml
with:
  ref: ${{ inputs.candidate_sha }}
```

Development Governance keeps `fetch-depth: 0` and invokes its checker with
`--base "${{ inputs.base_sha }}" --head "${{ inputs.candidate_sha }}"`.

- [x] **Step 3: Run the focused validator tests**

Run:

```bash
python3 -m unittest scripts.tests.test_validate_runner_workflows -v
```

Expected: automatic-trigger and checkout errors disappear; only the missing
unified entrypoint/fan-in errors keep the real-repository test RED.

- [x] **Step 4: Commit reusable workflow migration**

```bash
git add .github/workflows/b9-*.yml .github/workflows/development-governance.yml .github/workflows/kaiyuan-pr-a.yml .github/workflows/kaiyuan-upstream-runtime.yml
git commit -m "ci: expose exact-SHA reusable gates"
```

### Task 3: Add the unified exact-SHA tag gate

**Files:**
- Create: `.github/workflows/kaiyuan-major-version-gate.yml`
- Create: `scripts/build_runner_result.py`
- Create: `scripts/tests/test_build_runner_result.py`

**Interfaces:**
- Consumes: one lightweight pushed tag named `kaiyuan-runner/v2/<candidate_sha>`.
- Produces: preflight `candidate_sha`/`base_sha`, eight reusable workflow conclusions, tested schema `major-version-runner-result/v1` in `major-version-runner-result.json`, and `major-version-runner-result.json.sha256`.

- [x] **Step 1: Add exact-tag trigger and concurrency controls**

Use only `push.tags: kaiyuan-runner/v2/*`, set read-only contents permission,
and use a non-cancelling concurrency group keyed by `github.sha`. Do not add
`workflow_dispatch`, because GitHub requires that workflow file on the default
branch and v2 must not modify historical `main`.

- [x] **Step 2: Implement fail-closed preflight**

Checkout the input SHA with full history, then run shell checks equivalent to:

```bash
[[ "$candidate_sha" =~ ^[0-9a-f]{40}$ ]]
test "$GITHUB_REF_TYPE" = "tag"
test "$GITHUB_REF_NAME" = "kaiyuan-runner/v2/$candidate_sha"
test "$(git cat-file -t "$candidate_sha")" = "commit"
test "$(git rev-parse HEAD)" = "$candidate_sha"
git fetch --no-tags origin +refs/heads/stable/kaiyuan-v2:refs/remotes/origin/stable/kaiyuan-v2
base_sha=$(git rev-parse refs/remotes/origin/stable/kaiyuan-v2)
test "$candidate_sha" != "$base_sha"
git merge-base --is-ancestor "$base_sha" "$candidate_sha"
test "$(git merge-base "$base_sha" "$candidate_sha")" = "$base_sha"
```

Publish the two verified SHAs as job outputs.

- [x] **Step 3: Fan out to all eight reusable workflows**

Every call needs `preflight`, passes the verified candidate output, and the
governance call also passes the verified base. Do not use `secrets: inherit`.

- [x] **Step 4: Add always-running finalizer**

The finalizer lists preflight plus all eight reusable jobs in `needs`, checks
out the exact candidate and calls the tested standard-library result builder.
It builds a strict JSON record containing repository, workflow/run identity,
candidate, base and every job conclusion, writes a SHA-256 sidecar, uploads
both even on failure, and exits nonzero unless all nine required conclusions
are `success`.

- [x] **Step 5: Run GREEN**

Run:

```bash
python3 -m unittest scripts.tests.test_validate_runner_workflows -v
python3 scripts/validate_runner_workflows.py --root .
```

Expected: all tests pass and CLI prints the nine-workflow topology summary.

- [x] **Step 6: Commit unified entrypoint**

```bash
git add .github/workflows/kaiyuan-major-version-gate.yml
git commit -m "ci: add unified major-version Runner gate"
```

### Task 4: Document operation, verify and publish the pilot

**Files:**
- Create: `docs/development/GOV_T04_RUNBOOK.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: this plan

**Interfaces:**
- Consumes: exact feature head and GitHub unified workflow run.
- Produces: operator procedure, rollback, verification evidence and final task state.

- [x] **Step 1: Write the operator runbook**

Document copying the candidate full SHA, creating and pushing exactly one
lightweight `kaiyuan-runner/v2/<sha>` tag, verifying preflight/base/ref/result
artifact and sidecar, treating any incomplete result as blocked, and creating a
new tag only for a new exact candidate head.

- [x] **Step 2: Run complete local gates**

Run:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
python3 scripts/validate_runner_workflows.py --root .
python3 scripts/check_development_governance.py --base 96b41a4524d36c7ffb2f1e2ec66ca4aed1565962 --head HEAD
git diff --check 96b41a4524d36c7ffb2f1e2ec66ca4aed1565962...HEAD
```

Record exact totals; unavailable product dependency suites remain accurately
`NOT RUN`, never passed.

- [x] **Step 3: Mark GOV-T04 `VERIFYING` and commit final candidate**

Record local evidence and unchanged boundaries in `WORK_LOG.md`, change only
GOV-T04 from `IN_PROGRESS` to `VERIFYING`, complete plan checkboxes, then commit:

```bash
git add docs/development/GOV_T04_RUNBOOK.md docs/development/TASKS.md docs/development/PROJECT_MEMORY.md docs/development/WORK_LOG.md docs/superpowers/plans/2026-08-02-kaiyuan-major-version-runner-workflow.md
git commit -m "docs: prepare GOV-T04 Runner pilot"
```

- [x] **Step 4: Push and open a Draft PR**

Push `codex/kaiyuan-gov-t04-unified-runner-v1` and create a Draft PR targeting
only `stable/kaiyuan-v2`. Audit exact changed paths, review findings and live
PR #54 state.

- [x] **Step 5: Run the unified pilot on the reviewed implementation tag**

Lightweight tag `kaiyuan-runner/v2/ca7f05691fbb2a5ee9c1232950f8ad914f4b107f`
triggered run `30800888691`. Preflight, all eight reusable groups and finalize
succeeded. The downloaded ZIP SHA-256 was
`43ef662ce403904019d0c428b634e7aca82d178a84ac02db81f701c436069812`;
the sidecar recomputed the result JSON as
`f706719312d22a400a94e15375b493286ae74143d9abefa2198295dceef811fd`,
with exact candidate/base/ref/run identity and nine `success` results.

- [x] **Step 6: Prepare one non-self-referential closeout candidate**

The pilot evidence and first final review are recorded in the repository. The
four Important review findings are fixed together with this status update, and
GOV-T04 is marked `DONE` effective only if this resulting immutable head passes
one new exact-SHA tag run and PR #63 then merges to `stable/kaiyuan-v2` with an
expected-head lock. The new run ID, artifact hashes, zero Critical/Important
review verdict and merge result are recorded in immutable PR/GitHub metadata,
not another candidate-changing commit. Immediately before merge, live stable
must still equal the result artifact's `base_sha`; otherwise the candidate is
updated and the exact-head gate repeats.
