#!/usr/bin/env bash
set -Eeuo pipefail

MAX_SCREENSHOTS=30

: "${B9_OUTPUT_DIR:?set B9_OUTPUT_DIR to the fresh structured package directory}"
: "${B9_EVIDENCE_DIR:?set B9_EVIDENCE_DIR to the fresh evidence directory}"

CALLER_CWD="$(pwd -P)"
case "${B9_OUTPUT_DIR}" in
  /*) ;;
  *) B9_OUTPUT_DIR="${CALLER_CWD}/${B9_OUTPUT_DIR}" ;;
esac
case "${B9_EVIDENCE_DIR}" in
  /*) ;;
  *) B9_EVIDENCE_DIR="${CALLER_CWD}/${B9_EVIDENCE_DIR}" ;;
esac
export B9_OUTPUT_DIR B9_EVIDENCE_DIR

mkdir -p "${B9_EVIDENCE_DIR}"
B9_COLLECTOR_LOG="${B9_COLLECTOR_LOG:-${B9_EVIDENCE_DIR}/collector.log}"
export B9_COLLECTOR_LOG
exec > >(tee -a "${B9_COLLECTOR_LOG}") 2>&1

on_error() {
  local line="$1"
  local status="$2"
  printf 'collector failed: line=%s status=%s\n' "${line}" "${status}" >&2
}
trap 'on_error "${LINENO}" "$?"' ERR

if [[ "$(uname -s)" != "Darwin" ]]; then
  printf 'collector requires macOS\n' >&2
  exit 1
fi

for command_name in osascript open python; do
  command -v "${command_name}" >/dev/null 2>&1 || {
    printf 'missing command: %s\n' "${command_name}" >&2
    exit 1
  }
done

for required_path in \
  "${B9_OUTPUT_DIR}/preview.mp4" \
  "${B9_EVIDENCE_DIR}/renderer-hard-gate.json" \
  "${B9_EVIDENCE_DIR}/ai-assisted-visual-review.json"; do
  [[ -f "${required_path}" && ! -L "${required_path}" ]] || {
    printf 'missing required regular file: %s\n' "${required_path}" >&2
    exit 1
  }
done

shopt -s nullglob
SCREENSHOTS=("${B9_EVIDENCE_DIR}"/screenshots/*.png)
shopt -u nullglob
SCREENSHOT_COUNT="${#SCREENSHOTS[@]}"
if (( SCREENSHOT_COUNT < 1 )); then
  printf 'at least one screenshot is required\n' >&2
  exit 1
fi
if (( SCREENSHOT_COUNT > MAX_SCREENSHOTS )); then
  printf 'screenshot count exceeds %s: %s\n' \
    "${MAX_SCREENSHOTS}" "${SCREENSHOT_COUNT}" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"
cd "${REPO_ROOT}/apps/star-omen"

PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
python - <<'PY'
import hashlib
import os
from pathlib import Path

from src.video_pipeline.assisted_review import (
    AIAssistedVisualReviewV1,
    RendererHardGateReportV1,
    verify_ai_visual_review,
)

package = Path(os.environ["B9_OUTPUT_DIR"])
evidence = Path(os.environ["B9_EVIDENCE_DIR"])


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


hard_gate = RendererHardGateReportV1.model_validate_json(
    (evidence / "renderer-hard-gate.json").read_text(encoding="utf-8")
)
if hard_gate.status != "passed":
    raise SystemExit("renderer hard gate is not passed")
ai_review = AIAssistedVisualReviewV1.model_validate_json(
    (evidence / "ai-assisted-visual-review.json").read_text(encoding="utf-8")
)
screenshots = sorted((evidence / "screenshots").glob("*.png"))
verify_ai_visual_review(
    report=ai_review,
    hard_gate=hard_gate,
    preview_sha256=digest(package / "preview.mp4"),
    screenshot_sha256=[digest(path) for path in screenshots],
)
if ai_review.decision == "rejected":
    raise SystemExit("AI visual review rejected")
print(f"professional gates permit human confirmation: {ai_review.decision}")
PY

open -a "QuickTime Player" "${B9_OUTPUT_DIR}/preview.mp4"
open -a "Preview" "${SCREENSHOTS[@]}"

confirm_check() {
  local check_name="$1"
  local prompt="$2"
  local selection
  selection="$(
    osascript - "${check_name}" "${prompt}" <<'APPLESCRIPT'
on run argv
  set checkName to item 1 of argv
  set promptText to item 2 of argv
  tell application "System Events"
    activate
    return button returned of (display dialog promptText buttons {"Reject", "Confirm"} default button "Reject" cancel button "Reject" with title ("B9-G6 " & checkName))
  end tell
end run
APPLESCRIPT
  )"
  if [[ "${selection}" == "Confirm" ]]; then
    printf 'true'
  else
    printf 'false'
  fi
}

SUBTITLES_READABLE="$(
  confirm_check \
    "subtitles_readable" \
    "只确认：字幕是否肉眼清晰可读？不需要判断天文学。"
)"
NO_OBVIOUS_VISUAL_PROBLEM="$(
  confirm_check \
    "no_obvious_visual_problem" \
    "只确认：画面是否没有明显黑屏、异常窗口或观看问题？"
)"
EXPRESSION_MATCHES_EXPECTATION="$(
  confirm_check \
    "expression_matches_expectation" \
    "只确认：整体表达是否符合你的预期？"
)"
export \
  SUBTITLES_READABLE \
  NO_OBVIOUS_VISUAL_PROBLEM \
  EXPRESSION_MATCHES_EXPECTATION

PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
python - <<'PY'
import hashlib
import os
from pathlib import Path

from src.video_pipeline.assisted_review import (
    AIAssistedVisualReviewV1,
    HumanExperienceConfirmationV1,
    RendererHardGateReportV1,
    canonical_ai_visual_review_bytes,
    canonical_assisted_renderer_review_bytes,
    canonical_human_experience_confirmation_bytes,
    canonical_renderer_hard_gate_bytes,
    resolve_assisted_renderer_review,
    verify_ai_visual_review,
)

package = Path(os.environ["B9_OUTPUT_DIR"])
evidence = Path(os.environ["B9_EVIDENCE_DIR"])


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def checked(name: str) -> bool:
    value = os.environ[name]
    if value not in {"true", "false"}:
        raise ValueError(f"invalid confirmation value for {name}")
    return value == "true"


def write_exclusive(path: Path, content: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(content)


hard_gate = RendererHardGateReportV1.model_validate_json(
    (evidence / "renderer-hard-gate.json").read_text(encoding="utf-8")
)
ai_review = AIAssistedVisualReviewV1.model_validate_json(
    (evidence / "ai-assisted-visual-review.json").read_text(encoding="utf-8")
)
screenshots = sorted((evidence / "screenshots").glob("*.png"))
verify_ai_visual_review(
    report=ai_review,
    hard_gate=hard_gate,
    preview_sha256=digest(package / "preview.mp4"),
    screenshot_sha256=[digest(path) for path in screenshots],
)

human = HumanExperienceConfirmationV1(
    hard_gate_report_sha256=hashlib.sha256(
        canonical_renderer_hard_gate_bytes(hard_gate)
    ).hexdigest(),
    ai_visual_review_sha256=hashlib.sha256(
        canonical_ai_visual_review_bytes(ai_review)
    ).hexdigest(),
    subtitles_readable=checked("SUBTITLES_READABLE"),
    no_obvious_visual_problem=checked("NO_OBVIOUS_VISUAL_PROBLEM"),
    expression_matches_expectation=checked("EXPRESSION_MATCHES_EXPECTATION"),
)
final_review = resolve_assisted_renderer_review(
    hard_gate=hard_gate,
    ai_review=ai_review,
    human_confirmation=human,
)
write_exclusive(
    evidence / "human-experience-confirmation.json",
    canonical_human_experience_confirmation_bytes(human),
)
write_exclusive(
    evidence / "assisted-renderer-review.json",
    canonical_assisted_renderer_review_bytes(final_review),
)
print(f"assisted renderer review: {final_review.status}")
if final_review.status != "approved":
    raise SystemExit("human experience confirmation rejected")
PY

printf 'collector completed; log=%s\n' "${B9_COLLECTOR_LOG}"
