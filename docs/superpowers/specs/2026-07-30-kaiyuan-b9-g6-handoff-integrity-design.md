# B9-G6 Handoff Integrity Design

## Decision

Replace the hand-written Stellarium version and shell-built evidence archive
with one dependency-free repository command. The command reads the actual
Stellarium application bundle version, checks that
`LocalCapabilityEvidence/v1` records that version, builds a relative screenshot
hash inventory, and publishes a fixed-member tar.gz without overwriting an
existing output.

The command is a handoff packager, not a renderer or an approval tool. It does
not alter the preview, screenshots, assisted-review reports, structured
package, corpus, Qdrant, or publication authority.

## Reproduced failure

Run `20260730T121805Z` has a cryptographically valid core evidence chain:

- renderer hard gate passed with zero issues;
- AI visual review returned `needs_human_review`;
- all three human confirmations are true;
- the final assisted review resolves to `approved`;
- preview and screenshot bytes match the review and capability hashes.

The handoff archive is nevertheless invalid:

1. `local-capability-evidence.json` records Stellarium `26.2.0`, while the
   bound overview screenshot visibly identifies the running application as
   Stellarium `26.1`.
2. `screenshot-sha256.txt` contains five `/Users/...` absolute paths.
3. macOS `tar` added sixteen `._*` AppleDouble members. After extraction on
   Linux, five of them match `screenshots/*.png` and pollute evidence
   enumeration.

The first defect comes from a manually assigned environment variable. The
second comes from hashing screenshots outside the evidence directory. The
third comes from platform-specific archive behavior.

## Command interface

Add:

```text
python scripts/b9_g6_handoff.py \
  --stellarium-app PATH \
  --print-stellarium-version

python scripts/b9_g6_handoff.py \
  --evidence-dir PATH \
  --stellarium-app PATH \
  --output PATH
```

Inputs:

- `--evidence-dir` is an existing real directory containing the exact B9-G6
  evidence set.
- `--stellarium-app` is an existing `.app` bundle whose
  `Contents/Info.plist` supplies `CFBundleShortVersionString`.
- `--output` is a new `.tar.gz` path.
- `--print-stellarium-version` provides the normalized value required while
  rebuilding capability evidence and does not read or write an evidence
  directory.

The application version accepts `major.minor` or `major.minor.patch`, normalizes
the former to `.0`, and must remain in supported series `26.x`. The normalized
value must equal `local-capability-evidence.json.stellarium_version`.
The exact bounded capability bytes used for that comparison are also the bytes
written into the archive, eliminating validation-to-archive drift.

## Archive contract

The archive contains exactly these root files and one screenshot directory:

```text
local-capability-evidence.json
renderer-review-input.json
renderer-hard-gate.json
ai-assisted-visual-review.json
human-experience-confirmation.json
assisted-renderer-review.json
ocr-observations.json
ffprobe-preview.json
preview.mp4
scene.ssc
preview-command.json
package-manifest.json
screenshot-sha256.txt
screenshots/*.png
```

The packager enumerates regular, non-symlink PNG screenshots itself and creates
`screenshot-sha256.txt` in memory with relative paths such as
`screenshots/subtitle-02.png`. It does not copy a caller-provided inventory.
Only explicitly enumerated files enter the archive, so Finder metadata,
extended attributes, logs, `.env`, secrets, corpus data, and unrelated files
cannot enter by directory traversal or wildcard expansion.

Archive member names are canonical relative POSIX paths. Metadata is
normalized so identical inputs create identical archive bytes. Publication
uses a same-directory temporary file and exclusive no-overwrite finalization.

## Failure behavior

The command fails before output publication when:

- the app bundle or Info.plist is missing, malformed, or lacks a supported
  version;
- capability JSON is missing, malformed, or records a different version;
- a required evidence file or screenshot is missing, non-regular, or a
  symlink;
- the screenshot set is empty or exceeds 30 files;
- a member path is unsafe;
- the output already exists;
- temporary archive construction or final publication fails.

Failure never edits source evidence and never replaces an existing archive.

## Verification

Tests use real temporary files and real tar creation. They prove:

- a synthetic Stellarium `26.1` bundle rejects capability version `26.2.0`;
- `26.1` normalizes to `26.1.0`;
- a valid evidence set produces only the fixed member set;
- every screenshot inventory entry is relative and matches actual bytes;
- `._*` files and unrelated evidence-directory files are excluded;
- symlinks and an existing output fail closed;
- repeated packaging of identical inputs is byte-for-byte deterministic.

The B9 runbook replaces manual version assignment, `find | shasum`, and
platform `tar` with this single command.

## Boundaries

- Target only `stable/kaiyuan-v2`; never `main`.
- Do not write, delete, migrate, or inspect `local_kb_default`.
- Do not modify corpus, candidates, ingest, retrieval, Qdrant, or package
  scientific content.
- Do not reinterpret an assisted review or authorize publishing.
- The rejected historical runs remain immutable.
- Run `20260730T121805Z` stays unaccepted until its capability record is rebuilt
  from the actual app version and a clean archive passes independent review.
