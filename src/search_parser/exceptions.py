"""Custom exceptions for search engine parser."""


class SearchEngineParserError(Exception):
    """Base exception for search engine parser."""


class SearchEngineDetectionError(SearchEngineParserError):
    """Cannot determine which search engine the HTML came from."""


class ParserNotFoundError(SearchEngineParserError):
    """No parser available for the detected or specified search engine."""


class ParseError(SearchEngineParserError):
    """Failed to parse the HTML content."""


class InvalidHTMLError(SearchEngineParserError):
    """The HTML structure is invalid or cannot be processed."""
