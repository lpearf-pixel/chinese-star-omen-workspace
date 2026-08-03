from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_runner_result import REQUIRED_JOBS, build_result, publish_result


SHA_A = "a" * 40
SHA_B = "b" * 40


def valid_inputs() -> dict[str, object]:
    tag_name = f"kaiyuan-runner/v2/{SHA_A}"
    return {
        "repository": "lpearf-pixel/chinese-star-omen-workspace",
        "workflow": "Kaiyuan Major-Version Unified Gate",
        "workflow_ref": "lpearf-pixel/chinese-star-omen-workspace/.github/workflows/kaiyuan-major-version-gate.yml@refs/tags/"
        + tag_name,
        "workflow_sha": SHA_A,
        "event_sha": SHA_A,
        "trigger_ref": f"refs/tags/{tag_name}",
        "trigger_ref_name": tag_name,
        "trigger_ref_type": "tag",
        "candidate_sha": SHA_A,
        "verified_candidate_sha": SHA_A,
        "base_sha": SHA_B,
        "run_id": 12345,
        "run_attempt": 1,
        "job_results": {name: "success" for name in REQUIRED_JOBS},
    }


class RunnerResultTests(unittest.TestCase):
    def test_success_result_is_exact_tag_and_job_bound(self) -> None:
        result = build_result(**valid_inputs())

        self.assertEqual(result["schema_version"], "major-version-runner-result/v1")
        self.assertEqual(result["candidate_sha"], SHA_A)
        self.assertEqual(result["trigger_ref"], f"refs/tags/kaiyuan-runner/v2/{SHA_A}")
        self.assertEqual(result["job_results"], {name: "success" for name in REQUIRED_JOBS})
        self.assertTrue(result["all_required_succeeded"])

    def test_failed_job_is_preserved_and_fails_unified_result(self) -> None:
        values = valid_inputs()
        values["job_results"] = {
            **values["job_results"],
            "upstream_runtime": "failure",
        }

        result = build_result(**values)

        self.assertEqual(result["job_results"]["upstream_runtime"], "failure")
        self.assertFalse(result["all_required_succeeded"])

    def test_tag_candidate_mismatch_is_rejected(self) -> None:
        values = valid_inputs()
        values["trigger_ref_name"] = f"kaiyuan-runner/v2/{SHA_B}"

        with self.assertRaisesRegex(ValueError, "tag name must bind candidate_sha"):
            build_result(**values)

    def test_missing_required_job_is_rejected(self) -> None:
        values = valid_inputs()
        results = dict(values["job_results"])
        results.pop("governance")
        values["job_results"] = results

        with self.assertRaisesRegex(ValueError, "job_results keys"):
            build_result(**values)

    def test_publish_writes_verifiable_sidecar_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result_path, sidecar_path = publish_result(
                build_result(**valid_inputs()), root
            )
            result_bytes = result_path.read_bytes()
            digest = hashlib.sha256(result_bytes).hexdigest()

            self.assertEqual(
                json.loads(result_bytes), build_result(**valid_inputs())
            )
            self.assertEqual(
                sidecar_path.read_text(encoding="utf-8"),
                f"{digest}  major-version-runner-result.json\n",
            )
            with self.assertRaisesRegex(FileExistsError, "already exists"):
                publish_result(build_result(**valid_inputs()), root)


if __name__ == "__main__":
    unittest.main()
