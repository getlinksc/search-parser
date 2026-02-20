"""JSON output formatter."""

from __future__ import annotations

from search_engine_parser.core.models import SearchResults
from search_engine_parser.formatters.base import BaseFormatter


class JSONFormatter(BaseFormatter):
    """Formats search results as a JSON string using Pydantic serialization."""

    def format(self, results: SearchResults) -> str:
        """Format search results as a JSON string.

        Args:
            results: Parsed search results.

        Returns:
            JSON string representation.
        """
        return results.model_dump_json(indent=2)
