# Repository Development Instructions

These instructions apply to the entire repository unless a deeper `AGENTS.md` explicitly narrows them.

## Mandatory read order before any development

Before editing code, data, schemas, workflows, tests, or documentation, read these files in order:

1. `AGENTS.md`
2. `docs/development/DEVELOPMENT_MANUAL.md`
3. `docs/development/TASKS.md`
4. `docs/development/DECISIONS.md`
5. The relevant design in `docs/superpowers/specs/`
6. The relevant implementation plan in `docs/superpowers/plans/`
7. The newest applicable entries in `docs/development/WORK_LOG.md`

Do not begin implementation until the active task is recorded in `TASKS.md` and marked `IN_PROGRESS`.

## Non-negotiable project boundaries

- Do not modify or merge the Kaiyuan v2 release line into `main`.
- Release work targets `stable/kaiyuan-v2` through a feature branch and pull request.
- Never delete, recreate, migrate, or write to `local_kb_default` during v2 development or tests.
- Use an ephemeral collection or `local_kb_kaiyuan_v2` for v2 work.
- `apps/local-kb-unified` is the only component allowed to perform official ingest and write official Qdrant data.
- `apps/star-omen` may generate candidate artifacts but must not perform official ingest or write official Qdrant data.
- Pending, rejected, stale, or unverified candidates are not final evidence.
- Final citable evidence must pass source, locator, page, paragraph, heading, anchor, and hash validation.
- Raw corpus bytes, `<pb:...>` markers, original glyphs, and `&KRxxxx;` entities must not be silently rewritten.
- CText is a targeted/manual comparison source only. Do not add bulk crawling or automatic corpus replacement.
- Transport, authentication, timeout, contract, and collection errors must never be converted into a healthy empty result.
- Fixes require root-cause reproduction and tests. Completion claims require fresh verification evidence.

## Task and work-log protocol

- New work must be added to `docs/development/TASKS.md` before implementation.
- Allowed task states are: `BACKLOG`, `READY`, `IN_PROGRESS`, `BLOCKED`, `VERIFYING`, `DONE`, `CANCELLED`.
- Update the task to `VERIFYING` before the final test pass.
- Mark a task `DONE` only after recording commands, CI results, and the commit or PR reference in `WORK_LOG.md`.
- Any code-changing pull request must update `TASKS.md` or `WORK_LOG.md`.
- Important architecture, safety, corpus, or compatibility choices must be recorded in `DECISIONS.md`.

## Required engineering workflow

1. Read the files listed above.
2. Confirm the task scope and acceptance criteria in `TASKS.md`.
3. Add or update tests first for behavior changes.
4. Reproduce failures before fixing them.
5. Implement the smallest change that satisfies the accepted design.
6. Run focused tests, then repository gates relevant to the change.
7. Update `WORK_LOG.md` with evidence and remaining risks.
8. Keep the pull request in draft until every required gate is green.

The detailed policy and command matrix are maintained in `docs/development/DEVELOPMENT_MANUAL.md`.