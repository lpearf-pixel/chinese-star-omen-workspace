from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.verify_runner_candidate import (
    CandidateVerificationError,
    verify_candidate,
)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


class RunnerCandidateVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.work = self.root / "work"
        subprocess.run(
            ["git", "init", "--bare", str(self.remote)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "init", str(self.work)],
            check=True,
            capture_output=True,
        )
        _git(self.work, "config", "user.name", "Runner Test")
        _git(self.work, "config", "user.email", "runner-test@example.invalid")
        _git(self.work, "remote", "add", "origin", str(self.remote))
        (self.work / "state.txt").write_text("base\n", encoding="utf-8")
        _git(self.work, "add", "state.txt")
        _git(self.work, "commit", "-m", "base")
        _git(self.work, "branch", "stable/kaiyuan-v2")
        _git(self.work, "push", "origin", "refs/heads/stable/kaiyuan-v2")
        self.base_sha = _git(self.work, "rev-parse", "HEAD")
        (self.work / "state.txt").write_text("candidate\n", encoding="utf-8")
        _git(self.work, "add", "state.txt")
        _git(self.work, "commit", "-m", "candidate")
        self.candidate_sha = _git(self.work, "rev-parse", "HEAD")
        self.tag_name = f"kaiyuan-runner/v2/{self.candidate_sha}"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_lightweight_tag_directly_bound_to_candidate_is_accepted(self) -> None:
        _git(self.work, "tag", self.tag_name, self.candidate_sha)
        _git(self.work, "push", "origin", f"refs/tags/{self.tag_name}")

        candidate_sha, base_sha = verify_candidate(
            repository=self.work,
            remote="origin",
            stable_ref="refs/heads/stable/kaiyuan-v2",
            candidate_sha=self.candidate_sha,
            ref_type="tag",
            ref_name=self.tag_name,
        )

        self.assertEqual(candidate_sha, self.candidate_sha)
        self.assertEqual(base_sha, self.base_sha)

    def test_annotated_tag_over_same_commit_is_rejected(self) -> None:
        _git(
            self.work,
            "tag",
            "-a",
            self.tag_name,
            "-m",
            "annotated candidate",
            self.candidate_sha,
        )
        _git(self.work, "push", "origin", f"refs/tags/{self.tag_name}")

        with self.assertRaisesRegex(
            CandidateVerificationError,
            "tag ref must directly target candidate commit",
        ):
            verify_candidate(
                repository=self.work,
                remote="origin",
                stable_ref="refs/heads/stable/kaiyuan-v2",
                candidate_sha=self.candidate_sha,
                ref_type="tag",
                ref_name=self.tag_name,
            )


if __name__ == "__main__":
    unittest.main()
