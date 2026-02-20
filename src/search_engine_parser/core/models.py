"""Pydantic data models for search results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Single search result item."""

    title: str
    url: str
    description: str | None = None
    position: int
    result_type: Literal["organic", "featured_snippet", "knowledge_panel", "news", "image"] = (
        "organic"
    )
    metadata: dict[str, object] = Field(default_factory=dict)


class SearchResults(BaseModel):
    """Collection of search results from a page."""

    search_engine: str
    query: str | None = None
    total_results: int | None = None
    results: list[SearchResult]
    detection_confidence: float = Field(ge=0.0, le=1.0)
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, object] = Field(default_factory=dict)
