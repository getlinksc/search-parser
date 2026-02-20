"""Abstract base class for output formatters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from search_engine_parser.core.models import SearchResults


class BaseFormatter(ABC):
    """Abstract base class for output formatters.

    Subclass this to create custom output formats.
    """

    @abstractmethod
    def format(self, results: SearchResults) -> Any:
        """Format search results into the desired output.

        Args:
            results: Parsed search results to format.

        Returns:
            Formatted output (type depends on implementation).
        """
        ...
