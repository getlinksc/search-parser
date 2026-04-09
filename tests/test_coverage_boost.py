"""Additional tests to boost code coverage above 90%."""

from __future__ import annotations

import pytest

from search_parser.core.detector import SearchEngineDetector
from search_parser.core.models import SearchResult, SearchResults
from search_parser.core.parser import SearchParser
from search_parser.exceptions import ParseError
from search_parser.formatters.markdown_formatter import MarkdownFormatter
from search_parser.parsers.bing import BingParser
from search_parser.parsers.duckduckgo import DuckDuckGoParser
from search_parser.parsers.google import GoogleParser
from search_parser.utils import clean_text, make_soup

# --- Utils tests ---


class TestUtils:
    def test_clean_text_empty(self) -> None:
        assert clean_text("") == ""

    def test_clean_text_none(self) -> None:
        assert clean_text(None) == ""

    def test_clean_text_whitespace(self) -> None:
        assert clean_text("  hello   world  ") == "hello world"

    def test_make_soup(self) -> None:
        soup = make_soup("<html><body><p>test</p></body></html>")
        assert soup.find("p") is not None


# --- Detector edge cases ---


class TestDetectorEdgeCases:
    def setup_method(self) -> None:
        self.detector = SearchEngineDetector()

    def test_detect_bing_url_pattern(self) -> None:
        html = '<html><head><link rel="canonical" href="https://www.bing.com/search?q=test"></head><body></body></html>'
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "bing"

    def test_detect_duckduckgo_url_pattern(self) -> None:
        html = '<html><head><link rel="canonical" href="https://duckduckgo.com/?q=test"></head><body></body></html>'
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "duckduckgo"

    def test_detect_bing_link_pattern(self) -> None:
        html = '<html><head><link href="https://www.bing.com/style.css"></head><body></body></html>'
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "bing"

    def test_detect_duckduckgo_link_pattern(self) -> None:
        html = (
            '<html><head><link href="https://duckduckgo.com/style.css"></head><body></body></html>'
        )
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "duckduckgo"

    def test_detect_google_link_pattern(self) -> None:
        html = (
            '<html><head><link href="https://www.gstatic.com/style.css"></head><body></body></html>'
        )
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "google"

    def test_detect_duckduckgo_meta_tag(self) -> None:
        html = '<html><head><meta name="description" content="DuckDuckGo search results"></head><body></body></html>'
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "duckduckgo"

    def test_detect_low_confidence_returns_none(self) -> None:
        """Ensure very low confidence results return None."""
        html = "<html><body><div>just text</div></body></html>"
        result = self.detector.detect(html)
        assert result is None

    def test_detect_bing_meta_name(self) -> None:
        html = '<html><head><meta name="bing-something" content="value"></head><body></body></html>'
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "bing"

    def test_detect_div_result_as_duckduckgo(self) -> None:
        html = '<html><body><div class="result"><a href="https://example.com">Test</a></div></body></html>'
        result = self.detector.detect(html)
        assert result is not None
        assert result.engine == "duckduckgo"


# --- Parser base class tests ---


class TestBaseParser:
    def test_extract_query_from_input(self) -> None:
        parser = GoogleParser()
        soup = make_soup('<html><body><input name="q" value="test query"></body></html>')
        assert parser.extract_query(soup) == "test query"

    def test_extract_query_from_title_google(self) -> None:
        parser = GoogleParser()
        soup = make_soup(
            "<html><head><title>test query - Google Search</title></head><body></body></html>"
        )
        assert parser.extract_query(soup) == "test query"

    def test_extract_query_from_title_bing(self) -> None:
        parser = BingParser()
        soup = make_soup("<html><head><title>test query - Bing</title></head><body></body></html>")
        assert parser.extract_query(soup) == "test query"

    def test_extract_query_from_title_ddg(self) -> None:
        parser = DuckDuckGoParser()
        soup = make_soup(
            "<html><head><title>test query at DuckDuckGo</title></head><body></body></html>"
        )
        assert parser.extract_query(soup) == "test query"

    def test_extract_query_returns_none(self) -> None:
        parser = GoogleParser()
        soup = make_soup("<html><body></body></html>")
        assert parser.extract_query(soup) is None

    def test_extract_query_no_value(self) -> None:
        parser = GoogleParser()
        soup = make_soup('<html><body><input name="q" value=""></body></html>')
        # Empty value should fall through
        assert parser.extract_query(soup) is None

    def test_extract_query_title_no_suffix(self) -> None:
        parser = GoogleParser()
        soup = make_soup("<html><head><title>Some Random Title</title></head><body></body></html>")
        assert parser.extract_query(soup) is None


# --- Google parser edge cases ---


class TestGoogleEdgeCases:
    def test_parse_result_without_link_container(self) -> None:
        """Test parsing when result has direct a/h3 without yuRUbf container."""
        html = """
        <html><head><meta property="og:site_name" content="Google"></head>
        <body><div id="search">
            <div class="g">
                <a href="https://example.com"><h3>Direct Link Result</h3></a>
                <div class="VwiC3b">Some description</div>
            </div>
        </div></body></html>
        """
        parser = GoogleParser()
        results = parser.parse(html)
        assert len(results.results) == 1
        assert results.results[0].title == "Direct Link Result"

    def test_parse_result_no_link(self) -> None:
        html = """
        <html><head><meta property="og:site_name" content="Google"></head>
        <body><div id="search">
            <div class="g"><h3>No link here</h3></div>
        </div></body></html>
        """
        parser = GoogleParser()
        results = parser.parse(html)
        assert len(results.results) == 0

    def test_parse_result_link_container_no_link(self) -> None:
        html = """
        <html><head><meta property="og:site_name" content="Google"></head>
        <body><div id="search">
            <div class="g"><div class="yuRUbf"><h3>Title</h3></div></div>
        </div></body></html>
        """
        parser = GoogleParser()
        results = parser.parse(html)
        assert len(results.results) == 0

    def test_parse_result_no_description(self) -> None:
        html = """
        <html><head><meta property="og:site_name" content="Google"></head>
        <body><div id="search">
            <div class="g">
                <div class="yuRUbf"><a href="https://example.com"><h3>Title</h3></a></div>
            </div>
        </div></body></html>
        """
        parser = GoogleParser()
        results = parser.parse(html)
        assert len(results.results) == 1
        assert results.results[0].description is None

    def test_find_results_without_search_div(self) -> None:
        html = """
        <html><head><meta property="og:site_name" content="Google"></head>
        <body>
            <div class="g">
                <div class="yuRUbf"><a href="https://example.com"><h3>Result</h3></a></div>
                <div class="VwiC3b">Desc</div>
            </div>
        </body></html>
        """
        parser = GoogleParser()
        results = parser.parse(html)
        assert len(results.results) == 1


# --- Bing parser edge cases ---


class TestBingEdgeCases:
    def test_parse_result_no_h2(self) -> None:
        html = """
        <html><head><meta name="ms.application" content="Bing"></head>
        <body><li class="b_algo"><p>No heading</p></li></body></html>
        """
        parser = BingParser()
        results = parser.parse(html)
        assert len(results.results) == 0

    def test_parse_result_no_link(self) -> None:
        html = """
        <html><head><meta name="ms.application" content="Bing"></head>
        <body><li class="b_algo"><h2>No Link</h2></li></body></html>
        """
        parser = BingParser()
        results = parser.parse(html)
        assert len(results.results) == 0

    def test_parse_result_empty_title(self) -> None:
        html = """
        <html><head><meta name="ms.application" content="Bing"></head>
        <body><li class="b_algo"><h2><a href="https://example.com"></a></h2></li></body></html>
        """
        parser = BingParser()
        results = parser.parse(html)
        assert len(results.results) == 0

    def test_parse_result_no_caption(self) -> None:
        html = """
        <html><head><meta name="ms.application" content="Bing"></head>
        <body><li class="b_algo"><h2><a href="https://example.com">Title</a></h2></li></body></html>
        """
        parser = BingParser()
        results = parser.parse(html)
        assert len(results.results) == 1
        assert results.results[0].description is None

    def test_featured_snippet(self) -> None:
        html = """
        <html><head><meta name="ms.application" content="Bing"></head>
        <body>
            <div class="b_ans">
                <h2><a href="https://example.com">Featured Title</a></h2>
                <div class="b_rich">Featured description text</div>
            </div>
        </body></html>
        """
        parser = BingParser()
        results = parser.parse(html)
        assert results.featured_snippet is not None
        assert results.featured_snippet.title == "Featured Title"
        assert results.featured_snippet.result_type == "featured_snippet"

    def test_featured_snippet_not_in_organic(self) -> None:
        html = """
        <html><head><meta name="ms.application" content="Bing"></head>
        <body>
            <div class="b_ans">
                <h2><a href="https://example.com">Featured Title</a></h2>
                <div class="b_rich">Featured description text</div>
            </div>
        </body></html>
        """
        parser = BingParser()
        results = parser.parse(html)
        for r in results.results:
            assert r.result_type != "featured_snippet"

    def test_featured_snippet_no_h2(self) -> None:
        html = """
        <html><head><meta name="ms.application" content="Bing"></head>
        <body>
            <div class="b_ans">
                <p>No heading</p>
            </div>
        </body></html>
        """
        parser = BingParser()
        results = parser.parse(html)
        assert results.featured_snippet is None

    def test_featured_snippet_fallback_to_p(self) -> None:
        html = """
        <html><head><meta name="ms.application" content="Bing"></head>
        <body>
            <div class="b_ans">
                <h2><a href="https://example.com">Featured</a></h2>
                <p>Paragraph description</p>
            </div>
        </body></html>
        """
        parser = BingParser()
        results = parser.parse(html)
        assert results.featured_snippet is not None


# --- DuckDuckGo edge cases ---


class TestDDGEdgeCases:
    def test_article_no_h2(self) -> None:
        html = """
        <html><head><link rel="canonical" href="https://duckduckgo.com"></head>
        <body><article data-testid="result"><p>No heading</p></article></body></html>
        """
        parser = DuckDuckGoParser()
        results = parser.parse(html)
        assert len(results.results) == 0

    def test_article_no_link(self) -> None:
        html = """
        <html><head><link rel="canonical" href="https://duckduckgo.com"></head>
        <body><article data-testid="result"><h2>No Link</h2></article></body></html>
        """
        parser = DuckDuckGoParser()
        results = parser.parse(html)
        assert len(results.results) == 0

    def test_article_empty_title(self) -> None:
        html = """
        <html><head><link rel="canonical" href="https://duckduckgo.com"></head>
        <body><article data-testid="result"><h2><a href="https://example.com"></a></h2></article></body></html>
        """
        parser = DuckDuckGoParser()
        results = parser.parse(html)
        assert len(results.results) == 0

    def test_article_no_description(self) -> None:
        html = """
        <html><head><link rel="canonical" href="https://duckduckgo.com"></head>
        <body><article data-testid="result"><h2><a href="https://example.com">Title</a></h2></article></body></html>
        """
        parser = DuckDuckGoParser()
        results = parser.parse(html)
        assert len(results.results) == 1
        assert results.results[0].description is None

    def test_div_result_no_link(self) -> None:
        html = """
        <html><head><link rel="canonical" href="https://duckduckgo.com"></head>
        <body><div class="result"><p>No link here</p></div></body></html>
        """
        parser = DuckDuckGoParser()
        results = parser.parse(html)
        assert len(results.results) == 0

    def test_div_result_empty_title(self) -> None:
        html = """
        <html><head><link rel="canonical" href="https://duckduckgo.com"></head>
        <body><div class="result"><a class="result__a" href="https://example.com"></a></div></body></html>
        """
        parser = DuckDuckGoParser()
        results = parser.parse(html)
        assert len(results.results) == 0

    def test_div_result_fallback_snippet(self) -> None:
        html = """
        <html><head><link rel="canonical" href="https://duckduckgo.com"></head>
        <body><div class="result">
            <a class="result__a" href="https://example.com">Title</a>
            <div class="result__snippet">Some description</div>
        </div></body></html>
        """
        parser = DuckDuckGoParser()
        results = parser.parse(html)
        assert len(results.results) == 1
        assert results.results[0].description == "Some description"

    def test_div_result_fallback_link(self) -> None:
        """When result__a class is not found, falls back to first <a>."""
        html = """
        <html><head><link rel="canonical" href="https://duckduckgo.com"></head>
        <body><div class="result">
            <a href="https://example.com">Fallback Title</a>
        </div></body></html>
        """
        parser = DuckDuckGoParser()
        results = parser.parse(html)
        assert len(results.results) == 1
        assert results.results[0].title == "Fallback Title"


# --- Markdown formatter edge cases ---


class TestMarkdownFormatterEdgeCases:
    def setup_method(self) -> None:
        self.formatter = MarkdownFormatter()

    def test_format_knowledge_panel(self) -> None:
        results = SearchResults(
            search_engine="google",
            query="python",
            results=[
                SearchResult(
                    title="Python (programming language)",
                    url="https://en.wikipedia.org/wiki/Python",
                    description="A high-level programming language.",
                    position=1,
                    result_type="knowledge_panel",
                ),
            ],
            detection_confidence=0.9,
        )
        output = self.formatter.format(results)
        assert "## Knowledge Panel" in output
        assert "Python (programming language)" in output

    def test_format_news_results(self) -> None:
        results = SearchResults(
            search_engine="google",
            query="latest news",
            results=[],
            news=[
                SearchResult(
                    title="Breaking News",
                    url="https://news.example.com",
                    description="Something happened today.",
                    position=1,
                    result_type="news",
                ),
            ],
            detection_confidence=0.9,
        )
        output = self.formatter.format(results)
        assert "## News Results" in output
        assert "Breaking News" in output

    def test_format_no_total_results(self) -> None:
        results = SearchResults(
            search_engine="google",
            results=[],
            detection_confidence=0.9,
        )
        output = self.formatter.format(results)
        assert "Total Results" not in output

    def test_format_featured_no_description(self) -> None:
        results = SearchResults(
            search_engine="google",
            featured_snippet=SearchResult(
                title="Featured Title",
                url="https://example.com",
                position=0,
                result_type="featured_snippet",
            ),
            results=[],
            detection_confidence=0.9,
        )
        output = self.formatter.format(results)
        assert "Featured Title" in output

    def test_format_organic_no_description(self) -> None:
        results = SearchResults(
            search_engine="google",
            results=[
                SearchResult(
                    title="No Desc",
                    url="https://example.com",
                    position=1,
                    result_type="organic",
                ),
            ],
            detection_confidence=0.9,
        )
        output = self.formatter.format(results)
        assert "### 1. No Desc" in output


# --- SearchParser edge cases ---


class TestSearchParserEdgeCases:
    def test_invalid_output_format(self) -> None:
        parser = SearchParser()
        html = '<html><head><meta property="og:site_name" content="Google"></head><body><div id="search"></div></body></html>'
        with pytest.raises(ValueError, match="Unknown output format"):
            parser.parse(html, output_format="xml")  # type: ignore[arg-type]

    def test_parse_error_wrapping(self) -> None:
        """Ensure parser errors are wrapped in ParseError."""
        parser = SearchParser()
        # A google HTML that will be detected but the parser monkeypatched to fail
        html = '<html><head><meta property="og:site_name" content="Google"></head><body><div id="search"></div></body></html>'
        original_parse = parser._parsers["google"].parse

        def bad_parse(html: str) -> SearchResults:
            raise RuntimeError("Deliberate error")

        parser._parsers["google"].parse = bad_parse  # type: ignore[assignment]
        try:
            with pytest.raises(ParseError, match="Deliberate error"):
                parser.parse(html)
        finally:
            parser._parsers["google"].parse = original_parse  # type: ignore[assignment]
