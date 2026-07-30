# Kaiyuan AI Visual Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a hash-bound AI visual report that handles audience-facing inspection without becoming a scientific authority.

**Architecture:** Define a provider-neutral strict report and a pure verifier. External adapters may submit model output, but core code accepts only normalized JSON and validates it against a passed hard-gate report and exact preview/screenshot hashes.

**Tech Stack:** Python 3.12, Pydantic v2, pytest; no mandatory model SDK.

## Global Constraints

- Start only after B9-G6-E2 merges.
- AI never overrides hard rejection.
- No credentials or raw provider response in artifacts.
- No automatic publish authority.

---

### Task 1: Define `AIAssistedVisualReview/v1`

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/assisted_review.py`
- Test: `apps/star-omen/tests/video_pipeline/package_review/test_ai_visual_review_v1.py`

- [ ] Write RED tests for exact hash binding, confidence bounds, fixed check categories, frame references and canonical serialization.

```python
def test_ai_report_is_hash_bound_and_canonical():
    report = AIAssistedVisualReviewV1(
        review_input_sha256="a" * 64,
        hard_gate_report_sha256="b" * 64,
        preview_sha256="c" * 64,
        screenshot_sha256=["d" * 64],
        provider="openai-compatible",
        model="vision-model-v1",
        prompt_policy_version="b9-ai-visual/v1",
        decision="passed",
        confidence=0.96,
        checks=[visual_check("subtitle_readability", "passed", ["d" * 64])],
    )
    assert canonical_ai_visual_review_bytes(report).endswith(b"\n")
```
- [ ] Implement strict models and derived decision validation.
- [ ] Run focused GREEN.
- [ ] Commit: `feat: define hash bound ai visual review`

### Task 2: Add normalized report verifier

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/assisted_review.py`
- Test: `apps/star-omen/tests/video_pipeline/package_review/test_ai_visual_review_binding_v1.py`

- [ ] Write RED tests proving hard rejection, hash drift, missing frames and unsupported checks invalidate the report.

```python
def test_ai_report_cannot_override_hard_rejection():
    with pytest.raises(ValueError, match="hard gate"):
        verify_ai_visual_review(
            report=ai_report(decision="passed"),
            hard_gate=hard_gate(status="rejected"),
            preview_sha256="c" * 64,
            screenshot_sha256=["d" * 64],
        )
```
- [ ] Implement `verify_ai_visual_review(...)`.
- [ ] Run focused GREEN.
- [ ] Commit: `feat: verify ai visual report bindings`

### Task 3: Add provider-neutral handoff

**Files:**
- Create: `docs/development/B9_AI_VISUAL_REVIEW_HANDOFF.md`
- Modify: `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

- [ ] Document the exact normalized request and response JSON.

```json
{
  "schema_version": "ai-assisted-visual-review/v1",
  "review_input_sha256": "<64 lowercase hex>",
  "hard_gate_report_sha256": "<64 lowercase hex>",
  "preview_sha256": "<64 lowercase hex>",
  "screenshot_sha256": ["<64 lowercase hex>"],
  "provider": "provider-id",
  "model": "model-id",
  "prompt_policy_version": "b9-ai-visual/v1",
  "decision": "passed",
  "confidence": 0.96,
  "checks": []
}
```
- [ ] Require the adapter to supply model ID and prompt-policy version.
- [ ] Explicitly forbid secrets, absolute paths and raw model responses.
- [ ] Run package-review regression and commit: `docs: add ai visual review handoff`
