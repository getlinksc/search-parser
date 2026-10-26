"""Whole-page checks on a production Opera Mini (no-JS) results page with ads.

Fixture: ``best vpn``, captured 2026-10-26 through a US exit with the requests_proxy request
(curl_cffi, Opera Mobi UA, client=ms-opera-mini-android&channel=new).
"""

import gzip
from pathlib import Path

import pytest

from search_parser.core.models import SearchResults
from search_parser.parsers.google import GoogleParser

FIX = Path(__file__).parent.parent / "fixtures" / "google" / "aio" / "best_vpn.opera.html.gz"


@pytest.fixture(scope="module")
def page() -> SearchResults:
    with gzip.open(FIX, "rt", errors="replace") as f:
        return GoogleParser().parse(f.read())


def test_ads_link_to_the_advertiser_not_the_click_url(page: SearchResults) -> None:
    ads = page.sponsored
    assert [a.position for a in ads] == list(range(1, len(ads) + 1))
    first = ads[0]
    assert first.url == "https://www.surfshark.com/"
    assert first.metadata["domain"] == "surfshark.com"
    assert str(first.metadata["tracking_url"]).startswith("http://www.google.com/aclk?")
    assert first.description and first.description.startswith("Take a look at how Surfshark")
    for ad in ads:
        assert "/aclk" not in ad.url
        for sitelink in ad.metadata.get("sitelinks", []):
            assert set(sitelink) == {"title", "url", "tracking_url"}
            assert sitelink["url"] is None


def test_related_searches_are_numbered_clean_links(page: SearchResults) -> None:
    related = page.people_also_search
    assert [r.position for r in related] == list(range(1, len(related) + 1))
    assert related[0].url == "https://www.google.com/search?q=Best+VPN+free"
    assert all("client=" not in r.url and "sxsrf" not in r.url for r in related)


def test_ai_overview_titles_have_no_markup(page: SearchResults) -> None:
    assert page.ai_overview is not None
    for source in page.ai_overview.metadata["sources"]:
        assert "<" not in source["title"] and "&amp;" not in source["title"]


@pytest.mark.parametrize(
    ("url", "internal"),
    [
        ("https://www.google.com/search?tbm=isch&q=Inception", True),
        ("https://www.google.com/searchviewer/abc", True),
        ("/search?q=x", True),
        ("https://cloud.google.com/discover/what-is-web-hosting", False),
        ("/url?opi=89978449&q=CAESabc", False),
        ("https://example.com/search", False),
    ],
)
def test_google_internal_links(url: str, internal: bool) -> None:
    assert GoogleParser._is_google_internal(url) is internal


@pytest.mark.parametrize(
    ("href", "expected"),
    [
        ("/search?q=a+site:reddit.com", "https://www.google.com/search?q=a+site%3Areddit.com"),
        (
            "https://www.google.com/search?q=vpn&client=ms-opera-mini-android&hs=Ib&sca_esv=63&hl=en&channel=new",
            "https://www.google.com/search?q=vpn&hl=en",
        ),
        ("/search?q=x&udm=2&sxsrf=abc&ved=0", "https://www.google.com/search?q=x&udm=2"),
        ("/url?q=CAESabc", "/url?q=CAESabc"),
        ("/goto?url=CAESabc", "/goto?url=CAESabc"),
        ("https://example.com/", "https://example.com/"),
    ],
)
def test_absolute_google_url(href: str, expected: str) -> None:
    assert GoogleParser._absolute_google_url(href) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("<b>Best</b> Rewards <b>Credit...", "Best Rewards Credit..."),
        ("Inception (2010) - Full cast &amp;...", "Inception (2010) - Full cast &..."),
        ("Plain title", "Plain title"),
    ],
)
def test_plain_text(text: str, expected: str) -> None:
    assert GoogleParser._plain_text(text) == expected
