"""Search Engine Parser - Parse search engine HTML results into structured data."""

from search_parser.__version__ import __version__
from search_parser.core.models import SearchResult, SearchResults
from search_parser.core.parser import SearchParser

__all__ = [
    "__version__",
    "SearchParser",
    "SearchResult",
    "SearchResults",
]
