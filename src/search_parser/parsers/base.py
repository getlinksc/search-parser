"""Abstract base class for search engine parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from bs4 import BeautifulSoup, Tag

from search_parser.core.models import SearchResults


class BaseParser(ABC):
    """Abstract base class for search engine parsers.

    All search engine parsers must implement this interface.
    To add a new search engine, subclass this and implement the
    abstract methods, then register in parsers/__init__.py.
    """

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of the search engine (e.g., 'google')."""
        ...

    @abstractmethod
    def parse(self, html: str) -> SearchResults:
        """Parse HTML and extract search results.

        Args:
            html: Raw HTML string from the search engine.

        Returns:
            Parsed search results.
        """
        ...

    @abstractmethod
    def can_parse(self, soup: BeautifulSoup) -> float:
        """Check if this parser can handle the given HTML.

        Args:
            soup: Parsed BeautifulSoup object.

        Returns:
            Confidence score from 0.0 (cannot parse) to 1.0 (certain).
        """
        ...

    def extract_query(self, soup: BeautifulSoup) -> str | None:
        """Extract the search query from the HTML if possible.

        Args:
            soup: Parsed BeautifulSoup object.

        Returns:
            The search query string, or None if not found.
        """
        # Common: check <input> with name="q"
        q_input = soup.find("input", attrs={"name": "q"})
        if isinstance(q_input, Tag):
            value = q_input.get("value")
            if value:
                return str(value)

        # Check title tag
        title_tag = soup.find("title")
        if isinstance(title_tag, Tag) and title_tag.string:
            text = title_tag.string.strip()
            for suffix in [
                " - Google Search",
                " - Bing",
                " - Search",
                " at DuckDuckGo",
            ]:
                if text.endswith(suffix):
                    return text[: -len(suffix)]

        return None
