"""Search Engine Parser - Parse search engine HTML results into structured data."""

from search_parser.__version__ import __version__
from search_parser.core.models import SearchResult, SearchResults
from search_parser.core.parser import SearchParser
from search_parser.parsers.google_finance import GoogleFinanceParser
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
    "__version__",
    "SearchParser",
    "SearchResult",
    "SearchResults",
    "GoogleFinanceParser",
    "GoogleFinanceScraper",
    "GoogleFinanceData",
    "FinancialQuote",
    "CompanyInfo",
    "ChartData",
    "ChartPoint",
    "NewsItem",
    "FinancialStatement",
]
