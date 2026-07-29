# B9-G6-E1 Preview Media Evidence Hardening Start

## 2026-07-30 — task started

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Stable branch: stable/kaiyuan-v2
Verified stable HEAD: 41a613a1606cbbf8a77336fa01ea4c98236b57c7
Feature branch: codex/kaiyuan-b9-preview-media-evidence-v1
Task: B9-G6-E1 Preview media evidence hardening
State: IN_PROGRESS
```

## Live repository recovery

- remote `stable/kaiyuan-v2` was verified identical to `41a613a1606cbbf8a77336fa01ea4c98236b57c7`;
- open PRs remain legacy routes #1 and #7, neither targeting the stable v2 line;
- B9-PR-A through B9-PR-E implementation and implementation closeout are merged;
- B9 remains `VERIFYING` and B10 remains blocked.

## Reproduced design gap

The merged `LocalCapabilityEvidence/v1` binds the Stellarium script hash and preview-command hash and records whether a preview was observed. It does not bind the actual `preview.mp4` bytes or the media properties visible through ffprobe. An evidence record could therefore claim that a preview was observed without proving which media file was inspected.

## Fixed scope

This PR only adds a strict preview-media evidence boundary:

1. `PreviewMediaEvidence/v1` with confined `preview.mp4` path, byte size, SHA-256, dimensions, duration, codec and audio-stream count;
2. bounded local-file hashing and caller-supplied ffprobe metadata validation;
3. preview-observed and visual-approval invariants in `LocalCapabilityEvidence/v1`;
4. focused negative tests and runbook updates.

## Acceptance

- tests are committed and missing-model/helper RED is observed first;
- only a regular, non-symlink `preview.mp4` is accepted;
- preview bytes are hashed with a size limit and rechecked for identity change;
- accepted media is 1080x1920 H.264, approximately 80 seconds, with zero audio streams;
- non-finite, malformed, ambiguous or unsupported ffprobe data fails closed;
- observed preview requires preview-media evidence;
- approved visual review requires preview-media evidence and screenshots;
- no subprocess, shell or media generation is added to the evidence model;
- focused and full exact-head workflows pass.

## Exclusions

No hosted FFmpeg execution, no Stellarium execution, no arbitrary ffprobe runner, no `final.mp4`, TTS, publishing, batch media, corpus/candidate/ingest/Qdrant/collection mutation, `local_kb_default`, `main`, B10, B11 or B12 change.
