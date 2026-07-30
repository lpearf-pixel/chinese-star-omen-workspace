from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/collect_b9_g6_macos_evidence.sh"


def test_collector_uses_native_apps_and_has_no_terminal_approval() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert 'open -a "QuickTime Player"' in script
    assert 'open -a "Preview"' in script
    assert "IFS= read" not in script
    assert "read -r" not in script
    assert "subtitles_readable" in script
    assert "no_obvious_visual_problem" in script
    assert "expression_matches_expectation" in script
    assert 'buttons {"Reject", "Confirm"}' in script


def test_collector_gates_dialogs_and_bounds_screenshots() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    preflight = script.index("verify_ai_visual_review")
    quicktime = script.index('open -a "QuickTime Player"')
    dialog = script.index('display dialog')
    assert preflight < quicktime < dialog
    assert "MAX_SCREENSHOTS=30" in script
    assert 'if (( SCREENSHOT_COUNT > MAX_SCREENSHOTS ))' in script
    assert "renderer hard gate is not passed" in script
    assert "AI visual review rejected" in script


def test_collector_has_persistent_log_and_valid_bash_syntax() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert "B9_COLLECTOR_LOG" in script
    assert "tee -a" in script
    assert "trap 'on_error" in script
    completed = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
