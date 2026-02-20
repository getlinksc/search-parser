"""Tests for Google search results parser."""

from __future__ import annotations

from search_engine_parser.parsers.google import GoogleParser
from search_engine_parser.utils import make_soup


class TestGoogleParser:
    def setup_method(self) -> None:
        self.parser = GoogleParser()

    def test_engine_name(self) -> None:
        assert self.parser.engine_name == "google"

    def test_can_parse_google_html(self, google_organic_html: str) -> None:
        soup = make_soup(google_organic_html)
        confidence = self.parser.can_parse(soup)
        assert confidence >= 0.8

    def test_can_parse_non_google_html(self) -> None:
        html = "<html><body><p>Not a search page</p></body></html>"
        soup = make_soup(html)
        confidence = self.parser.can_parse(soup)
        assert confidence == 0.0

    def test_parse_organic_results(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.search_engine == "google"
        assert len(results.results) == 3
        assert results.query == "python web scraping"

        first = results.results[0]
        assert first.title == "Web Scraping with Python - Real Python"
        assert first.url == "https://realpython.com/python-web-scraping/"
        assert first.position == 1
        assert first.result_type == "organic"
        assert first.description is not None

    def test_parse_organic_result_positions(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        positions = [r.position for r in results.results]
        assert positions == [1, 2, 3]

    def test_parse_featured_snippet(self, google_featured_html: str) -> None:
        results = self.parser.parse(google_featured_html)
        featured = [r for r in results.results if r.result_type == "featured_snippet"]
        assert len(featured) == 1
        assert featured[0].position == 0
        assert featured[0].title == "What is Web Scraping?"
        assert featured[0].description is not None

    def test_parse_featured_with_organic(self, google_featured_html: str) -> None:
        results = self.parser.parse(google_featured_html)
        organic = [r for r in results.results if r.result_type == "organic"]
        assert len(organic) == 2

    def test_parse_empty_html(self) -> None:
        results = self.parser.parse("<html><body></body></html>")
        assert results.search_engine == "google"
        assert len(results.results) == 0

    def test_parse_malformed_results(self) -> None:
        html = """
        <html><head><meta property="og:site_name" content="Google"></head>
        <body><div id="search">
            <div class="g"><div class="yuRUbf"><a href=""><h3></h3></a></div></div>
        </div></body></html>
        """
        results = self.parser.parse(html)
        # Empty title/url results should be skipped
        assert len(results.results) == 0

    def test_detection_confidence(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.detection_confidence >= 0.8
