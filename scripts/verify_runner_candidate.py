from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class CandidateVerificationError(ValueError):
    pass


def _git(
    repository: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", "-C", str(repository), *args],
        capture_output=True,
        text=True,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise CandidateVerificationError(
            f"git {' '.join(args)} failed: {detail or completed.returncode}"
        )
    return completed


def _single_sha(value: str, field: str) -> str:
    value = value.strip()
    if not SHA_PATTERN.fullmatch(value):
        raise CandidateVerificationError(
            f"{field} must be a full lowercase 40-hex commit SHA"
        )
    return value


def verify_candidate(
    *,
    repository: Path,
    remote: str,
    stable_ref: str,
    candidate_sha: str,
    ref_type: str,
    ref_name: str,
) -> tuple[str, str]:
    repository = repository.resolve()
    candidate_sha = _single_sha(candidate_sha, "candidate_sha")
    expected_tag = f"kaiyuan-runner/v2/{candidate_sha}"
    if ref_type != "tag":
        raise CandidateVerificationError("ref_type must be tag")
    if ref_name != expected_tag:
        raise CandidateVerificationError("tag name must bind candidate_sha")

    object_type = _git(
        repository, "cat-file", "-t", candidate_sha
    ).stdout.strip()
    if object_type != "commit":
        raise CandidateVerificationError("candidate_sha must identify a commit")
    checkout_sha = _single_sha(
        _git(repository, "rev-parse", "HEAD").stdout,
        "checkout HEAD",
    )
    if checkout_sha != candidate_sha:
        raise CandidateVerificationError("checkout HEAD must equal candidate_sha")

    tag_ref = f"refs/tags/{expected_tag}"
    remote_lines = [
        line
        for line in _git(
            repository,
            "ls-remote",
            "--refs",
            remote,
            tag_ref,
        ).stdout.splitlines()
        if line.strip()
    ]
    if len(remote_lines) != 1:
        raise CandidateVerificationError("exact remote candidate tag ref is required")
    fields = remote_lines[0].split()
    if len(fields) != 2 or fields[1] != tag_ref:
        raise CandidateVerificationError("remote candidate tag response is invalid")
    direct_tag_sha = _single_sha(fields[0], "remote tag object")
    if direct_tag_sha != candidate_sha:
        raise CandidateVerificationError(
            "tag ref must directly target candidate commit; annotated tags are forbidden"
        )

    local_stable_ref = "refs/remotes/kaiyuan-runner/stable"
    _git(
        repository,
        "fetch",
        "--no-tags",
        remote,
        f"+{stable_ref}:{local_stable_ref}",
    )
    base_sha = _single_sha(
        _git(repository, "rev-parse", local_stable_ref).stdout,
        "base_sha",
    )
    if base_sha == candidate_sha:
        raise CandidateVerificationError("candidate must be strictly ahead of stable")
    ancestor = _git(
        repository,
        "merge-base",
        "--is-ancestor",
        base_sha,
        candidate_sha,
        check=False,
    )
    if ancestor.returncode != 0:
        raise CandidateVerificationError("stable must be an ancestor of candidate")
    merge_base = _single_sha(
        _git(repository, "merge-base", base_sha, candidate_sha).stdout,
        "merge base",
    )
    if merge_base != base_sha:
        raise CandidateVerificationError("stable must be the exact merge base")
    return candidate_sha, base_sha


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a GOV-T04 exact-SHA lightweight tag candidate."
    )
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--stable-ref", default="refs/heads/stable/kaiyuan-v2")
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--ref-type", required=True)
    parser.add_argument("--ref-name", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    candidate_sha, base_sha = verify_candidate(
        repository=args.repository,
        remote=args.remote,
        stable_ref=args.stable_ref,
        candidate_sha=args.candidate_sha,
        ref_type=args.ref_type,
        ref_name=args.ref_name,
    )
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            output.write(f"candidate_sha={candidate_sha}\n")
            output.write(f"base_sha={base_sha}\n")
    print(f"Runner candidate verified: candidate={candidate_sha} base={base_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
