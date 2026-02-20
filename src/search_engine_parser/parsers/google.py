"""Google search results parser."""

from __future__ import annotations

import logging

from bs4 import BeautifulSoup, Tag

from search_engine_parser.core.models import SearchResult, SearchResults
from search_engine_parser.parsers.base import BaseParser
from search_engine_parser.utils import clean_text, make_soup

logger = logging.getLogger(__name__)


class GoogleParser(BaseParser):
    """Parser for Google search result pages."""

    @property
    def engine_name(self) -> str:
        return "google"

    def can_parse(self, soup: BeautifulSoup) -> float:
        """Check if this HTML is from Google."""
        confidence = 0.0

        og_site = soup.find("meta", attrs={"property": "og:site_name"})
        if isinstance(og_site, Tag) and str(og_site.get("content", "")).lower() == "google":
            confidence = max(confidence, 0.95)

        if soup.find("div", id="search"):
            confidence = max(confidence, 0.8)

        if soup.find_all("div", class_="g"):
            confidence = max(confidence, 0.7)

        return confidence

    def parse(self, html: str) -> SearchResults:
        """Parse Google search results HTML."""
        soup = make_soup(html)
        results: list[SearchResult] = []
        position = 1

        # Extract featured snippet
        featured = self._extract_featured_snippet(soup)
        if featured:
            results.append(featured)

        # Extract organic results
        for item in self._find_organic_results(soup):
            result = self._parse_organic_result(item, position)
            if result:
                results.append(result)
                position += 1

        query = self.extract_query(soup)
        confidence = self.can_parse(soup)

        return SearchResults(
            search_engine=self.engine_name,
            query=query,
            results=results,
            detection_confidence=confidence,
        )

    def _find_organic_results(self, soup: BeautifulSoup) -> list[Tag]:
        """Find all organic result containers."""
        search_div = soup.find("div", id="search")
        if isinstance(search_div, Tag):
            return [
                t
                for t in search_div.find_all("div", class_="g", recursive=True)
                if isinstance(t, Tag)
            ]
        return [t for t in soup.find_all("div", class_="g") if isinstance(t, Tag)]

    def _parse_organic_result(self, item: Tag, position: int) -> SearchResult | None:
        """Parse a single organic result div."""
        # Find the title link
        link_container = item.find("div", class_="yuRUbf")
        if not isinstance(link_container, Tag):
            # Try finding a direct link with h3
            link = item.find("a")
            h3 = item.find("h3")
            if not isinstance(link, Tag) or not isinstance(h3, Tag):
                return None
            url = str(link.get("href", ""))
            title = clean_text(h3.get_text())
        else:
            link = link_container.find("a")
            if not isinstance(link, Tag):
                return None
            url = str(link.get("href", ""))
            h3 = link.find("h3")
            title = clean_text(h3.get_text()) if isinstance(h3, Tag) else ""

        if not url or not title:
            return None

        # Find description
        desc_div = item.find("div", class_="VwiC3b")
        if not isinstance(desc_div, Tag):
            desc_div = item.find("span", class_="st")
        description = clean_text(desc_div.get_text()) if isinstance(desc_div, Tag) else None

        return SearchResult(
            title=title,
            url=url,
            description=description,
            position=position,
            result_type="organic",
        )

    def _extract_featured_snippet(self, soup: BeautifulSoup) -> SearchResult | None:
        """Extract featured snippet if present."""
        snippet_container = soup.find("div", class_="xpdopen")
        if not isinstance(snippet_container, Tag):
            snippet_container = soup.find("block-component")
        if not isinstance(snippet_container, Tag):
            return None

        h3 = snippet_container.find("h3")
        link = snippet_container.find("a")
        if not isinstance(h3, Tag) or not isinstance(link, Tag):
            return None

        title = clean_text(h3.get_text())
        url = str(link.get("href", ""))

        # Get snippet text
        desc_span = snippet_container.find("span", class_="hgKElc")
        if not isinstance(desc_span, Tag):
            desc_span = snippet_container.find("div", class_="LGOjhe")
        description = clean_text(desc_span.get_text()) if isinstance(desc_span, Tag) else None

        if not title or not url:
            return None

        return SearchResult(
            title=title,
            url=url,
            description=description,
            position=0,
            result_type="featured_snippet",
            metadata={"snippet_type": "paragraph"},
        )
