"""Unit tests for GoogleParser._splice_jsl_dh: which element each jsl.dh fragment lands in."""

from __future__ import annotations

from bs4 import BeautifulSoup

from search_parser.parsers.google import GoogleParser
from search_parser.utils import make_soup

PARSER = GoogleParser()


def _spliced(body: str, *frags: tuple[str, str]) -> BeautifulSoup:
    scripts = "".join(f"<script>window.jsl.dh('{fid}','{html}');</script>" for fid, html in frags)
    soup = make_soup(f"<html><body>{body}{scripts}</body></html>")
    PARSER._splice_jsl_dh(soup, soup)
    for script in soup.find_all("script"):
        script.decompose()
    return soup


def _texts(soup: BeautifulSoup, fid: str) -> list[str]:
    return [el.get_text() for el in soup.find_all(id=fid)]


def test_a_fragment_replaces_its_targets_content() -> None:
    soup = _spliced('<div id="a">old</div>', ("a", "<p>new</p>"))
    assert _texts(soup, "a") == ["new"]


def test_a_fragment_can_target_an_id_another_fragment_created() -> None:
    # listed before the fragment that creates its target: lands on the next round
    soup = _spliced('<div id="a"></div>', ("b", "<i>inner</i>"), ("a", '<span id="b"></span>'))
    assert _texts(soup, "b") == ["inner"]
    assert _texts(soup, "a") == ["inner"]


def test_a_repeated_id_takes_the_first_in_document_order() -> None:
    soup = _spliced('<div id="a">1</div><div id="a">2</div>', ("a", "x"))
    assert _texts(soup, "a") == ["x", "2"]


def test_an_id_cleared_away_is_no_longer_a_target() -> None:
    # #b goes with #a's old content, so its fragment has nowhere to land
    soup = _spliced(
        '<div id="a"><div id="b">b</div></div>', ("a", "<p>new</p>"), ("b", "<p>lost</p>")
    )
    assert _texts(soup, "a") == ["new"]
    assert "lost" not in soup.get_text()


def test_a_new_element_with_a_cleared_id_is_the_target() -> None:
    soup = _spliced(
        '<div id="a"><div id="b">old</div></div>',
        ("a", '<div id="b"></div>'),
        ("b", "<p>new</p>"),
    )
    assert _texts(soup, "b") == ["new"]


def test_no_fragments_leaves_the_tree_alone() -> None:
    assert _texts(_spliced('<div id="a">old</div>'), "a") == ["old"]
