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
        "job",
        "discussion",
        "shopping_ad",
        "stock_quote",
        "company_info",
        "stock_chart",
        "financials",
        "financial_news",
        "local_business",
    ] = "organic"
    # Engine- and result-specific rich fields (for example ratings or sitelinks).
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
    jobs: list[SearchResult] = Field(default_factory=list)
    discussions: list[SearchResult] = Field(default_factory=list)
    shopping_ads: list[SearchResult] = Field(default_factory=list)
    news: list[SearchResult] = Field(default_factory=list)
    local_businesses: list[SearchResult] = Field(default_factory=list)

    # Google Finance dedicated fields
    stock_quote: Optional[SearchResult] = None  # noqa: UP045
    company_info: Optional[SearchResult] = None  # noqa: UP045
    stock_chart: Optional[SearchResult] = None  # noqa: UP045
    financial_statements: Optional[SearchResult] = None  # noqa: UP045
    financial_news: list[SearchResult] = Field(default_factory=list)

    detection_confidence: float = Field(ge=0.0, le=1.0)
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Page-level fields (for example search location or pagination links).
    metadata: dict[str, object] = Field(default_factory=dict)

    def to_json(self, indent: int = 2) -> str:
        """Serialize results to a JSON string.

        Args:
            indent: Number of spaces for indentation (default 2).

        Returns:
            JSON string representation of all fields.
        """
        import json  # noqa: PLC0415

        return json.dumps(self.model_dump(mode="json"), indent=indent, ensure_ascii=False)

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


class GoogleMapsPlace(BaseModel):
    """One place decoded from Google Maps' structured search response."""

    position: int
    name: str
    data_id: str
    place_id: Optional[str] = None  # noqa: UP045
    google_maps_url: Optional[str] = None  # noqa: UP045
    website: Optional[str] = None  # noqa: UP045
    domain: Optional[str] = None  # noqa: UP045
    address: Optional[str] = None  # noqa: UP045
    address_lines: list[str] = Field(default_factory=list)
    district: Optional[str] = None  # noqa: UP045
    latitude: float
    longitude: float
    rating: Optional[float] = None  # noqa: UP045
    review_count: Optional[int] = None  # noqa: UP045
    review_url: Optional[str] = None  # noqa: UP045
    categories: list[str] = Field(default_factory=list)
    category_ids: list[str] = Field(default_factory=list)
    phone: Optional[str] = None  # noqa: UP045
    phone_e164: Optional[str] = None  # noqa: UP045
    timezone: Optional[str] = None  # noqa: UP045
    thumbnail: Optional[str] = None  # noqa: UP045
    opening_hours: dict[str, str] = Field(default_factory=dict)


class GoogleMapsResults(BaseModel):
    """Structured Google Maps places returned for one query."""

    search_engine: Literal["google_maps"] = "google_maps"
    query: Optional[str] = None  # noqa: UP045
    places: list[GoogleMapsPlace] = Field(default_factory=list)
    result_count: int = 0
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, object] = Field(default_factory=dict)

    def to_json(self, indent: int = 2) -> str:
        """Serialize the Maps result set to JSON."""
        import json  # noqa: PLC0415

        return json.dumps(self.model_dump(mode="json"), indent=indent, ensure_ascii=False)
