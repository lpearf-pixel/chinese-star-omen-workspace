from __future__ import annotations

import json
from pathlib import Path

from kb_text_core import audit_ctext_spot_checks


def test_spot_check_audit_reports_exact_normalized_mismatch_and_missing(tmp_path: Path):
    corpus = tmp_path / "corpus"
    volume = corpus / "分卷" / "KR3g0018_031.md"
    volume.parent.mkdir(parents=True)
    volume.write_text(
        "<pb:KR3g0018_WYG_031-17a>\n"
        "石氏曰熒惑守心，天下兵起。\n"
        "<pb:KR3g0018_WYG_031-17b>\n"
        "甘氏曰熒 惑 守 心，有急兵。\n",
        encoding="utf-8",
    )
    checks = {
        "schema_version": "kaiyuan-ctext-spot-checks/v1",
        "source": {
            "platform": "Chinese Text Project",
            "url": "https://ctext.org/wiki.pl?if=gb&res=348345&remap=gb",
            "accessed_on": "2026-07-17",
            "automatic_bulk_download": False,
        },
        "checks": [
            {
                "id": "exact",
                "local_relative_path": "分卷/KR3g0018_031.md",
                "source_locator": "KR3g0018_031",
                "page_marker": "KR3g0018_WYG_031-17a",
                "reference_text": "石氏曰熒惑守心，天下兵起。",
            },
            {
                "id": "normalized",
                "local_relative_path": "分卷/KR3g0018_031.md",
                "source_locator": "KR3g0018_031",
                "page_marker": "KR3g0018_WYG_031-17b",
                "reference_text": "甘氏曰荧惑守心，有急兵。",
            },
            {
                "id": "mismatch",
                "local_relative_path": "分卷/KR3g0018_031.md",
                "source_locator": "KR3g0018_031",
                "page_marker": "KR3g0018_WYG_031-17b",
                "reference_text": "本页没有此句。",
            },
            {
                "id": "missing",
                "local_relative_path": "分卷/KR3g0018_099.md",
                "source_locator": "KR3g0018_099",
                "page_marker": "KR3g0018_WYG_099-1a",
                "reference_text": "缺卷。",
            },
        ],
    }
    config = tmp_path / "checks.json"
    config.write_text(
        json.dumps(checks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = audit_ctext_spot_checks(config, corpus)

    assert report["schema_version"] == "kaiyuan-ctext-spot-check-report/v1"
    assert report["network_accessed"] is False
    assert report["source"]["automatic_bulk_download"] is False
    assert report["counts"] == {
        "exact_raw": 1,
        "exact_normalized": 1,
        "mismatch": 1,
        "missing_source": 1,
        "missing_page": 0,
        "invalid": 0,
    }
    assert [row["status"] for row in report["checks"]] == [
        "exact_raw",
        "exact_normalized",
        "mismatch",
        "missing_source",
    ]
    assert report["checks"][1]["local_raw_preserved"] is True
    assert report["all_matched"] is False
