from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Mapping


REQUIRED_JOBS = (
    "preflight",
    "governance",
    "b9_assisted_renderer_review",
    "b9_editorial_stellarium",
    "b9_package_review_preview",
    "b9_rule_assessment",
    "b9_scientific_provider",
    "stable_core",
    "upstream_runtime",
)
ALLOWED_RESULTS = {"success", "failure", "cancelled", "skipped"}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

JOB_ENVIRONMENT = {
    "preflight": "PREFLIGHT_RESULT",
    "governance": "GOVERNANCE_RESULT",
    "b9_assisted_renderer_review": "B9_ASSISTED_RESULT",
    "b9_editorial_stellarium": "B9_EDITORIAL_RESULT",
    "b9_package_review_preview": "B9_PACKAGE_RESULT",
    "b9_rule_assessment": "B9_RULE_RESULT",
    "b9_scientific_provider": "B9_SCIENTIFIC_RESULT",
    "stable_core": "STABLE_CORE_RESULT",
    "upstream_runtime": "UPSTREAM_RUNTIME_RESULT",
}


def _sha(value: str, field: str) -> str:
    if not isinstance(value, str) or not SHA_PATTERN.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase 40-hex SHA")
    return value


def _positive_integer(value: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


def build_result(
    *,
    repository: str,
    workflow: str,
    workflow_ref: str,
    workflow_sha: str,
    event_sha: str,
    trigger_ref: str,
    trigger_ref_name: str,
    trigger_ref_type: str,
    candidate_sha: str,
    verified_candidate_sha: str,
    base_sha: str,
    run_id: int,
    run_attempt: int,
    job_results: Mapping[str, str],
) -> dict[str, object]:
    candidate_sha = _sha(candidate_sha, "candidate_sha")
    event_sha = _sha(event_sha, "event_sha")
    verified_candidate_sha = _sha(
        verified_candidate_sha, "verified_candidate_sha"
    )
    workflow_sha = _sha(workflow_sha, "workflow_sha")
    base_sha = _sha(base_sha, "base_sha")
    if len({candidate_sha, event_sha, verified_candidate_sha, workflow_sha}) != 1:
        raise ValueError("candidate, event, verified and workflow SHAs must match")
    if base_sha == candidate_sha:
        raise ValueError("base_sha must differ from candidate_sha")

    expected_tag = f"kaiyuan-runner/v2/{candidate_sha}"
    expected_ref = f"refs/tags/{expected_tag}"
    if trigger_ref_type != "tag":
        raise ValueError("trigger_ref_type must be tag")
    if trigger_ref_name != expected_tag:
        raise ValueError("tag name must bind candidate_sha")
    if trigger_ref != expected_ref:
        raise ValueError("trigger_ref must bind candidate_sha")
    if not workflow_ref.endswith(f"@{expected_ref}"):
        raise ValueError("workflow_ref must bind the candidate tag")

    if not repository or not workflow:
        raise ValueError("repository and workflow are required")
    results = dict(job_results)
    if set(results) != set(REQUIRED_JOBS):
        raise ValueError("job_results keys must equal the required job set")
    invalid_results = {
        name: result
        for name, result in results.items()
        if result not in ALLOWED_RESULTS
    }
    if invalid_results:
        raise ValueError(f"invalid job results: {invalid_results}")

    ordered_results = {name: results[name] for name in REQUIRED_JOBS}
    return {
        "schema_version": "major-version-runner-result/v1",
        "repository": repository,
        "workflow": workflow,
        "workflow_ref": workflow_ref,
        "workflow_sha": workflow_sha,
        "event_sha": event_sha,
        "trigger_ref": trigger_ref,
        "trigger_ref_name": trigger_ref_name,
        "trigger_ref_type": trigger_ref_type,
        "candidate_sha": candidate_sha,
        "verified_candidate_sha": verified_candidate_sha,
        "base_sha": base_sha,
        "run_id": _positive_integer(run_id, "run_id"),
        "run_attempt": _positive_integer(run_attempt, "run_attempt"),
        "job_results": ordered_results,
        "all_required_succeeded": all(
            result == "success" for result in ordered_results.values()
        ),
    }


def publish_result(
    result: Mapping[str, object], output_root: Path
) -> tuple[Path, Path]:
    result_path = output_root / "major-version-runner-result.json"
    sidecar_path = output_root / "major-version-runner-result.json.sha256"
    if result_path.exists() or sidecar_path.exists():
        raise FileExistsError("Runner result artifact already exists")
    result_bytes = (
        json.dumps(
            dict(result),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")
    digest = hashlib.sha256(result_bytes).hexdigest()
    with result_path.open("xb") as handle:
        handle.write(result_bytes)
    with sidecar_path.open("x", encoding="utf-8") as handle:
        handle.write(f"{digest}  {result_path.name}\n")
    return result_path, sidecar_path


def _environment_result() -> dict[str, object]:
    return build_result(
        repository=os.environ["GITHUB_REPOSITORY"],
        workflow=os.environ["GITHUB_WORKFLOW"],
        workflow_ref=os.environ["GITHUB_WORKFLOW_REF"],
        workflow_sha=os.environ["WORKFLOW_SHA"],
        event_sha=os.environ["GITHUB_SHA"],
        trigger_ref=os.environ["GITHUB_REF"],
        trigger_ref_name=os.environ["GITHUB_REF_NAME"],
        trigger_ref_type=os.environ["GITHUB_REF_TYPE"],
        candidate_sha=os.environ["CANDIDATE_SHA"],
        verified_candidate_sha=os.environ["VERIFIED_CANDIDATE_SHA"],
        base_sha=os.environ["BASE_SHA"],
        run_id=int(os.environ["GITHUB_RUN_ID"]),
        run_attempt=int(os.environ["GITHUB_RUN_ATTEMPT"]),
        job_results={
            name: os.environ[environment]
            for name, environment in JOB_ENVIRONMENT.items()
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the fail-closed GOV-T04 Runner result artifact."
    )
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = _environment_result()
    publish_result(result, args.output_root)
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a", encoding="utf-8") as output:
            output.write(
                "all_required_succeeded="
                f"{'true' if result['all_required_succeeded'] else 'false'}\n"
            )
    print(
        "Runner result: "
        f"candidate={result['candidate_sha']} "
        f"passed={str(result['all_required_succeeded']).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
