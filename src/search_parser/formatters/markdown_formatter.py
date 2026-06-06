"""Markdown output formatter for LLM-friendly consumption."""

from __future__ import annotations

from search_parser.__version__ import __version__
from search_parser.core.models import SearchResult, SearchResults
from search_parser.formatters.base import BaseFormatter


class MarkdownFormatter(BaseFormatter):
    """Formats search results as Markdown text.

    Produces a clean, hierarchical Markdown document suitable for
    both human reading and LLM consumption.
    """

    def format(self, results: SearchResults) -> str:
        """Format search results as Markdown.

        Args:
            results: Parsed search results.

        Returns:
            Markdown string.
        """
        lines: list[str] = []

        # Header
        title = f"Search Results: {results.query}" if results.query else "Search Results"
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"**Search Engine:** {results.search_engine.title()}")

        if results.total_results is not None:
            lines.append(f"**Total Results:** ~{results.total_results:,}")

        parsed_time = results.parsed_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"**Parsed:** {parsed_time}")
        lines.append("")
        lines.append("---")
        lines.append("")

        if results.featured_snippet:
            lines.append("## Featured Snippet")
            lines.append("")
            lines.extend(self._format_featured(results.featured_snippet))
            lines.append("---")
            lines.append("")

        knowledge = [r for r in results.results if r.result_type == "knowledge_panel"]
        if knowledge:
            lines.append("## Knowledge Panel")
            lines.append("")
            for result in knowledge:
                lines.extend(self._format_result(result))
            lines.append("---")
            lines.append("")

        organic = [r for r in results.results if r.result_type == "organic"]
        if organic:
            lines.append("## Organic Results")
            lines.append("")
            for result in organic:
                lines.extend(self._format_organic(result))

        if results.news:
            lines.append("## News Results")
            lines.append("")
            for result in results.news:
                lines.extend(self._format_news(result))

        if results.jobs:
            lines.append("## Jobs")
            lines.append("")
            for result in results.jobs:
                lines.extend(self._format_job(result))

        if results.local_businesses:
            lines.append("## Local Businesses")
            lines.append("")
            for result in results.local_businesses:
                lines.extend(self._format_local_business(result))

        if results.discussions:
            lines.append("## Discussions and Forums")
            lines.append("")
            for result in results.discussions:
                lines.extend(self._format_result(result))

        if results.shopping_ads:
            lines.append("## Shopping Ads")
            lines.append("")
            for result in results.shopping_ads:
                lines.extend(self._format_shopping_ad(result))

        lines.append("---")
        lines.append("")
        lines.append(f"*Parsed with search-engine-parser v{__version__}*")
        lines.append("")

        return "\n".join(lines)

    def _format_featured(self, result: SearchResult) -> list[str]:
        """Format a featured snippet result."""
        lines: list[str] = []
        lines.append(f"### {result.title}")
        lines.append("")
        if result.description:
            lines.append(result.description)
            lines.append("")
        # Extract domain from URL for source
        lines.append(f"**Source:** [{result.url}]({result.url})")
        lines.append("")
        return lines

    def _format_organic(self, result: SearchResult) -> list[str]:
        """Format an organic search result."""
        lines: list[str] = []
        lines.append(f"### {result.position}. {result.title}")
        lines.append("")
        if result.description:
            lines.append(result.description)
            lines.append("")
        lines.append(f"**URL:** {result.url}")
        lines.append("")
        return lines

    def _format_job(self, result: SearchResult) -> list[str]:
        """Format a job listing result."""
        lines: list[str] = []
        lines.append(f"### {result.title}")
        lines.append("")
        if result.metadata.get("company"):
            lines.append(f"**Company:** {result.metadata['company']}")
        if result.metadata.get("location"):
            lines.append(f"**Location:** {result.metadata['location']}")
        if result.metadata.get("salary"):
            lines.append(f"**Salary:** {result.metadata['salary']}")
        if result.metadata.get("employment_type"):
            lines.append(f"**Type:** {result.metadata['employment_type']}")
        if result.url:
            lines.append(f"**URL:** {result.url}")
        lines.append("")
        return lines

    def _format_shopping_ad(self, result: SearchResult) -> list[str]:
        """Format a shopping ad card."""
        lines: list[str] = []
        lines.append(f"### {result.title}")
        lines.append("")
        if result.metadata.get("price"):
            lines.append(f"**Price:** {result.metadata['price']}")
        if result.metadata.get("merchant"):
            lines.append(f"**Merchant:** {result.metadata['merchant']}")
        if result.url:
            lines.append(f"**URL:** {result.url}")
        lines.append("")
        return lines

    def _format_news(self, result: SearchResult) -> list[str]:
        """Format a news article result."""
        lines: list[str] = []
        lines.append(f"### {result.position}. {result.title}")
        lines.append("")
        if result.metadata.get("source"):
            meta = str(result.metadata["source"])
            if result.metadata.get("published_time"):
                meta += f" · {result.metadata['published_time']}"
            lines.append(f"**Source:** {meta}")
            lines.append("")
        if result.description:
            lines.append(result.description)
            lines.append("")
        lines.append(f"**URL:** {result.url}")
        lines.append("")
        return lines

    def _format_local_business(self, result: SearchResult) -> list[str]:
        """Format a local business pack result."""
        lines: list[str] = []
        sponsored = " (Sponsored)" if result.metadata.get("sponsored") else ""
        lines.append(f"### {result.title}{sponsored}")
        lines.append("")
        if result.metadata.get("rating"):
            rating_str = f"**Rating:** {result.metadata['rating']}"
            if result.metadata.get("reviews"):
                rating_str += f" ({result.metadata['reviews']} reviews)"
            lines.append(rating_str)
        if result.metadata.get("category"):
            lines.append(f"**Category:** {result.metadata['category']}")
        if result.metadata.get("location"):
            lines.append(f"**Location:** {result.metadata['location']}")
        if result.metadata.get("hours"):
            lines.append(f"**Hours:** {result.metadata['hours']}")
        if result.metadata.get("phone"):
            lines.append(f"**Phone:** {result.metadata['phone']}")
        lines.append("")
        return lines

    def _format_result(self, result: SearchResult) -> list[str]:
        """Format a generic result."""
        lines: list[str] = []
        lines.append(f"### {result.title}")
        lines.append("")
        if result.description:
            lines.append(result.description)
            lines.append("")
        lines.append(f"**URL:** {result.url}")
        lines.append("")
        return lines
