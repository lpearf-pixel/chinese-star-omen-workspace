from __future__ import annotations

import argparse
import json
import shutil
import sys
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_REPO_URL = "https://github.com/lpearf-pixel/kaiyuanzhanjin.git"
DEFAULT_REF = "main"
DEFAULT_DESTS = [
    Path("apps/star-omen/data/sources/古籍/唐開元占經"),
    Path("apps/local-kb-unified/data/sources/古籍/唐開元占經"),
]
EXCLUDED_NAMES = {".git", ".DS_Store", "__pycache__"}


def _copy_tree_contents(source_root: Path, dest: Path, *, clean: bool) -> int:
    if clean and dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    copied = 0
    for item in sorted(source_root.iterdir()):
        if item.name in EXCLUDED_NAMES:
            continue
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target, ignore=shutil.ignore_patterns(*EXCLUDED_NAMES))
            copied += sum(1 for p in target.rglob("*") if p.is_file())
        elif item.is_file():
            shutil.copy2(item, target)
            copied += 1
    return copied


def _clone_repo(repo_url: str, ref: str, workdir: Path) -> Path:
    target = workdir / "kaiyuanzhanjin"
    cmd = ["git", "clone", "--depth", "1", "--branch", ref, repo_url, str(target)]
    try:
        subprocess.run(cmd, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(
            f"failed to clone {repo_url}@{ref}: {stderr or exc}. "
            "If this environment cannot access GitHub, clone lpearf-pixel/kaiyuanzhanjin locally "
            "and rerun with --source-dir /path/to/kaiyuanzhanjin, or set KAIYUAN_SOURCE_DIR for make sync-kaiyuan-source."
        ) from exc
    return target


def sync_kaiyuan_source(*, source_dir: Path | None, repo_url: str, ref: str, dests: Iterable[Path], clean: bool) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="kaiyuan-source-") as tmp:
        source_root = source_dir if source_dir is not None else _clone_repo(repo_url, ref, Path(tmp))
        source_root = source_root.resolve()
        if not source_root.exists():
            raise FileNotFoundError(f"source directory not found: {source_root}")
        if not (source_root / "分卷").exists():
            raise FileNotFoundError(f"expected kaiyuanzhanjin repo layout with a 分卷 directory: {source_root}")

        results = []
        for dest in dests:
            copied = _copy_tree_contents(source_root, dest, clean=clean)
            manifest = {
                "source_repo_url": repo_url,
                "source_ref": ref,
                "source_dir": str(source_root),
                "book_id": "kaiyuan_zhanjing",
                "book_title": "唐開元占經",
                "synced_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "files_copied": copied,
                "layout": "古籍/唐開元占經/{分卷,全文合併版,...}",
            }
            (dest / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            results.append({"dest": str(dest), "files_copied": copied, "manifest": str(dest / "source_manifest.json")})
        return {"source": str(source_root), "repo_url": repo_url, "ref": ref, "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync the open-source lpearf-pixel/kaiyuanzhanjin text repo into monorepo KB source roots."
    )
    parser.add_argument("--source-dir", type=Path, help="Use an already-cloned kaiyuanzhanjin directory instead of cloning from GitHub")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help="Git repository URL to clone when --source-dir is omitted")
    parser.add_argument("--ref", default=DEFAULT_REF, help="Git branch/tag to clone when --source-dir is omitted")
    parser.add_argument(
        "--dest",
        action="append",
        type=Path,
        help="Destination root. May be repeated. Defaults to both upstream and downstream data/sources/古籍/唐開元占經",
    )
    parser.add_argument("--clean", action="store_true", help="Remove each destination before copying")
    args = parser.parse_args()
    dests = args.dest if args.dest else DEFAULT_DESTS
    try:
        result = sync_kaiyuan_source(source_dir=args.source_dir, repo_url=args.repo_url, ref=args.ref, dests=dests, clean=args.clean)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
