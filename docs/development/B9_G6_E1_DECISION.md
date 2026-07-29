# B9-G6-E1 Preview Media Evidence Decision

## Status

```text
Task: B9-G6-E1
Branch: codex/kaiyuan-b9-preview-media-evidence-v1
PR: #42
Base: stable/kaiyuan-v2 at 41a613a1606cbbf8a77336fa01ea4c98236b57c7
Successful implementation head before final docs: 0b641533088095cf8bd2f80fde2afa4614f58557
State: VERIFYING
B9 overall: VERIFYING
```

## Reproduced gap

The first merged `LocalCapabilityEvidence/v1` recorded tool versions, the generated Stellarium script hash, the preview-command hash, an observed flag and screenshots. It did not bind the actual `preview.mp4` bytes or decoded media properties. An observed flag alone could not prove which preview was inspected.

No accepted real G6 evidence existed before this hardening, so the v1 evidence contract is tightened before its first production evidence record.

## Accepted preview-media contract

`PreviewMediaEvidence/v1` records:

```text
path = preview.mp4
byte_size
sha256
width = 1080
height = 1920
duration_ms within 80000 ± 500
video_codec = h264
video_stream_count = 1
audio_stream_count = 0
```

The path is intentionally the path-free logical name `preview.mp4`. Machine absolute paths are not serialized.

## Accepted file-inspection boundary

`inspect_preview_media_evidence(...)`:

- accepts only an existing regular non-symlink file named `preview.mp4`;
- applies a caller-configurable size bound that cannot exceed 512 MiB;
- hashes the file incrementally with SHA-256;
- compares device, inode, size and nanosecond mtime before and after the read;
- fails if the file changes during inspection;
- compares ffprobe-reported size with the actual byte size;
- does not launch ffprobe, FFmpeg, a shell or any external process.

The helper consumes caller-supplied normalized ffprobe JSON. This separation keeps command execution outside the evidence model and makes the model independently testable.

## Accepted ffprobe boundary

The accepted payload contains `streams` and `format`. Empty `programs` and `stream_groups` sections are tolerated because current ffprobe versions may emit them automatically. Non-empty program or stream-group sections fail closed.

The payload must prove:

- exactly one video stream;
- zero audio streams;
- unique stream indexes;
- H.264 codec;
- 1080x1920 dimensions;
- MP4 in the format-name set;
- logical filename `preview.mp4`;
- finite duration within the accepted tolerance;
- reported size equal to the inspected file size.

Unknown fields, unsupported stream types, ambiguous video streams, audio, malformed numeric values, non-finite duration and mismatched bytes fail closed.

## Local capability invariants

`LocalCapabilityEvidence/v1` now includes optional `preview_media` with the following state rules:

```text
preview_observed=true  → preview_media required
preview_observed=false → preview_media forbidden
visual_review=approved → observed media plus at least one screenshot required
visual_review=not_run  → preview cannot be marked observed
```

The media logical path and duration must agree with the frozen preview command. Canonical capability bytes include the actual preview SHA-256 and decoded properties.

## Runbook and evidence handoff

The local G6 runbook now:

- creates a fresh timestamped package rather than deleting an old output;
- executes the frozen preview argv with `shell=false`;
- invokes ffprobe separately with a bounded field selection;
- validates the real preview through the project helper;
- includes `preview.mp4`, normalized ffprobe JSON, `scene.ssc`, preview command, package manifest, screenshots and canonical capability evidence in the handoff archive.

Media remains external evidence and is not inserted into the deterministic structured package manifest.

## TDD and verification evidence

```text
Initial RED: PreviewMediaEvidenceV1 import missing
Implementation migration: 42 passed / 3 failed
Migrated GREEN: 45 passed
ffprobe compatibility RED: 1 failed / 47 passed
Final focused GREEN: 48 passed in 1.42s
Full downstream GREEN: 443 passed in 3.98s
```

Exact implementation head:

```text
0b641533088095cf8bd2f80fde2afa4614f58557
```

Workflows:

```text
Development Governance: 30493574389 — success
B9 Package Review Preview: 30493574356 — success
Kaiyuan Stable Core: 30493574387 — success
Kaiyuan Upstream Runtime: 30493574435 — success
```

## Explicit exclusions

This change does not generate preview media in hosted CI, run ffprobe or FFmpeg from production evidence code, launch Stellarium, add arbitrary media inspection, create `final.mp4`, publish content, add TTS, change corpus/candidates/ingest/Qdrant/collections, access `local_kb_default`, modify `main`, or start B10–B12.

## Follow-on

After this PR and its docs-only closeout merge, B9-G6 becomes ready. The user runs the media-bound macOS evidence collector, uploads the resulting archive, and the evidence is independently verified before B9 can be marked `DONE`.
