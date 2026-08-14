"""Google search results parser."""

from __future__ import annotations

import copy
import json
import logging
import re
from urllib.parse import parse_qs, unquote, urljoin, urlparse

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

        # Mobile Google pages lack div#search and div.g but have these signals
        if soup.find_all("div", class_="xpd"):
            confidence = max(confidence, 0.7)
        if soup.find_all(class_="zBAuLc"):
            confidence = max(confidence, 0.8)

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
            jobs=self._extract_jobs(soup),
            discussions=self._extract_discussions(soup),
            shopping_ads=self._extract_shopping_ads(soup),
            news=self._extract_news_results(soup),
            local_businesses=self._extract_local_businesses(soup),
            detection_confidence=confidence,
            metadata=self._extract_page_metadata(soup),
        )

    def _find_organic_results(self, soup: BeautifulSoup) -> list[Tag]:
        """Find all organic result containers (desktop and mobile)."""
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

        # Desktop fallback without #search container
        g_divs = [t for t in soup.find_all("div", class_="g") if isinstance(t, Tag)]
        if g_divs:
            return g_divs

        # Mobile Google pages use div.xpd containers with egMi0 for organic results
        mobile = self._find_mobile_organic_results(soup)
        if mobile:
            return mobile

        # No-JS mobile layout: same div.xpd shell, but the title lives in
        # an h3.zBAuLc instead of an egMi0 block.
        return self._find_no_js_mobile_organic_results(soup)

    def _find_mobile_organic_results(self, soup: BeautifulSoup) -> list[Tag]:
        """Find organic result containers on mobile Google pages (div.xpd with egMi0)."""
        return [
            t
            for t in soup.find_all("div", class_="xpd")
            if isinstance(t, Tag) and t.find(class_="egMi0")
        ]

    def _find_no_js_mobile_organic_results(self, soup: BeautifulSoup) -> list[Tag]:
        """Find organic result containers on no-JS mobile pages (div.xpd with h3.zBAuLc)."""
        return [
            t
            for t in soup.find_all("div", class_="xpd")
            if isinstance(t, Tag) and t.find("h3", class_="zBAuLc")
        ]

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
        """Parse a single organic result div (desktop or mobile)."""
        # Mobile path: containers have egMi0 class
        if item.find(class_="egMi0"):
            return self._parse_mobile_organic_result(item, position)

        # No-JS mobile path: title is an h3.zBAuLc wrapped in the result's anchor
        if item.find("h3", class_="zBAuLc"):
            return self._parse_no_js_mobile_organic_result(item, position)

        # Desktop path
        link_container = item.find("div", class_="yuRUbf")
        if not isinstance(link_container, Tag):
            # Try finding a direct link with h3
            link = item.find("a")
            h3 = item.find("h3")
            if not isinstance(link, Tag) or not isinstance(h3, Tag):
                return None
            url = self._decode_google_redirect(str(link.get("href", "")))
            title = clean_text(h3.get_text())
        else:
            link = link_container.find("a")
            if not isinstance(link, Tag):
                return None
            url = self._decode_google_redirect(str(link.get("href", "")))
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

    def _parse_mobile_organic_result(self, item: Tag, position: int) -> SearchResult | None:
        """Parse a single mobile Google organic result (div.xpd with egMi0 container)."""
        title_block = item.find(class_="egMi0")
        if not isinstance(title_block, Tag):
            return None

        h3 = title_block.find("h3")
        if not isinstance(h3, Tag):
            return None
        title = clean_text(h3.get_text())
        if not title:
            return None

        link = title_block.find("a")
        if not isinstance(link, Tag):
            return None
        url = self._decode_google_redirect(str(link.get("href", "")))
        if not url:
            return None

        # Description is in the second kCrYT div (the one without egMi0)
        description: str | None = None
        kcryt_divs = item.find_all(class_="kCrYT")
        for k in kcryt_divs:
            if not isinstance(k, Tag) or k.find(class_="egMi0"):
                continue
            text = clean_text(k.get_text())
            if text:
                description = text
                break

        return SearchResult(
            title=title,
            url=url,
            description=description,
            position=position,
            result_type="organic",
        )

    def _parse_no_js_mobile_organic_result(self, item: Tag, position: int) -> SearchResult | None:
        """Parse one no-JS mobile organic result (div.xpd with an h3.zBAuLc title).

        Google serves this stripped no-JS layout to some mobile clients.
        The title and link share one anchor inside a div.sHTlR block; the snippet
        sits in the sibling div.lQigmf alongside any sitelinks.
        """
        h3 = item.find("h3", class_="zBAuLc")
        if not isinstance(h3, Tag):
            return None
        title = clean_text(h3.get_text())

        link = h3.find_parent("a")
        if not isinstance(link, Tag):
            return None
        url = self._decode_google_redirect(str(link.get("href", "")))
        if not url or not title:
            return None

        metadata = self._extract_no_js_mobile_result_metadata(item, h3)

        return SearchResult(
            title=title,
            url=url,
            description=self._no_js_mobile_description(item, h3),
            position=position,
            result_type="organic",
            metadata=metadata,
        )

    @staticmethod
    def _no_js_mobile_description(item: Tag, h3: Tag) -> str | None:
        """Pull the snippet out of the lQigmf block that doesn't hold the title.

        Sitelinks live in that same block as nested anchors, so they are dropped
        from a copy of the tag before the text is collected.
        """
        for block in item.find_all("div", class_="lQigmf"):
            if not isinstance(block, Tag) or h3 in block.descendants:
                continue

            # Prefer the leaf snippet node.  Rich result metadata (rating,
            # reviews, delivery) is rendered in the same lQigmf wrapper and
            # should not be folded into the description.
            candidates: list[str] = []
            for candidate in block.find_all("div", class_="H66NU"):
                if not isinstance(candidate, Tag) or candidate.find("div"):
                    continue
                if candidate.find("a"):
                    continue
                if candidate.find(class_="yi40Hd") or candidate.find(class_="RDApEe"):
                    continue
                candidate_copy = copy.copy(candidate)
                for metadata_el in candidate_copy.find_all(class_="UK5aid"):
                    metadata_el.decompose()
                text = clean_text(candidate_copy.get_text()).lstrip("· ")
                if text:
                    candidates.append(text)
            if candidates:
                return max(candidates, key=len)

            block = copy.copy(block)
            for anchor in block.find_all("a"):
                anchor.decompose()
            text = clean_text(block.get_text())
            if text:
                return text
        return None

    def _extract_no_js_mobile_result_metadata(self, item: Tag, h3: Tag) -> dict[str, object]:
        """Extract rich metadata and sitelinks from a no-JS mobile result."""
        metadata: dict[str, object] = {}

        title_block = h3.find_parent("a")
        display_el = title_block.find(class_="BamJPe") if isinstance(title_block, Tag) else None
        if isinstance(display_el, Tag):
            display_url = clean_text(display_el.get_text())
            if display_url:
                metadata["display_url"] = display_url

        rating_el = item.find(class_="yi40Hd")
        if isinstance(rating_el, Tag):
            rating = clean_text(rating_el.get_text())
            if rating:
                metadata["rating"] = rating

        reviews_el = item.find(class_="RDApEe")
        if isinstance(reviews_el, Tag):
            reviews = clean_text(reviews_el.get_text()).strip("()")
            if reviews:
                metadata["reviews"] = reviews

        attributes: list[str] = []
        published_time: str | None = None
        for attribute_el in item.find_all(class_="UK5aid"):
            if not isinstance(attribute_el, Tag):
                continue
            if attribute_el.find(class_="yi40Hd") or attribute_el.find(class_="RDApEe"):
                continue
            text = clean_text(attribute_el.get_text()).strip("· ")
            if not text or text in attributes:
                continue
            if self._looks_like_published_time(text):
                published_time = published_time or text
            else:
                attributes.append(text)
        if published_time:
            metadata["published_time"] = published_time
        if attributes:
            metadata["attributes"] = attributes

        sitelinks: list[dict[str, str]] = []
        seen_sitelinks: set[tuple[str, str]] = set()
        for block in item.find_all("div", class_="lQigmf"):
            if not isinstance(block, Tag) or h3 in block.descendants:
                continue
            for anchor in block.find_all("a", href=True):
                if not isinstance(anchor, Tag):
                    continue
                title = clean_text(anchor.get_text())
                url = self._decode_google_redirect(str(anchor.get("href", "")))
                key = (title.casefold(), url)
                if title and url and key not in seen_sitelinks:
                    seen_sitelinks.add(key)
                    sitelinks.append({"title": title, "url": url})
        if sitelinks:
            metadata["sitelinks"] = sitelinks

        return metadata

    @staticmethod
    def _looks_like_published_time(text: str) -> bool:
        """Return whether a rich-result attribute looks like a publication date."""
        month = (
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
            r"(?:uary|ruary|ch|il|e|y|ust|tember|ober|ember)?"
        )
        return bool(
            re.search(rf"\b{month}\s+\d{{1,2}},\s+\d{{4}}\b", text, re.I)
            or re.search(
                r"\b\d+\s+(?:minutes?|hours?|days?|weeks?|months?|years?)\s+ago\b", text, re.I
            )
        )

    @staticmethod
    def _decode_google_redirect(href: str) -> str:
        """Decode a Google /url?q=... redirect to the actual destination URL.

        Some Google buckets instead serve ``/goto?url=<blob>`` where the blob is
        encrypted server-side — the destination is nowhere in the HTML, so those
        hrefs are returned unchanged for the caller to resolve over the network.
        """
        if not href:
            return href
        m = re.search(r"/url\?q=([^&]+)", href)
        if m:
            return unquote(m.group(1))
        return href

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

        # No-JS mobile ads are wrapped in data-text-ad containers and use
        # the same xpd card shell as other mobile result types.
        opera_results: list[SearchResult] = []
        for ad_wrapper in soup.find_all(attrs={"data-text-ad": "1"}):
            if not isinstance(ad_wrapper, Tag):
                continue
            result = self._parse_no_js_mobile_sponsored_ad(ad_wrapper)
            if result:
                opera_results.append(result)

        # Google commonly repeats the same ad above and below the organic
        # results.  Merge those copies so bottom-only phone/sitelink data is not
        # lost while callers receive one advertiser result.
        deduplicated: dict[tuple[str, str], SearchResult] = {}
        for result in opera_results:
            display_url = str(result.metadata.get("display_url", ""))
            key = (result.title.casefold(), display_url.casefold() or result.url)
            existing = deduplicated.get(key)
            if existing is None:
                deduplicated[key] = result
                continue
            if not existing.description and result.description:
                existing.description = result.description
            self._merge_result_metadata(existing.metadata, result.metadata)
        results.extend(deduplicated.values())
        return results

    def _parse_no_js_mobile_sponsored_ad(self, wrapper: Tag) -> SearchResult | None:
        """Parse one sponsored result from Google's no-JS mobile layout."""
        card = wrapper.find("div", class_="xpd")
        if not isinstance(card, Tag):
            card = wrapper

        link = card.find("a", class_="cz3goc")
        if not isinstance(link, Tag):
            return None
        heading = link.find(attrs={"role": "heading"})
        title = clean_text(heading.get_text()) if isinstance(heading, Tag) else ""
        url = str(link.get("href", ""))
        if not title or not url:
            return None

        description_el = card.find(class_="r025kc")
        description = (
            clean_text(description_el.get_text()) if isinstance(description_el, Tag) else None
        )

        metadata: dict[str, object] = {}
        display_el = card.find(attrs={"data-dtld": True})
        if isinstance(display_el, Tag):
            display_url = clean_text(display_el.get_text()) or str(display_el.get("data-dtld", ""))
            if display_url:
                metadata["display_url"] = display_url

        rating_el = card.find(class_="yi40Hd")
        if isinstance(rating_el, Tag):
            rating = clean_text(rating_el.get_text())
            if rating:
                metadata["rating"] = rating

        phone_link = card.find("a", href=re.compile(r"^tel:"))
        if isinstance(phone_link, Tag):
            phone = clean_text(phone_link.get_text()) or str(phone_link.get("href", ""))[4:]
            phone = re.sub(r"^Call\s+", "", phone, flags=re.I)
            if phone:
                metadata["phone"] = phone

        sitelinks: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for sitelink_root in card.select(".E8hWLe, .qmaLCb"):
            for sitelink in sitelink_root.find_all("a", href=True):
                if not isinstance(sitelink, Tag):
                    continue
                sitelink_title = clean_text(sitelink.get_text())
                sitelink_url = str(sitelink.get("href", ""))
                key = (sitelink_title.casefold(), sitelink_url)
                if sitelink_title and sitelink_url and key not in seen:
                    seen.add(key)
                    sitelinks.append({"title": sitelink_title, "url": sitelink_url})
        if sitelinks:
            metadata["sitelinks"] = sitelinks

        return SearchResult(
            title=title,
            url=url,
            description=description,
            position=0,
            result_type="sponsored",
            metadata=metadata,
        )

    @staticmethod
    def _merge_result_metadata(target: dict[str, object], source: dict[str, object]) -> None:
        """Merge metadata from duplicate result cards without dropping list items."""
        for key, value in source.items():
            if key not in target:
                target[key] = value
                continue
            target_value = target[key]
            if not isinstance(target_value, list) or not isinstance(value, list):
                continue
            target_list: list[object] = target_value
            for item in value:
                duplicate = item in target_list
                if isinstance(item, dict) and isinstance(item.get("title"), str):
                    item_title = item["title"].casefold()
                    duplicate = duplicate or any(
                        isinstance(existing, dict)
                        and isinstance(existing.get("title"), str)
                        and existing["title"].casefold() == item_title
                        for existing in target_list
                    )
                if not duplicate:
                    target_list.append(item)

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
        """Extract AI Overview section if present (desktop and mobile)."""
        # Desktop: div.YzCcne container
        container = soup.find("div", class_="YzCcne")
        if isinstance(container, Tag):
            content_div = container.find("div", class_="mZJni")
            if isinstance(content_div, Tag):
                description = clean_text(content_div.get_text())
                if description:
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

        # Mobile: AI Overview content is in div.frRrnc inside xpd block with gqwIMe header
        for xpd in soup.find_all("div", class_="xpd"):
            if not isinstance(xpd, Tag):
                continue
            if not xpd.find(class_="gqwIMe"):
                continue
            content_div = xpd.find("div", class_="frRrnc")
            if not isinstance(content_div, Tag):
                continue
            description = clean_text(content_div.get_text())
            if description:
                metadata = self._extract_mobile_ai_metadata(soup, xpd)
                return SearchResult(
                    title="AI Overview",
                    url="",
                    description=description,
                    position=0,
                    result_type="ai_overview",
                    metadata=metadata,
                )

        return None

    def _extract_mobile_ai_metadata(self, soup: BeautifulSoup, container: Tag) -> dict[str, object]:
        """Extract AI citations and expanded facts, including JS-injected HTML."""
        roots: list[BeautifulSoup | Tag] = [container]
        placeholder_ids = {
            str(element.get("id"))
            for element in container.find_all(id=True)
            if str(element.get("id", "")).startswith("accdef_")
        }
        roots.extend(self._extract_jsl_dh_fragments(soup, placeholder_ids or None))

        sources: list[dict[str, str]] = []
        seen_sources: set[tuple[str, str]] = set()
        details: list[str] = []

        for root in roots:
            for card in root.select(".pcitem"):
                link = card.find("a", href=True)
                title_el = card.find(class_="UFvD1")
                if not isinstance(link, Tag) or not isinstance(title_el, Tag):
                    continue
                title = clean_text(title_el.get_text())
                url = self._decode_google_redirect(str(link.get("href", "")))
                source_el = card.find(class_="BamJPe")
                source = clean_text(source_el.get_text()) if isinstance(source_el, Tag) else ""
                key = (title.casefold(), url)
                if not title or not url or key in seen_sources:
                    continue
                seen_sources.add(key)
                citation = {"title": title, "url": url}
                if source:
                    citation["source"] = source
                sources.append(citation)

            details_root = root.find(id="B2Jtyd")
            if not isinstance(details_root, Tag):
                continue
            for detail_el in details_root.find_all("li"):
                if not isinstance(detail_el, Tag):
                    continue
                detail = clean_text(detail_el.get_text())
                if detail and detail not in details:
                    details.append(detail)

        metadata: dict[str, object] = {"sources": sources}
        if details:
            metadata["details"] = details
        return metadata

    @staticmethod
    def _extract_jsl_dh_fragments(
        soup: BeautifulSoup, allowed_ids: set[str] | None = None
    ) -> list[BeautifulSoup]:
        """Decode inert HTML fragments passed to Google's ``window.jsl.dh`` helper."""
        fragments: list[BeautifulSoup] = []
        call_pattern = re.compile(
            r"window\.jsl\.dh\(\s*['\"]([^'\"]+)['\"]\s*,\s*\"((?:\\.|[^\"\\])*)\"",
            re.S,
        )
        for script in soup.find_all("script"):
            if not isinstance(script, Tag):
                continue
            script_text = script.string or script.get_text()
            if "window.jsl.dh(" not in script_text:
                continue
            for match in call_pattern.finditer(script_text):
                if allowed_ids is not None and match.group(1) not in allowed_ids:
                    continue
                encoded = match.group(2)
                encoded = re.sub(
                    r"\\x([0-9a-fA-F]{2})",
                    lambda value: chr(int(value.group(1), 16)),
                    encoded,
                )
                try:
                    decoded = json.loads(f'"{encoded}"')
                except json.JSONDecodeError:
                    logger.debug("Unable to decode Google jsl.dh fragment", exc_info=True)
                    continue
                if "<" in decoded:
                    fragments.append(make_soup(decoded))
        return fragments

    def _extract_shopping_ads(self, soup: BeautifulSoup) -> list[SearchResult]:
        """Extract shopping ad cards (mobile and desktop Google Shopping units)."""
        results: list[SearchResult] = []

        # Mobile: div.wywECb wrapper contains div.qvfQJe product cards
        shopping_wrapper = soup.find("div", class_="wywECb")
        if isinstance(shopping_wrapper, Tag):
            for card in shopping_wrapper.find_all("div", class_="qvfQJe"):
                if not isinstance(card, Tag):
                    continue
                result = self._parse_shopping_card(card)
                if result:
                    results.append(result)

        return results

    def _parse_shopping_card(self, card: Tag) -> SearchResult | None:
        """Parse a single mobile shopping product card (div.qvfQJe)."""
        title_container = card.find(class_="bXPcId")
        if not isinstance(title_container, Tag):
            return None
        first_div = title_container.find("div")
        title = (
            clean_text(first_div.get_text())
            if isinstance(first_div, Tag)
            else clean_text(title_container.get_text())
        )
        if not title:
            return None

        link = card.find("a")
        url = str(link.get("href", "")) if isinstance(link, Tag) else ""

        price_el = card.find(class_="VbBaOe")
        price = clean_text(price_el.get_text()) if isinstance(price_el, Tag) else None

        merchant_el = card.find(class_="BZuDuc")
        merchant = clean_text(merchant_el.get_text()) if isinstance(merchant_el, Tag) else None

        metadata: dict[str, object] = {}
        if price:
            metadata["price"] = price
        if merchant:
            metadata["merchant"] = merchant

        return SearchResult(
            title=title,
            url=url,
            description=None,
            position=0,
            result_type="shopping_ad",
            metadata=metadata,
        )

    def _extract_people_also_ask(self, soup: BeautifulSoup) -> list[SearchResult]:
        """Extract People Also Ask questions (desktop and mobile)."""
        results: list[SearchResult] = []

        # Desktop: related-question-pair divs
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

        # Mobile: questions in div.Lt3Tzc inside xpd blocks
        if not results:
            for question_div in soup.find_all("div", class_="Lt3Tzc"):
                if not isinstance(question_div, Tag):
                    continue
                question = clean_text(question_div.get_text())
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
        """Extract 'People Also Search For' carousel items (desktop and mobile)."""
        results: list[SearchResult] = []

        # Desktop: oIk2Cb > XNfAUb carousel
        outer = soup.find("div", class_="oIk2Cb")
        if isinstance(outer, Tag):
            carousel = outer.find("div", class_="XNfAUb")
            if isinstance(carousel, Tag):
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

        # Mobile: a.Q71vJc links inside xpd blocks
        if not results:
            for link in soup.find_all("a", class_="Q71vJc"):
                if not isinstance(link, Tag):
                    continue
                url = str(link.get("href", ""))
                title = clean_text(link.get_text())
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

        # No-JS mobile: a heading and a stack of HA0EX search links inside an xpd card.
        seen = {result.title.casefold() for result in results}
        for header in soup.find_all("div", class_="E3VR9e"):
            if not isinstance(header, Tag):
                continue
            if clean_text(header.get_text()).casefold() != "people also search for":
                continue
            container = header.find_parent("div", class_="xpd")
            if not isinstance(container, Tag):
                continue
            for link in container.find_all("a", class_="HA0EX"):
                if not isinstance(link, Tag):
                    continue
                title_el = link.find(class_="hvqeqc")
                title = clean_text(
                    title_el.get_text() if isinstance(title_el, Tag) else link.get_text()
                )
                url = str(link.get("href", ""))
                if not title or not url or title.casefold() in seen:
                    continue
                seen.add(title.casefold())
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

    @staticmethod
    def _extract_page_metadata(soup: BeautifulSoup) -> dict[str, object]:
        """Extract page-level location and pagination metadata."""
        metadata: dict[str, object] = {}

        location_el = soup.select_one("#ewlSqd .AhYzQb")
        if isinstance(location_el, Tag):
            location = clean_text(location_el.get_text())
            if location:
                metadata["location"] = location

        location_container = soup.find(id="ewlSqd")
        if isinstance(location_container, Tag):
            for element in location_container.find_all(["span", "div"]):
                if not isinstance(element, Tag) or element.find(["span", "div"]):
                    continue
                text = clean_text(element.get_text())
                if text.casefold().startswith("from your "):
                    metadata["location_source"] = text
                    break

        pagination: dict[str, object] = {}
        footer = soup.find("footer")
        if isinstance(footer, Tag):
            for link in footer.find_all("a", href=True):
                if not isinstance(link, Tag):
                    continue
                label = clean_text(link.get_text()).casefold()
                aria_label = str(link.get("aria-label", "")).casefold()
                direction = None
                if label.startswith("next") or aria_label == "next page":
                    direction = "next"
                elif label.startswith("previous") or aria_label == "previous page":
                    direction = "previous"
                if direction is None:
                    continue
                url = urljoin("https://www.google.com", str(link.get("href", "")))
                pagination[f"{direction}_url"] = url
                start = parse_qs(urlparse(url).query).get("start")
                if start and start[0].isdigit():
                    pagination[f"{direction}_start"] = int(start[0])
        if pagination:
            metadata["pagination"] = pagination

        return metadata

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

    def _extract_jobs(self, soup: BeautifulSoup) -> list[SearchResult]:
        """Extract Google Jobs widget listings.

        Jobs are rendered inside a dedicated widget (``div.iYivne``) and are
        intentionally kept out of the organic ``results`` list.
        """
        results: list[SearchResult] = []
        widget = soup.find("div", class_="iYivne")
        if not isinstance(widget, Tag):
            return results
        for item in widget.find_all("div", class_="EimVGf"):
            if not isinstance(item, Tag):
                continue
            title_div = item.find("div", class_="tNxQIb")
            company_div = item.find("div", class_="a3jPc")
            location_div = item.find("div", class_="FqK3wc")
            link = item.find("a", class_="MQUd2b")
            title = clean_text(title_div.get_text()) if isinstance(title_div, Tag) else ""
            if not title:
                continue
            url = str(link.get("href", "")) if isinstance(link, Tag) else ""
            company = clean_text(company_div.get_text()) if isinstance(company_div, Tag) else None
            location = (
                clean_text(location_div.get_text()) if isinstance(location_div, Tag) else None
            )

            # Salary has the extra QZEeP class; employment type and other tags share K3eUK only
            salary_div = item.find("div", class_="QZEeP")
            salary = clean_text(salary_div.get_text()) if isinstance(salary_div, Tag) else None

            # Employment type: K3eUK entries that are NOT the salary and NOT a date ("X days ago")
            employment_type: str | None = None
            for tag_div in item.find_all("div", class_="K3eUK"):
                if not isinstance(tag_div, Tag):
                    continue
                if "QZEeP" in (tag_div.get("class") or []):
                    continue  # skip salary
                text = clean_text(tag_div.get_text())
                if text and not re.search(r"\d+\s+\w+\s+ago", text):
                    employment_type = text
                    break

            benefits = [
                clean_text(b.get_text())
                for b in item.find_all("div", class_="HvHIEc")
                if isinstance(b, Tag) and clean_text(b.get_text())
            ]

            metadata: dict[str, object] = {}
            if company:
                metadata["company"] = company
            if location:
                metadata["location"] = location
            if salary:
                metadata["salary"] = salary
            if employment_type:
                metadata["employment_type"] = employment_type
            if benefits:
                metadata["benefits"] = benefits
            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    description=None,
                    position=0,
                    result_type="job",
                    metadata=metadata,
                )
            )
        return results

    def _extract_discussions(self, soup: BeautifulSoup) -> list[SearchResult]:
        """Extract 'Discussions and forums' widget entries."""
        results: list[SearchResult] = []
        header = soup.find("div", class_="DuxCpf")
        if not isinstance(header, Tag):
            return results
        container = header.find_parent("div", class_="Ww4FFb")
        if not isinstance(container, Tag):
            return results
        for item in container.find_all("div", class_="xYkm8c"):
            if not isinstance(item, Tag):
                continue
            title_div = item.find("div", class_="j29v2b")
            link = item.find("a", class_="KYg7td")
            meta_div = item.find("div", class_="LbKnXb")
            desc_div = item.find("div", class_="bCOlv")
            title = clean_text(title_div.get_text()) if isinstance(title_div, Tag) else ""
            if not title:
                continue
            url = str(link.get("href", "")) if isinstance(link, Tag) else ""
            description = clean_text(desc_div.get_text()) if isinstance(desc_div, Tag) else None
            metadata: dict[str, object] = {}
            if isinstance(meta_div, Tag):
                metadata["source"] = clean_text(meta_div.get_text())
            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    description=description,
                    position=0,
                    result_type="discussion",
                    metadata=metadata,
                )
            )
        return results

    def _extract_news_results(self, soup: BeautifulSoup) -> list[SearchResult]:
        """Extract news articles from Google News tab (div.SoaBEf cards)."""
        results: list[SearchResult] = []
        position = 1
        for article in soup.find_all("div", class_="SoaBEf"):
            if not isinstance(article, Tag):
                continue
            result = self._parse_news_result(article, position)
            if result:
                results.append(result)
                position += 1
        return results

    def _parse_news_result(self, article: Tag, position: int) -> SearchResult | None:
        """Parse a single Google News tab article card (div.SoaBEf)."""
        link = article.find("a", class_="WlydOe")
        if not isinstance(link, Tag):
            return None
        url = str(link.get("href", ""))
        if not url:
            return None

        title_div = article.find("div", class_="n0jPhd")
        title = clean_text(title_div.get_text()) if isinstance(title_div, Tag) else ""
        if not title:
            return None

        source_div = article.find("div", class_="MgUUmf")
        source = clean_text(source_div.get_text()) if isinstance(source_div, Tag) else None

        desc_div = article.find("div", class_="UqSP2b")
        description = clean_text(desc_div.get_text()) if isinstance(desc_div, Tag) else None

        time_div = article.find("div", class_="OSrXXb")
        published_time = clean_text(time_div.get_text()) if isinstance(time_div, Tag) else None

        metadata: dict[str, object] = {}
        if source:
            metadata["source"] = source
        if published_time:
            metadata["published_time"] = published_time

        return SearchResult(
            title=title,
            url=url,
            description=description,
            position=position,
            result_type="news",
            metadata=metadata,
        )

    def _extract_local_businesses(self, soup: BeautifulSoup) -> list[SearchResult]:
        """Extract local business pack results (div.cXedhc cards)."""
        results: list[SearchResult] = []
        for item in soup.find_all("div", class_="cXedhc"):
            if not isinstance(item, Tag):
                continue
            result = self._parse_local_business(item)
            if result:
                results.append(result)
        return results

    def _parse_local_business(self, item: Tag) -> SearchResult | None:
        """Parse a single local business pack card (div.cXedhc)."""
        name_el = item.find("span", class_="OSrXXb")
        if not isinstance(name_el, Tag):
            return None
        name = clean_text(name_el.get_text())
        if not name:
            return None

        rating_el = item.find("span", class_="yi40Hd")
        rating = clean_text(rating_el.get_text()) if isinstance(rating_el, Tag) else None

        reviews_el = item.find("span", class_="RDApEe")
        reviews_raw = clean_text(reviews_el.get_text()) if isinstance(reviews_el, Tag) else None
        reviews = re.sub(r"[()]", "", reviews_raw).strip() if reviews_raw else None

        sponsored_el = item.find("span", class_="gghBu")
        sponsored = isinstance(sponsored_el, Tag) and "sponsored" in sponsored_el.get_text().lower()

        # Un-classed leaf divs carry category, location, hours, and phone
        leaf_divs = [
            d
            for d in item.find_all("div")
            if isinstance(d, Tag)
            and not d.get("class")
            and not d.find("div")
            and d.get_text(strip=True)
        ]

        category: str | None = None
        location: str | None = None
        hours: str | None = None
        phone: str | None = None

        for div in leaf_divs:
            text = div.get_text(separator="|", strip=True)
            # "4.9|(813)|· Personal injury attorney" — category follows "· "
            cat_match = re.search(r"·\s+(.+)$", text.replace("|", " "))
            if cat_match and not category:
                candidate = cat_match.group(1).strip()
                if not re.search(r"\d+\s*(hours?|year|min)", candidate, re.I):
                    category = candidate
                    continue
            # "15+ years in business · Chantilly, VA" — split on " · "
            if "years in business" in text or re.search(r"\d+\+?\s+year", text):
                parts = text.replace("|", " ").split(" · ", 1)
                if len(parts) == 2:
                    location = parts[1].strip()
                continue
            # "Open 24 hours · (703) 952-3191"
            if re.search(r"open|closed|\d{1,2}:\d{2}", text, re.I):
                parts = text.replace("|", " ").split("· ", 1)
                hours = parts[0].strip()
                if len(parts) == 2:
                    phone = parts[1].strip()
                continue

        metadata: dict[str, object] = {}
        if rating:
            metadata["rating"] = rating
        if reviews:
            metadata["reviews"] = reviews
        if category:
            metadata["category"] = category
        if location:
            metadata["location"] = location
        if hours:
            metadata["hours"] = hours
        if phone:
            metadata["phone"] = phone
        if sponsored:
            metadata["sponsored"] = True

        return SearchResult(
            title=name,
            url="",
            description=None,
            position=0,
            result_type="local_business",
            metadata=metadata,
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
