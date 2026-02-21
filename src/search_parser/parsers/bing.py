"""Bing search results parser."""

from __future__ import annotations

import logging

from bs4 import BeautifulSoup, Tag

from search_parser.core.models import SearchResult, SearchResults
from search_parser.parsers.base import BaseParser
from search_parser.utils import clean_text, make_soup

logger = logging.getLogger(__name__)


class BingParser(BaseParser):
    """Parser for Bing search result pages."""

    @property
    def engine_name(self) -> str:
        return "bing"

    def can_parse(self, soup: BeautifulSoup) -> float:
        """Check if this HTML is from Bing."""
        confidence = 0.0

        ms_app = soup.find("meta", attrs={"name": "ms.application"})
        if isinstance(ms_app, Tag) and "bing" in str(ms_app.get("content", "")).lower():
            confidence = max(confidence, 0.95)

        if soup.find_all("li", class_="b_algo"):
            confidence = max(confidence, 0.85)

        for meta in soup.find_all("meta"):
            content = str(meta.get("content", "")).lower()
            if "bing" in content:
                confidence = max(confidence, 0.7)

        return confidence

    def parse(self, html: str) -> SearchResults:
        """Parse Bing search results HTML."""
        soup = make_soup(html)
        organic: list[SearchResult] = []
        position = 1

        for item in soup.find_all("li", class_="b_algo"):
            if not isinstance(item, Tag):
                continue
            result = self._parse_organic_result(item, position)
            if result:
                organic.append(result)
                position += 1

        query = self.extract_query(soup)
        confidence = self.can_parse(soup)

        return SearchResults(
            search_engine=self.engine_name,
            query=query,
            results=organic,
            featured_snippet=self._extract_featured_snippet(soup),
            detection_confidence=confidence,
        )

    def _parse_organic_result(self, item: Tag, position: int) -> SearchResult | None:
        """Parse a single Bing organic result."""
        h2 = item.find("h2")
        if not isinstance(h2, Tag):
            return None

        link = h2.find("a")
        if not isinstance(link, Tag):
            return None

        title = clean_text(link.get_text())
        url = str(link.get("href", ""))

        if not title or not url:
            return None

        # Find description
        desc_div = item.find("div", class_="b_caption")
        description = None
        if isinstance(desc_div, Tag):
            p = desc_div.find("p")
            if isinstance(p, Tag):
                description = clean_text(p.get_text())

        return SearchResult(
            title=title,
            url=url,
            description=description,
            position=position,
            result_type="organic",
        )

    def _extract_featured_snippet(self, soup: BeautifulSoup) -> SearchResult | None:
        """Extract featured snippet if present."""
        snippet = soup.find("div", class_="b_ans")
        if not isinstance(snippet, Tag):
            return None

        h2 = snippet.find("h2")
        link = snippet.find("a")
        if not isinstance(h2, Tag) or not isinstance(link, Tag):
            return None

        title = clean_text(h2.get_text())
        url = str(link.get("href", ""))
        if not title or not url:
            return None

        # Get snippet body text
        body = snippet.find("div", class_="b_rich")
        if not isinstance(body, Tag):
            body = snippet.find("p")
        description = clean_text(body.get_text()) if isinstance(body, Tag) else None

        return SearchResult(
            title=title,
            url=url,
            description=description,
            position=0,
            result_type="featured_snippet",
            metadata={"snippet_type": "paragraph"},
        )
