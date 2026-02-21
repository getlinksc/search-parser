"""Utility functions for search engine parser."""

from __future__ import annotations

import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def make_soup(html: str) -> BeautifulSoup:
    """Parse HTML string into a BeautifulSoup object.

    Args:
        html: Raw HTML string to parse.

    Returns:
        Parsed BeautifulSoup object.
    """
    return BeautifulSoup(html, "lxml")


def clean_text(text: str | None) -> str:
    """Clean and normalize text extracted from HTML.

    Args:
        text: Raw text that may contain extra whitespace.

    Returns:
        Cleaned text with normalized whitespace.
    """
    if not text:
        return ""
    return " ".join(text.split()).strip()
