"""Search engine auto-detection from HTML content."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from search_engine_parser.utils import make_soup

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Result of search engine detection."""

    engine: str
    confidence: float


class SearchEngineDetector:
    """Detects which search engine produced the given HTML.

    Detection is performed in priority order:
    1. HTML meta tags
    2. DOM structure patterns
    3. URL patterns in the HTML
    """

    def detect(self, html: str) -> DetectionResult | None:
        """Detect the search engine from HTML content.

        Args:
            html: Raw HTML string to analyze.

        Returns:
            DetectionResult with engine name and confidence, or None if
            confidence is below threshold.
        """
        soup = make_soup(html)
        candidates: list[DetectionResult] = []

        for check in [
            self._check_meta_tags,
            self._check_dom_structure,
            self._check_url_patterns,
        ]:
            result = check(soup)
            if result:
                candidates.append(result)

        if not candidates:
            return None

        best = max(candidates, key=lambda r: r.confidence)
        if best.confidence < 0.3:
            return None
        return best

    def _check_meta_tags(self, soup: BeautifulSoup) -> DetectionResult | None:
        """Check HTML meta tags for search engine identification."""
        # Google: <meta property="og:site_name" content="Google">
        og_site = soup.find("meta", attrs={"property": "og:site_name"})
        if isinstance(og_site, Tag) and str(og_site.get("content", "")).lower() == "google":
            return DetectionResult(engine="google", confidence=0.95)

        # Bing: <meta name="ms.application" content="Bing">
        ms_app = soup.find("meta", attrs={"name": "ms.application"})
        if isinstance(ms_app, Tag) and "bing" in str(ms_app.get("content", "")).lower():
            return DetectionResult(engine="bing", confidence=0.95)

        # Check for Bing in any meta content
        for meta in soup.find_all("meta"):
            content = str(meta.get("content", "")).lower()
            name = str(meta.get("name", "")).lower()
            if "bing" in content or "bing" in name:
                return DetectionResult(engine="bing", confidence=0.85)

        # DuckDuckGo: Check for DDG-specific meta tags
        for meta in soup.find_all("meta"):
            content = str(meta.get("content", "")).lower()
            if "duckduckgo" in content:
                return DetectionResult(engine="duckduckgo", confidence=0.95)

        return None

    def _check_dom_structure(self, soup: BeautifulSoup) -> DetectionResult | None:
        """Check DOM structure patterns for search engine identification."""
        # Google: div#search or div.g
        if soup.find("div", id="search") or soup.find_all("div", class_="g"):
            return DetectionResult(engine="google", confidence=0.8)

        # Bing: div.b_algo
        if soup.find_all("li", class_="b_algo"):
            return DetectionResult(engine="bing", confidence=0.85)

        # DuckDuckGo: various DDG-specific classes
        if soup.find_all("article", attrs={"data-testid": "result"}):
            return DetectionResult(engine="duckduckgo", confidence=0.85)
        if soup.find_all("div", class_="result"):
            return DetectionResult(engine="duckduckgo", confidence=0.6)

        return None

    # Allowed hostnames for each engine (exact match or subdomain of these)
    _ALLOWED_HOSTS: dict[str, list[str]] = {
        "google": ["google.com", "gstatic.com"],
        "bing": ["bing.com"],
        "duckduckgo": ["duckduckgo.com"],
    }

    @staticmethod
    def _parse_host(href: str) -> str:
        """Return the lowercase hostname from a URL, or '' on error."""
        try:
            return urlparse(href).hostname or ""
        except ValueError:
            return ""

    @classmethod
    def _match_engine(cls, host: str) -> str | None:
        """Return the engine name if *host* belongs to one of the allowed sets."""
        for engine, allowed in cls._ALLOWED_HOSTS.items():
            for allowed_host in allowed:
                if host == allowed_host or host.endswith("." + allowed_host):
                    return engine
        return None

    def _check_url_patterns(self, soup: BeautifulSoup) -> DetectionResult | None:
        """Check URL patterns in HTML for search engine identification."""
        # Check canonical URL first (higher confidence)
        canonical = soup.find("link", attrs={"rel": "canonical"})
        if isinstance(canonical, Tag):
            host = self._parse_host(str(canonical.get("href", "")))
            engine = self._match_engine(host)
            if engine:
                return DetectionResult(engine=engine, confidence=0.9)

        # Check other <link> elements
        for link in soup.find_all("link"):
            host = self._parse_host(str(link.get("href", "")))
            engine = self._match_engine(host)
            if engine:
                return DetectionResult(engine=engine, confidence=0.6)

        return None
