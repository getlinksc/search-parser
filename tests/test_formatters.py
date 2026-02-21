"""Tests for output formatters."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from search_parser.core.models import SearchResult, SearchResults
from search_parser.formatters.json_formatter import JSONFormatter
from search_parser.formatters.markdown_formatter import MarkdownFormatter


def _make_results() -> SearchResults:
    """Create sample SearchResults for testing."""
    return SearchResults(
        search_engine="google",
        query="python web scraping",
        total_results=1250000,
        featured_snippet=SearchResult(
            title="What is Web Scraping?",
            url="https://example.com/what-is-web-scraping",
            description="Web scraping is the process of extracting data from websites.",
            position=0,
            result_type="featured_snippet",
            metadata={"snippet_type": "paragraph"},
        ),
        results=[
            SearchResult(
                title="Web Scraping with Python - Real Python",
                url="https://realpython.com/python-web-scraping/",
                description="Learn how to scrape websites with Python.",
                position=1,
                result_type="organic",
            ),
            SearchResult(
                title="Beautiful Soup Tutorial",
                url="https://example.com/bs4",
                description="A comprehensive guide to BS4.",
                position=2,
                result_type="organic",
            ),
        ],
        detection_confidence=0.95,
        parsed_at=datetime(2026, 2, 20, 15, 30, 0, tzinfo=timezone.utc),
    )


class TestJSONFormatter:
    def setup_method(self) -> None:
        self.formatter = JSONFormatter()

    def test_format_returns_valid_json(self) -> None:
        results = _make_results()
        output = self.formatter.format(results)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_format_contains_all_fields(self) -> None:
        results = _make_results()
        output = self.formatter.format(results)
        parsed = json.loads(output)
        assert parsed["search_engine"] == "google"
        assert parsed["query"] == "python web scraping"
        assert parsed["total_results"] == 1250000
        assert len(parsed["results"]) == 2
        assert parsed["detection_confidence"] == 0.95

    def test_format_featured_snippet_field(self) -> None:
        results = _make_results()
        output = self.formatter.format(results)
        parsed = json.loads(output)
        snippet = parsed["featured_snippet"]
        assert snippet["title"] == "What is Web Scraping?"
        assert snippet["url"] == "https://example.com/what-is-web-scraping"
        assert snippet["position"] == 0
        assert snippet["result_type"] == "featured_snippet"

    def test_format_empty_results(self) -> None:
        results = SearchResults(
            search_engine="google",
            results=[],
            detection_confidence=0.9,
        )
        output = self.formatter.format(results)
        parsed = json.loads(output)
        assert parsed["results"] == []


class TestMarkdownFormatter:
    def setup_method(self) -> None:
        self.formatter = MarkdownFormatter()

    def test_format_returns_string(self) -> None:
        results = _make_results()
        output = self.formatter.format(results)
        assert isinstance(output, str)

    def test_format_contains_header(self) -> None:
        results = _make_results()
        output = self.formatter.format(results)
        assert "# Search Results: python web scraping" in output

    def test_format_contains_engine_name(self) -> None:
        results = _make_results()
        output = self.formatter.format(results)
        assert "**Search Engine:** Google" in output

    def test_format_contains_total_results(self) -> None:
        results = _make_results()
        output = self.formatter.format(results)
        assert "**Total Results:** ~1,250,000" in output

    def test_format_contains_featured_snippet(self) -> None:
        results = _make_results()
        output = self.formatter.format(results)
        assert "## Featured Snippet" in output
        assert "What is Web Scraping?" in output

    def test_format_contains_organic_results(self) -> None:
        results = _make_results()
        output = self.formatter.format(results)
        assert "## Organic Results" in output
        assert "### 1. Web Scraping with Python - Real Python" in output
        assert "### 2. Beautiful Soup Tutorial" in output

    def test_format_contains_urls(self) -> None:
        results = _make_results()
        output = self.formatter.format(results)
        assert "https://realpython.com/python-web-scraping/" in output

    def test_format_contains_version(self) -> None:
        results = _make_results()
        output = self.formatter.format(results)
        assert "search-engine-parser v" in output

    def test_format_empty_results(self) -> None:
        results = SearchResults(
            search_engine="google",
            results=[],
            detection_confidence=0.9,
        )
        output = self.formatter.format(results)
        assert "# Search Results" in output

    def test_format_without_query(self) -> None:
        results = SearchResults(
            search_engine="google",
            results=[],
            detection_confidence=0.9,
        )
        output = self.formatter.format(results)
        assert "# Search Results\n" in output
        # Should not have a query appended
        assert "# Search Results:" not in output


class TestSearchResultsMethods:
    """Tests for SearchResults.to_json() and to_markdown() convenience methods."""

    def test_to_json_returns_string(self) -> None:
        assert isinstance(_make_results().to_json(), str)

    def test_to_json_is_valid_json(self) -> None:
        parsed = json.loads(_make_results().to_json())
        assert isinstance(parsed, dict)

    def test_to_json_matches_json_formatter(self) -> None:
        results = _make_results()
        assert results.to_json() == JSONFormatter().format(results)

    def test_to_json_contains_expected_fields(self) -> None:
        parsed = json.loads(_make_results().to_json())
        assert parsed["search_engine"] == "google"
        assert parsed["query"] == "python web scraping"
        assert parsed["total_results"] == 1250000
        assert len(parsed["results"]) == 2
        assert parsed["featured_snippet"]["title"] == "What is Web Scraping?"

    def test_to_json_indent_default(self) -> None:
        output = _make_results().to_json()
        # Default indent=2 means lines are indented
        assert "\n  " in output

    def test_to_json_indent_zero(self) -> None:
        output = _make_results().to_json(indent=0)
        assert isinstance(json.loads(output), dict)
        # indent=0 produces newlines but no leading spaces on values
        assert "\n  " not in output

    def test_to_json_empty_results(self) -> None:
        results = SearchResults(search_engine="bing", results=[], detection_confidence=0.9)
        parsed = json.loads(results.to_json())
        assert parsed["results"] == []
        assert parsed["featured_snippet"] is None

    def test_to_markdown_returns_string(self) -> None:
        assert isinstance(_make_results().to_markdown(), str)

    def test_to_markdown_matches_markdown_formatter(self) -> None:
        results = _make_results()
        assert results.to_markdown() == MarkdownFormatter().format(results)

    def test_to_markdown_contains_header(self) -> None:
        assert "# Search Results: python web scraping" in _make_results().to_markdown()

    def test_to_markdown_contains_featured_snippet(self) -> None:
        output = _make_results().to_markdown()
        assert "## Featured Snippet" in output
        assert "What is Web Scraping?" in output

    def test_to_markdown_contains_organic_results(self) -> None:
        output = _make_results().to_markdown()
        assert "## Organic Results" in output
        assert "Web Scraping with Python" in output

    def test_to_markdown_empty_results(self) -> None:
        results = SearchResults(search_engine="google", results=[], detection_confidence=0.9)
        output = results.to_markdown()
        assert "# Search Results" in output
