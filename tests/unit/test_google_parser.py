"""Tests for Google search results parser."""

from __future__ import annotations

from search_parser.parsers.google import GoogleParser
from search_parser.utils import make_soup


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

    # --- jobs ---

    def test_parse_jobs(self, google_supply_chain_jobs_html: str) -> None:
        results = self.parser.parse(google_supply_chain_jobs_html)
        assert len(results.jobs) == 3
        titles = [r.title for r in results.jobs]
        assert "Global Supply Chain Director" in titles
        assert "Sr. Manager, Supply Chain" in titles

    def test_parse_jobs_have_company_and_location(self, google_supply_chain_jobs_html: str) -> None:
        for job in self.parser.parse(google_supply_chain_jobs_html).jobs:
            assert job.result_type == "job"
            assert job.position == 0
            assert "company" in job.metadata
            assert "location" in job.metadata
            assert job.metadata["company"]
            assert job.metadata["location"]

    def test_parse_jobs_not_in_organic(self, google_supply_chain_jobs_html: str) -> None:
        results = self.parser.parse(google_supply_chain_jobs_html)
        assert len(results.jobs) == 3
        for r in results.results:
            assert r.result_type != "job"

    def test_parse_no_jobs_returns_empty(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.jobs == []

    def test_parse_jobs_metadata(self, google_supply_chain_jobs_html: str) -> None:
        jobs = self.parser.parse(google_supply_chain_jobs_html).jobs
        companies = [str(j.metadata["company"]) for j in jobs]
        assert "InterSources, Inc." in companies
        assert "Legrand North America" in companies
        assert "Thermo Fisher Scientific" in companies

    def test_parse_jobs_salary_when_present(self, google_supply_chain_jobs_html: str) -> None:
        jobs = self.parser.parse(google_supply_chain_jobs_html).jobs
        # First job (InterSources) has a salary range; others do not
        intersources = next(j for j in jobs if j.metadata.get("company") == "InterSources, Inc.")
        assert intersources.metadata.get("salary") == "150K–200K a year"

    def test_parse_jobs_employment_type(self, google_supply_chain_jobs_html: str) -> None:
        for job in self.parser.parse(google_supply_chain_jobs_html).jobs:
            assert job.metadata.get("employment_type") == "Full-time"

    # --- discussions ---

    def test_parse_discussions(self, google_supply_chain_jobs_html: str) -> None:
        results = self.parser.parse(google_supply_chain_jobs_html)
        assert len(results.discussions) == 3
        titles = [r.title for r in results.discussions]
        assert "Being considered for Director of Supply Chain" in titles
        assert "Director level" in titles

    def test_parse_discussions_have_urls(self, google_supply_chain_jobs_html: str) -> None:
        for disc in self.parser.parse(google_supply_chain_jobs_html).discussions:
            assert disc.result_type == "discussion"
            assert disc.url.startswith("https://")

    def test_parse_discussions_have_descriptions(self, google_supply_chain_jobs_html: str) -> None:
        for disc in self.parser.parse(google_supply_chain_jobs_html).discussions:
            assert disc.description is not None
            assert len(disc.description) > 0

    def test_parse_discussions_have_source_metadata(self, google_supply_chain_jobs_html: str) -> None:
        for disc in self.parser.parse(google_supply_chain_jobs_html).discussions:
            assert "source" in disc.metadata
            assert disc.metadata["source"]

    def test_parse_discussions_not_in_organic(self, google_supply_chain_jobs_html: str) -> None:
        results = self.parser.parse(google_supply_chain_jobs_html)
        assert len(results.discussions) == 3
        for r in results.results:
            assert r.result_type != "discussion"

    def test_parse_no_discussions_returns_empty(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.discussions == []

    # --- mobile organic results ---

    def test_parse_mobile_organic_results(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        assert results.search_engine == "google"
        assert results.query == "contact lens weekly"
        assert len(results.results) == 10

    def test_parse_mobile_organic_result_positions(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        assert [r.position for r in results.results] == list(range(1, 11))

    def test_parse_mobile_organic_urls_are_decoded(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        for r in results.results:
            assert r.url.startswith("https://")
            assert "/url?q=" not in r.url

    def test_parse_mobile_organic_have_titles(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        titles = [r.title for r in results.results]
        assert "Weekly and Bi-Weekly Contact Lenses | Target Optical" in titles
        assert "Weekly Contact Lenses - LensDirect" in titles

    def test_parse_mobile_organic_not_in_other_fields(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        for r in results.results:
            assert r.result_type == "organic"

    def test_parse_mobile_detection_confidence(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        assert results.detection_confidence >= 0.8

    # --- mobile people_also_ask ---

    def test_parse_mobile_people_also_ask(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        assert len(results.people_also_ask) == 3
        questions = [r.title for r in results.people_also_ask]
        assert "Is there a weekly contact lens?" in questions
        assert "Can I wear contact lenses 7 days a week?" in questions

    def test_parse_mobile_people_also_ask_not_in_organic(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        for r in results.results:
            assert r.result_type != "people_also_ask"

    # --- mobile people_also_search ---

    def test_parse_mobile_people_also_search(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        assert len(results.people_also_search) == 6
        titles = [r.title for r in results.people_also_search]
        assert "Contact lens weekly walmart" in titles

    def test_parse_mobile_people_also_search_not_in_organic(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        for r in results.results:
            assert r.result_type != "people_also_search"

    # --- mobile ai_overview ---

    def test_parse_mobile_ai_overview(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        assert results.ai_overview is not None
        assert results.ai_overview.title == "AI Overview"
        assert results.ai_overview.description is not None
        assert "weekly" in results.ai_overview.description.lower()
        assert results.ai_overview.result_type == "ai_overview"

    def test_parse_mobile_ai_overview_not_in_organic(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        for r in results.results:
            assert r.result_type != "ai_overview"

    # --- shopping ads ---

    def test_parse_shopping_ads(self, google_weekly_contacts_mobile_html: str) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        assert len(results.shopping_ads) == 4

    def test_parse_shopping_ads_have_titles(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        ads = self.parser.parse(google_weekly_contacts_mobile_html).shopping_ads
        titles = [r.title for r in ads]
        assert "ALCON - Precision7 , 12 Pack" in titles
        assert "Acuvue Oasys 12 Pack Contact Lenses" in titles

    def test_parse_shopping_ads_have_price_and_merchant(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        for ad in self.parser.parse(google_weekly_contacts_mobile_html).shopping_ads:
            assert ad.result_type == "shopping_ad"
            assert ad.position == 0
            assert "price" in ad.metadata
            assert "merchant" in ad.metadata
            assert ad.metadata["price"]
            assert ad.metadata["merchant"]

    def test_parse_shopping_ads_prices(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        ads = self.parser.parse(google_weekly_contacts_mobile_html).shopping_ads
        prices = [str(r.metadata["price"]) for r in ads]
        assert "$51.19" in prices
        assert "$83.99" in prices
        assert "$48.79" in prices
        assert "$72.79" in prices

    def test_parse_shopping_ads_merchants(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        ads = self.parser.parse(google_weekly_contacts_mobile_html).shopping_ads
        merchants = [str(r.metadata["merchant"]) for r in ads]
        assert "Contacts Direct" in merchants
        assert "1800Contacts" in merchants

    def test_parse_shopping_ads_not_in_organic(
        self, google_weekly_contacts_mobile_html: str
    ) -> None:
        results = self.parser.parse(google_weekly_contacts_mobile_html)
        for r in results.results:
            assert r.result_type != "shopping_ad"

    def test_parse_no_shopping_ads_returns_empty(self, google_organic_html: str) -> None:
        results = self.parser.parse(google_organic_html)
        assert results.shopping_ads == []

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
            "job",
            "discussion",
            "shopping_ad",
        }
        results = self.parser.parse(google_web_scraping_html)
        for r in results.results:
            assert r.result_type not in non_organic
