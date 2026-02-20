"""End-to-end integration tests for SearchParser."""

from __future__ import annotations

import json

import pytest

from search_engine_parser import SearchParser
from search_engine_parser.exceptions import (
    ParserNotFoundError,
    SearchEngineDetectionError,
)


class TestSearchParserEndToEnd:
    def setup_method(self) -> None:
        self.parser = SearchParser()

    # --- Google ---

    def test_google_json_output(self, google_organic_html: str) -> None:
        result = self.parser.parse(google_organic_html, output_format="json")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["search_engine"] == "google"
        assert len(parsed["results"]) == 3
        assert parsed["query"] == "python web scraping"

    def test_google_markdown_output(self, google_organic_html: str) -> None:
        result = self.parser.parse(google_organic_html, output_format="markdown")
        assert isinstance(result, str)
        assert "# Search Results" in result
        assert "Google" in result
        assert "Web Scraping with Python" in result

    def test_google_dict_output(self, google_organic_html: str) -> None:
        result = self.parser.parse(google_organic_html, output_format="dict")
        assert isinstance(result, dict)
        assert result["search_engine"] == "google"
        assert len(result["results"]) == 3

    # --- Bing ---

    def test_bing_json_output(self, bing_organic_html: str) -> None:
        result = self.parser.parse(bing_organic_html, output_format="json")
        parsed = json.loads(result)
        assert parsed["search_engine"] == "bing"
        assert len(parsed["results"]) == 3

    def test_bing_markdown_output(self, bing_organic_html: str) -> None:
        result = self.parser.parse(bing_organic_html, output_format="markdown")
        assert isinstance(result, str)
        assert "Bing" in result

    def test_bing_dict_output(self, bing_organic_html: str) -> None:
        result = self.parser.parse(bing_organic_html, output_format="dict")
        assert isinstance(result, dict)
        assert result["search_engine"] == "bing"

    # --- DuckDuckGo ---

    def test_duckduckgo_json_output(self, duckduckgo_organic_html: str) -> None:
        result = self.parser.parse(duckduckgo_organic_html, output_format="json")
        parsed = json.loads(result)
        assert parsed["search_engine"] == "duckduckgo"
        assert len(parsed["results"]) == 3

    def test_duckduckgo_markdown_output(self, duckduckgo_organic_html: str) -> None:
        result = self.parser.parse(duckduckgo_organic_html, output_format="markdown")
        assert isinstance(result, str)
        assert "Duckduckgo" in result

    def test_duckduckgo_dict_output(self, duckduckgo_organic_html: str) -> None:
        result = self.parser.parse(duckduckgo_organic_html, output_format="dict")
        assert isinstance(result, dict)
        assert result["search_engine"] == "duckduckgo"

    # --- Manual engine specification ---

    def test_manual_engine_google(self, google_organic_html: str) -> None:
        result = self.parser.parse(google_organic_html, engine="google", output_format="dict")
        assert isinstance(result, dict)
        assert result["search_engine"] == "google"

    def test_manual_engine_bing(self, bing_organic_html: str) -> None:
        result = self.parser.parse(bing_organic_html, engine="bing", output_format="dict")
        assert isinstance(result, dict)
        assert result["search_engine"] == "bing"

    # --- Error handling ---

    def test_detection_error_for_unknown_html(self) -> None:
        with pytest.raises(SearchEngineDetectionError):
            self.parser.parse("<html><body><p>Not a search page</p></body></html>")

    def test_parser_not_found_error(self) -> None:
        with pytest.raises(ParserNotFoundError):
            self.parser.parse("<html></html>", engine="yahoo")

    # --- Featured snippets end-to-end ---

    def test_google_featured_snippet_json(self, google_featured_html: str) -> None:
        result = self.parser.parse(google_featured_html, output_format="json")
        parsed = json.loads(result)
        featured = [r for r in parsed["results"] if r["result_type"] == "featured_snippet"]
        assert len(featured) == 1
        assert featured[0]["position"] == 0

    def test_all_three_formats_same_content(self, google_organic_html: str) -> None:
        """Ensure all three formats produce consistent data."""
        json_result = self.parser.parse(google_organic_html, output_format="json")
        dict_result = self.parser.parse(google_organic_html, output_format="dict")
        md_result = self.parser.parse(google_organic_html, output_format="markdown")

        # JSON and dict should have the same data
        json_parsed = json.loads(json_result)
        assert json_parsed["search_engine"] == dict_result["search_engine"]
        assert len(json_parsed["results"]) == len(dict_result["results"])

        # Markdown should mention all result titles
        assert isinstance(md_result, str)
        for r in dict_result["results"]:
            assert r["title"] in md_result
