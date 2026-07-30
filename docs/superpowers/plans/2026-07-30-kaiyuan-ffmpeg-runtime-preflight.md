# Kaiyuan B9 FFmpeg Runtime Preflight Implementation Plan

> **For agentic workers:** implement task-by-task with strict TDD and verify
> each command from the repository root unless a step says otherwise.

**Goal:** Make every B9 preview fail early with an actionable FFmpeg capability
diagnostic and provide one stable preview command that works across shell
sessions.

**Architecture:** A dependency-light Python CLI resolves a caller override or
PATH, runs a bounded executable subtitle smoke, then executes the unchanged
package argv with only argv zero replaced by the verified binary. Package
contracts stay deterministic and machine-independent.

**Tech stack:** Python 3.12 standard library, pytest, Make, FFmpeg/ffprobe as
external local executables.

## Task 1 — Register and reproduce the runtime failure

**Files:**

- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/WORK_LOG.md`
- Test: `tests/test_b9_preview_script.py`

- [x] Mark `B9-G6-E5` `IN_PROGRESS`.
- [x] Add fake FFmpeg/ffprobe fixtures.
- [x] Write behavior tests for missing subtitle filter and a listed filter
  whose minimal render still fails.
- [x] Run focused tests and observe the expected RED because the CLI is absent.

## Task 2 — Implement fail-closed preflight and exact preview execution

**Files:**

- Create: `scripts/b9_preview.py`
- Test: `tests/test_b9_preview_script.py`

- [x] Resolve `B9_FFMPEG_BIN` / `B9_FFPROBE_BIN` or PATH to executable files.
- [x] Parse version output and require `subtitles` plus `libx264`.
- [x] Run a temporary one-frame SRT burn-in and ffprobe verification.
- [x] Validate `preview-command.json` is shell-free, uses `ffmpeg`, targets
  `preview.mp4`, has a bounded timeout and has not already produced output.
- [x] Replace argv zero only and execute with `shell=False`.
- [x] Run focused GREEN and refactor diagnostics without changing behavior.

## Task 3 — Establish the canonical operator entrypoint

**Files:**

- Modify: `Makefile`
- Modify: `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`
- Modify: `.env.workspace.example`
- Modify: `docs/development/DECISIONS.md`
- Test: `tests/test_b9_preview_script.py`

- [x] Add `make b9-preview B9_OUTPUT_DIR=...`.
- [x] Document optional executable overrides without saving per-run output
  directories in `.env.workspace`.
- [x] Replace the embedded Python preview recipe in the runbook.
- [x] Record why absolute binary paths are runtime configuration rather than
  structured package data.
- [x] Test the Make entrypoint against fake tools.

## Task 4 — Verify and publish

**Files:**

- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/WORK_LOG.md`

- [x] Move `B9-G6-E5` to `VERIFYING`.
- [x] Run focused runner tests.
- [x] Run B9 package-review tests.
- [x] Run shared contracts, text-core, full downstream and governance gates.
- [x] Run `python -m compileall`, runbook embedded-Python parsing and
  `git diff --check`.
- [x] Record exact commands, counts, commit and remaining real-macOS evidence
  requirement.
- [ ] Push a Draft PR targeting only `stable/kaiyuan-v2`; require exact-head
  workflows before merge.
