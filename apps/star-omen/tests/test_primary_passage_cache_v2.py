from __future__ import annotations

import os
from pathlib import Path

import pytest

import src.connectors.primary_passage_cache as cache_module
from src.connectors.primary_passage_cache import (
    PrimaryPassageCache,
    PrimarySourceReadError,
    build_primary_source_snapshot,
)


def _load(cache: PrimaryPassageCache, path: Path, **overrides):
    options = {
        "card_type": "fenjuan",
        "kb_book_id": "kaiyuan_zhanjing",
        "book_title": "唐開元占經",
    }
    options.update(overrides)
    return cache.load(path, **options)


def test_unchanged_exact_bytes_parse_once(monkeypatch, tmp_path: Path):
    source = tmp_path / "KR3g0018_031.md"
    source.write_text("<pb:KR3g0018_WYG_031-17a>\n熒惑守心。", encoding="utf-8")
    real_parser = cache_module.parse_kaiyuan_passages
    calls = []

    def counting_parser(*args, **kwargs):
        calls.append((args, kwargs))
        return real_parser(*args, **kwargs)

    monkeypatch.setattr(cache_module, "parse_kaiyuan_passages", counting_parser)
    cache = PrimaryPassageCache(max_entries=2)

    first = _load(cache, source)
    second = _load(cache, source)

    assert len(calls) == 1
    assert first is second
    assert isinstance(first.passages, tuple)
    assert first.content_hash.startswith("sha256:")
    assert first.text.endswith("熒惑守心。")


def test_hash_invalidates_when_size_and_mtime_are_preserved(monkeypatch, tmp_path: Path):
    source = tmp_path / "KR3g0018_031.md"
    source.write_text("甲乙丙丁", encoding="utf-8")
    original_stat = source.stat()
    real_parser = cache_module.parse_kaiyuan_passages
    calls = 0

    def counting_parser(*args, **kwargs):
        nonlocal calls
        calls += 1
        return real_parser(*args, **kwargs)

    monkeypatch.setattr(cache_module, "parse_kaiyuan_passages", counting_parser)
    cache = PrimaryPassageCache()
    first = _load(cache, source)

    source.write_text("戊己庚辛", encoding="utf-8")
    os.utime(source, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    second = _load(cache, source)

    assert source.stat().st_size == original_stat.st_size
    assert source.stat().st_mtime_ns == original_stat.st_mtime_ns
    assert calls == 2
    assert first.content_hash != second.content_hash
    assert second.text == "戊己庚辛"


def test_parser_identity_is_part_of_cache_key(monkeypatch, tmp_path: Path):
    source = tmp_path / "唐開元占經-全文合併版.md"
    source.write_text("熒惑守心。", encoding="utf-8")
    real_parser = cache_module.parse_kaiyuan_passages
    calls = 0

    def counting_parser(*args, **kwargs):
        nonlocal calls
        calls += 1
        return real_parser(*args, **kwargs)

    monkeypatch.setattr(cache_module, "parse_kaiyuan_passages", counting_parser)
    cache = PrimaryPassageCache()

    _load(cache, source, card_type="fenjuan")
    fulltext = _load(cache, source, card_type="fulltext")

    assert calls == 2
    assert fulltext.passages[0].card_type == "fulltext"


def test_cached_passage_heading_path_cannot_poison_later_loads(tmp_path: Path):
    source = tmp_path / "KR3g0018_031.md"
    source.write_text(
        "# 唐開元占經\n\n## 熒惑占\n"
        "<pb:KR3g0018_WYG_031-17a>\n熒惑守心。",
        encoding="utf-8",
    )
    cache = PrimaryPassageCache()

    first = _load(cache, source)

    assert first.passages[0].heading_path == ("唐開元占經", "熒惑占")
    with pytest.raises(AttributeError):
        first.passages[0].heading_path.append("污染")

    second = _load(cache, source)
    assert second.passages[0].heading_path == ("唐開元占經", "熒惑占")


def test_deleted_or_invalid_utf8_source_never_returns_stale_snapshot(tmp_path: Path):
    source = tmp_path / "KR3g0018_031.md"
    source.write_text("熒惑守心。", encoding="utf-8")
    cache = PrimaryPassageCache()
    _load(cache, source)

    source.unlink()
    with pytest.raises(PrimarySourceReadError, match="source_read_failed"):
        _load(cache, source)

    source.write_bytes(b"\xff\xfe")
    with pytest.raises(PrimarySourceReadError, match="source_decode_failed"):
        _load(cache, source)


def test_lru_capacity_evicts_least_recently_used(monkeypatch, tmp_path: Path):
    paths = [tmp_path / f"KR3g0018_0{index}.md" for index in range(1, 4)]
    for index, path in enumerate(paths):
        path.write_text(f"第{index}條。", encoding="utf-8")
    real_parser = cache_module.parse_kaiyuan_passages
    calls = 0

    def counting_parser(*args, **kwargs):
        nonlocal calls
        calls += 1
        return real_parser(*args, **kwargs)

    monkeypatch.setattr(cache_module, "parse_kaiyuan_passages", counting_parser)
    cache = PrimaryPassageCache(max_entries=2)

    _load(cache, paths[0])
    _load(cache, paths[1])
    _load(cache, paths[0])
    _load(cache, paths[2])
    _load(cache, paths[1])

    assert calls == 4


@pytest.mark.parametrize("capacity", [0, -1, True, 1.5])
def test_cache_rejects_invalid_capacity(capacity):
    with pytest.raises(ValueError, match="max_entries"):
        PrimaryPassageCache(max_entries=capacity)


def test_pure_byte_builder_preserves_explicit_integer_mtime_and_passage_hashes(
    tmp_path: Path,
):
    raw = (
        "# 唐開元占經\n<pb:KR3g0018_WYG_031-17a>\n石氏曰熒惑守心。"
    ).encode("utf-8")
    path = tmp_path / "古籍" / "唐開元占經" / "分卷" / "KR3g0018_031.md"

    snapshot = build_primary_source_snapshot(
        raw,
        path=path,
        mtime_ns=123456789,
        card_type="fenjuan",
        kb_book_id="kaiyuan_zhanjing",
        book_title="唐開元占經",
    )

    assert snapshot.path == path
    assert snapshot.mtime_ns == 123456789
    assert type(snapshot.mtime_ns) is int
    assert snapshot.text.endswith("石氏曰熒惑守心。")
    assert snapshot.passages[0].raw_content_hash.startswith("sha256:")


@pytest.mark.parametrize("mtime_ns", [None, True, 1.0, "1"])
def test_pure_byte_builder_rejects_non_integer_mtime(tmp_path: Path, mtime_ns):
    with pytest.raises(TypeError, match="mtime_ns"):
        build_primary_source_snapshot(
            b"source",
            path=tmp_path / "source.md",
            mtime_ns=mtime_ns,
            card_type="fenjuan",
            kb_book_id="kaiyuan_zhanjing",
            book_title="唐開元占經",
        )
