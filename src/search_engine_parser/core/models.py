"""Pydantic data models for search results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Single search result item."""

    title: str
    url: str
    description: Optional[str] = None
    position: int
    result_type: Literal["organic", "featured_snippet", "knowledge_panel", "news", "image"] = (
        "organic"
    )
    metadata: Dict[str, object] = Field(default_factory=dict)


class SearchResults(BaseModel):
    """Collection of search results from a page."""

    search_engine: str
    query: Optional[str] = None
    total_results: Optional[int] = None
    results: List[SearchResult]
    detection_confidence: float = Field(ge=0.0, le=1.0)
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, object] = Field(default_factory=dict)
