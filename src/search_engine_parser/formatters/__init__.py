"""Output formatters for search results."""

from search_engine_parser.formatters.base import BaseFormatter
from search_engine_parser.formatters.json_formatter import JSONFormatter
from search_engine_parser.formatters.markdown_formatter import MarkdownFormatter

__all__ = [
    "BaseFormatter",
    "JSONFormatter",
    "MarkdownFormatter",
]
