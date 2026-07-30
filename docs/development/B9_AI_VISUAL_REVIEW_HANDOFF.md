# B9 AI Visual Review Handoff

This handoff lets a local or hosted vision adapter inspect audience-facing media without making the provider part of the B9 core or giving it scientific authority.

## Boundary

The adapter runs only after `renderer-hard-gate.json` has status `passed`. It may inspect:

- whether the visible celestial object matches the intended shot;
- subtitle readability, clipping and occlusion;
- black or frozen frames;
- unexpected windows, cursors or capture artifacts;
- internal field names leaking into audience copy;
- overall audience-facing coherence.

It must not judge astronomy, ancient-text provenance, classical evidence, artifact lineage, publication readiness or legal/compliance status. A machine hard-gate rejection is final for that evidence run.

## Normalized request

The orchestration layer sends this JSON and supplies the exact preview and screenshots out of band by SHA-256. URIs, filesystem paths, credentials and provider-specific request bodies are not part of the normalized request.

```json
{
  "schema_version": "ai-visual-review-request/v1",
  "review_input_sha256": "<64 lowercase hex>",
  "hard_gate_report_sha256": "<64 lowercase hex>",
  "preview_sha256": "<64 lowercase hex>",
  "screenshot_sha256": [
    "<64 lowercase hex>"
  ],
  "prompt_policy_version": "b9-ai-visual/v1",
  "allowed_checks": [
    "celestial_object_shot_match",
    "subtitle_readability",
    "playback_integrity",
    "unexpected_window_or_cursor",
    "internal_field_leakage",
    "audience_coherence"
  ]
}
```

The screenshot list is ordered and contains at most 30 unique hashes. The adapter must not add a check outside `allowed_checks`.

## Normalized response

The adapter returns only this strict report:

```json
{
  "schema_version": "ai-assisted-visual-review/v1",
  "review_input_sha256": "<64 lowercase hex>",
  "hard_gate_report_sha256": "<64 lowercase hex>",
  "preview_sha256": "<64 lowercase hex>",
  "screenshot_sha256": [
    "<64 lowercase hex>"
  ],
  "provider": "provider-id",
  "model": "model-id",
  "prompt_policy_version": "b9-ai-visual/v1",
  "decision": "passed",
  "confidence": 0.96,
  "checks": [
    {
      "schema_version": "ai-assisted-visual-check/v1",
      "category": "subtitle_readability",
      "status": "passed",
      "evidence_frame_sha256": [
        "<64 lowercase hex>"
      ],
      "summary": "Subtitles remain readable and within the frame."
    }
  ]
}
```

`decision` and each check `status` use exactly:

```text
passed
rejected
needs_human_review
```

The total decision is derived: any rejected check means `rejected`; otherwise any uncertain check means `needs_human_review`; otherwise it is `passed`. Every evidence-frame hash must occur in the ordered screenshot list. Check categories are unique and use the request order.

## Adapter requirements

- Set the real provider ID, exact model ID and `b9-ai-visual/v1` prompt-policy version.
- Normalize provider output before it crosses into core code.
- Never include API keys, authorization headers, signed URLs, account IDs, absolute paths, environment variables, raw provider responses, chain-of-thought or unrelated machine logs.
- Do not persist provider-native request or response payloads in the evidence archive.
- Do not silently convert provider timeout, authentication, quota, transport or malformed-output errors into `needs_human_review`; those are run-level failures and no report is produced.
- Do not call a provider automatically from contract or package code.

## Core verification

Core code parses the normalized response as `AIAssistedVisualReviewV1` and calls:

```python
verify_ai_visual_review(
    report=report,
    hard_gate=hard_gate,
    preview_sha256=observed_preview_sha256,
    screenshot_sha256=ordered_observed_screenshot_sha256,
)
```

Verification rejects a failed hard gate, review-input drift, hard-gate-report drift, preview drift, screenshot drift, missing evidence frames, unsupported categories, invalid confidence or a non-derived decision. The canonical accepted artifact is `ai-assisted-visual-review.json`.

An accepted AI report is review evidence only. It cannot approve the final assisted review or publish media.
