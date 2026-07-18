import json

import pytest
from kb_text_core import parse_kaiyuan_passages

pytest.importorskip("typer")
pytest.importorskip("jsonschema")

from typer.testing import CliRunner

from src.cli import app


PAGE = "KR3g0018_WYG_031-17a"
RAW = "石氏曰熒惑守心，天下兵起。"


def test_audit_rules_command(tmp_path):
    source = tmp_path / "古籍" / "唐開元占經" / "分卷" / "KR3g0018_031.md"
    source.parent.mkdir(parents=True)
    text = (
        "# 唐開元占經 卷31\n\n"
        "　熒惑占二\n"
        "　　　熒惑犯心五\n"
        f"<pb:{PAGE}>\n{RAW}\n"
    )
    source.write_text(text, encoding="utf-8")
    passage = parse_kaiyuan_passages(
        text,
        source_path=str(source),
        card_type="fenjuan",
    )[0]

    rules = [
        {
            "id": "r1",
            "evidence": {
                "kb_book_id": "kaiyuan_zhanjing",
                "card_type": "fenjuan",
                "relative_path": "古籍/唐開元占經/分卷/KR3g0018_031.md",
                "source_locator": "KR3g0018_031",
                "page_marker": PAGE,
                "heading_path": passage.heading_path,
                "paragraph_index": passage.paragraph_index,
                "anchor_text": RAW,
                "content_hash": passage.raw_content_hash,
            },
        },
        {
            "id": "r2",
            "evidence": {
                "card_type": "term_card",
            },
        },
        {
            "id": "r3",
        },
    ]
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "audit-rules",
            "--rules-path",
            str(rules_path),
            "--kb-root",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    body = json.loads(result.stdout)
    assert body["total_rules"] == 3
    assert body["citable"] == 1
    assert body["candidate_only"] == 1
    assert body["missing_evidence"] == 1
