"""Tests for Bing search results parser."""

from __future__ import annotations

from search_engine_parser.parsers.bing import BingParser
from search_engine_parser.utils import make_soup


class TestBingParser:
    def setup_method(self) -> None:
        self.parser = BingParser()

    def test_engine_name(self) -> None:
        assert self.parser.engine_name == "bing"

    def test_can_parse_bing_html(self, bing_organic_html: str) -> None:
        soup = make_soup(bing_organic_html)
        confidence = self.parser.can_parse(soup)
        assert confidence >= 0.85

    def test_can_parse_non_bing_html(self) -> None:
        html = "<html><body><p>Not a search page</p></body></html>"
        soup = make_soup(html)
        confidence = self.parser.can_parse(soup)
        assert confidence == 0.0

    def test_parse_organic_results(self, bing_organic_html: str) -> None:
        results = self.parser.parse(bing_organic_html)
        assert results.search_engine == "bing"
        assert len(results.results) == 3
        assert results.query == "python web scraping"

        first = results.results[0]
        assert first.title == "Web Scraping with Python - Real Python"
        assert first.url == "https://realpython.com/python-web-scraping/"
        assert first.position == 1
        assert first.result_type == "organic"

    def test_parse_result_descriptions(self, bing_organic_html: str) -> None:
        results = self.parser.parse(bing_organic_html)
        for result in results.results:
            assert result.description is not None
            assert len(result.description) > 0

    def test_parse_result_positions(self, bing_organic_html: str) -> None:
        results = self.parser.parse(bing_organic_html)
        positions = [r.position for r in results.results]
        assert positions == [1, 2, 3]

    def test_parse_empty_html(self) -> None:
        results = self.parser.parse("<html><body></body></html>")
        assert results.search_engine == "bing"
        assert len(results.results) == 0

    def test_detection_confidence(self, bing_organic_html: str) -> None:
        results = self.parser.parse(bing_organic_html)
        assert results.detection_confidence >= 0.85
