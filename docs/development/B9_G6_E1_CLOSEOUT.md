# B9-G6-E1 Preview Media Evidence Closeout

```text
Implementation PR: #42
Base: 41a613a1606cbbf8a77336fa01ea4c98236b57c7
Final feature head: 88e66d8e5ec85db78f4fddecec2c4d7ffc6a9895
Squash merge: b0a39ff4ec243aefb324287e1ab1b1a564fc38b6
Focused: 48 passed in 1.42s
Full downstream: 443 passed in 3.98s
Development Governance: 30493748550 — success
B9 Package Review Preview: 30493748497 — success
Kaiyuan Stable Core: 30493748498 — success
Kaiyuan Upstream Runtime: 30493748522 — success
Changed files: 8 expected
Review threads: 0
Submitted reviews: 0
```

The merged contract binds local renderer evidence to the actual `preview.mp4` byte size, SHA-256 and strict ffprobe-visible properties. It accepts only a regular non-symlink `preview.mp4`, one 1080x1920 H.264 video stream, zero audio streams and an approximately 80-second finite duration. File size, media metadata and actual bytes are cross-checked.

The evidence model does not run FFmpeg, ffprobe, Stellarium or a shell. External tools are invoked only by the local runbook, and their normalized evidence is validated by pure project code.

Observed preview evidence now requires media evidence. Approved visual evidence additionally requires screenshots. Empty ffprobe program/stream-group compatibility sections are accepted; non-empty sections fail closed.

B9 remains `VERIFYING`. The next task is the real macOS G6 run using `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`. B10 remains blocked until that evidence is reviewed and final B9 closeout is merged.
