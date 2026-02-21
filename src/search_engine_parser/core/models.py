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
    """Collection of search results from a page."""

    search_engine: str
    query: Optional[str] = None  # noqa: UP045
    total_results: Optional[int] = None  # noqa: UP045
    results: list[SearchResult]
    detection_confidence: float = Field(ge=0.0, le=1.0)
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, object] = Field(default_factory=dict)
