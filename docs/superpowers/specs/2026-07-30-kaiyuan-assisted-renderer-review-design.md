# B9-G6 Assisted Renderer Review Design

## Decision

Replace the generic professional `y/n` visual approval with three ordered gates:

```text
machine hard gate
→ hash-bound AI visual review
→ lightweight human experience confirmation
```

A later gate can narrow or reject an earlier pass. It can never upgrade an earlier rejection.

## Reproduced failure

The first real macOS archive was structurally trustworthy but factually wrong. `tests/fixtures/evidence/v1/july-21-event.json` declared `3.25°`, a placeholder ephemeris SHA-256 and an outdated provider version. Editorial compilation faithfully turned that fixture into narration. Existing G6 checks bound media and screenshots but never recomputed the astronomical assertion.

The failure is therefore upstream scientific provenance, not a screenshot or FFmpeg defect.

## Gate 1: deterministic machine review

The hard gate consumes exact bytes or canonical models for:

- astronomy event;
- verified provider recomputation;
- rule assessment and evidence bundle;
- editorial package and SRT;
- Stellarium script;
- preview command and ffprobe evidence;
- preview bytes;
- screenshot inventory;
- caller-supplied OCR observations.

It produces `RendererHardGateReport/v1` with:

```text
status = passed | rejected
review_input_sha256
checked_artifact_sha256
issues[]
```

Each issue has a stable code, severity `hard`, artifact, field and bounded explanation. At minimum:

```text
astronomy.provenance_placeholder
astronomy.recomputation_mismatch
astronomy.observer_mismatch
astronomy.time_mismatch
lineage.hash_mismatch
media.contract_mismatch
screenshot.inventory_mismatch
ocr.subtitle_missing
ocr.subtitle_order_mismatch
ocr.subtitle_out_of_frame
```

Scientific comparison uses the existing offline `SkyfieldEphemerisProvider` and verified ephemeris boundary. Event type, bodies, UTC, observer, frame and toolchain identity must agree. Angular separation uses an explicit tolerance of `0.01°`; the serialized narration rounds only after the verified value is established.

OCR remains caller-supplied in B9. The evidence model does not launch OCR, a shell or a network client.

## Gate 2: AI visual review

`AIAssistedVisualReview/v1` binds:

- `review_input_sha256`;
- `hard_gate_report_sha256`;
- preview SHA-256;
- ordered screenshot SHA-256 values;
- model/provider identifier;
- prompt-policy version;
- decision `passed | rejected | needs_human_review`;
- confidence in `[0,1]`;
- itemized checks and evidence-frame references.

Allowed AI checks:

- visible celestial object and shot match;
- subtitle readability, clipping and occlusion;
- black frames, frozen frames, unexpected windows or cursor artifacts;
- internal field names leaking into audience copy;
- overall audience-facing coherence.

AI cannot adjudicate astronomy, classical evidence, provenance or publishability. A report is invalid unless the hard gate passed and all hashes match.

No hosted model is required by the core contract. A local or external adapter may create the report, but credentials, raw provider responses and machine paths are excluded from artifacts.

## Gate 3: lightweight human confirmation

The human UI contains exactly three layperson checks:

```text
subtitles_readable
no_obvious_visual_problem
expression_matches_expectation
```

It displays the machine and AI summaries. Approval is available only when the hard gate passed and AI did not reject. The result binds the exact hard-gate and AI-report hashes.

The UI must not ask the user to judge ephemerides, coordinates, ancient-text provenance or artifact hashes.

## Final decision

`AssistedRendererReview/v1` resolves:

```text
hard rejected                         → rejected
AI rejected                           → rejected
AI needs_human_review + human reject  → rejected
all required reports valid + human approve → approved
missing/invalid report                → incomplete
```

`approved` is evidence acceptance only. It does not authorize publishing, classical quotation, TTS, `final.mp4`, batch production or B10.

## Compatibility and migration

- Keep `LocalCapabilityEvidence/v1` readable; do not reinterpret historical `visual_review_status`.
- Add assisted-review artifacts beside local capability evidence.
- The rejected first archive stays immutable and rejected.
- Regenerate the July sample from verified scientific inputs; do not edit the old archive.
- B9 final closeout requires a fresh archive containing every assisted-review artifact.

## Security and scope

- No `main` changes.
- No corpus/candidate/ingest/Qdrant/collection mutation.
- Never access or write `local_kb_default`.
- No raw model response, secret, absolute path or unrelated machine log in evidence.
- Maximum 30 screenshots remains unchanged.
- No automatic publishing or `final.mp4`.
