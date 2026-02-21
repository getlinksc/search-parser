"""Search engine parser implementations."""

from search_parser.parsers.base import BaseParser
from search_parser.parsers.bing import BingParser
from search_parser.parsers.duckduckgo import DuckDuckGoParser
from search_parser.parsers.google import GoogleParser

# Registry of all available parsers
PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    "google": GoogleParser,
    "bing": BingParser,
    "duckduckgo": DuckDuckGoParser,
}

__all__ = [
    "BaseParser",
    "BingParser",
    "DuckDuckGoParser",
    "GoogleParser",
    "PARSER_REGISTRY",
]
