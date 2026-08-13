# Repository Development Instructions

These instructions apply to the entire repository unless a deeper `AGENTS.md` explicitly narrows them.

## Mandatory read order before any development

Before editing code, data, schemas, workflows, tests, or documentation, read and verify these sources in order:

1. `AGENTS.md`
2. `agent.md`
3. `summary.md`
4. `docs/development/PROJECT_MEMORY.md`
5. Resolve the current remote `stable/kaiyuan-v2` HEAD and all open pull requests; update stale memory facts before relying on them
6. `docs/development/DEVELOPMENT_MANUAL.md`
7. `docs/development/TASKS.md`
8. `docs/development/DECISIONS.md`
9. The relevant design in `docs/superpowers/specs/`
10. The relevant implementation plan in `docs/superpowers/plans/`
11. The newest applicable entries in `docs/development/WORK_LOG.md`

Do not begin implementation until the active task is recorded in `TASKS.md` and marked `IN_PROGRESS`.

`PROJECT_MEMORY.md` is the cross-session recovery entrypoint, not a replacement for live repository facts. A recorded SHA or PR state must be rechecked against GitHub before starting work.

## Non-negotiable project boundaries

- Do not modify or merge the Kaiyuan v2 release line into `main`.
- Release work targets `stable/kaiyuan-v2` through a feature branch and pull request.
- Never delete, recreate, migrate, or write to `local_kb_default` during v2 development or tests.
- Use an ephemeral collection or `local_kb_kaiyuan_v2` for v2 work.
- `apps/local-kb-unified` is the only component allowed to perform official ingest and write official Qdrant data.
- `apps/star-omen` may generate candidate artifacts but must not perform official ingest or write official Qdrant data.
- Pending, rejected, stale, ambiguous, candidate-only, or unverified artifacts are not final evidence.
- Final citable evidence must pass source, locator, page, paragraph, heading, anchor, and hash validation.
- Raw corpus bytes, `<pb:...>` markers, original glyphs, and `&KRxxxx;` entities must not be silently rewritten.
- CText is a targeted/manual comparison source only. Do not add bulk crawling or automatic corpus replacement.
- Transport, authentication, timeout, contract, and collection errors must never be converted into a healthy empty result.
- Fixes require root-cause reproduction and tests. Completion claims require fresh verification evidence.
- Models may generate candidates only; they must not approve rules or convert uncertain evidence into a classical claim.
- Stellarium is a visualization renderer, not the sole authority for astronomy facts.

## Task and work-log protocol

- New work must be added to `docs/development/TASKS.md` before implementation.
- Allowed task states are: `BACKLOG`, `READY`, `IN_PROGRESS`, `BLOCKED`, `VERIFYING`, `DONE`, `CANCELLED`.
- Update the task to `VERIFYING` before the final test pass.
- Mark a task `DONE` only after recording commands, CI results, and the commit or PR reference in `WORK_LOG.md`.
- Any code-changing pull request must update `TASKS.md` or `WORK_LOG.md`.
- Important architecture, safety, corpus, compatibility, scientific-convention, or test-data choices must be recorded in durable repository documentation.

## Required engineering workflow

1. Read and verify the files and remote facts listed above.
2. Confirm the task scope and acceptance criteria in `TASKS.md`.
3. Add or update tests first for behavior changes.
4. Reproduce failures before fixing them.
5. Implement the smallest change that satisfies the accepted design.
6. Run focused tests, then repository gates relevant to the change.
7. Update `WORK_LOG.md` with evidence and remaining risks.
8. Apply the local-first verification and Runner policy below.

## Local-first verification and Runner policy

- Routine development, bug fixes, documentation changes, task-sized feature
  pull requests, and intermediate heads use focused tests plus all applicable
  local regression and governance gates.
- Do not schedule, retry, or wait for a remote/self-hosted Runner after every
  routine commit or pull-request update. Runner availability is not a
  prerequisite for continuing locally verifiable product work.
- Run one final unified Runner validation only when a major-version merge
  candidate is ready to merge into `stable/kaiyuan-v2`. The validation must
  target the exact candidate head after all intended code and documentation
  changes.
- Any change to that exact head invalidates the final Runner evidence and
  requires one new final unified run before the major-version stable merge.
- If the final Runner validation is unavailable or incomplete, record it as
  `NOT RUN` or `BLOCKED`, never as passed. Continue unrelated routine
  development, but do not merge that major-version candidate into stable.
- Real-device, scientific, corpus, human-review, migration, security, or
  production-release evidence remains governed by its explicit task contract.
  Such evidence cannot be replaced by Runner output and does not make Runner a
  routine development dependency.
- `gh` is an optional GitHub client, not a project gate. Use an authenticated
  GitHub App or API when it provides an equivalent auditable operation.

## B9–B12 scope-control rule

The accepted sequence is:

```text
B9 contracts plus one vertical sample
→ B10 whole-book rule structuring
→ B11 rule-engine 2.0 driven by B10 evidence
→ B12 batch media production and publishing assistance
```

Do not pull B10–B12 scope into B9. Once a versioned public contract is frozen, breaking semantic changes require a new contract version rather than an in-place reinterpretation.

The detailed policy and command matrix are maintained in `docs/development/DEVELOPMENT_MANUAL.md`. The current B9–B10 test strategy is in `docs/development/B9_B10_TEST_STRATEGY.md`.
