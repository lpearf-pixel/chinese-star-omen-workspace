#!/usr/bin/env python3
"""Validate repository development-governance requirements.

This gate is intentionally dependency-free so it can run before project setup.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REQUIRED_FILES = (
    "AGENTS.md",
    "docs/development/DEVELOPMENT_MANUAL.md",
    "docs/development/TASKS.md",
    "docs/development/WORK_LOG.md",
    "docs/development/DECISIONS.md",
)

TASK_OR_LOG_FILES = {
    "docs/development/TASKS.md",
    "docs/development/WORK_LOG.md",
}

ALLOWED_TASK_STATES = {
    "BACKLOG",
    "READY",
    "IN_PROGRESS",
    "BLOCKED",
    "VERIFYING",
    "DONE",
    "CANCELLED",
}

CODE_PREFIXES = (
    "apps/",
    "packages/",
    "scripts/",
    ".github/workflows/",
    "corpus/",
    "config/",
    "schemas/",
)

CODE_ROOT_FILES = {
    "Makefile",
    "pyproject.toml",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    ".env.workspace.example",
    ".gitignore",
}

STATUS_PATTERN = re.compile(r"\*\*Status:\*\*\s*`([A-Z_]+)`")


def changed_files_from_git(root: Path, base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "unable to calculate changed files: "
            + (result.stderr.strip() or f"git exited {result.returncode}")
        )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_code_change(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    if normalized in CODE_ROOT_FILES:
        return True
    return normalized.startswith(CODE_PREFIXES)


def validate_task_states(tasks_text: str) -> list[str]:
    states = STATUS_PATTERN.findall(tasks_text)
    errors: list[str] = []
    if not states:
        errors.append("TASKS.md contains no '**Status:** `STATE`' entries")
        return errors
    invalid = sorted(set(states) - ALLOWED_TASK_STATES)
    if invalid:
        errors.append("TASKS.md contains invalid states: " + ", ".join(invalid))
    return errors


def validate_repository(root: Path, changed_files: Iterable[str]) -> list[str]:
    changed = {path.replace("\\", "/").lstrip("./") for path in changed_files}
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"required development file is missing: {relative}")

    agents_path = root / "AGENTS.md"
    if agents_path.is_file():
        agents_text = agents_path.read_text(encoding="utf-8", errors="strict")
        for required_reference in (
            "docs/development/DEVELOPMENT_MANUAL.md",
            "docs/development/TASKS.md",
            "docs/development/WORK_LOG.md",
        ):
            if required_reference not in agents_text:
                errors.append(f"AGENTS.md does not reference {required_reference}")

    tasks_path = root / "docs/development/TASKS.md"
    if tasks_path.is_file():
        tasks_text = tasks_path.read_text(encoding="utf-8", errors="strict")
        errors.extend(validate_task_states(tasks_text))

    code_changes = sorted(path for path in changed if is_code_change(path))
    if code_changes and not (changed & TASK_OR_LOG_FILES):
        errors.append(
            "code-changing PR must update docs/development/TASKS.md or "
            "docs/development/WORK_LOG.md; code paths: "
            + ", ".join(code_changes[:12])
        )

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check mandatory Kaiyuan development documentation and task logging."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base", help="base commit/ref for git diff")
    parser.add_argument("--head", help="head commit/ref for git diff")
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="explicit changed path; repeat for tests or local checks",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.changed_file:
        changed = list(args.changed_file)
    else:
        if not args.base or not args.head:
            print("ERROR: provide --base and --head, or at least one --changed-file", file=sys.stderr)
            return 2
        try:
            changed = changed_files_from_git(root, args.base, args.head)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    errors = validate_repository(root, changed)
    if errors:
        print("Development governance check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    code_count = sum(1 for path in changed if is_code_change(path))
    print(
        "Development governance check passed: "
        f"changed_files={len(changed)} code_files={code_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
