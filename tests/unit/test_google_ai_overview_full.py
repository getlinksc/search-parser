"""AI Overview: full text, sources with real URLs, citations, truncated (Chrome and Opera layouts).

Fixtures are raw documents captured 2026-10-26 through a US exit:
*.desktop / *.mobile = CloakBrowser Chrome 146 (desktop / Pixel 8 identity), *.opera = the production
requests_proxy request (curl_cffi chrome110, Opera Mobi UA, client=ms-opera-mini-android&channel=new).
"""

import gzip
from pathlib import Path

import pytest

from search_parser.parsers.google import GoogleParser
from search_parser.utils import make_soup

FIX = Path(__file__).parent.parent / "fixtures" / "google" / "aio"


def aio(name: str):
    with gzip.open(FIX / f"{name}.html.gz", "rt", errors="replace") as f:
        html = f.read()
    return GoogleParser()._extract_ai_overview(make_soup(html))


@pytest.mark.parametrize("layout", ["desktop", "mobile"])
def test_chrome_a2x_sources_and_citations(layout: str) -> None:
    r = aio(f"a2x_alternatives.{layout}")
    assert r is not None
    m = r.metadata
    assert m["present"] is True and m["layout"] == "chrome" and m["truncated"] is True
    # full text, including the part behind "Show more"
    assert "Finaloop" in m["text"] and "Higher-cost and setup-heavy" in m["text"]
    assert "AI Mode replied" not in m["text"]
    srcs = m["sources"]
    assert [s["position"] for s in srcs] == list(range(1, len(srcs) + 1))
    assert [s["domain"] for s in srcs] == [
        "linkmybooks.com",
        "taxomate.com",
        "taxomate.com",
        "synctools.ai",
        "beanhawk.com",
        "g2.com",
        "finaloop.com",
    ]
    by_title = {s["title"]: s for s in srcs}
    assert by_title["Best Taxomate Alternatives in 2026: Honest Comparison"]["url"] == (
        "https://taxomate.com/blog/taxomate-alternatives"
    )
    assert by_title["A2X Alternative at Less Than Half the Price | Taxomate"]["url"] == (
        "https://taxomate.com/a2x-alternative"
    )
    # beanhawk has no plain URL anywhere in the page: the /goto token is returned for server-side resolution
    assert by_title["Best A2X Alternatives for Ecommerce Sellers in 2026"]["url"].startswith(
        "/goto?url=CAES"
    )
    assert sum(s["url"].startswith("http") for s in srcs) == 6
    assert all(s["source"] and "<b>" not in s["title"] and "&amp;" not in s["title"] for s in srcs)
    cites = {c["sentence"]: c["source_positions"] for c in m["citations"]}
    assert cites[
        "Offers a free tier for up to 200 orders/month; paid plans start around $59/month."
    ] == [4]
    assert all(p >= 1 for c in m["citations"] for p in c["source_positions"])


def test_chrome_capital_records_order() -> None:
    m = aio("what_is_the_capital_of_australia.desktop").metadata
    assert m["text"].startswith("The capital of Australia is Canberra.")
    assert {s["domain"] for s in m["sources"]} >= {"en.wikipedia.org", "britannica.com"}
    assert m["citations"][0]["sentence"] == "The capital of Australia is Canberra."


def test_opera_full_text_and_sources() -> None:
    m = aio("a2x_alternatives.opera").metadata
    assert m["layout"] == "opera" and m["truncated"] is True and m["citations"] == []
    assert "4. Bookkeep" in m["text"] and "Higher-cost and setup-heavy." in m["text"]
    assert "Show more" not in m["text"] and "Can't generate" not in m["text"]
    srcs = m["sources"]
    assert [s["source"] for s in srcs].count("Taxomate") == 2
    # Opera cards only carry the encrypted redirect; keep it whole for the API resolver
    assert all(s["url"].startswith("/url?") and "q=CAES" in s["url"] for s in srcs)
    assert [s["position"] for s in srcs] == list(range(1, len(srcs) + 1))


def test_opera_no_people_also_ask() -> None:
    with gzip.open(FIX / "quickbooks_alternatives.opera.html.gz", "rt") as f:
        html = f.read()
    assert GoogleParser()._extract_people_also_ask(make_soup(html)) == []  # layout has none
