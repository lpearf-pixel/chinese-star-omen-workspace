# B9 FFmpeg Runtime Preflight Design

## Context

The first source-backed macOS preview package passed deterministic package and
manifest verification, then failed only when FFmpeg parsed
`subtitles=subtitles.srt`:

```text
No option name near 'subtitles.srt'
Error parsing filterchain 'subtitles=subtitles.srt'
```

The package contained `subtitles.srt`, and FFmpeg itself started. The failure
therefore proves neither a missing file nor one specific installation defect.
The runtime may have selected an FFmpeg build without the required subtitle
stack, or a build whose advertised filter cannot complete a real subtitle
render. The existing runbook relied on PATH and trusted a hand-declared
`PreviewCapabilityV1`; it did not test the selected executable before the
80-second render.

## Decision

Add one repository-owned, fail-closed runtime adapter for B9 preview
generation.

1. Resolve FFmpeg and ffprobe once.
   - `B9_FFMPEG_BIN` and `B9_FFPROBE_BIN` are optional explicit executable
     overrides.
   - Otherwise resolve both from PATH.
   - The runner records the resolved executable identity for diagnostics but
     does not write machine paths into structured package members.
2. Run a bounded preflight before the real preview:
   - verify both executables exist and are executable;
   - parse the FFmpeg version;
   - require the `subtitles` filter;
   - require the `libx264` encoder;
   - execute a tiny temporary SRT burn-in smoke using the same argv shape as
     B9;
   - require ffprobe to read the smoke output.
3. Execute the frozen `preview-command.json` without a shell after replacing
   only argv element zero with the already resolved FFmpeg executable.
   `preview-command.json`, its hashes and public `PreviewCommand/v1` semantics
   remain unchanged.
4. Expose the workflow through one repository script and one Make target.
   The runbook must call that entrypoint instead of embedding a free-form
   Python subprocess block.
5. Fail with one actionable diagnostic that includes the failed capability and
   the explicit override names. On macOS, it may recommend a suitable Homebrew
   build, but package-manager discovery is advisory and is never treated as
   proof.

## Alternatives Rejected

### Write an absolute Homebrew path into `preview-command.json`

Rejected because it would make a deterministic package machine-specific,
change structured-member hashes and couple the public command contract to one
package manager and CPU architecture.

### Add only `export PATH="$(brew --prefix ffmpeg-full)/bin:$PATH"` to the runbook

Rejected because PATH order can drift between shells and environments, and an
installation label does not prove that the selected executable can render
subtitles. The same failure would recur outside Homebrew or after upgrades.

### Check only `ffmpeg -filters`

Rejected because advertised capability is weaker than an executable smoke.
The actual defect appeared at filtergraph execution time, so the gate must
exercise the real subtitle path.

## Components

### `scripts/b9_preview.py`

A dependency-light CLI that validates environment and runs the exact package
preview. It owns executable resolution, bounded subprocess calls, temporary
smoke artifacts, actionable errors and the final no-shell invocation.

It must not:

- alter structured package members;
- create or replace the package directory;
- invoke a network client;
- write Qdrant, corpus, candidate or collection data;
- generate `final.mp4`;
- silently retry with an unverified executable.

### `tests/test_b9_preview_script.py`

Behavior tests use small fake FFmpeg/ffprobe executables and temporary package
directories. They cover missing filter, missing encoder, smoke failure,
explicit override selection, successful execution and refusal to overwrite an
existing preview.

### Makefile and runbook

`make b9-preview B9_OUTPUT_DIR=...` is the canonical operator entrypoint.
The runbook documents the optional binary overrides and removes the embedded
preview subprocess recipe.

## Error Handling

All failures occur before the real preview unless the frozen preview command
itself fails. Diagnostics distinguish:

- executable missing or non-executable;
- version output invalid;
- required filter absent;
- required encoder absent;
- subtitle smoke failed;
- ffprobe smoke verification failed;
- package command invalid;
- output already exists;
- real preview command failed or timed out.

The runner preserves the real process exit status as a failed operation and
does not continue into ffprobe, screenshots or review gates.

## Acceptance

- A fake FFmpeg that reproduces the missing subtitle capability is rejected
  before the real preview invocation.
- A build that lists features but fails the tiny subtitle render is rejected.
- Explicit executable overrides work without editing PATH.
- A valid toolchain executes the unchanged package argv with `shell=False`.
- Existing `preview.mp4` is never overwritten.
- Focused tests, package-review tests, governance, shell/Python syntax and the
  full downstream suite pass.
- The incident, durable decision and operator recovery path are recorded in
  `TASKS.md`, `DECISIONS.md`, `PROJECT_MEMORY.md`, `WORK_LOG.md` and the B9
  runbook.
