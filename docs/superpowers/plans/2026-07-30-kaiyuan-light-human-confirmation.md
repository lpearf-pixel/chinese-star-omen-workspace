# Kaiyuan Lightweight Human Confirmation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace expert `y/n` approval with three layperson checks shown only after professional gates permit confirmation.

**Architecture:** Add a strict human-experience report and final pure resolver. The macOS collector uses native dialogs and Preview/QuickTime, but the evidence model contains no AppleScript or subprocess behavior.

**Tech Stack:** Python 3.12, Pydantic v2, pytest; macOS shell collector only in the runbook.

## Global Constraints

- No terminal `read` and no generic `y`.
- Approval UI is unavailable after machine or AI rejection.
- Human input cannot change scientific or evidence fields.

---

### Task 1: Define human and final decision contracts

**Files:**
- Modify: `apps/star-omen/src/video_pipeline/assisted_review.py`
- Test: `apps/star-omen/tests/video_pipeline/package_review/test_assisted_renderer_final_decision_v1.py`

- [ ] Write RED tests for the exact three booleans, report hash bindings and the `approved|rejected|incomplete` truth table.

```python
@pytest.mark.parametrize(
    ("hard", "ai", "human", "expected"),
    [
        ("rejected", "passed", True, "rejected"),
        ("passed", "rejected", True, "rejected"),
        ("passed", "needs_human_review", False, "rejected"),
        ("passed", "passed", True, "approved"),
    ],
)
def test_final_review_truth_table(hard, ai, human, expected):
    assert resolve_assisted_renderer_review(
        hard_gate=hard_gate(status=hard),
        ai_review=ai_report(decision=ai),
        human_confirmation=human_report(all_confirmed=human),
    ).status == expected
```
- [ ] Implement `HumanExperienceConfirmationV1`, `AssistedRendererReviewV1` and `resolve_assisted_renderer_review(...)`.
- [ ] Run focused GREEN.
- [ ] Commit: `feat: resolve assisted renderer review`

### Task 2: Update macOS collector workflow

**Files:**
- Modify: `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`
- Create: `scripts/collect_b9_g6_macos_evidence.sh`
- Test: `tests/test_collect_b9_g6_macos_evidence_script.py`

- [ ] Write static RED tests for QuickTime/Preview app selection, three named checks, no stdin read, no approval after hard reject, persistent logs and bounded screenshots.

```python
def test_collector_uses_native_apps_and_has_no_terminal_approval():
    script = SCRIPT.read_text(encoding="utf-8")
    assert 'open -a "QuickTime Player"' in script
    assert 'open -a "Preview"' in script
    assert "IFS= read" not in script
    assert "subtitles_readable" in script
    assert "no_obvious_visual_problem" in script
    assert "expression_matches_expectation" in script
```
- [ ] Implement the collector script as a repository asset.
- [ ] Run `bash -n` and static focused tests.
- [ ] Commit: `feat: add lightweight macos g6 confirmation`

### Task 3: Regenerate and independently verify G6

**Files:**
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/WORK_LOG.md`
- Create: `docs/development/B9_G6_FINAL_EVIDENCE.md`

- [ ] Run the collector on macOS with a fresh run ID.
- [ ] Require hard gate pass, hash-bound AI report and three-check human approval.
- [ ] Independently verify the archive; do not trust UI state alone.
- [ ] Record exact archive SHA-256 and gate results.
- [ ] Move B9-G6 to `VERIFYING`; commit: `docs: record assisted g6 evidence`
