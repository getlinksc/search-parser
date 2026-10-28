"""Layouts found in production zero-result samples (2026-10-28).

Both fixtures are synthetic, reduced copies of the real markup:

* ``video_card_results.html``: desktop Chrome page where some or all organic results are video
  cards (div.PmEWq, title link ``a.zReHs > h3.LC20lb``, snippet div.ITZIwc) with no yuRUbf.
* ``no_js_places_only.html``: no-JS (Opera Mini) page whose only block is a places pack of
  div.GanCKe cards linking to ``/searchviewer``.
"""

from pathlib import Path

import pytest

from search_parser.core.models import SearchResults
from search_parser.parsers.google import GoogleParser

FIX = Path(__file__).parent.parent / "fixtures" / "google"


def _parse(name: str) -> SearchResults:
    return GoogleParser().parse((FIX / name).read_text())


@pytest.fixture(scope="module")
def videos() -> SearchResults:
    return _parse("video_card_results.html")


@pytest.fixture(scope="module")
def places() -> SearchResults:
    return _parse("no_js_places_only.html")


def test_video_cards_are_organic_results_in_page_order(videos: SearchResults) -> None:
    assert [r.url for r in videos.results] == [
        "https://example.com/guide",
        "https://video.example.org/watch/1",
        "/goto?url=CAESabcdef",
    ]
    assert [r.position for r in videos.results] == [1, 2, 3]
    assert {r.result_type for r in videos.results} == {"organic"}


def test_video_cards_carry_title_and_snippet(videos: SearchResults) -> None:
    card = videos.results[1]
    assert card.title == "How to tamp espresso evenly"
    assert card.description == "A barista shows a level tamp in three steps."
    assert videos.results[0].description == "How hard to tamp and why it matters."


def test_page_of_only_video_cards_is_not_empty() -> None:
    html = (FIX / "video_card_results.html").read_text()
    start = html.index('<div class="MjjYud"><div class="N54PNb">')
    end = html.index('<div class="MjjYud"><div jsname="x"')
    results = GoogleParser().parse(html[:start] + html[end:]).results
    assert [r.title for r in results] == ["How to tamp espresso evenly", "Tamper pressure tested"]


def test_places_cards_are_local_businesses(places: SearchResults) -> None:
    assert [b.title for b in places.local_businesses] == [
        "Fast Feet Running",
        "Trail Pizza Co",
        "Corner Fuel",
    ]
    assert {b.result_type for b in places.local_businesses} == {"local_business"}
    assert places.results == []


def test_places_card_fields(places: SearchResults) -> None:
    shop, pizza, fuel = (b.metadata for b in places.local_businesses)
    assert shop == {
        "rating": "4.7",
        "reviews": "148",
        "category": "Running store",
        "location": "Ashburn, VA",
        "hours": "Closed · Opens 12 PM Mon",
        "details": ["Running store ⋅ Ashburn, VA", "Closed · Opens 12 PM Mon"],
    }
    assert pizza["price"] == "$10–20"
    assert pizza["category"] == "Pizza"
    assert pizza["reviews"] == "1,577"
    # Lines without a telling shape are kept, not guessed into category/location
    assert fuel == {
        "hours": "Open 24 hours",
        "details": ["Convenience store", "Ashburn, VA", "Open 24 hours", "$4.10/Regular"],
    }
