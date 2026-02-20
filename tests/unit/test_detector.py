"""Tests for search engine detector."""

from __future__ import annotations

from search_engine_parser.core.detector import SearchEngineDetector


class TestSearchEngineDetector:
    def setup_method(self) -> None:
        self.detector = SearchEngineDetector()

    def test_detect_google_meta_tag(self, google_organic_html: str) -> None:
        result = self.detector.detect(google_organic_html)
        assert result is not None
        assert result.engine == "google"
        assert result.confidence >= 0.9

    def test_detect_bing_meta_tag(self, bing_organic_html: str) -> None:
        result = self.detector.detect(bing_organic_html)
        assert result is not None
        assert result.engine == "bing"
        assert result.confidence >= 0.9

    def test_detect_duckduckgo(self, duckduckgo_organic_html: str) -> None:
        result = self.detector.detect(duckduckgo_organic_html)
        assert result is not None
        assert result.engine == "duckduckgo"
        assert result.confidence >= 0.5

    def test_detect_google_dom_structure(self) -> None:
        html = '<html><body><div id="search"><div class="g"></div></div></body></html>'
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "google"

    def test_detect_bing_dom_structure(self) -> None:
        html = '<html><body><li class="b_algo"><h2><a href="https://example.com">Test</a></h2></li></body></html>'
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "bing"

    def test_detect_duckduckgo_dom_structure(self) -> None:
        html = '<html><body><article data-testid="result"><h2><a href="https://example.com">Test</a></h2></article></body></html>'
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "duckduckgo"

    def test_detect_returns_none_for_unknown(self) -> None:
        html = "<html><body><p>Just a paragraph</p></body></html>"
        result = self.detector.detect(html)
        assert result is None

    def test_detect_empty_html(self) -> None:
        result = self.detector.detect("")
        assert result is None

    def test_detect_url_patterns(self) -> None:
        html = '<html><head><link rel="canonical" href="https://www.google.com/search?q=test"></head><body></body></html>'
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "google"
