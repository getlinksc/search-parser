"""Google search results parser."""

from __future__ import annotations

import logging
import re

from bs4 import BeautifulSoup, Tag

from search_parser.core.models import SearchResult, SearchResults
from search_parser.parsers.base import BaseParser
from search_parser.utils import clean_text, make_soup

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
        position = 1

        organic: list[SearchResult] = []
        for item in self._find_organic_results(soup):
            result = self._parse_organic_result(item, position)
            if result:
                organic.append(result)
                position += 1

        query = self.extract_query(soup)
        confidence = self.can_parse(soup)
        total_results = self._extract_total_results(soup)

        return SearchResults(
            search_engine=self.engine_name,
            query=query,
            results=organic,
            total_results=total_results,
            sponsored=self._extract_sponsored_results(soup),
            featured_snippet=self._extract_featured_snippet(soup),
            ai_overview=self._extract_ai_overview(soup),
            people_also_ask=self._extract_people_also_ask(soup),
            people_saying=self._extract_people_saying(soup),
            people_also_search=self._extract_people_also_search(soup),
            related_products=self._extract_related_products(soup),
            detection_confidence=confidence,
        )

    def _find_organic_results(self, soup: BeautifulSoup) -> list[Tag]:
        """Find all organic result containers."""
        search_div = soup.find("div", id="search")
        if isinstance(search_div, Tag):
            g_divs = [
                t
                for t in search_div.find_all("div", class_="g", recursive=True)
                if isinstance(t, Tag)
            ]
            if g_divs:
                return g_divs
            # Fallback: locate results by their yuRUbf (title/link) sections
            # and walk up to find a container that also holds the description.
            return self._find_results_by_title_links(search_div)
        return [t for t in soup.find_all("div", class_="g") if isinstance(t, Tag)]

    def _find_results_by_title_links(self, root: Tag) -> list[Tag]:
        """Find result containers by locating yuRUbf divs and their ancestors."""
        containers: list[Tag] = []
        seen: set[int] = set()
        for yu in root.find_all("div", class_="yuRUbf", recursive=True):
            container = self._find_result_container(yu, root)
            if isinstance(container, Tag) and id(container) not in seen:
                seen.add(id(container))
                containers.append(container)
        return containers

    def _find_result_container(self, title_link: Tag, root: Tag) -> Tag | None:
        """Walk up from a yuRUbf div to find the closest ancestor with a description."""
        ancestor = title_link.parent
        for _ in range(5):
            if not isinstance(ancestor, Tag) or ancestor is root:
                break
            if ancestor.find("div", class_="VwiC3b") or ancestor.find("span", class_="st"):
                return ancestor
            ancestor = ancestor.parent
        # No description ancestor found; use direct parent of yuRUbf
        return title_link.parent if isinstance(title_link.parent, Tag) else None

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

    def _extract_sponsored_results(self, soup: BeautifulSoup) -> list[SearchResult]:
        """Extract sponsored (ad) results from Google search pages."""
        results: list[SearchResult] = []
        for block in soup.find_all("div", class_="vbIt3d"):
            if not isinstance(block, Tag):
                continue
            for ad in block.find_all("div", class_="uEierd"):
                result = self._parse_sponsored_ad(ad)
                if result:
                    results.append(result)
        return results

    def _parse_sponsored_ad(self, ad: Tag) -> SearchResult | None:
        """Parse a single Google sponsored ad container."""
        link = ad.find("a", class_="sVXRqc")
        if not isinstance(link, Tag):
            return None

        url = str(link.get("href", ""))
        if not url or not url.startswith("http"):
            return None

        heading = link.find(attrs={"role": "heading"})
        title = clean_text(heading.get_text()) if isinstance(heading, Tag) else ""
        if not title:
            return None

        # Find description outside the main ad link
        description = None
        for desc_div in ad.find_all("div", class_="Va3FIb"):
            if not isinstance(desc_div, Tag):
                continue
            if desc_div.find_parent("a", class_="sVXRqc"):
                continue
            text = clean_text(desc_div.get_text())
            if text and text != title:
                description = text
                break

        return SearchResult(
            title=title,
            url=url,
            description=description,
            position=0,
            result_type="sponsored",
        )

    def _extract_total_results(self, soup: BeautifulSoup) -> int | None:
        """Extract Google's 'About X results' count from result-stats div."""
        stats_div = soup.find("div", id="result-stats")
        if not isinstance(stats_div, Tag):
            return None
        # Remove the <nobr> timing element, e.g. "(0.40 seconds)"
        nobr = stats_div.find("nobr")
        if isinstance(nobr, Tag):
            nobr.decompose()
        text = stats_div.get_text()
        match = re.search(r"([\d,]+)\s+results", text)
        if not match:
            return None
        try:
            return int(match.group(1).replace(",", ""))
        except ValueError:
            return None

    def _extract_ai_overview(self, soup: BeautifulSoup) -> SearchResult | None:
        """Extract AI Overview section if present."""
        container = soup.find("div", class_="YzCcne")
        if not isinstance(container, Tag):
            return None

        content_div = container.find("div", class_="mZJni")
        if not isinstance(content_div, Tag):
            return None

        description = clean_text(content_div.get_text())
        if not description:
            return None

        sources: list[dict[str, str]] = []
        for link in container.find_all("a", href=True):
            if not isinstance(link, Tag):
                continue
            href = str(link.get("href", ""))
            text = clean_text(link.get_text())
            if href.startswith("http") and text:
                sources.append({"title": text, "url": href})

        return SearchResult(
            title="AI Overview",
            url="",
            description=description,
            position=0,
            result_type="ai_overview",
            metadata={"sources": sources},
        )

    def _extract_people_also_ask(self, soup: BeautifulSoup) -> list[SearchResult]:
        """Extract People Also Ask questions."""
        results: list[SearchResult] = []
        for item in soup.find_all("div", class_="related-question-pair"):
            if not isinstance(item, Tag):
                continue
            question = str(item.get("data-q", ""))
            if not question:
                span = item.find("span", class_="CSkcDe")
                if isinstance(span, Tag):
                    question = clean_text(span.get_text())
            if question:
                results.append(
                    SearchResult(
                        title=question,
                        url="",
                        description=None,
                        position=0,
                        result_type="people_also_ask",
                    )
                )
        return results

    def _extract_people_saying(self, soup: BeautifulSoup) -> list[SearchResult]:
        """Extract 'What People Are Saying' social posts."""
        results: list[SearchResult] = []
        section = soup.find("g-section-with-header", class_="yG4QQe")
        if not isinstance(section, Tag):
            return results
        for post in section.find_all("div", class_="dz3f7e"):
            if not isinstance(post, Tag):
                continue
            link = post.find("a", class_="WlydOe")
            if not isinstance(link, Tag):
                continue
            url = str(link.get("href", ""))
            text_div = post.find("div", class_="eAaXgc")
            title = clean_text(text_div.get_text()) if isinstance(text_div, Tag) else ""
            if url:
                results.append(
                    SearchResult(
                        title=title or url,
                        url=url,
                        description=None,
                        position=0,
                        result_type="people_saying",
                    )
                )
        return results

    def _extract_people_also_search(self, soup: BeautifulSoup) -> list[SearchResult]:
        """Extract 'People Also Search For' carousel items."""
        results: list[SearchResult] = []
        outer = soup.find("div", class_="oIk2Cb")
        if not isinstance(outer, Tag):
            return results
        carousel = outer.find("div", class_="XNfAUb")
        if not isinstance(carousel, Tag):
            return results
        for item in carousel.find_all("div", class_="XRVJtc"):
            if not isinstance(item, Tag):
                continue
            link = item.find("a", class_="qrtwm")
            span = item.find("span", class_="Yt787")
            if not isinstance(link, Tag) or not isinstance(span, Tag):
                continue
            url = str(link.get("href", ""))
            title = clean_text(span.get_text())
            if title:
                results.append(
                    SearchResult(
                        title=title,
                        url=url,
                        description=None,
                        position=0,
                        result_type="people_also_search",
                    )
                )
        return results

    def _extract_related_products(self, soup: BeautifulSoup) -> list[SearchResult]:
        """Extract 'Find Related Products & Services' ad suggestions."""
        results: list[SearchResult] = []
        container = soup.find("div", id="HbKV2c")
        if not isinstance(container, Tag):
            return results
        for link in container.find_all("a", href=True):
            if not isinstance(link, Tag):
                continue
            url = str(link.get("href", ""))
            title = clean_text(link.get_text())
            if title and url:
                results.append(
                    SearchResult(
                        title=title,
                        url=url,
                        description=None,
                        position=0,
                        result_type="related_products",
                    )
                )
        return results

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
