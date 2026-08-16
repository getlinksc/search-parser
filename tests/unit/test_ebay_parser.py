"""Tests for eBay search results parser."""

from __future__ import annotations

from search_parser.parsers.ebay import EbayParser
from search_parser.utils import make_soup


class TestEbayParser:
    def setup_method(self) -> None:
        self.parser = EbayParser()

    def test_engine_name(self) -> None:
        assert self.parser.engine_name == "ebay"

    def test_can_parse_ebay_html(self, ebay_search_slipknot_html: str) -> None:
        soup = make_soup(ebay_search_slipknot_html)
        confidence = self.parser.can_parse(soup)
        assert confidence >= 0.85

    def test_can_parse_non_ebay_html(self) -> None:
        html = "<html><body><p>Not a search page</p></body></html>"
        soup = make_soup(html)
        confidence = self.parser.can_parse(soup)
        assert confidence == 0.0

    def test_parse_query(self, ebay_search_slipknot_html: str) -> None:
        results = self.parser.parse(ebay_search_slipknot_html)
        assert results.search_engine == "ebay"
        assert results.query == "slipknot"

    def test_parse_filters_house_ad_placeholder(self, ebay_search_slipknot_html: str) -> None:
        results = self.parser.parse(ebay_search_slipknot_html)
        titles = [r.title.lower() for r in results.results]
        assert "shop on ebay" not in titles

    def test_parse_listing_fields(self, ebay_search_slipknot_html: str) -> None:
        results = self.parser.parse(ebay_search_slipknot_html)
        assert len(results.results) > 0

        first = results.results[0]
        assert first.title
        assert first.url.startswith("https://www.ebay.com/itm/")
        assert first.position == 1
        assert first.result_type == "organic"
        assert "price" in first.metadata
        assert "condition" in first.metadata
        assert "image" in first.metadata

    def test_parse_result_positions_sequential(self, ebay_search_slipknot_html: str) -> None:
        results = self.parser.parse(ebay_search_slipknot_html)
        positions = [r.position for r in results.results]
        assert positions == list(range(1, len(positions) + 1))

    def test_parse_seller_metadata(self, ebay_search_slipknot_html: str) -> None:
        results = self.parser.parse(ebay_search_slipknot_html)
        with_seller = [r for r in results.results if "seller" in r.metadata]
        assert with_seller
        assert isinstance(with_seller[0].metadata["seller"], str)

    def test_parse_empty_html(self) -> None:
        results = self.parser.parse("<html><body></body></html>")
        assert results.search_engine == "ebay"
        assert len(results.results) == 0

    def test_detection_confidence(self, ebay_search_slipknot_html: str) -> None:
        results = self.parser.parse(ebay_search_slipknot_html)
        assert results.detection_confidence >= 0.85
