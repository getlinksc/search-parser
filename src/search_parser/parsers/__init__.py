"""Search engine parser implementations."""

from search_parser.parsers.base import BaseParser
from search_parser.parsers.bing import BingParser
from search_parser.parsers.duckduckgo import DuckDuckGoParser
from search_parser.parsers.ebay import EbayParser
from search_parser.parsers.google import GoogleParser
from search_parser.parsers.google_finance import GoogleFinanceParser
from search_parser.parsers.google_maps import GoogleMapsParser

# Registry of all available parsers
PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    "google": GoogleParser,
    "bing": BingParser,
    "duckduckgo": DuckDuckGoParser,
    "google_finance": GoogleFinanceParser,
    "ebay": EbayParser,
}

__all__ = [
    "BaseParser",
    "BingParser",
    "DuckDuckGoParser",
    "EbayParser",
    "GoogleParser",
    "GoogleFinanceParser",
    "GoogleMapsParser",
    "PARSER_REGISTRY",
]
