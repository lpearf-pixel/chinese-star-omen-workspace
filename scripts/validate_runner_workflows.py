from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable


REUSABLE_WORKFLOWS = (
    "b9-assisted-renderer-review.yml",
    "b9-editorial-stellarium.yml",
    "b9-package-review-preview.yml",
    "b9-rule-assessment.yml",
    "b9-scientific-provider.yml",
    "development-governance.yml",
    "kaiyuan-pr-a.yml",
    "kaiyuan-upstream-runtime.yml",
)
UNIFIED_WORKFLOW = "kaiyuan-major-version-gate.yml"
ORDINARY_EVENTS = {"pull_request", "pull_request_target", "push"}
PR_EVENTS = {"pull_request", "pull_request_target"}
CALL_JOBS = {
    "b9-assisted-renderer-review.yml": "b9-assisted-renderer-review",
    "b9-editorial-stellarium.yml": "b9-editorial-stellarium",
    "b9-package-review-preview.yml": "b9-package-review-preview",
    "b9-rule-assessment.yml": "b9-rule-assessment",
    "b9-scientific-provider.yml": "b9-scientific-provider",
    "development-governance.yml": "governance",
    "kaiyuan-pr-a.yml": "stable-core",
    "kaiyuan-upstream-runtime.yml": "upstream-runtime",
}


def _top_level_block(text: str, key: str) -> str | None:
    lines = text.splitlines(keepends=True)
    start = next(
        (index for index, line in enumerate(lines) if line.rstrip() == f"{key}:"),
        None,
    )
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.strip() and not line.startswith((" ", "\t", "#")):
            end = index
            break
    return "".join(lines[start:end])


def _event_keys(text: str) -> set[str]:
    block = _top_level_block(text, "on")
    if block is None:
        return set()
    return {
        match.group(1)
        for match in re.finditer(r"(?m)^  ([A-Za-z_][A-Za-z0-9_-]*):", block)
    }


def _nested_block(text: str, key: str, indent: int) -> str | None:
    lines = text.splitlines(keepends=True)
    marker = f"{' ' * indent}{key}:"
    start = next(
        (index for index, line in enumerate(lines) if line.rstrip() == marker),
        None,
    )
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        current_indent = len(line) - len(line.lstrip(" "))
        if line.strip() and current_indent <= indent:
            end = index
            break
    return "".join(lines[start:end])


def _mapping_keys(text: str, indent: int) -> list[str]:
    indentation = re.escape(" " * indent)
    return [
        match.group(1)
        for match in re.finditer(
            rf"(?m)^{indentation}([A-Za-z_][A-Za-z0-9_-]*):", text
        )
    ]


def _sequence_values(text: str, key: str, indent: int) -> list[str]:
    block = _nested_block(text, key, indent)
    if block is None:
        return []
    values: list[str] = []
    item_indent = " " * (indent + 2)
    for line in block.splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if not line.startswith(item_indent + "- "):
            return []
        values.append(stripped[2:].strip().strip('"').strip("'"))
    return values


def _input_block(on_block: str, name: str) -> str | None:
    lines = on_block.splitlines(keepends=True)
    marker = f"      {name}:"
    start = next(
        (index for index, line in enumerate(lines) if line.rstrip() == marker),
        None,
    )
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.strip() and len(line) - len(line.lstrip(" ")) <= 6:
            end = index
            break
    return "".join(lines[start:end])


def _required_string_input(on_block: str, name: str) -> bool:
    block = _input_block(on_block, name)
    if block is None:
        return False
    return bool(
        re.search(r"(?m)^        required: true\s*$", block)
        and re.search(r"(?m)^        type: string\s*$", block)
    )


def _checkout_blocks(text: str) -> list[str]:
    lines = text.splitlines(keepends=True)
    blocks: list[str] = []
    for start, line in enumerate(lines):
        if line.strip() != "- uses: actions/checkout@v4":
            continue
        indent = len(line) - len(line.lstrip(" "))
        end = len(lines)
        for index in range(start + 1, len(lines)):
            candidate = lines[index]
            candidate_indent = len(candidate) - len(candidate.lstrip(" "))
            if (
                candidate.strip().startswith("- ")
                and candidate_indent == indent
            ):
                end = index
                break
        blocks.append("".join(lines[start:end]))
    return blocks


def _checkout_ref_errors(text: str, expected_ref: str, name: str) -> list[str]:
    errors: list[str] = []
    blocks = _checkout_blocks(text)
    if not blocks:
        return [f"{name}: at least one checkout is required"]
    for index, block in enumerate(blocks, start=1):
        refs = [
            match.group(1).strip()
            for match in re.finditer(r"(?m)^\s+ref:\s*(.+?)\s*$", block)
        ]
        if refs != [expected_ref]:
            errors.append(
                f"{name}: checkout {index} must have exactly one checkout ref "
                f"bound to {expected_ref}"
            )
    return errors


def _job_blocks(text: str) -> dict[str, str]:
    jobs = _top_level_block(text, "jobs")
    if jobs is None:
        return {}
    lines = jobs.splitlines(keepends=True)
    starts: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^  ([a-z0-9][a-z0-9-]*):\s*$", line)
        if match:
            starts.append((index, match.group(1)))
    result: dict[str, str] = {}
    for position, (start, name) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        result[name] = "".join(lines[start:end])
    return result


def _validate_reusable(path: Path) -> list[str]:
    errors: list[str] = []
    name = path.name
    if not path.is_file():
        return [f"{name}: missing reusable workflow"]
    text = path.read_text(encoding="utf-8")
    events = _event_keys(text)
    automatic = events & ORDINARY_EVENTS
    if automatic:
        errors.append(f"{name}: automatic trigger forbidden: {sorted(automatic)}")
    if events != {"workflow_call"}:
        errors.append(f"{name}: expected only workflow_call, found {sorted(events)}")
    on_block = _top_level_block(text, "on") or ""
    if not _required_string_input(on_block, "candidate_sha"):
        errors.append(f"{name}: candidate_sha must be a required string input")
    if name == "development-governance.yml" and not _required_string_input(
        on_block, "base_sha"
    ):
        errors.append(f"{name}: base_sha must be a required string input")

    checkout_errors = _checkout_ref_errors(
        text, "${{ inputs.candidate_sha }}", name
    )
    errors.extend(checkout_errors)
    if checkout_errors:
        errors.append(f"{name}: every checkout needs candidate_sha checkout binding")
    if name == "development-governance.yml":
        if '--base "${{ inputs.base_sha }}"' not in text:
            errors.append(f"{name}: governance base is not input-bound")
        if '--head "${{ inputs.candidate_sha }}"' not in text:
            errors.append(f"{name}: governance head is not input-bound")
    return errors


def _validate_unified(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"{path.name}: missing unified workflow"]
    text = path.read_text(encoding="utf-8")
    events = _event_keys(text)
    if "workflow_dispatch" in events:
        errors.append(
            f"{path.name}: default-branch-only workflow_dispatch is forbidden"
        )
    automatic = events & PR_EVENTS
    if automatic:
        errors.append(f"{path.name}: automatic trigger forbidden: {sorted(automatic)}")
    if events != {"push"}:
        errors.append(
            f"{path.name}: expected only exact candidate tag push, found {sorted(events)}"
        )
    on_block = _top_level_block(text, "on") or ""
    push_block = _nested_block(on_block, "push", 2) or ""
    push_keys = _mapping_keys(push_block, 4)
    branch_keys = {"branches", "branches-ignore"} & set(push_keys)
    if branch_keys:
        errors.append(
            f"{path.name}: branch push filter forbidden: {sorted(branch_keys)}"
        )
    if push_keys != ["tags"]:
        errors.append(
            f"{path.name}: push must contain only one tags filter"
        )
    tag_filters = _sequence_values(push_block, "tags", 4)
    if tag_filters != ["kaiyuan-runner/v2/*"]:
        errors.append(
            f"{path.name}: exactly one tag filter kaiyuan-runner/v2/* is required"
        )
    if "permissions:\n  contents: read" not in text:
        errors.append(f"{path.name}: contents permission must be read-only")
    errors.extend(
        _checkout_ref_errors(text, "${{ github.sha }}", path.name)
    )

    jobs = _job_blocks(text)
    preflight = jobs.get("preflight", "")
    if not preflight:
        errors.append(f"{path.name}: preflight job is required")
    else:
        markers = (
            "ref: ${{ github.sha }}",
            "candidate_sha: ${{ github.sha }}",
            "python3 scripts/verify_runner_candidate.py",
            '--candidate-sha "$candidate_sha"',
            '--ref-type "$GITHUB_REF_TYPE"',
            '--ref-name "$GITHUB_REF_NAME"',
            "--stable-ref refs/heads/stable/kaiyuan-v2",
            '--github-output "$GITHUB_OUTPUT"',
            "candidate_sha: ${{ steps.verify.outputs.candidate_sha }}",
            "base_sha: ${{ steps.verify.outputs.base_sha }}",
        )
        for marker in markers:
            if marker not in preflight:
                errors.append(f"{path.name}: preflight missing marker: {marker}")

    for reusable, job_name in CALL_JOBS.items():
        call = jobs.get(job_name, "")
        expected_use = f"uses: ./.github/workflows/{reusable}"
        if expected_use not in call:
            errors.append(f"{path.name}: missing reusable workflow {reusable}")
            continue
        if "needs: preflight" not in call:
            errors.append(f"{path.name}: {job_name} must need preflight")
        if "candidate_sha: ${{ needs.preflight.outputs.candidate_sha }}" not in call:
            errors.append(f"{path.name}: {job_name} candidate input is not verified")
        if re.search(r"(?m)^    secrets:\s*inherit\s*$", call):
            errors.append(f"{path.name}: {job_name} must not inherit secrets")
        if reusable == "development-governance.yml" and (
            "base_sha: ${{ needs.preflight.outputs.base_sha }}" not in call
        ):
            errors.append(f"{path.name}: governance base input is not verified")

    finalizer = jobs.get("finalize", "")
    if not finalizer:
        errors.append(f"{path.name}: finalize job is required")
    else:
        if "if: ${{ always() }}" not in finalizer:
            errors.append(f"{path.name}: finalize must always run")
        for needed in ("preflight", *CALL_JOBS.values()):
            if f"      - {needed}\n" not in finalizer:
                errors.append(f"{path.name}: finalize needs missing job {needed}")
        for marker in (
            "uses: actions/checkout@v4",
            "ref: ${{ github.sha }}",
            "python3 scripts/build_runner_result.py",
            "actions/upload-artifact@v4",
            "major-version-runner-result.json.sha256",
            "exit 1",
        ):
            if marker not in finalizer:
                errors.append(f"{path.name}: finalize missing evidence marker {marker}")
    return errors


def _workflow_files(root: Path) -> Iterable[Path]:
    workflow_root = root / ".github" / "workflows"
    yield from sorted(workflow_root.glob("*.yml"))
    yield from sorted(workflow_root.glob("*.yaml"))


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    workflow_root = root / ".github" / "workflows"
    errors: list[str] = []
    for path in _workflow_files(root):
        events = _event_keys(path.read_text(encoding="utf-8"))
        automatic = events & PR_EVENTS
        if "push" in events and path.name != UNIFIED_WORKFLOW:
            automatic.add("push")
        if automatic:
            errors.append(
                f"{path.name}: automatic trigger forbidden repository-wide: {sorted(automatic)}"
            )
    for name in REUSABLE_WORKFLOWS:
        errors.extend(_validate_reusable(workflow_root / name))
    errors.extend(_validate_unified(workflow_root / UNIFIED_WORKFLOW))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate GOV-T04 exact-SHA Runner workflow topology."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = validate_repository(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Runner workflow topology: PASS (8 reusable + 1 unified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
