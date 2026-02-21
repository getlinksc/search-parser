"""DuckDuckGo search results parser."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from search_parser.core.models import SearchResult, SearchResults
from search_parser.parsers.base import BaseParser
from search_parser.utils import clean_text, make_soup

logger = logging.getLogger(__name__)


class DuckDuckGoParser(BaseParser):
    """Parser for DuckDuckGo search result pages."""

    @property
    def engine_name(self) -> str:
        return "duckduckgo"

    def can_parse(self, soup: BeautifulSoup) -> float:
        """Check if this HTML is from DuckDuckGo."""
        confidence = 0.0

        for meta in soup.find_all("meta"):
            content = str(meta.get("content", "")).lower()
            if "duckduckgo" in content:
                confidence = max(confidence, 0.95)

        if soup.find_all("article", attrs={"data-testid": "result"}):
            confidence = max(confidence, 0.85)

        if soup.find_all("div", class_="result"):
            confidence = max(confidence, 0.5)

        # Check for DDG-specific link patterns (compare hostname, not substring)
        for link in soup.find_all("link"):
            href = str(link.get("href", ""))
            try:
                host = urlparse(href).hostname or ""
            except ValueError:
                host = ""
            if host == "duckduckgo.com" or host.endswith(".duckduckgo.com"):
                confidence = max(confidence, 0.8)

        return confidence

    def parse(self, html: str) -> SearchResults:
        """Parse DuckDuckGo search results HTML."""
        soup = make_soup(html)
        results: list[SearchResult] = []
        position = 1

        # Try article-based results (newer DDG layout)
        articles = soup.find_all("article", attrs={"data-testid": "result"})
        if articles:
            for article in articles:
                if not isinstance(article, Tag):
                    continue
                result = self._parse_article_result(article, position)
                if result:
                    results.append(result)
                    position += 1
        else:
            # Fallback to div.result layout
            for item in soup.find_all("div", class_="result"):
                if not isinstance(item, Tag):
                    continue
                result = self._parse_div_result(item, position)
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

    def _parse_article_result(self, article: Tag, position: int) -> SearchResult | None:
        """Parse a DDG article-based result."""
        h2 = article.find("h2")
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
        desc = article.find("span", attrs={"data-testid": "result-snippet"})
        if not isinstance(desc, Tag):
            desc = article.find("div", class_="snippet")
        description = clean_text(desc.get_text()) if isinstance(desc, Tag) else None

        return SearchResult(
            title=title,
            url=url,
            description=description,
            position=position,
            result_type="organic",
        )

    def _parse_div_result(self, item: Tag, position: int) -> SearchResult | None:
        """Parse a DDG div.result-based result."""
        link = item.find("a", class_="result__a")
        if not isinstance(link, Tag):
            link = item.find("a")
        if not isinstance(link, Tag):
            return None

        title = clean_text(link.get_text())
        url = str(link.get("href", ""))

        if not title or not url:
            return None

        desc = item.find("a", class_="result__snippet")
        if not isinstance(desc, Tag):
            desc = item.find("div", class_="result__snippet")
        description = clean_text(desc.get_text()) if isinstance(desc, Tag) else None

        return SearchResult(
            title=title,
            url=url,
            description=description,
            position=position,
            result_type="organic",
        )
