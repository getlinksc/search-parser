"""Google Finance HTML parser."""

from __future__ import annotations

import contextlib
import json
import logging
import re
from typing import Any
from urllib.parse import unquote

from bs4 import BeautifulSoup, Tag

from search_parser.core.models import SearchResult, SearchResults
from search_parser.parsers.base import BaseParser
from search_parser.utils import clean_text, make_soup

logger = logging.getLogger(__name__)

_TYPE_MAP: dict[int, str] = {0: "stock", 1: "index", 3: "crypto", 5: "etf"}


class GoogleFinanceParser(BaseParser):
    """Parser for Google Finance HTML pages.

    Extracts embedded ``AF_initDataCallback`` data blocks to return structured
    quote, company, chart, news, and financial-statement data.  Supports stocks,
    ETFs, indices, crypto, and FX pairs without making any network calls.
    """

    @property
    def engine_name(self) -> str:
        return "google_finance"

    def can_parse(self, soup: BeautifulSoup) -> float:
        """Detect Google Finance pages by canonical URL and embedded script markers."""
        confidence = 0.0

        canonical = soup.find("link", attrs={"rel": "canonical"})
        if isinstance(canonical, Tag) and "google.com/finance" in str(canonical.get("href", "")):
            confidence += 0.6

        script_text = " ".join(s.string or "" for s in soup.find_all("script") if s.string)
        if "AF_dataServiceRequests" in script_text:
            confidence += 0.25
        if "AF_initDataCallback" in script_text:
            confidence += 0.15

        return min(confidence, 1.0)

    def extract_query(self, soup: BeautifulSoup) -> str | None:
        """Extract the ticker symbol from the canonical URL or page title."""
        canonical = soup.find("link", attrs={"rel": "canonical"})
        if isinstance(canonical, Tag):
            m = re.search(r"/finance/quote/([^?#/]+)", str(canonical.get("href", "")))
            if m:
                return unquote(m.group(1))

        title_tag = soup.find("title")
        if isinstance(title_tag, Tag) and title_tag.string:
            m = re.match(r"^([A-Z0-9.\-]+(?::[A-Z0-9]+)?)\s*[-–]", title_tag.string.strip())
            if m:
                return m.group(1).strip()

        return None

    def parse(self, html: str) -> SearchResults:
        """Parse a Google Finance HTML page into structured results.

        Args:
            html: Raw HTML from a ``google.com/finance/quote/`` page.

        Returns:
            :class:`SearchResults` with ``stock_quote``, ``company_info``,
            ``stock_chart``, ``financial_statements``, and ``financial_news``
            fields populated where data is available.
        """
        soup = make_soup(html)
        confidence = self.can_parse(soup)
        query = self.extract_query(soup)

        script_text = "\n".join(s.string or "" for s in soup.find_all("script") if s.string)
        method_map = _extract_method_map(script_text)
        data_blocks = _extract_data_blocks(script_text)

        stock_quote: SearchResult | None = None
        company_info: SearchResult | None = None
        stock_chart: SearchResult | None = None
        financial_statements: SearchResult | None = None
        financial_news: list[SearchResult] = []
        position = 1
        seen: set[str] = set()

        for key, data in data_blocks:
            method_id = method_map.get(key)
            if not method_id or method_id in seen:
                continue
            seen.add(method_id)

            if method_id == "xh8wxf":
                result = _parse_quote(data, position, query)
                if result:
                    stock_quote = result
                    position += 1
            elif method_id == "HqGpWd":
                result = _parse_company_info(data, position)
                if result:
                    company_info = result
                    position += 1
            elif method_id == "AiCwsd":
                result = _parse_chart(data, position)
                if result:
                    stock_chart = result
                    position += 1
            elif method_id == "nBEQBc":
                items = _parse_news(data, position)
                financial_news = items
                position += len(items)
            elif method_id == "Pr8h2e":
                result = _parse_financials(data, position)
                if result:
                    financial_statements = result
                    position += 1

        return SearchResults(
            search_engine=self.engine_name,
            query=query,
            total_results=None,
            results=[],
            detection_confidence=confidence,
            stock_quote=stock_quote,
            company_info=company_info,
            stock_chart=stock_chart,
            financial_statements=financial_statements,
            financial_news=financial_news,
        )


# ---------------------------------------------------------------------------
# Module-level helpers (keep parser methods short)
# ---------------------------------------------------------------------------


def _extract_method_map(script_text: str) -> dict[str, str]:
    """Return a ``ds:N → RPC-ID`` mapping from ``AF_dataServiceRequests``."""
    method_map: dict[str, str] = {}
    m = re.search(r"AF_dataServiceRequests\s*=\s*\{([\s\S]*?)\};", script_text)
    if not m:
        return method_map
    for entry in re.finditer(r"'(ds:\d+)'\s*:\s*\{id:'([^']+)'", m.group(1)):
        method_map[entry.group(1)] = entry.group(2)
    return method_map


def _extract_data_blocks(script_text: str) -> list[tuple[str, Any]]:
    """Extract every ``AF_initDataCallback`` data blob via bracket counting."""
    results: list[tuple[str, Any]] = []
    pattern = re.compile(r"AF_initDataCallback\(\{key:\s*'(ds:\d+)',\s*hash:\s*'\d+',\s*data:")
    for m in pattern.finditer(script_text):
        raw = _extract_balanced(script_text, m.end())
        if raw is None:
            continue
        with contextlib.suppress(json.JSONDecodeError):
            results.append((m.group(1), json.loads(raw)))
    return results


def _extract_balanced(text: str, start: int) -> str | None:
    """Return the balanced JSON value (array or object) starting at *start*."""
    depth = 0
    in_str = False
    escape = False
    i = start
    while i < len(text):
        ch = text[i]
        if escape:
            escape = False
        elif ch == "\\":
            escape = True
        elif ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch in ("[", "{"):
                depth += 1
            elif ch in ("]", "}"):
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        i += 1
    return None


def _parse_quote(data: Any, position: int, query: str | None) -> SearchResult | None:
    """Build a ``stock_quote`` SearchResult from the xh8wxf data blob."""
    try:
        q: list[Any] = data[0][0][0]
    except (IndexError, TypeError):
        return None
    if not isinstance(q, list):
        return None

    is_crypto = q[3] == 3
    ticker = str(q[21] or "") if is_crypto else str((q[1] or [""])[0])
    exchange = "" if is_crypto else str((q[1] or ["", ""])[1])
    price_arr: list[float] = q[5] if isinstance(q[5], list) else []
    ah_arr: list[Any] = q[16] if len(q) > 16 and isinstance(q[16], list) else []
    after_hours = (
        {"price": ah_arr[0], "change": ah_arr[1], "change_pct": ah_arr[2]}
        if len(ah_arr) >= 3 and ah_arr[0] is not None
        else None
    )

    return SearchResult(
        title=str(q[2] or ""),
        url=f"https://www.google.com/finance/quote/{query or ticker}",
        description=f"{ticker}{(':' + exchange) if exchange else ''} — {_TYPE_MAP.get(q[3], 'other')}",
        position=position,
        result_type="stock_quote",
        metadata={
            "ticker": ticker,
            "exchange": exchange or None,
            "name": str(q[2] or ""),
            "type": _TYPE_MAP.get(q[3], "other"),
            "price": price_arr[0] if price_arr else None,
            "change": price_arr[1] if len(price_arr) > 1 else None,
            "change_pct": price_arr[2] if len(price_arr) > 2 else None,
            "previous_close": q[7] if len(q) > 7 else None,
            "currency": str(q[4] or ""),
            "timezone": str(q[12]) if len(q) > 12 and q[12] else None,
            "after_hours": after_hours,
        },
    )


def _parse_company_info(data: Any, position: int) -> SearchResult | None:
    """Build a ``company_info`` SearchResult from the HqGpWd data blob."""
    try:
        info: list[Any] = data[0][0]
    except (IndexError, TypeError):
        return None
    if not isinstance(info, list):
        return None

    description = clean_text(str(info[2])) if len(info) > 2 and info[2] else None
    if not description:
        return None

    def _get(idx: int) -> Any:
        return info[idx] if len(info) > idx else None

    hq_arr = _get(3)
    hq = ", ".join(str(x) for x in hq_arr if x) if isinstance(hq_arr, list) else None

    return SearchResult(
        title="Company Information",
        url="",
        description=description,
        position=position,
        result_type="company_info",
        metadata={
            "description": description,
            "headquarters": hq,
            "ceo": _get(5),
            "employees": _get(6),
            "market_cap": _get(7),
            "open": _get(9),
            "day_high": _get(10),
            "day_low": _get(11),
            "fifty_two_week_high": _get(12),
            "fifty_two_week_low": _get(13),
            "pe_ratio": _get(16),
            "volume": _get(18),
            "sector": _get(71),
        },
    )


def _parse_chart(data: Any, position: int) -> SearchResult | None:
    """Build a ``stock_chart`` SearchResult from the AiCwsd data blob."""
    try:
        chart_raw: list[Any] = data[0][0]
    except (IndexError, TypeError):
        return None
    if not isinstance(chart_raw, list):
        return None

    points: list[dict[str, object]] = []
    for period in chart_raw[3] if len(chart_raw) > 3 and isinstance(chart_raw[3], list) else []:
        for pt in period[1] if isinstance(period, list) and len(period) > 1 else []:
            if not (
                isinstance(pt, list)
                and len(pt) >= 2
                and isinstance(pt[0], list)
                and isinstance(pt[1], list)
            ):
                continue
            y, m, d = pt[0][0], pt[0][1], pt[0][2]
            points.append(
                {
                    "date": f"{y}-{m:02d}-{d:02d}",
                    "price": pt[1][0],
                    "volume": pt[2] if len(pt) > 2 else None,
                }
            )

    if not points:
        return None

    return SearchResult(
        title="Price Chart",
        url="",
        description=None,
        position=position,
        result_type="stock_chart",
        metadata={"previous_close": chart_raw[6] if len(chart_raw) > 6 else None, "points": points},
    )


def _parse_news(data: Any, position: int) -> list[SearchResult]:
    """Build ``financial_news`` SearchResults from the nBEQBc data blob."""
    try:
        news_arr: list[Any] = data[0]
    except (IndexError, TypeError):
        return []
    if not isinstance(news_arr, list):
        return []

    items: list[SearchResult] = []
    for i, item in enumerate(news_arr):
        if not (isinstance(item, list) and len(item) > 1 and item[1]):
            continue
        items.append(
            SearchResult(
                title=clean_text(str(item[1])),
                url=str(item[0] or ""),
                description=None,
                position=position + i,
                result_type="financial_news",
                metadata={
                    "source": item[2] if len(item) > 2 else None,
                    "timestamp": item[4] if len(item) > 4 else None,
                },
            )
        )
    return items


def _parse_financials(data: Any, position: int) -> SearchResult | None:
    """Build a ``financials`` SearchResult from the Pr8h2e data blob."""
    statements: list[dict[str, object]] = []
    _find_financial_arrays(data, statements)
    if not statements:
        return None

    return SearchResult(
        title="Financial Statements",
        url="",
        description=None,
        position=position,
        result_type="financials",
        metadata={"statements": statements},
    )


def _find_financial_arrays(data: Any, results: list[dict[str, object]]) -> None:
    """Recursively locate 39-field financial statement arrays."""
    if not isinstance(data, list):
        return
    if (
        len(data) >= 38
        and isinstance(data[0], (int, float))
        and data[0] > 1_000_000_000
        and isinstance(data[2], (int, float))
        and data[2] < 1000
    ):
        results.append(_parse_financial_row(data))
        return
    for item in data:
        _find_financial_arrays(item, results)


def _parse_financial_row(row: list[Any]) -> dict[str, object]:
    """Convert a positional financial array into a named dict."""

    def _get(idx: int) -> Any:
        return row[idx] if len(row) > idx else None

    period = _get(17)
    period_str: str | None = None
    if isinstance(period, list) and len(period) >= 3:
        period_str = f"{period[0]}-{int(period[1]):02d}-{int(period[2]):02d}"

    return {
        "revenue": _get(0),
        "net_income": _get(1),
        "eps": _get(2),
        "operating_margin": _get(3),
        "operating_income": _get(4),
        "ebitda": _get(7),
        "shares_outstanding": _get(8),
        "eps_diluted": _get(9),
        "revenue_growth_yoy": _get(11),
        "currency": _get(16),
        "period": period_str,
        "period_type": "annual"
        if isinstance(period, list) and len(period) > 1 and period[1] == 12
        else "quarterly",
        "pe_ratio": _get(18),
        "total_assets": _get(23),
        "total_liabilities": _get(24),
        "total_equity": _get(25),
        "operating_cash_flow": _get(28),
        "profit_margin": _get(33),
        "free_cash_flow": _get(36),
        "capital_expenditure": _get(38),
    }
