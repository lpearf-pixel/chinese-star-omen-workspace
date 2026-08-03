# GOV-T04 Major-Version Unified Runner Workflow Design

Task: `GOV-T04`
Base: `stable/kaiyuan-v2@96b41a4524d36c7ffb2f1e2ec66ca4aed1565962`
Status: accepted implementation design

## 1. Mission and non-goals

GOV-T04 makes remote Runner use an explicit, auditable release action rather
than an automatic side effect of routine pull requests. A major-version
candidate may merge into `stable/kaiyuan-v2` only after one unified run passes
against its exact 40-character commit SHA.

It does not replace local verification, nightly quality work, real macOS and
Stellarium evidence, corpus review, security/migration evidence or the two
independent humans required by PR #54. It does not change product code, corpus,
Qdrant, `local_kb_default`, B10 thresholds, publishing authority or `main`.

## 2. Stakeholders and system boundary

| Actor/system | Responsibility | Controlled input | Auditable output |
|---|---|---|---|
| Release operator | creates one lightweight candidate tag whose suffix is the exact SHA | `kaiyuan-runner/v2/<sha>` | immutable tag/ref identity |
| GitHub Actions | resolves the pushed candidate tag and executes workflows | event SHA/ref, run ID/attempt | job conclusions |
| Stable v2 branch | supplies the required merge base | latest remote stable SHA | ancestry proof |
| Reusable gate workflows | run one bounded verification group | exact candidate/base SHA | pass/fail |
| Independent evidence owners | produce human, corpus, device or release evidence | task-specific inputs | separate artifacts |

Controlled variables are the lightweight candidate tag and job composition.
Directly observed variables are `github.sha`, tag name/type, Git object type,
checkout `HEAD`, remote stable `HEAD`, job results and artifact bytes. The
future availability of hosted or self-hosted Runner capacity is unknown and
never inferred as success.

## 3. Context and feedback loop

The minimum closed loop is:

```text
operator pushes lightweight tag kaiyuan-runner/v2/<candidate-sha>
→ preflight observes tag/event SHA, checkout HEAD and latest stable HEAD
→ preflight accepts or rejects exact identity and ancestry
→ reusable workflows run against the accepted SHA
→ finalizer observes every required job result
→ result JSON plus SHA-256 sidecar is uploaded
→ release operator merges or fixes the candidate and pushes a new SHA tag
```

Any candidate change creates a different SHA and invalidates the previous run.
Any missing, skipped, cancelled or failed required job produces a failed
unified result.

## 4. Subsystems and interfaces

| Subsystem | Input contract | Output contract | Failure behavior |
|---|---|---|---|
| Unified entrypoint | push of `kaiyuan-runner/v2/<40-hex-sha>` | verified candidate/base outputs | reject annotated/wrong-name/mismatched/stable-equal/behind candidate |
| Governance workflow | `candidate_sha`, `base_sha` | governance job conclusion | fail on task/log/state violation |
| Seven reusable test workflows | `candidate_sha` | existing focused/full job conclusions and logs | checkout exact SHA; ordinary PR and branch push cannot trigger |
| Finalizer | preflight plus all reusable job results | `major-version-runner-result/v1` and `.sha256` | upload evidence and exit nonzero unless all required results are success |
| Static workflow validator | repository workflow files | deterministic validation errors | fail on automatic triggers, missing inputs, unbound checkout or incomplete fan-in |

Reusable workflows remain replaceable units. The unified entrypoint composes
them but does not copy their test commands.

## 5. Observation, hypothesis, decision and outcome

- Observation: all eight current workflows have automatic `pull_request` or
  `push` triggers.
- Hypothesis: converting them to `workflow_call` and composing one exact-SHA tag
  gate removes routine remote consumption without weakening the final release
  gate.
- Contrary evidence: `workflow_dispatch` requires its workflow file on the
  repository default branch. The default is protected historical `main`, so a
  new stable-v2-only manual workflow would not be dispatchable without violating
  the project boundary.
- Decision: use only push tags matching `kaiyuan-runner/v2/*`; require a
  lightweight tag whose suffix equals `github.sha`, require the object type to
  be `commit`, require checkout `HEAD` equality, then require current stable to
  be the exact merge base and the candidate to be strictly ahead.
- Verification: a standard-library static validator and unit tests enforce the
  workflow shape; a controlled lightweight tag on the feature head proves
  GitHub execution and artifact binding.

## 6. Minimum closed-loop pilot

The pilot is this GOV-T04 feature branch only. After local tests and review,
push `kaiyuan-runner/v2/<exact-feature-head>` as a lightweight tag.
The pilot exits only if the preflight, all eight reusable workflows, finalizer,
artifact inventory and SHA sidecar pass. Failure stops merge and preserves the
run for diagnosis; it does not re-enable automatic PR triggers.

## 7. Metrics and validation

- automatic `pull_request`/ordinary branch-push workflow triggers: `0`;
- unified exact-SHA tag entrypoints: exactly `1`;
- reusable workflows called by the entrypoint: `8/8`;
- reusable checkout bindings to `inputs.candidate_sha`: `8/8`; preflight is
  bound to `github.sha` and the exact tag suffix;
- required job results recorded by finalizer: `8/8` plus preflight;
- malformed/mismatched/behind/equal-stable candidate acceptance: `0`;
- local validator and governance tests: all pass;
- pilot exact-head run: all required jobs success and evidence hash verified.

## 8. Human review and escalation

The release operator owns candidate-tag creation and merge authorization. A failed or
unavailable Runner is recorded `BLOCKED` or `NOT RUN`; nobody may translate it
to passed. Workflow review must verify permissions, triggers, exact-SHA
checkout, ancestry, fan-in, artifact contents and rollback. PR #54 Reviewer A/B
remain separate humans and are not workflow reviewers.

## 9. Risks, unknowns and reversible decisions

| Risk | Test/observation | Reversible response |
|---|---|---|
| wrong or annotated tag | ref-name, object-type and event/checkout checks | create a new lightweight exact-SHA tag |
| candidate is behind stable | merge-base/ancestor preflight | update branch and push a new SHA tag |
| reusable workflow omitted | static inventory and finalizer fan-in test | add missing call before merge |
| branch protection still names obsolete PR checks | inspect repository rules before closeout | update rules separately; do not restore auto triggers silently |
| nightly or real-environment evidence is confused with unified gate | docs and workflow trigger inventory | keep separate workflow/task contract |
| hosted Runner outage | no complete result artifact | record `BLOCKED`; do not merge major version |

Rollback is a revert of the GOV-T04 merge, restoring the previous workflow
files and their triggers. No data migration or external state rollback is
required.

## 10. Stage gates and entry criteria

| Stage | Entry | Exit | Forbidden expansion |
|---|---|---|---|
| Design | GOV-T03 accepted; live workflow audit complete | this spec, decision and task `IN_PROGRESS` | workflow edits |
| Local implementation | design committed | RED/GREEN validator tests and all local applicable gates pass | product/data changes |
| GitHub pilot | reviewed exact feature head | one successful tag-triggered exact-head run and verified evidence | stable merge on partial results |
| Stable integration | pilot green; PR review clean; branch current | squash merge only to `stable/kaiyuan-v2` and post-merge identity check | `main`, PR #54 gate changes |

GitHub documents that `workflow_dispatch` requires the workflow file on the
default branch; tag-filtered push workflows may target explicit tags. This
design therefore does not modify `main` or the repository default branch.

Nightly automation is not invented in GOV-T04 because no scheduled workflow
exists on the audited baseline. Future nightly work must be a separate task and
must not become an ordinary PR prerequisite.
