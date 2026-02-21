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

    def test_parse_github_repos_results(self, google_github_repos_html: str) -> None:
        results = self.parser.parse(google_github_repos_html)
        assert results.search_engine == "google"
        assert results.query == "github repos"
        assert results.detection_confidence >= 0.8
        organic = [r for r in results.results if r.result_type == "organic"]
        assert len(organic) == 5

        first = organic[0]
        assert first.title == "Trending repositories on GitHub today"
        assert first.url == "https://github.com/trending"
        assert first.position == 1
        assert first.result_type == "organic"
        assert first.description is not None

    def test_parse_github_repos_positions(self, google_github_repos_html: str) -> None:
        results = self.parser.parse(google_github_repos_html)
        organic = [r for r in results.results if r.result_type == "organic"]
        positions = [r.position for r in organic]
        assert positions == [1, 2, 3, 4, 5]

    def test_parse_github_repos_all_have_descriptions(self, google_github_repos_html: str) -> None:
        results = self.parser.parse(google_github_repos_html)
        organic = [r for r in results.results if r.result_type == "organic"]
        for r in organic:
            assert r.description is not None
            assert len(r.description) > 0

    def test_parse_sponsored_results(self, google_scheduling_app_html: str) -> None:
        results = self.parser.parse(google_scheduling_app_html)
        sponsored = [r for r in results.results if r.result_type == "sponsored"]
        assert len(sponsored) == 6
        assert sponsored[0].title == "Employee Scheduling Software"
        assert sponsored[0].url.startswith("https://www.inovalon.com/")
        assert sponsored[0].position == 0

    def test_parse_sponsored_all_have_descriptions(self, google_scheduling_app_html: str) -> None:
        results = self.parser.parse(google_scheduling_app_html)
        sponsored = [r for r in results.results if r.result_type == "sponsored"]
        for r in sponsored:
            assert r.description is not None
            assert len(r.description) > 0

    def test_parse_sponsored_with_organic(self, google_scheduling_app_html: str) -> None:
        results = self.parser.parse(google_scheduling_app_html)
        sponsored = [r for r in results.results if r.result_type == "sponsored"]
        organic = [r for r in results.results if r.result_type == "organic"]
        assert len(sponsored) == 6
        assert len(organic) == 8
        assert results.query == "best employee scheduling app"

    def test_parse_need_javascript_returns_no_results(
        self, google_need_javascript_html: str
    ) -> None:
        results = self.parser.parse(google_need_javascript_html)
        assert results.search_engine == "google"
        assert len(results.results) == 0

    def test_parse_need_javascript_has_no_query(
        self, google_need_javascript_html: str
    ) -> None:
        results = self.parser.parse(google_need_javascript_html)
        assert results.query is None

    def test_parse_need_javascript_low_confidence(
        self, google_need_javascript_html: str
    ) -> None:
        soup = make_soup(google_need_javascript_html)
        confidence = self.parser.can_parse(soup)
        assert confidence == 0.0

    def test_parse_ai_overview(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        ai = [r for r in results.results if r.result_type == "ai_overview"]
        assert len(ai) == 1
        assert ai[0].title == "AI Overview"
        assert ai[0].description is not None
        assert len(ai[0].description) > 0
        assert "Python" in ai[0].description

    def test_parse_ai_overview_has_sources(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        ai = [r for r in results.results if r.result_type == "ai_overview"]
        assert len(ai) == 1
        sources = ai[0].metadata.get("sources")
        assert isinstance(sources, list)
        assert len(sources) > 0
        first_source = sources[0]
        assert isinstance(first_source, dict)
        assert "url" in first_source
        assert "title" in first_source
        assert first_source["url"].startswith("http")

    def test_parse_people_also_ask(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        paa = [r for r in results.results if r.result_type == "people_also_ask"]
        assert len(paa) == 4
        questions = [r.title for r in paa]
        assert "Is Python good for web scraping?" in questions
        assert "Is data scraping illegal?" in questions

    def test_parse_people_also_ask_positions(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        paa = [r for r in results.results if r.result_type == "people_also_ask"]
        for item in paa:
            assert item.position == 0
            assert item.url == ""

    def test_parse_people_saying(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        saying = [r for r in results.results if r.result_type == "people_saying"]
        assert len(saying) >= 1
        assert saying[0].url.startswith("https://x.com/")
        assert saying[0].title != ""

    def test_parse_people_also_search_for(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        pasf = [r for r in results.results if r.result_type == "people_also_search"]
        assert len(pasf) == 6
        titles = [r.title for r in pasf]
        assert "Beautiful Soup" in titles
        assert "Scrapy" in titles
        assert "pandas" in titles

    def test_parse_people_also_search_have_urls(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        pasf = [r for r in results.results if r.result_type == "people_also_search"]
        for item in pasf:
            assert item.url != ""

    def test_parse_related_products(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        products = [r for r in results.results if r.result_type == "related_products"]
        assert len(products) == 2
        titles = [r.title for r in products]
        assert "Web scraping tools AI" in titles
        assert "Web scraping code GitHub" in titles

    def test_parse_web_scraping_has_all_section_types(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        types = {r.result_type for r in results.results}
        assert "ai_overview" in types
        assert "people_also_ask" in types
        assert "people_saying" in types
        assert "people_also_search" in types
        assert "related_products" in types
