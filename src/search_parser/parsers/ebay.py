"""eBay search results parser (ebay.com/sch/i.html).

Built against a live capture of eBay's current "s-card" layout (2026), which
replaced the older "s-item" markup that most eBay scraping references still
describe. Secondary listing details (shipping cost, watcher count, bids,
"or best offer", time left) are rendered as unlabeled `.s-card__attribute-row`
spans with no per-field class, and their text is locale-dependent, so they are
surfaced verbatim in ``metadata["attributes"]`` rather than guessed at.
"""

from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup, Tag

from search_parser.core.models import SearchResult, SearchResults
from search_parser.parsers.base import BaseParser
from search_parser.utils import clean_text, make_soup

logger = logging.getLogger(__name__)

_TOTAL_RESULTS_RE = re.compile(r"([\d,]+)\+?\s*results?", re.IGNORECASE)

# eBay renders one or two "Shop on eBay" house-ad cards at the top of every
# results page, sharing a generic placeholder item id/link -- not a real listing.
_PLACEHOLDER_TITLES = {"shop on ebay"}


class EbayParser(BaseParser):
    """Parser for eBay search result pages."""

    @property
    def engine_name(self) -> str:
        return "ebay"

    def can_parse(self, soup: BeautifulSoup) -> float:
        """Check if this HTML is from eBay search results."""
        confidence = 0.0

        og_site = soup.find("meta", attrs={"property": "og:site_name"})
        if isinstance(og_site, Tag) and str(og_site.get("content", "")).lower() == "ebay":
            confidence = max(confidence, 0.95)

        if soup.find("ul", class_="srp-results"):
            confidence = max(confidence, 0.9)

        if soup.find_all("li", class_="s-card") or soup.find_all("li", class_="s-item"):
            confidence = max(confidence, 0.85)

        canonical = soup.find("link", attrs={"rel": "canonical"})
        if isinstance(canonical, Tag) and "ebay.com" in str(canonical.get("href", "")):
            confidence = max(confidence, 0.7)

        return confidence

    def extract_query(self, soup: BeautifulSoup) -> str | None:
        """Extract the search query, preferring eBay's `_nkw` input."""
        nkw_input = soup.find("input", attrs={"name": "_nkw"})
        if isinstance(nkw_input, Tag):
            value = nkw_input.get("value")
            if value:
                return str(value)

        title_tag = soup.find("title")
        if isinstance(title_tag, Tag) and title_tag.string:
            text = title_tag.string.strip()
            if text.endswith(" | eBay"):
                return text[: -len(" | eBay")]

        return super().extract_query(soup)

    def parse(self, html: str) -> SearchResults:
        """Parse eBay search results HTML."""
        soup = make_soup(html)
        organic: list[SearchResult] = []
        position = 1

        for item in soup.find_all("li", class_="s-card"):
            if not isinstance(item, Tag):
                continue
            result = self._parse_listing(item, position)
            if result:
                organic.append(result)
                position += 1

        query = self.extract_query(soup)
        confidence = self.can_parse(soup)

        return SearchResults(
            search_engine=self.engine_name,
            query=query,
            results=organic,
            total_results=self._extract_total_results(soup),
            detection_confidence=confidence,
        )

    def _parse_listing(self, item: Tag, position: int) -> SearchResult | None:
        """Parse a single eBay listing card."""
        title_el = item.find(class_="s-card__title")
        if not isinstance(title_el, Tag):
            return None

        title = self._extract_title_text(title_el)
        if not title or title.lower() in _PLACEHOLDER_TITLES:
            return None

        link = item.find("a", class_="s-card__link")
        if not isinstance(link, Tag):
            return None
        url = str(link.get("href", ""))
        if not url:
            return None

        metadata: dict[str, object] = {}

        price_el = item.find(class_="s-card__price")
        if isinstance(price_el, Tag):
            metadata["price"] = clean_text(price_el.get_text())

        was_price = item.find(
            lambda tag: (
                isinstance(tag, Tag)
                and "su-styled-text" in tag.get("class", [])
                and "strikethrough" in tag.get("class", [])
            )
        )
        if isinstance(was_price, Tag):
            metadata["was_price"] = clean_text(was_price.get_text())

        condition_el = item.find(class_="s-card__subtitle")
        if isinstance(condition_el, Tag):
            metadata["condition"] = clean_text(condition_el.get_text())

        if item.find(class_="s-card__new-listing"):
            metadata["new_listing"] = True

        time_left = item.find(class_="s-card__time")
        time_left_text = clean_text(time_left.get_text()) if isinstance(time_left, Tag) else ""
        if time_left_text:
            metadata["time_left"] = time_left_text

        image = item.find("img", class_="s-card__image")
        if isinstance(image, Tag):
            img_src = image.get("data-defer-load") or image.get("src")
            if img_src:
                metadata["image"] = str(img_src)

        seller_block = item.find(class_="su-card-container__attributes__secondary")
        if isinstance(seller_block, Tag):
            seller_texts = [
                clean_text(span.get_text())
                for span in seller_block.find_all(class_="su-styled-text")
            ]
            seller_texts = [text for text in seller_texts if text]
            if seller_texts:
                metadata["seller"] = seller_texts[0]
                if len(seller_texts) > 1:
                    metadata["seller_feedback"] = seller_texts[1]

        primary_block = item.find(class_="su-card-container__attributes__primary")
        if isinstance(primary_block, Tag):
            extra_attributes = [
                clean_text(row.get_text())
                for row in primary_block.find_all(class_="s-card__attribute-row")
            ]
            extra_attributes = [
                text
                for text in extra_attributes
                if text and text not in (metadata.get("price"), metadata.get("was_price"))
            ]
            if extra_attributes:
                metadata["attributes"] = extra_attributes

        return SearchResult(
            title=title,
            url=url,
            position=position,
            result_type="organic",
            metadata=metadata,
        )

    @staticmethod
    def _extract_title_text(title_el: Tag) -> str:
        """Pull the visible title text, skipping badge/accessibility spans."""
        for span in title_el.find_all("span", recursive=False):
            classes = span.get("class", [])
            if "s-card__new-listing" in classes or "clipped" in classes:
                continue
            text = clean_text(span.get_text())
            if text:
                return text
        return clean_text(title_el.get_text())

    def _extract_total_results(self, soup: BeautifulSoup) -> int | None:
        """Extract the total result count heading (for example '1,234 results').

        English-locale heading text only; returns None for other locales.
        """
        heading = soup.find(class_="srp-controls__count-heading")
        if not isinstance(heading, Tag):
            return None
        match = _TOTAL_RESULTS_RE.search(clean_text(heading.get_text()))
        if not match:
            return None
        try:
            return int(match.group(1).replace(",", ""))
        except ValueError:
            return None
