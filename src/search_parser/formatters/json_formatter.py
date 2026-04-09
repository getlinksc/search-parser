"""JSON output formatter."""

from __future__ import annotations

import json

from search_parser.core.models import SearchResults
from search_parser.formatters.base import BaseFormatter


class JSONFormatter(BaseFormatter):
    """Formats search results as a JSON string using Pydantic serialization."""

    def format(self, results: SearchResults) -> str:
        """Format search results as a JSON string.

        Args:
            results: Parsed search results.

        Returns:
            JSON string representation.
        """
        return json.dumps(results.model_dump(mode="json"), indent=2, ensure_ascii=False)
