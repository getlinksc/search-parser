"""Pydantic data models for search results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Single search result item."""

    title: str
    url: str
    description: Optional[str] = None  # noqa: UP045 - Pydantic evaluates at runtime; breaks on 3.9
    position: int
    result_type: Literal[
        "organic",
        "featured_snippet",
        "knowledge_panel",
        "news",
        "image",
        "sponsored",
        "ai_overview",
        "people_also_ask",
        "people_saying",
        "people_also_search",
        "related_products",
    ] = "organic"
    metadata: dict[str, object] = Field(default_factory=dict)


class SearchResults(BaseModel):
    """Collection of search results from a page.

    Organic results are in ``results``.  All other result types have their
    own dedicated field so callers never have to filter by ``result_type``.
    """

    search_engine: str
    query: Optional[str] = None  # noqa: UP045
    total_results: Optional[int] = None  # noqa: UP045

    # Organic results only
    results: list[SearchResult]

    # Dedicated fields for every other result type
    sponsored: list[SearchResult] = Field(default_factory=list)
    featured_snippet: Optional[SearchResult] = None  # noqa: UP045
    ai_overview: Optional[SearchResult] = None  # noqa: UP045
    people_also_ask: list[SearchResult] = Field(default_factory=list)
    people_saying: list[SearchResult] = Field(default_factory=list)
    people_also_search: list[SearchResult] = Field(default_factory=list)
    related_products: list[SearchResult] = Field(default_factory=list)

    detection_confidence: float = Field(ge=0.0, le=1.0)
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, object] = Field(default_factory=dict)

    def to_json(self, indent: int = 2) -> str:
        """Serialize results to a JSON string.

        Args:
            indent: Number of spaces for indentation (default 2).

        Returns:
            JSON string representation of all fields.
        """
        return self.model_dump_json(indent=indent)

    def to_markdown(self) -> str:
        """Render results as a Markdown string suitable for human or LLM consumption.

        Returns:
            Markdown string with sections for each result type present.
        """
        # Deferred import avoids a circular dependency (MarkdownFormatter imports models).
        from search_parser.formatters.markdown_formatter import (
            MarkdownFormatter,  # noqa: PLC0415
        )

        return MarkdownFormatter().format(self)
