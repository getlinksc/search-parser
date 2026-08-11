"""Google Finance live data scraper using the internal batchexecute RPC endpoint."""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_BATCHEXECUTE_URL = "https://www.google.com/finance/_/GoogleFinanceUi/data/batchexecute"

_DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
    "Cookie": "CONSENT=YES+",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
}

_TYPE_MAP: dict[int, str] = {0: "stock", 1: "index", 3: "crypto", 5: "etf"}


@dataclass
class FinancialQuote:
    """Real-time price quote for any Google Finance instrument."""

    ticker: str
    exchange: str
    name: str
    type: str  # "stock" | "etf" | "index" | "crypto" | "other"
    price: float
    change: float
    change_pct: float
    previous_close: float
    currency: str
    timezone: str | None = None
    after_hours: dict[str, float] | None = None


@dataclass
class CompanyInfo:
    """Company fundamentals returned by the HqGpWd RPC method."""

    description: str | None = None
    headquarters: str | None = None
    ceo: str | None = None
    employees: int | None = None
    market_cap: float | None = None
    open: float | None = None
    day_high: float | None = None
    day_low: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    pe_ratio: float | None = None
    volume: int | None = None
    sector: str | None = None


@dataclass
class ChartPoint:
    """A single date/price/volume data point from the price chart."""

    date: str  # YYYY-MM-DD
    price: float
    volume: int | None = None


@dataclass
class ChartData:
    """Historical price chart returned by the AiCwsd RPC method."""

    previous_close: float | None
    points: list[ChartPoint] = field(default_factory=list)


@dataclass
class NewsItem:
    """A news article returned by the nBEQBc RPC method."""

    url: str
    title: str
    source: str | None = None
    timestamp: int | None = None  # Unix timestamp


@dataclass
class FinancialStatement:
    """One period of financial data returned by the Pr8h2e RPC method."""

    revenue: float | None = None
    net_income: float | None = None
    eps: float | None = None
    operating_margin: float | None = None
    operating_income: float | None = None
    ebitda: float | None = None
    shares_outstanding: float | None = None
    eps_diluted: float | None = None
    revenue_growth_yoy: float | None = None
    currency: str | None = None
    period: str | None = None  # YYYY-MM-DD of fiscal period end
    period_type: str = "quarterly"  # "annual" | "quarterly"
    pe_ratio: float | None = None
    total_assets: float | None = None
    total_liabilities: float | None = None
    total_equity: float | None = None
    operating_cash_flow: float | None = None
    profit_margin: float | None = None
    free_cash_flow: float | None = None
    capital_expenditure: float | None = None


@dataclass
class GoogleFinanceData:
    """All data fetched for a single ticker in one batched RPC call."""

    quote: FinancialQuote
    company: CompanyInfo | None = None
    chart: ChartData | None = None
    news: list[NewsItem] = field(default_factory=list)
    financials: list[FinancialStatement] = field(default_factory=list)


class GoogleFinanceScraper:
    """Fetches live data from Google Finance's internal ``batchexecute`` endpoint.

    No API key required.  Works for any instrument Google Finance supports:
    stocks (``GOOGL:NASDAQ``), ETFs (``SPY:NYSEARCA``), indices
    (``.DJI:INDEXDJX``), crypto (``BTC-USD``), and FX pairs (``EUR-USD``).

    Example::

        scraper = GoogleFinanceScraper()
        data = scraper.scrape("GOOGL:NASDAQ")
        print(data.quote.price, data.company.ceo)
    """

    def __init__(self, extra_headers: dict[str, str] | None = None) -> None:
        self._headers: dict[str, str] = {**_DEFAULT_HEADERS, **(extra_headers or {})}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape(self, ticker: str) -> GoogleFinanceData:
        """Fetch and parse all available data for *ticker*.

        Args:
            ticker: Instrument identifier — ``SYMBOL:EXCHANGE`` for
                stocks/ETFs/indices, ``BASE-QUOTE`` for crypto/FX.

        Returns:
            :class:`GoogleFinanceData` populated where data is available.

        Raises:
            urllib.error.HTTPError: On non-2xx HTTP responses.
            ValueError: If the response contains no quote data for *ticker*.
        """
        t = _ticker_tuple(ticker)
        is_crypto = "-" in ticker and ":" not in ticker

        requests = [
            {"id": "xh8wxf", "req": [[t], 1]},
            {"id": "HqGpWd", "req": [[t]]},
            {"id": "Pr8h2e", "req": [[t]]},
            {"id": "AiCwsd", "req": [[t], 3]},
            {"id": "nBEQBc", "req": [6 if is_crypto else 5, 3, [t]]},
        ]
        rpc_ids = ",".join(dict.fromkeys(r["id"] for r in requests))
        url = f"{_BATCHEXECUTE_URL}?rpcids={rpc_ids}&source-path=/finance/quote/{ticker}&hl=en&gl=us&rt=c"

        chunks = self._post(url, _build_body(requests))

        def get(rpc_id: str) -> Any:
            return next((c["data"] for c in chunks if c["id"] == rpc_id), None)

        if get("xh8wxf") is None:
            raise ValueError(f"No data returned for {ticker!r}")

        return GoogleFinanceData(
            quote=_extract_quote(get("xh8wxf"), ticker, is_crypto),
            company=_extract_company(get("HqGpWd")),
            chart=_extract_chart(get("AiCwsd")),
            news=_extract_news(get("nBEQBc")),
            financials=_extract_financials(get("Pr8h2e")),
        )

    def _post(self, url: str, body: bytes) -> list[dict[str, Any]]:
        req = urllib.request.Request(url, data=body, headers=self._headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
        return _parse_rpc_response(raw)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _ticker_tuple(ticker: str) -> list[Any]:
    """Convert a ticker string to a Google Finance positional tuple."""
    if "-" in ticker and ":" not in ticker:
        base, _, quote = ticker.partition("-")
        return [None, None, [base, quote]]
    sym, _, exchange = ticker.partition(":")
    return [None, [sym, exchange]]


def _build_body(requests: list[dict[str, Any]]) -> bytes:
    arr = [[r["id"], json.dumps(r["req"]), None, str(i + 1)] for i, r in enumerate(requests)]
    return f"f.req={urllib.parse.quote(json.dumps([arr]))}".encode()


def _parse_rpc_response(raw: str) -> list[dict[str, Any]]:
    """Decode the ``)]}'`` prefixed chunked RPC response format."""
    stripped = re.sub(r"^\)\]\}'\n\n?", "", raw)
    results: list[dict[str, Any]] = []
    lines = stripped.split("\n")
    i = 0
    while i < len(lines):
        if re.fullmatch(r"[0-9a-fA-F]+", lines[i].strip()) and i + 1 < len(lines):
            try:
                for entry in json.loads(lines[i + 1]):
                    if entry[0] == "wrb.fr":
                        results.append({"id": entry[1], "data": json.loads(entry[2])})
            except (json.JSONDecodeError, IndexError, KeyError):
                pass
            i += 2
        else:
            i += 1
    return results


def _extract_quote(data: Any, ticker: str, is_crypto: bool) -> FinancialQuote:
    try:
        q: list[Any] = data[0][0][0]
    except (IndexError, TypeError) as exc:
        raise ValueError(f"Unexpected quote structure for {ticker!r}") from exc

    price_arr: list[float] = q[5] if isinstance(q[5], list) else []
    ah_arr: list[Any] = q[16] if len(q) > 16 and isinstance(q[16], list) else []
    after_hours = (
        {"price": ah_arr[0], "change": ah_arr[1], "change_pct": ah_arr[2]}
        if len(ah_arr) >= 3 and ah_arr[0] is not None
        else None
    )

    return FinancialQuote(
        ticker=str(q[21] or "") if is_crypto else str((q[1] or [""])[0]),
        exchange="" if is_crypto else str((q[1] or ["", ""])[1]),
        name=str(q[2] or ""),
        type=_TYPE_MAP.get(q[3], "other"),
        price=price_arr[0] if price_arr else 0.0,
        change=price_arr[1] if len(price_arr) > 1 else 0.0,
        change_pct=price_arr[2] if len(price_arr) > 2 else 0.0,
        previous_close=q[7] if len(q) > 7 else 0.0,
        currency=str(q[4] or ""),
        timezone=str(q[12]) if len(q) > 12 and q[12] else None,
        after_hours=after_hours,
    )


def _extract_company(data: Any) -> CompanyInfo | None:
    try:
        info: list[Any] = data[0][0]
    except (IndexError, TypeError):
        return None
    if not isinstance(info, list):
        return None

    def _get(idx: int) -> Any:
        return info[idx] if len(info) > idx else None

    hq_arr = _get(3)
    hq = ", ".join(str(x) for x in hq_arr if x) if isinstance(hq_arr, list) else None

    return CompanyInfo(
        description=str(_get(2)) if _get(2) else None,
        headquarters=hq,
        ceo=str(_get(5)) if _get(5) else None,
        employees=int(_get(6)) if _get(6) else None,
        market_cap=float(_get(7)) if _get(7) else None,
        open=float(_get(9)) if _get(9) else None,
        day_high=float(_get(10)) if _get(10) else None,
        day_low=float(_get(11)) if _get(11) else None,
        fifty_two_week_high=float(_get(12)) if _get(12) else None,
        fifty_two_week_low=float(_get(13)) if _get(13) else None,
        pe_ratio=float(_get(16)) if _get(16) else None,
        volume=int(_get(18)) if _get(18) else None,
        sector=str(_get(71)) if _get(71) else None,
    )


def _extract_chart(data: Any) -> ChartData | None:
    try:
        chart_raw: list[Any] = data[0][0]
    except (IndexError, TypeError):
        return None
    if not isinstance(chart_raw, list):
        return None

    points: list[ChartPoint] = []
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
                ChartPoint(
                    date=f"{y}-{m:02d}-{d:02d}",
                    price=pt[1][0],
                    volume=pt[2] if len(pt) > 2 else None,
                )
            )

    return ChartData(previous_close=chart_raw[6] if len(chart_raw) > 6 else None, points=points)


def _extract_news(data: Any) -> list[NewsItem]:
    try:
        news_arr: list[Any] = data[0]
    except (IndexError, TypeError):
        return []
    if not isinstance(news_arr, list):
        return []

    items: list[NewsItem] = []
    for item in news_arr:
        if not (isinstance(item, list) and len(item) > 1 and item[1]):
            continue
        items.append(
            NewsItem(
                url=str(item[0] or ""),
                title=str(item[1] or ""),
                source=str(item[2]) if len(item) > 2 and item[2] else None,
                timestamp=int(item[4]) if len(item) > 4 and item[4] else None,
            )
        )
    return items


def _extract_financials(data: Any) -> list[FinancialStatement]:
    rows: list[Any] = []
    _find_financial_arrays(data, rows)
    return [_row_to_statement(r) for r in rows]


def _find_financial_arrays(data: Any, results: list[Any]) -> None:
    if not isinstance(data, list):
        return
    if (
        len(data) >= 38
        and isinstance(data[0], (int, float))
        and data[0] > 1_000_000_000
        and isinstance(data[2], (int, float))
        and data[2] < 1000
    ):
        results.append(data)
        return
    for item in data:
        _find_financial_arrays(item, results)


def _row_to_statement(row: list[Any]) -> FinancialStatement:
    def _get(idx: int) -> Any:
        return row[idx] if len(row) > idx else None

    period = _get(17)
    period_str: str | None = None
    if isinstance(period, list) and len(period) >= 3:
        period_str = f"{period[0]}-{int(period[1]):02d}-{int(period[2]):02d}"

    return FinancialStatement(
        revenue=_get(0),
        net_income=_get(1),
        eps=_get(2),
        operating_margin=_get(3),
        operating_income=_get(4),
        ebitda=_get(7),
        shares_outstanding=_get(8),
        eps_diluted=_get(9),
        revenue_growth_yoy=_get(11),
        currency=_get(16),
        period=period_str,
        period_type="annual"
        if isinstance(period, list) and len(period) > 1 and period[1] == 12
        else "quarterly",
        pe_ratio=_get(18),
        total_assets=_get(23),
        total_liabilities=_get(24),
        total_equity=_get(25),
        operating_cash_flow=_get(28),
        profit_margin=_get(33),
        free_cash_flow=_get(36),
        capital_expenditure=_get(38),
    )
