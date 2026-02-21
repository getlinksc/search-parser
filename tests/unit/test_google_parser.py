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

    # --- organic results ---

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

    def test_organic_results_only_contain_organic(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        for r in results.results:
            assert r.result_type == "organic"

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
        assert len(results.results) == 0

    def test_detection_confidence(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.detection_confidence >= 0.8

    def test_parse_github_repos_results(self, google_github_repos_html: str) -> None:
        results = self.parser.parse(google_github_repos_html)
        assert results.search_engine == "google"
        assert results.query == "github repos"
        assert results.detection_confidence >= 0.8
        assert len(results.results) == 5

        first = results.results[0]
        assert first.title == "Trending repositories on GitHub today"
        assert first.url == "https://github.com/trending"
        assert first.position == 1
        assert first.result_type == "organic"
        assert first.description is not None

    def test_parse_github_repos_positions(self, google_github_repos_html: str) -> None:
        results = self.parser.parse(google_github_repos_html)
        positions = [r.position for r in results.results]
        assert positions == [1, 2, 3, 4, 5]

    def test_parse_github_repos_all_have_descriptions(self, google_github_repos_html: str) -> None:
        results = self.parser.parse(google_github_repos_html)
        for r in results.results:
            assert r.description is not None
            assert len(r.description) > 0

    # --- featured snippet ---

    def test_parse_featured_snippet(self, google_featured_html: str) -> None:
        results = self.parser.parse(google_featured_html)
        assert results.featured_snippet is not None
        assert results.featured_snippet.position == 0
        assert results.featured_snippet.title == "What is Web Scraping?"
        assert results.featured_snippet.description is not None
        assert results.featured_snippet.result_type == "featured_snippet"

    def test_parse_featured_not_in_organic(self, google_featured_html: str) -> None:
        results = self.parser.parse(google_featured_html)
        assert len(results.results) == 2
        for r in results.results:
            assert r.result_type == "organic"

    def test_parse_no_featured_snippet_returns_none(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.featured_snippet is None

    # --- sponsored ---

    def test_parse_sponsored_results(self, google_scheduling_app_html: str) -> None:
        results = self.parser.parse(google_scheduling_app_html)
        assert len(results.sponsored) == 6
        assert results.sponsored[0].title == "Employee Scheduling Software"
        assert results.sponsored[0].url.startswith("https://www.inovalon.com/")
        assert results.sponsored[0].position == 0
        assert results.sponsored[0].result_type == "sponsored"

    def test_parse_sponsored_all_have_descriptions(self, google_scheduling_app_html: str) -> None:
        for r in self.parser.parse(google_scheduling_app_html).sponsored:
            assert r.description is not None
            assert len(r.description) > 0

    def test_parse_sponsored_not_in_organic(self, google_scheduling_app_html: str) -> None:
        results = self.parser.parse(google_scheduling_app_html)
        assert len(results.sponsored) == 6
        assert len(results.results) == 8
        assert results.query == "best employee scheduling app"
        for r in results.results:
            assert r.result_type == "organic"

    def test_parse_no_sponsored_returns_empty(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.sponsored == []

    # --- javascript required page ---

    def test_parse_need_javascript_returns_no_results(
        self, google_need_javascript_html: str
    ) -> None:
        results = self.parser.parse(google_need_javascript_html)
        assert results.search_engine == "google"
        assert len(results.results) == 0

    def test_parse_need_javascript_has_no_query(self, google_need_javascript_html: str) -> None:
        results = self.parser.parse(google_need_javascript_html)
        assert results.query is None

    def test_parse_need_javascript_low_confidence(self, google_need_javascript_html: str) -> None:
        soup = make_soup(google_need_javascript_html)
        confidence = self.parser.can_parse(soup)
        assert confidence == 0.0

    # --- total results ---

    def test_parse_total_results(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        assert results.total_results == 26_200_000

    def test_parse_total_results_none_when_absent(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.total_results is None

    # --- ai_overview ---

    def test_parse_ai_overview(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        assert results.ai_overview is not None
        assert results.ai_overview.title == "AI Overview"
        assert results.ai_overview.description is not None
        assert "Python" in results.ai_overview.description
        assert results.ai_overview.result_type == "ai_overview"

    def test_parse_ai_overview_has_sources(self, google_web_scraping_html: str) -> None:
        ai = self.parser.parse(google_web_scraping_html).ai_overview
        assert ai is not None
        sources = ai.metadata.get("sources")
        assert isinstance(sources, list)
        assert len(sources) > 0
        first = sources[0]
        assert isinstance(first, dict)
        assert first["url"].startswith("http")
        assert first["title"]

    def test_parse_ai_overview_not_in_organic(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        for r in results.results:
            assert r.result_type != "ai_overview"

    def test_parse_no_ai_overview_returns_none(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.ai_overview is None

    # --- people_also_ask ---

    def test_parse_people_also_ask(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        assert len(results.people_also_ask) == 4
        questions = [r.title for r in results.people_also_ask]
        assert "Is Python good for web scraping?" in questions
        assert "Is data scraping illegal?" in questions

    def test_parse_people_also_ask_not_in_organic(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        for r in results.results:
            assert r.result_type != "people_also_ask"

    def test_parse_people_also_ask_have_no_url(self, google_web_scraping_html: str) -> None:
        for r in self.parser.parse(google_web_scraping_html).people_also_ask:
            assert r.url == ""
            assert r.result_type == "people_also_ask"

    def test_parse_no_people_also_ask_returns_empty(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.people_also_ask == []

    # --- people_saying ---

    def test_parse_people_saying(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        assert len(results.people_saying) >= 1
        assert results.people_saying[0].url.startswith("https://x.com/")
        assert results.people_saying[0].title != ""
        assert results.people_saying[0].result_type == "people_saying"

    def test_parse_people_saying_not_in_organic(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        for r in results.results:
            assert r.result_type != "people_saying"

    def test_parse_no_people_saying_returns_empty(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.people_saying == []

    # --- people_also_search ---

    def test_parse_people_also_search(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        assert len(results.people_also_search) == 6
        titles = [r.title for r in results.people_also_search]
        assert "Beautiful Soup" in titles
        assert "Scrapy" in titles
        assert "pandas" in titles

    def test_parse_people_also_search_have_urls(self, google_web_scraping_html: str) -> None:
        for r in self.parser.parse(google_web_scraping_html).people_also_search:
            assert r.url != ""
            assert r.result_type == "people_also_search"

    def test_parse_people_also_search_not_in_organic(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        for r in results.results:
            assert r.result_type != "people_also_search"

    def test_parse_no_people_also_search_returns_empty(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.people_also_search == []

    # --- related_products ---

    def test_parse_related_products(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        assert len(results.related_products) == 2
        titles = [r.title for r in results.related_products]
        assert "Web scraping tools AI" in titles
        assert "Web scraping code GitHub" in titles

    def test_parse_related_products_have_urls(self, google_web_scraping_html: str) -> None:
        for r in self.parser.parse(google_web_scraping_html).related_products:
            assert r.url != ""
            assert r.result_type == "related_products"

    def test_parse_related_products_not_in_organic(self, google_web_scraping_html: str) -> None:
        results = self.parser.parse(google_web_scraping_html)
        for r in results.results:
            assert r.result_type != "related_products"

    def test_parse_no_related_products_returns_empty(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.related_products == []

    # --- isolation check: non-organic types never leak into results ---

    def test_all_dedicated_fields_absent_from_organic(self, google_web_scraping_html: str) -> None:
        non_organic = {
            "featured_snippet",
            "sponsored",
            "ai_overview",
            "people_also_ask",
            "people_saying",
            "people_also_search",
            "related_products",
        }
        results = self.parser.parse(google_web_scraping_html)
        for r in results.results:
            assert r.result_type not in non_organic
