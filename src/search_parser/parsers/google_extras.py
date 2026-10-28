"""Extra Google fields: videos, pagination, answers, knowledge panel, discussions, ads, result count.

``GoogleExtrasMixin.parse_extras`` returns plain dicts and lists for page parts that the typed
``SearchResults`` model does not carry. Every part is independent: a selector that stops matching
costs only that key. Only keys that were found are returned.
"""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class GoogleExtrasMixin:
    """Adds ``parse_extras`` to ``GoogleParser``."""

    _EXTRAS_ORIGIN = "https://www.google.com"

    def _x_href(self, href: Any) -> str:
        """Absolutise a root-relative href. /goto tokens stay unresolved on
        purpose (the API resolves them); javascript: and fragments are dropped."""
        value = str(href or "").strip()
        if not value or value.startswith("#") or value.lower().startswith("javascript:"):
            return ""
        if value.startswith("/goto"):
            return value
        if value.startswith("//"):
            return "https:" + value
        if value.startswith("/"):
            return self._EXTRAS_ORIGIN + value
        return value

    @staticmethod
    def _x_text(
        el: Any, limit: int | None = None, sep: str = " ", skip_hidden: bool = False
    ) -> str:
        if el is None:
            return ""
        if skip_hidden:
            # aria-hidden spans duplicate the visible value (price digits, chart axes)
            parts = []
            for n in el.find_all(string=True):
                if type(n).__name__ != "NavigableString":
                    continue  # skip script/style/comment text
                hidden = False
                for p in n.parents:
                    if p.get("aria-hidden") == "true":
                        hidden = True
                        break
                    if p is el:
                        break
                if not hidden and str(n).strip():
                    parts.append(str(n).strip())
            t = re.sub(r"\s+", " ", sep.join(parts).replace("\xa0", " ")).strip()
            return t[:limit] if limit else t
        t = re.sub(r"\s+", " ", el.get_text(sep, strip=True).replace("\xa0", " ")).strip()
        return t[:limit] if limit else t

    @staticmethod
    def _x_start(a: Tag | None) -> int | None:
        if a is None:
            return None
        try:
            q = parse_qs(urlparse(str(a.get("href") or "")).query)
            return int(q["start"][0]) if "start" in q else 0
        except Exception:
            return None

    def _x_total(self, content: str) -> dict[str, Any]:
        # #result-stats is filled by a JS string in the raw document, e.g.
        # result-stats\">About 101 results\x3cnobr> (0.24s) ; in a rendered DOM it is
        # plain markup. The CSS rule "result-stats{" has no quote, so it never matches.
        # Some pages carry a placeholder "About 0 results" before the real figure,
        # so take the first non-zero match and fall back to the first one.
        best = None
        for m in re.finditer(r'result-stats\\?"[^>]*>(.{0,160}?)(?:\\x3c|<)', content or "", re.S):
            text = (
                m.group(1)
                .replace("\\x26nbsp;", " ")
                .replace("&nbsp;", " ")
                .replace("\xa0", " ")
                .strip()
            )
            if not text:
                continue
            cur = {"total_text": text}
            n = re.search(
                r"(\d[\d,.\s\u202f]*)\s*\S*\s*(?:results?|resultados|r\u00e9sultats|Ergebnisse|risultati)",
                text,
                re.I,
            )
            if n:
                digits = re.sub(r"\D", "", n.group(1))
                if digits:
                    cur["total"] = int(digits)
            if best is None:
                best = cur
            if cur.get("total"):
                return cur
        return best or {}

    def _x_videos(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        videos: list[dict[str, Any]] = []
        for blk in soup.select("div.xe8e1b"):
            h3 = blk.find("h3")
            a = (
                blk.select_one("a.zReHs")
                or (h3.find_parent("a") if h3 else None)
                or blk.find("a", href=True)
            )
            if not h3 or a is None:
                continue
            site = channel = None
            span = blk.select_one("span.VuuXrf")
            if span is not None:
                parts = [p.strip() for p in self._x_text(span).split("·")]
                site = parts[0] or None
                channel = " · ".join(parts[1:]).strip() or None
            cite = blk.select_one("cite")
            meta = (
                [p.strip() for p in self._x_text(cite).split("·") if p.strip()]
                if cite is not None
                else []
            )
            date = stats = None
            for p in meta:
                if re.search(r"\bago\b|\b(19|20)\d\d\b|^(yesterday|today)$", p, re.I):
                    date = date or p
                else:
                    stats = stats or p
            dur = re.search(r"(?<![\d:])(\d{1,2}:\d{2}(?::\d{2})?)(?![\d:])", self._x_text(blk))
            videos.append(
                {
                    "title": self._x_text(h3),
                    "url": self._x_href(a.get("href") if isinstance(a, Tag) else None),
                    "site": site,
                    "channel": channel,
                    "stats": stats,
                    "date": date,
                    "duration": dur.group(1) if dur else None,
                    "position": len(videos) + 1,
                }
            )
        return videos

    def _x_pagination(self, soup: BeautifulSoup) -> dict[str, Any]:
        nxt, prv = soup.select_one("a#pnnext"), soup.select_one("a#pnprev")
        if nxt is None and prv is None:
            return {}
        return {
            "next_start": self._x_start(nxt),
            "prev_start": self._x_start(prv),
            "has_next": nxt is not None,
        }

    def _x_answers(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        seen: set[Any] = set()
        for el in soup.select("[data-attrid]"):
            if el.find_parent(attrs={"data-attrid": True}) is not None:
                continue  # outermost only
            text = self._x_text(el, 500, skip_hidden=True)
            attrid = el.get("data-attrid")
            if not text or (attrid, text) in seen:
                continue
            seen.add((attrid, text))
            link: Any = el.find("a", href=True)
            out.append(
                {
                    "attrid": attrid,
                    "text": text,
                    "url": self._x_href(link.get("href")) if link else "",
                }
            )
            if len(out) >= 12:
                break
        return out

    def _x_answer_box(self, soup: BeautifulSoup) -> dict[str, Any]:
        box = soup.select_one(".xpdopen")
        if box is None:
            return {}
        head = box.find(["h2", "h3"]) or box.find(attrs={"role": "heading"})
        link: Any = box.find("a", href=True)
        return {
            "title": self._x_text(head, 200) or None,
            "text": self._x_text(box, 1500, skip_hidden=True),
            "url": self._x_href(link.get("href")) if link else "",
        }

    def _x_knowledge_panel(self, soup: BeautifulSoup) -> dict[str, Any]:
        rhs = soup.select_one("#rhs")
        if rhs is None or not self._x_text(rhs):
            return {}
        title = None
        for h in rhs.find_all(
            ["h2", "h3", "div", "span"], attrs={"role": "heading"}
        ) + rhs.find_all(["h2", "h3"]):
            t = self._x_text(h, 200)
            if t and t.lower() != "complementary results":
                title = t
                break
        links, seen = [], set()
        for a in rhs.find_all("a", href=True):
            url = self._x_href(a.get("href"))
            text = self._x_text(a, 120)
            if not url or not text or (url, text) in seen:
                continue
            seen.add((url, text))
            links.append({"text": text, "url": url})
            if len(links) >= 25:
                break
        return {"title": title, "text": self._x_text(rhs, 2000, skip_hidden=True), "links": links}

    def _x_discussions(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        head = None
        for h in soup.find_all(attrs={"role": "heading"}):
            if self._x_text(h).lower() == "discussions and forums":
                head = h
                break
        if head is None:
            return []

        def threads(node: Any) -> list[Any]:
            return [
                a
                for a in node.find_all("a", href=True)
                if a["href"].startswith("/goto") and a.find(attrs={"role": "heading"})
            ]

        node = head.parent
        while node is not None and not threads(node):
            node = node.parent
        if node is None or node.name in ("body", "html", "[document]"):
            return []
        out: list[dict[str, Any]] = []
        seen: set[Any] = set()
        for a in threads(node):
            url = self._x_href(a["href"])
            title = self._x_text(a.find(attrs={"role": "heading"}))
            if not title or url in seen:
                continue
            seen.add(url)
            src = a.select_one(".R8BTeb")
            source = self._x_text(src).strip(" ·") or None
            rest = self._x_text(a).replace(title, "", 1)
            if source:
                rest = rest.replace(source, "", 1)
            meta = [p.strip() for p in rest.split("·") if p.strip()]
            out.append(
                {
                    "title": title,
                    "url": url,
                    "source": source,
                    "meta": meta,
                    "position": len(out) + 1,
                }
            )
        return out

    def _x_ads(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Chrome-layout ads. The advertiser URL comes from data-pcu; the /aclk
        click URL (data-rw / href) is never read, followed or returned."""
        out: list[dict[str, Any]] = []
        seen: set[Any] = set()
        for a in soup.select("a[data-pcu]"):
            pcu = str(a.get("data-pcu") or "").strip()
            heading = a.find(attrs={"role": "heading"}) or a.find("h3")
            title = self._x_text(heading)
            if not pcu or not title:
                continue
            box = a.find_parent(attrs={"data-text-ad": True})
            key = (pcu, title, box.get("data-ta-slot") if box else None)
            if key in seen:
                continue
            seen.add(key)
            disp = a.find(attrs={"data-dtld": True})
            adv = a.select_one(".Aozhyc")
            desc = None
            if box is not None:
                d = box.select_one(".p4wth") or box.select_one(".r025kc")
                desc = self._x_text(d) or None
            out.append(
                {
                    "title": title,
                    "link": pcu,
                    "display_url": self._x_text(disp) or None,
                    "advertiser": self._x_text(adv) or None,
                    "description": desc,
                    "position": len(out) + 1,
                    "result_type": "ad",
                    "metadata": {"slot": box.get("data-ta-slot") if box else None},
                }
            )
        return out

    def parse_extras(self, content: str, soup: BeautifulSoup | None = None) -> dict[str, Any]:
        """Fields the search-parser/_parse pair leave out. Returns only keys it
        found; every part is independent so one failing selector costs only itself.

        ``soup`` is ``content`` already parsed (``parse`` passes its own), which saves
        building a second tree of a page that can be megabytes; none of the parts
        change it."""
        if not content:
            return {}
        if soup is None:
            soup = BeautifulSoup(content, "lxml")
        out = {}
        parts = (
            ("total", lambda: self._x_total(content)),
            ("videos", lambda: {"videos": self._x_videos(soup)}),
            ("pagination", lambda: {"pagination": self._x_pagination(soup)}),
            ("answers", lambda: {"answers": self._x_answers(soup)}),
            ("answer_box", lambda: {"answer_box": self._x_answer_box(soup)}),
            ("knowledge_panel", lambda: {"knowledge_panel": self._x_knowledge_panel(soup)}),
            ("discussions", lambda: {"discussions": self._x_discussions(soup)}),
            ("ads", lambda: {"ads": self._x_ads(soup)}),
        )
        for name, fn in parts:
            try:
                for k, v in fn().items():
                    if v not in (None, "", [], {}):
                        out[k] = v
            except Exception as e:
                logger.warning("parse_extras %s failed: %s", name, e)
        return out
