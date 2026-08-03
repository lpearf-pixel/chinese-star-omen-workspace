from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime, timezone
from urllib.parse import quote

import pytest
from pydantic import ValidationError

from kb_contracts import CaptureStatus, ResearchAccessionV1


BASE = {
    "schema_version": "research-accession/v1",
    "accession_id": "zhws-yisizhan-5-r854562",
    "family_id": "yisizhan",
    "work_printed": "乙巳占",
    "work_normalized_candidate": "乙巳占",
    "page_title": "乙巳占/5",
    "oldid": 854562,
    "permanent_url": (
        "https://zh.wikisource.org/w/index.php?"
        "title=%E4%B9%99%E5%B7%B3%E5%8D%A0/5&oldid=854562"
    ),
    "floating_url": "https://zh.wikisource.org/wiki/%E4%B9%99%E5%B7%B3%E5%8D%A0/5",
    "revision_timestamp": "2017-04-16T03:54:43Z",
    "accessed_on": "2026-08-01",
    "locator": "卷五",
    "version_family": "Wikisource transcription; print edition unknown.",
    "author_or_compiler": "李淳風",
    "license_note": (
        "CC BY-SA site metadata; ancient text separately public-domain."
    ),
    "independent_witness_note": "No independent witness established.",
    "core14_cases": ["C09", "C13"],
    "relevant_excerpt": "火逆行氐，失地。",
    "excerpt_locator": "raw line 11",
    "raw_path": (
        "corpus/research_sources/related-wikisource/p0/yisizhan/raw/"
        "yisizhan-5-oldid-854562.wikitext"
    ),
    "raw_sha256": (
        "15d1774880be1178b7d61bdbcca45bedd"
        "9611fd60925e3e9b35c909cae435078"
    ),
    "raw_byte_count": 31158,
    "capture_status": "complete",
    "capture_note": "complete_separable_page_wikitext",
}


def test_complete_accession_is_deeply_frozen_and_canonical() -> None:
    """Catches mutable case collections or nondeterministic JSON encoding."""
    item = ResearchAccessionV1.model_validate(BASE)

    assert item.capture_status is CaptureStatus.COMPLETE
    assert item.core14_cases == ("C09", "C13")
    assert item.canonical_json_bytes() == json.dumps(
        item.model_dump(mode="json", exclude_none=False),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert b'"accessed_on":"2026-08-01"' in item.canonical_json_bytes()
    assert b'"revision_timestamp":"2017-04-16T03:54:43Z"' in (
        item.canonical_json_bytes()
    )

    with pytest.raises(ValidationError):
        item.oldid = 1
    with pytest.raises(AttributeError):
        item.core14_cases.append("C47")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("accession_id", "乙巳占"),
        ("accession_id", "zhws/yisizhan"),
        ("family_id", "yi si zhan"),
        ("family_id", "works/yisizhan"),
        ("oldid", 0),
        ("oldid", True),
        ("raw_sha256", "bad"),
        ("raw_sha256", "A" * 64),
        ("raw_byte_count", -1),
        ("raw_byte_count", True),
        ("core14_cases", ["C13", "C09"]),
        ("core14_cases", ["C09", "C09"]),
        ("core14_cases", ["C9"]),
    ],
)
def test_accession_rejects_invalid_identity_digest_or_case_order(
    field: str, value: object
) -> None:
    """Catches unsafe IDs, weak raw identity, and unstable case ordering."""
    payload = deepcopy(BASE)
    payload[field] = value

    with pytest.raises(ValidationError):
        ResearchAccessionV1.model_validate(payload)


@pytest.mark.parametrize(
    "permanent_url",
    [
        "https://zh.wikisource.org/wiki/乙巳占/5",
        "https://zh.wikisource.org/w/index.php?title=乙巳占/5&oldid=1854562",
        (
            "https://zh.wikisource.org/w/index.php?title=乙巳占/5"
            "&oldid=854562&oldid=854562"
        ),
        "http://zh.wikisource.org/w/index.php?title=乙巳占/5&oldid=854562",
    ],
)
def test_complete_accession_requires_exact_oldid_in_https_permanent_url(
    permanent_url: str,
) -> None:
    """Catches floating, wrong-revision, and non-HTTPS replay URLs."""
    payload = deepcopy(BASE)
    payload["permanent_url"] = permanent_url

    with pytest.raises(ValidationError, match="permanent_url"):
        ResearchAccessionV1.model_validate(payload)


@pytest.mark.parametrize(
    "permanent_url",
    [
        (
            "https://attacker.example/w/index.php?"
            "title=%E4%B9%99%E5%B7%B3%E5%8D%A0/5&oldid=854562"
        ),
        (
            "https://user@zh.wikisource.org/w/index.php?"
            "title=%E4%B9%99%E5%B7%B3%E5%8D%A0/5&oldid=854562"
        ),
        (
            "https://zh.wikisource.org/wiki/%E4%B9%99%E5%B7%B3%E5%8D%A0/5?"
            "title=%E4%B9%99%E5%B7%B3%E5%8D%A0/5&oldid=854562"
        ),
        (
            "https://zh.wikisource.org/w/index.php;evil?"
            "title=%E4%B9%99%E5%B7%B3%E5%8D%A0/5&oldid=854562"
        ),
        (
            "https://zh.wikisource.org/w/index.php?"
            "title=%E4%B9%99%E5%B7%B3%E5%8D%A0/6&oldid=854562"
        ),
        (
            "https://zh.wikisource.org/w/index.php?"
            "title=%E4%B9%99%E5%B7%B3%E5%8D%A0/5&"
            "title=%E4%B9%99%E5%B7%B3%E5%8D%A0/5&oldid=854562"
        ),
        (
            "https://zh.wikisource.org/w/index.php?"
            "title=%E4%B9%99%E5%B7%B3%E5%8D%A0/5&oldid=854562&action=raw"
        ),
    ],
)
def test_permanent_url_is_confined_to_exact_wikisource_revision_route(
    permanent_url: str,
) -> None:
    """Catches host, userinfo, route, title, duplicate, and extra-query attacks."""
    payload = deepcopy(BASE)
    payload["permanent_url"] = permanent_url

    with pytest.raises(ValidationError, match="permanent_url"):
        ResearchAccessionV1.model_validate(payload)


@pytest.mark.parametrize(
    "floating_url",
    [
        "https://attacker.example/wiki/%E4%B9%99%E5%B7%B3%E5%8D%A0/5",
        "https://user@zh.wikisource.org/wiki/%E4%B9%99%E5%B7%B3%E5%8D%A0/5",
        "http://zh.wikisource.org/wiki/%E4%B9%99%E5%B7%B3%E5%8D%A0/5",
        "https://zh.wikisource.org/%77iki/%E4%B9%99%E5%B7%B3%E5%8D%A0/5",
        "https://zh.wikisource.org/zh-hans/%E4%B9%99%E5%B7%B3%E5%8D%A0/5",
        "https://zh.wikisource.org/wiki/%E4%B9%99%E5%B7%B3%E5%8D%A0/6",
        "https://zh.wikisource.org/wiki/%E4%B9%99%E5%B7%B3%E5%8D%A0/5;evil",
        "https://zh.wikisource.org/wiki/%E4%B9%99%E5%B7%B3%E5%8D%A0/5?oldid=1",
    ],
)
def test_floating_url_is_confined_to_matching_wikisource_wiki_route(
    floating_url: str,
) -> None:
    """Catches floating links that cannot identify the declared page title."""
    payload = deepcopy(BASE)
    payload["floating_url"] = floating_url

    with pytest.raises(ValidationError, match="floating_url"):
        ResearchAccessionV1.model_validate(payload)


@pytest.mark.parametrize(
    ("page_title", "floating_url"),
    [
        (
            "宋書/卷23",
            "https://zh.wikisource.org/zh-hant/%E5%AE%8B%E6%9B%B8/%E5%8D%B723",
        ),
        (
            "後漢紀 (四庫全書本)/卷16",
            "https://zh.wikisource.org/wiki/後漢紀_(四庫全書本)/卷16",
        ),
    ],
)
def test_floating_url_preserves_fixed_legacy_wikisource_route_forms(
    page_title: str, floating_url: str
) -> None:
    """Catches rejection of the two route/title forms in the fixed denominator."""
    payload = deepcopy(BASE)
    payload["page_title"] = page_title
    payload["floating_url"] = floating_url
    payload["permanent_url"] = (
        "https://zh.wikisource.org/w/index.php?title="
        f"{quote(page_title, safe='/')}&oldid=854562"
    )

    assert ResearchAccessionV1.model_validate(payload).floating_url == floating_url


def test_permanent_url_compares_mediawiki_underscore_as_space() -> None:
    """Catches rejection of the fixed 後漢紀 revision title spelling."""
    payload = deepcopy(BASE)
    payload.update(
        {
            "page_title": "後漢紀 (四庫全書本)/卷16",
            "floating_url": (
                "https://zh.wikisource.org/wiki/後漢紀_(四庫全書本)/卷16"
            ),
            "permanent_url": (
                "https://zh.wikisource.org/w/index.php?"
                "title=後漢紀_(四庫全書本)/卷16&oldid=854562"
            ),
        }
    )

    assert ResearchAccessionV1.model_validate(payload).page_title == payload[
        "page_title"
    ]


def test_permanent_url_rejects_normalized_mediawiki_title_mismatch() -> None:
    """Catches a different volume hidden behind otherwise valid title syntax."""
    payload = deepcopy(BASE)
    payload.update(
        {
            "page_title": "後漢紀 (四庫全書本)/卷16",
            "floating_url": (
                "https://zh.wikisource.org/wiki/後漢紀_(四庫全書本)/卷16"
            ),
            "permanent_url": (
                "https://zh.wikisource.org/w/index.php?"
                "title=後漢紀_(四庫全書本)/卷17&oldid=854562"
            ),
        }
    )

    with pytest.raises(ValidationError, match="permanent_url"):
        ResearchAccessionV1.model_validate(payload)


@pytest.mark.parametrize(
    "raw_path",
    [
        "/corpus/research_sources/related-wikisource/raw/object.wikitext",
        "corpus/research_sources/related-wikisource/../outside.wikitext",
        "corpus/research_sources/other/object.wikitext",
        (
            "corpus/research_sources/related-wikisource//p0/yisizhan/raw/"
            "object.wikitext"
        ),
        (
            "corpus/research_sources/related-wikisource/p0/./yisizhan/raw/"
            "object.wikitext"
        ),
        (
            "corpus/research_sources/related-wikisource/p0/yisizhan/raw/"
            "object.wikitext\x00"
        ),
    ],
)
def test_raw_path_is_confined_to_research_source_package(raw_path: str) -> None:
    """Catches absolute, traversal, and out-of-package raw paths."""
    payload = deepcopy(BASE)
    payload["raw_path"] = raw_path

    with pytest.raises(ValidationError, match="raw_path"):
        ResearchAccessionV1.model_validate(payload)


def test_noncomplete_accession_requires_reason_and_coherent_raw_identity() -> None:
    """Catches status-only failures and partially fabricated raw identities."""
    payload = deepcopy(BASE)
    payload.update(
        {
            "capture_status": "partial_with_reason",
            "failure_reason": "revision replay returned only a partial carrier page",
            "raw_path": None,
            "raw_sha256": None,
            "raw_byte_count": None,
        }
    )

    item = ResearchAccessionV1.model_validate(payload)
    assert item.capture_status is CaptureStatus.PARTIAL_WITH_REASON
    assert item.failure_reason == (
        "revision replay returned only a partial carrier page"
    )

    missing_reason = deepcopy(payload)
    missing_reason["failure_reason"] = None
    with pytest.raises(ValidationError, match="failure_reason"):
        ResearchAccessionV1.model_validate(missing_reason)

    incomplete_identity = deepcopy(payload)
    incomplete_identity["raw_path"] = BASE["raw_path"]
    with pytest.raises(ValidationError, match="raw identity"):
        ResearchAccessionV1.model_validate(incomplete_identity)


def test_complete_accession_requires_raw_identity_and_revision_metadata() -> None:
    """Catches complete captures that cannot be replayed byte-for-byte."""
    for field in (
        "oldid",
        "permanent_url",
        "revision_timestamp",
        "raw_path",
        "raw_sha256",
        "raw_byte_count",
    ):
        payload = deepcopy(BASE)
        payload[field] = None
        with pytest.raises(ValidationError, match=field):
            ResearchAccessionV1.model_validate(payload)


def test_complete_accession_rejects_failure_reason() -> None:
    """Catches contradictory complete-plus-failure preservation records."""
    payload = deepcopy(BASE)
    payload["failure_reason"] = "source replay failed after capture"

    with pytest.raises(ValidationError, match="failure_reason"):
        ResearchAccessionV1.model_validate(payload)


def test_legacy_hypothesis_strings_are_preserved_without_interpretation() -> None:
    """Catches normalization or promotion of compatibility hypothesis strings."""
    payload = deepcopy(BASE)
    payload.update(
        {
            "work_normalized_candidate": " 乙巳占（候选，未定） ",
            "version_family": " 底本不明；仅保留平台转录说明。\n",
            "independent_witness_note": (
                "\t独立见证状态未定，不得据此批准。 "
            ),
            "author_or_compiler": (
                " 李淳風？（平台题署，未核权威底本）\t"
            ),
        }
    )

    item = ResearchAccessionV1.model_validate(payload)

    assert item.work_normalized_candidate == payload["work_normalized_candidate"]
    assert item.version_family == payload["version_family"]
    assert item.independent_witness_note == payload["independent_witness_note"]
    assert item.author_or_compiler == payload["author_or_compiler"]


@pytest.mark.parametrize(
    "field",
    [
        "work_printed",
        "work_normalized_candidate",
        "page_title",
        "floating_url",
        "locator",
        "version_family",
        "author_or_compiler",
        "license_note",
        "independent_witness_note",
        "excerpt_locator",
        "capture_note",
    ],
)
def test_required_preserved_text_rejects_blank_only(field: str) -> None:
    """Catches blank required metadata after global whitespace stripping is removed."""
    payload = deepcopy(BASE)
    payload[field] = " \t\n "

    with pytest.raises(ValidationError, match=field):
        ResearchAccessionV1.model_validate(payload)


def test_relevant_excerpt_allows_empty_and_preserves_whitespace() -> None:
    """Catches accidental nonblank enforcement or normalization of source excerpts."""
    empty = deepcopy(BASE)
    empty["relevant_excerpt"] = ""
    assert ResearchAccessionV1.model_validate(empty).relevant_excerpt == ""

    spaced = deepcopy(BASE)
    spaced["relevant_excerpt"] = "  火逆行氐。\n"
    assert ResearchAccessionV1.model_validate(spaced).relevant_excerpt == spaced[
        "relevant_excerpt"
    ]


@pytest.mark.parametrize(
    "accessed_on",
    [
        "2026-08-01T00:00:00",
        "2026-08-01T00:00:00Z",
        datetime(2026, 8, 1),
        datetime(2026, 8, 1, tzinfo=timezone.utc),
    ],
)
def test_accessed_on_rejects_datetime_values(accessed_on: object) -> None:
    """Catches lossy midnight-datetime coercion into an accession date."""
    payload = deepcopy(BASE)
    payload["accessed_on"] = accessed_on

    with pytest.raises(ValidationError, match="accessed_on"):
        ResearchAccessionV1.model_validate(payload)


@pytest.mark.parametrize("accessed_on", ["2026-08-01", date(2026, 8, 1)])
def test_accessed_on_accepts_exact_date_inputs(accessed_on: object) -> None:
    """Catches over-strict date handling that rejects the two contract forms."""
    payload = deepcopy(BASE)
    payload["accessed_on"] = accessed_on

    assert ResearchAccessionV1.model_validate(payload).accessed_on == date(2026, 8, 1)


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "rule_status",
        "reviewer_decision",
        "production_ingest",
        "canonical_text",
        "independent_witness",
    ],
)
def test_research_contract_forbids_production_or_approval_fields(
    forbidden_field: str,
) -> None:
    """Catches accidental promotion of a preservation record into approval state."""
    payload = deepcopy(BASE)
    payload[forbidden_field] = False

    with pytest.raises(ValidationError, match="Extra inputs"):
        ResearchAccessionV1.model_validate(payload)
