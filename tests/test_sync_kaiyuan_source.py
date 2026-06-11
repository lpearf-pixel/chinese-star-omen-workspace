from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sync_kaiyuan_source import sync_kaiyuan_source


def test_sync_kaiyuan_source_copies_repo_layout(tmp_path: Path):
    source = tmp_path / "kaiyuanzhanjin"
    (source / "分卷").mkdir(parents=True)
    (source / "分卷" / "KR3g0018_031.md").write_text("# 唐開元占經 卷31\n\n熒惑守心。\n", encoding="utf-8")
    (source / "唐開元占經-全文合併版.md").write_text("熒惑守心。\n", encoding="utf-8")
    (source / ".git").mkdir()
    (source / ".git" / "ignored").write_text("ignore", encoding="utf-8")
    dest = tmp_path / "workspace" / "apps" / "star-omen" / "data" / "sources" / "古籍" / "唐開元占經"

    out = sync_kaiyuan_source(source_dir=source, repo_url="local", ref="main", dests=[dest], clean=True)

    assert out["results"][0]["files_copied"] == 2
    assert (dest / "分卷" / "KR3g0018_031.md").exists()
    assert (dest / "唐開元占經-全文合併版.md").exists()
    assert (dest / "source_manifest.json").exists()
    assert not (dest / ".git").exists()
