"""Unit tests for GoogleFinanceParser."""

from __future__ import annotations

import pytest

from search_parser.parsers.google_finance import GoogleFinanceParser
from search_parser.utils import make_soup


class TestGoogleFinanceParser:
    def setup_method(self) -> None:
        self.parser = GoogleFinanceParser()

    # ------------------------------------------------------------------
    # Basic properties
    # ------------------------------------------------------------------

    def test_engine_name(self) -> None:
        assert self.parser.engine_name == "google_finance"

    # ------------------------------------------------------------------
    # can_parse
    # ------------------------------------------------------------------

    def test_can_parse_finance_html(self, google_finance_quote_html: str) -> None:
        soup = make_soup(google_finance_quote_html)
        assert self.parser.can_parse(soup) >= 0.8

    def test_can_parse_crypto_html(self, google_finance_crypto_html: str) -> None:
        soup = make_soup(google_finance_crypto_html)
        assert self.parser.can_parse(soup) >= 0.8

    def test_can_parse_empty_html(self) -> None:
        soup = make_soup("<html><head></head><body></body></html>")
        assert self.parser.can_parse(soup) == 0.0

    def test_can_parse_only_canonical(self) -> None:
        html = '<html><head><link rel="canonical" href="https://www.google.com/finance/quote/AAPL:NASDAQ"></head><body></body></html>'
        soup = make_soup(html)
        assert self.parser.can_parse(soup) >= 0.6

    # ------------------------------------------------------------------
    # extract_query
    # ------------------------------------------------------------------

    def test_extract_query_stock(self, google_finance_quote_html: str) -> None:
        soup = make_soup(google_finance_quote_html)
        assert self.parser.extract_query(soup) == "GOOGL:NASDAQ"

    def test_extract_query_crypto(self, google_finance_crypto_html: str) -> None:
        soup = make_soup(google_finance_crypto_html)
        assert self.parser.extract_query(soup) == "BTC-USD"

    def test_extract_query_no_canonical(self) -> None:
        soup = make_soup("<html><head></head><body></body></html>")
        assert self.parser.extract_query(soup) is None

    # ------------------------------------------------------------------
    # parse – top-level SearchResults fields
    # ------------------------------------------------------------------

    def test_parse_engine_name(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.search_engine == "google_finance"

    def test_parse_query(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.query == "GOOGL:NASDAQ"

    def test_parse_confidence(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.detection_confidence >= 0.8

    def test_parse_organic_results_empty(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.results == []

    def test_parse_has_parsed_at(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.parsed_at is not None

    # ------------------------------------------------------------------
    # stock_quote
    # ------------------------------------------------------------------

    def test_stock_quote_exists(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None

    def test_stock_quote_result_type(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.result_type == "stock_quote"

    def test_stock_quote_title(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.title == "Alphabet Inc Class A"

    def test_stock_quote_url(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert "google.com/finance/quote" in results.stock_quote.url

    def test_stock_quote_price(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["price"] == 339.32

    def test_stock_quote_change(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["change"] == 7.03

    def test_stock_quote_change_pct(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["change_pct"] == 2.12

    def test_stock_quote_previous_close(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["previous_close"] == 332.29

    def test_stock_quote_ticker(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["ticker"] == "GOOGL"

    def test_stock_quote_exchange(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["exchange"] == "NASDAQ"

    def test_stock_quote_type_stock(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["type"] == "stock"

    def test_stock_quote_currency(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["currency"] == "USD"

    def test_stock_quote_timezone(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["timezone"] == "America/New_York"

    def test_stock_quote_after_hours(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        ah = results.stock_quote.metadata["after_hours"]
        assert isinstance(ah, dict)
        assert ah["price"] == 336.63
        assert ah["change"] == -2.69

    def test_stock_quote_position_is_one(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_quote is not None
        assert results.stock_quote.position == 1

    # ------------------------------------------------------------------
    # company_info
    # ------------------------------------------------------------------

    def test_company_info_exists(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.company_info is not None

    def test_company_info_result_type(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.company_info is not None
        assert results.company_info.result_type == "company_info"

    def test_company_info_description(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.company_info is not None
        assert "Alphabet" in (results.company_info.description or "")

    def test_company_info_ceo(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.company_info is not None
        assert results.company_info.metadata["ceo"] == "Sundar Pichai"

    def test_company_info_employees(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.company_info is not None
        assert results.company_info.metadata["employees"] == 190820

    def test_company_info_market_cap(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.company_info is not None
        assert results.company_info.metadata["market_cap"] == 4090000000000

    def test_company_info_pe_ratio(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.company_info is not None
        assert results.company_info.metadata["pe_ratio"] == 31.4

    def test_company_info_sector(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.company_info is not None
        assert results.company_info.metadata["sector"] == "Interactive Media & Services"

    def test_company_info_52_week_high(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.company_info is not None
        assert results.company_info.metadata["fifty_two_week_high"] == 349

    def test_company_info_headquarters(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.company_info is not None
        hq = results.company_info.metadata["headquarters"]
        assert isinstance(hq, str)
        assert "Mountain View" in hq

    # ------------------------------------------------------------------
    # financial_news
    # ------------------------------------------------------------------

    def test_financial_news_present(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert len(results.financial_news) > 0

    def test_financial_news_result_type(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        for item in results.financial_news:
            assert item.result_type == "financial_news"

    def test_financial_news_titles_and_urls(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        for item in results.financial_news:
            assert item.title
            assert item.url

    def test_financial_news_source(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.financial_news[0].metadata["source"] in ("Reuters", "Bloomberg", "CNBC")

    def test_financial_news_sequential_positions(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        positions = [item.position for item in results.financial_news]
        for i in range(1, len(positions)):
            assert positions[i] == positions[i - 1] + 1

    # ------------------------------------------------------------------
    # stock_chart
    # ------------------------------------------------------------------

    def test_stock_chart_exists(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_chart is not None

    def test_stock_chart_result_type(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_chart is not None
        assert results.stock_chart.result_type == "stock_chart"

    def test_stock_chart_points(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_chart is not None
        points = results.stock_chart.metadata["points"]
        assert isinstance(points, list)
        assert len(points) > 0

    def test_stock_chart_point_format(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_chart is not None
        for pt in results.stock_chart.metadata["points"]:  # type: ignore[union-attr]
            assert isinstance(pt, dict)
            assert "date" in pt and "price" in pt
            assert pt["date"].count("-") == 2

    def test_stock_chart_previous_close(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        assert results.stock_chart is not None
        assert results.stock_chart.metadata["previous_close"] == 332.29

    # ------------------------------------------------------------------
    # Crypto
    # ------------------------------------------------------------------

    def test_crypto_engine_name(self, google_finance_crypto_html: str) -> None:
        results = self.parser.parse(google_finance_crypto_html)
        assert results.search_engine == "google_finance"

    def test_crypto_query(self, google_finance_crypto_html: str) -> None:
        results = self.parser.parse(google_finance_crypto_html)
        assert results.query == "BTC-USD"

    def test_crypto_quote_exists(self, google_finance_crypto_html: str) -> None:
        results = self.parser.parse(google_finance_crypto_html)
        assert results.stock_quote is not None

    def test_crypto_quote_type(self, google_finance_crypto_html: str) -> None:
        results = self.parser.parse(google_finance_crypto_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["type"] == "crypto"

    def test_crypto_quote_price(self, google_finance_crypto_html: str) -> None:
        results = self.parser.parse(google_finance_crypto_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["price"] == 77877

    def test_crypto_ticker(self, google_finance_crypto_html: str) -> None:
        results = self.parser.parse(google_finance_crypto_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["ticker"] == "BTC-USD"

    def test_crypto_no_after_hours(self, google_finance_crypto_html: str) -> None:
        results = self.parser.parse(google_finance_crypto_html)
        assert results.stock_quote is not None
        assert results.stock_quote.metadata["after_hours"] is None

    def test_crypto_has_news(self, google_finance_crypto_html: str) -> None:
        results = self.parser.parse(google_finance_crypto_html)
        assert len(results.financial_news) > 0

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_empty_html_does_not_raise(self) -> None:
        results = self.parser.parse("<html><head></head><body></body></html>")
        assert results.search_engine == "google_finance"
        assert results.stock_quote is None

    def test_malformed_script_does_not_raise(self) -> None:
        html = (
            '<html><head><link rel="canonical" href="https://www.google.com/finance/quote/AAPL:NASDAQ"></head>'
            "<body><script>AF_dataServiceRequests = {'ds:0': {id:'xh8wxf'}};</script>"
            "<script>AF_initDataCallback({key: 'ds:0', hash: '1', data: INVALID, sideChannel: {}});</script></body></html>"
        )
        results = self.parser.parse(html)
        assert results.stock_quote is None

    def test_serializes_to_json(self, google_finance_quote_html: str) -> None:
        results = self.parser.parse(google_finance_quote_html)
        json_str = results.to_json()
        import json

        parsed = json.loads(json_str)
        assert parsed["search_engine"] == "google_finance"
        assert parsed["stock_quote"] is not None
