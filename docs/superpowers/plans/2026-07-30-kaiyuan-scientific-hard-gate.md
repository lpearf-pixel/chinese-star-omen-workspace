# Kaiyuan Scientific Hard Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make G6 recompute and reject incorrect scientific claims before local evidence can be approved.

**Architecture:** Add a pure, canonical hard-gate report beside the existing capability evidence. The local collector supplies an event recomputed by the existing verified offline Skyfield provider plus normalized OCR observations; the gate verifies scientific identity, lineage, media and screenshot bindings without launching processes or network clients.

**Tech Stack:** Python 3.12, Pydantic v2, Skyfield 1.51, pytest, existing B9 contracts.

## Global Constraints

- Base only `stable/kaiyuan-v2`; never target `main`.
- Do not mutate corpus, candidate, ingest, Qdrant, collections or `local_kb_default`.
- Preserve `LocalCapabilityEvidence/v1` compatibility.
- Hard rejection cannot be overridden.
- Evidence artifacts are canonical, path-free and secret-free.

---

### Task 1: Define scientific hard-gate report

**Files:**
- Create: `apps/star-omen/src/video_pipeline/assisted_review.py`
- Test: `apps/star-omen/tests/video_pipeline/package_review/test_renderer_hard_gate_v1.py`

**Interfaces:**
- Produces: `ReviewIssueV1`, `RendererReviewInputV1`, `RendererHardGateReportV1`, `build_renderer_hard_gate_report(...)`, `canonical_renderer_hard_gate_bytes(...)`.

- [x] **Step 1: Write failing contract tests**

Cover strict status/issue enums, UTC and numeric validation, canonical bytes, sorted stable issues, duplicate artifact rejection, path-free output and rejection when any hard issue exists.

```python
def test_hard_gate_derives_rejection_and_canonical_issue_order():
    report = build_renderer_hard_gate_report(
        review_input=review_input(),
        issues=[
            ReviewIssueV1(code="media.contract_mismatch", artifact="preview.mp4", field="width", message="wrong width"),
            ReviewIssueV1(code="astronomy.recomputation_mismatch", artifact="astronomy-event.json", field="measurements", message="separation drift"),
        ],
    )
    assert report.status == "rejected"
    assert [item.code for item in report.issues] == [
        "astronomy.recomputation_mismatch",
        "media.contract_mismatch",
    ]
    assert canonical_renderer_hard_gate_bytes(report).endswith(b"\n")
```

- [x] **Step 2: Run RED**

Run:

```bash
cd apps/star-omen
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
python -m pytest -q tests/video_pipeline/package_review/test_renderer_hard_gate_v1.py
```

Expected: collection fails because `src.video_pipeline.assisted_review` does not exist.

- [x] **Step 3: Implement the minimum strict models and canonical serialization**

Use `StrictContractModel`, `allow_nan=False`, sorted keys and a trailing newline. Issue order is `(code, artifact, field)`. `status` is derived, never caller-selected.

- [x] **Step 4: Run GREEN and commit**

Expected: new focused file passes.

Commit: `feat: define renderer hard gate report`

### Task 2: Verify recomputed astronomy

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/assisted_review.py`
- Test: `apps/star-omen/tests/video_pipeline/package_review/test_renderer_scientific_gate_v1.py`

**Interfaces:**
- Consumes: two `AstronomyEventV1` values: packaged and recomputed.
- Produces: `verify_recomputed_astronomy(packaged, recomputed, angular_tolerance_deg=0.01) -> list[ReviewIssueV1]`.

- [x] **Step 1: Write failing tests**

Include exact pass plus failures for `3.25` versus approximately `5.4`, placeholder ephemeris hash, provider/toolchain drift, UTC drift, observer drift, body/target drift, reference-frame drift, duplicate/missing angular measurement and non-finite values.

```python
def test_scientific_gate_rejects_hand_authored_july_separation():
    issues = verify_recomputed_astronomy(
        packaged=july_event(value=3.25, ephemeris_sha256="a" * 64),
        recomputed=july_event(value=5.405, ephemeris_sha256=DE421_SHA256),
    )
    assert {item.code for item in issues} == {
        "astronomy.provenance_placeholder",
        "astronomy.recomputation_mismatch",
    }
```

- [x] **Step 2: Run RED**

Expected: missing verifier.

- [x] **Step 3: Implement exact identity checks and bounded numeric comparison**

Treat an ephemeris hash made from one repeated character as `astronomy.provenance_placeholder`. Compare angular values with `Decimal` and `0.01°` maximum absolute difference.

- [x] **Step 4: Run GREEN and commit**

Commit: `feat: reject astronomy recomputation drift`

### Task 3: Remove hand-authored July science from the collector path

**Files:**
- Create: `apps/star-omen/src/video_pipeline/local_sample.py`
- Modify: `apps/star-omen/tests/video_pipeline/package_review/helpers.py`
- Modify: `tests/fixtures/evidence/v1/july-21-event.json`
- Create: `tests/fixtures/evidence/v1/july-21-scientific-review.json`
- Test: `apps/star-omen/tests/video_pipeline/package_review/test_local_sample_science_v1.py`

**Interfaces:**
- Produces: `build_july_21_event(provider, observer, at_utc) -> AstronomyEventV1`.
- Consumes: `SkyfieldEphemerisProvider.calculate_angular_separation_event(primary_body="moon", target_modern_object_id="spica", ...)`.

- [x] **Step 1: Add a regression test that the current `3.25°` fixture is rejected**

```python
def test_july_fixture_cannot_bypass_provider_recomputation(provider):
    packaged = AstronomyEventV1.model_validate_json(JULY_FIXTURE.read_text())
    recomputed = build_july_21_event(
        provider=provider,
        observer=packaged.observer,
        at_utc=packaged.peak_utc,
    )
    assert [issue.code for issue in verify_recomputed_astronomy(packaged, recomputed)] == [
        "astronomy.provenance_placeholder",
        "astronomy.recomputation_mismatch",
    ]
```

- [x] **Step 2: Run RED and record the stable issue code**

Expected: `astronomy.recomputation_mismatch`.

- [x] **Step 3: Build the source-backed fixture from the verified provider**

Record real provider version, `de421.bsp` identity and `topocentric-apparent` frame. Update editorial/package expectations to derive narration from this verified event.

```python
def build_july_21_event(*, provider, observer, at_utc):
    return provider.calculate_angular_separation_event(
        primary_body="moon",
        target_modern_object_id="spica",
        at_utc=at_utc,
        observer=observer,
    )
```

- [x] **Step 4: Run astronomy, editorial and package focused tests**

Run:

```bash
python -m pytest -q \
  tests/video_pipeline/astronomy \
  tests/video_pipeline/editorial \
  tests/video_pipeline/package_review
```

- [x] **Step 5: Commit**

Commit: `fix: source july sample from verified astronomy`

### Task 4: Bind lineage, media, screenshots and OCR

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/assisted_review.py`
- Test: `apps/star-omen/tests/video_pipeline/package_review/test_renderer_artifact_gate_v1.py`

**Interfaces:**
- Produces: `OCRObservationV1` and `verify_renderer_artifacts(...)`.

- [x] **Step 1: Write failing tests**

Test exact artifact hashes, manifest membership, scene/event identity, preview-command/media agreement, screenshot inventory order and OCR subtitle presence/order/bounds.

```python
def test_artifact_gate_rejects_missing_and_out_of_order_subtitles():
    issues = verify_renderer_artifacts(
        artifacts=artifact_bindings(),
        ocr=[
            OCRObservationV1(frame_sha256="1" * 64, text="第二段", order=2, fully_in_frame=True),
            OCRObservationV1(frame_sha256="2" * 64, text="第一段", order=1, fully_in_frame=False),
        ],
        expected_subtitles=["第一段", "第二段"],
    )
    assert {item.code for item in issues} == {
        "ocr.subtitle_order_mismatch",
        "ocr.subtitle_out_of_frame",
    }
```

- [x] **Step 2: Run RED**

- [x] **Step 3: Implement pure verification**

Accept caller-supplied OCR only. Do not import subprocess, shell, HTTP or an OCR SDK.

- [x] **Step 4: Run GREEN and commit**

Commit: `feat: gate renderer artifact and OCR evidence`

### Task 5: Update G6 runbook and verification gates

**Files:**
- Modify: `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`
- Create: `.github/workflows/b9-assisted-renderer-review.yml`

**Interfaces:**
- Produces: fresh archive members `renderer-review-input.json` and `renderer-hard-gate.json`.

- [x] **Step 1: Update the runbook**

Require verified local ephemeris inputs, provider recomputation and hard-gate `passed` before any visual confirmation.

- [x] **Step 2: Add focused CI**

Run the new hard-gate tests plus existing astronomy/editorial/package-review tests. CI stays hermetic and does not claim real renderer evidence.

- [x] **Step 3: Run full applicable gates**

```bash
make contracts-test
make text-core-test
make downstream-test
```

- [x] **Step 4: Move task to `VERIFYING`, record exact results and commit**

Commit: `docs: record scientific hard gate verification`
