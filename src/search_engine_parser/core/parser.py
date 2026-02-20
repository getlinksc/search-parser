"""Main SearchParser class - the primary public API."""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from search_engine_parser.core.detector import SearchEngineDetector
from search_engine_parser.core.models import SearchResults
from search_engine_parser.exceptions import (
    ParseError,
    ParserNotFoundError,
    SearchEngineDetectionError,
)
from search_engine_parser.formatters.json_formatter import JSONFormatter
from search_engine_parser.formatters.markdown_formatter import MarkdownFormatter
from search_engine_parser.parsers import PARSER_REGISTRY
from search_engine_parser.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class SearchParser:
    """Main entry point for parsing search engine HTML.

    Automatically detects the search engine and parses results
    into structured data in the requested format.

    Example:
        >>> parser = SearchParser()
        >>> json_output = parser.parse(html_string)
        >>> markdown_output = parser.parse(html_string, output_format="markdown")
        >>> dict_output = parser.parse(html_string, output_format="dict")
    """

    def __init__(self) -> None:
        self._detector = SearchEngineDetector()
        self._json_formatter = JSONFormatter()
        self._markdown_formatter = MarkdownFormatter()
        self._parsers: dict[str, BaseParser] = {
            name: cls() for name, cls in PARSER_REGISTRY.items()
        }

    def parse(
        self,
        html: str,
        engine: str | None = None,
        output_format: Literal["json", "markdown", "dict"] = "json",
    ) -> str | dict[str, Any]:
        """Parse search engine HTML and return results.

        Args:
            html: HTML string to parse.
            engine: Optionally specify engine ("google", "bing", "duckduckgo").
                If None, will auto-detect.
            output_format: Output format - "json" (default), "markdown", or "dict".
                - "json": Returns JSON string
                - "markdown": Returns Markdown string
                - "dict": Returns Python dictionary

        Returns:
            JSON string, Markdown string, or Python dictionary depending
            on output_format.

        Raises:
            SearchEngineDetectionError: If engine cannot be detected and not specified.
            ParserNotFoundError: If no parser available for the detected/specified engine.
            ParseError: If parsing fails.
        """
        # Determine which engine to use
        engine_name = self._resolve_engine(html, engine)

        # Get the parser
        parser = self._parsers.get(engine_name)
        if not parser:
            raise ParserNotFoundError(
                f"No parser available for engine: {engine_name!r}. "
                f"Available parsers: {list(self._parsers.keys())}"
            )

        # Parse the HTML
        try:
            results = parser.parse(html)
        except Exception as e:
            raise ParseError(f"Failed to parse HTML: {e}") from e

        # Format the output
        return self._format_output(results, output_format)

    def _resolve_engine(self, html: str, engine: str | None) -> str:
        """Resolve the search engine name, either from user input or auto-detection."""
        if engine:
            return engine.lower()

        detection = self._detector.detect(html)
        if not detection:
            raise SearchEngineDetectionError(
                "Could not detect the search engine. "
                "Please specify the engine manually using the 'engine' parameter."
            )

        logger.info(
            "Detected engine: %s (confidence: %.2f)",
            detection.engine,
            detection.confidence,
        )
        return detection.engine

    def _format_output(
        self,
        results: SearchResults,
        output_format: Literal["json", "markdown", "dict"],
    ) -> str | dict[str, Any]:
        """Format results into the requested output format."""
        if output_format == "json":
            return self._json_formatter.format(results)
        elif output_format == "markdown":
            return self._markdown_formatter.format(results)
        elif output_format == "dict":
            result: dict[str, Any] = json.loads(results.model_dump_json())
            return result
        else:
            raise ValueError(f"Unknown output format: {output_format!r}")
