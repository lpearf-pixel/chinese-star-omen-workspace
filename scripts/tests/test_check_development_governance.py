from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "check_development_governance.py"
SPEC = importlib.util.spec_from_file_location("check_development_governance", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GovernanceCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs/development").mkdir(parents=True)
        (self.root / "AGENTS.md").write_text(
            "\n".join(
                [
                    "docs/development/DEVELOPMENT_MANUAL.md",
                    "docs/development/TASKS.md",
                    "docs/development/WORK_LOG.md",
                ]
            ),
            encoding="utf-8",
        )
        (self.root / "docs/development/DEVELOPMENT_MANUAL.md").write_text(
            "manual\n", encoding="utf-8"
        )
        (self.root / "docs/development/TASKS.md").write_text(
            "### T-1\n\n- **Status:** `IN_PROGRESS`\n",
            encoding="utf-8",
        )
        (self.root / "docs/development/WORK_LOG.md").write_text(
            "work log\n", encoding="utf-8"
        )
        (self.root / "docs/development/DECISIONS.md").write_text(
            "decisions\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_docs_only_change_does_not_require_task_log_change(self) -> None:
        errors = MODULE.validate_repository(self.root, ["README.md"])
        self.assertEqual(errors, [])

    def test_code_change_requires_task_or_work_log_update(self) -> None:
        errors = MODULE.validate_repository(
            self.root,
            ["apps/star-omen/src/example.py"],
        )
        self.assertTrue(any("code-changing PR" in error for error in errors))

    def test_code_change_passes_when_work_log_is_changed(self) -> None:
        errors = MODULE.validate_repository(
            self.root,
            [
                "apps/star-omen/src/example.py",
                "docs/development/WORK_LOG.md",
            ],
        )
        self.assertEqual(errors, [])

    def test_invalid_task_state_fails(self) -> None:
        tasks = self.root / "docs/development/TASKS.md"
        tasks.write_text("- **Status:** `STARTED`\n", encoding="utf-8")
        errors = MODULE.validate_repository(
            self.root,
            ["docs/development/TASKS.md"],
        )
        self.assertTrue(any("invalid states" in error for error in errors))

    def test_missing_required_file_fails(self) -> None:
        (self.root / "docs/development/DECISIONS.md").unlink()
        errors = MODULE.validate_repository(self.root, ["README.md"])
        self.assertTrue(any("DECISIONS.md" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
