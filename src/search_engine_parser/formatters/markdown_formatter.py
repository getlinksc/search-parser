"""Markdown output formatter for LLM-friendly consumption."""

from __future__ import annotations

from search_engine_parser.__version__ import __version__
from search_engine_parser.core.models import SearchResult, SearchResults
from search_engine_parser.formatters.base import BaseFormatter


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

        # Group results by type
        featured = [r for r in results.results if r.result_type == "featured_snippet"]
        organic = [r for r in results.results if r.result_type == "organic"]
        knowledge = [r for r in results.results if r.result_type == "knowledge_panel"]
        news = [r for r in results.results if r.result_type == "news"]

        if featured:
            lines.append("## Featured Snippet")
            lines.append("")
            for result in featured:
                lines.extend(self._format_featured(result))
            lines.append("---")
            lines.append("")

        if knowledge:
            lines.append("## Knowledge Panel")
            lines.append("")
            for result in knowledge:
                lines.extend(self._format_result(result))
            lines.append("---")
            lines.append("")

        if organic:
            lines.append("## Organic Results")
            lines.append("")
            for result in organic:
                lines.extend(self._format_organic(result))

        if news:
            lines.append("## News Results")
            lines.append("")
            for result in news:
                lines.extend(self._format_result(result))

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
