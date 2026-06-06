"""Web scrapers that fetch live data from supported platforms."""

from search_parser.scrapers.google_finance import (
    ChartData,
    ChartPoint,
    CompanyInfo,
    FinancialQuote,
    FinancialStatement,
    GoogleFinanceData,
    GoogleFinanceScraper,
    NewsItem,
)

__all__ = [
    "GoogleFinanceScraper",
    "GoogleFinanceData",
    "FinancialQuote",
    "CompanyInfo",
    "ChartData",
    "ChartPoint",
    "NewsItem",
    "FinancialStatement",
]
