from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_runner_workflows import validate_repository


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class RunnerWorkflowValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        workflow_root = self.root / ".github" / "workflows"
        workflow_root.parent.mkdir(parents=True)
        shutil.copytree(REPOSITORY_ROOT / ".github" / "workflows", workflow_root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_repository_has_one_complete_exact_sha_tag_gate(self) -> None:
        self.assertEqual(validate_repository(REPOSITORY_ROOT), [])

    def test_automatic_trigger_is_rejected(self) -> None:
        path = self.root / ".github/workflows/b9-scientific-provider.yml"
        text = path.read_text(encoding="utf-8")
        text = text.replace("  workflow_call:\n", "  pull_request:\n", 1)
        path.write_text(text, encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertTrue(any("automatic trigger" in error for error in errors))

    def test_checkout_without_candidate_sha_is_rejected(self) -> None:
        path = self.root / ".github/workflows/b9-rule-assessment.yml"
        text = path.read_text(encoding="utf-8")
        text = text.replace("        with:\n          ref: ${{ inputs.candidate_sha }}\n", "", 1)
        path.write_text(text, encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertTrue(
            any("candidate_sha checkout" in error for error in errors)
        )

    def test_incomplete_orchestrator_fan_in_is_rejected(self) -> None:
        path = self.root / ".github/workflows/kaiyuan-major-version-gate.yml"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            text = text.replace(
                "    uses: ./.github/workflows/b9-package-review-preview.yml\n",
                "    uses: ./.github/workflows/b9-rule-assessment.yml\n",
                1,
            )
        else:
            text = "name: Incomplete gate\non:\n  workflow_dispatch:\njobs:\n"
        path.write_text(text, encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertTrue(any("missing reusable workflow" in error for error in errors))

    def test_default_branch_only_dispatch_is_rejected(self) -> None:
        path = self.root / ".github/workflows/kaiyuan-major-version-gate.yml"
        text = path.read_text(encoding="utf-8")
        if "  workflow_dispatch:\n" not in text:
            text = re.sub(
                r"(?ms)^on:\n.*?(?=^[A-Za-z_][A-Za-z0-9_-]*:\n)",
                "on:\n  workflow_dispatch:\n    inputs:\n"
                "      candidate_sha:\n        required: true\n"
                "        type: string\n\n",
                text,
                count=1,
            )
        path.write_text(text, encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertTrue(
            any("default-branch-only workflow_dispatch" in error for error in errors)
        )

    def test_unified_branch_push_filter_is_rejected(self) -> None:
        path = self.root / ".github/workflows/kaiyuan-major-version-gate.yml"
        text = path.read_text(encoding="utf-8").replace(
            "  push:\n    tags:\n",
            '  push:\n    branches:\n      - "**"\n    tags:\n',
            1,
        )
        path.write_text(text, encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertTrue(any("branch push filter" in error for error in errors))

    def test_unified_extra_tag_filter_is_rejected(self) -> None:
        path = self.root / ".github/workflows/kaiyuan-major-version-gate.yml"
        text = path.read_text(encoding="utf-8").replace(
            '      - "kaiyuan-runner/v2/*"\n',
            '      - "kaiyuan-runner/v2/*"\n      - "release/*"\n',
            1,
        )
        path.write_text(text, encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertTrue(any("exactly one tag filter" in error for error in errors))

    def test_reusable_call_cannot_inherit_secrets(self) -> None:
        path = self.root / ".github/workflows/kaiyuan-major-version-gate.yml"
        text = path.read_text(encoding="utf-8").replace(
            "    uses: ./.github/workflows/b9-scientific-provider.yml\n",
            "    uses: ./.github/workflows/b9-scientific-provider.yml\n"
            "    secrets: inherit\n",
            1,
        )
        path.write_text(text, encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertTrue(any("must not inherit secrets" in error for error in errors))

    def test_duplicate_checkout_ref_cannot_override_candidate(self) -> None:
        path = self.root / ".github/workflows/kaiyuan-major-version-gate.yml"
        text = path.read_text(encoding="utf-8").replace(
            "          ref: ${{ github.sha }}\n",
            "          ref: ${{ github.sha }}\n          ref: main\n",
            1,
        )
        path.write_text(text, encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertTrue(any("exactly one checkout ref" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
