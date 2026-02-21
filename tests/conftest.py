"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def google_organic_html() -> str:
    return (FIXTURES_DIR / "google" / "organic_results.html").read_text()


@pytest.fixture()
def google_featured_html() -> str:
    return (FIXTURES_DIR / "google" / "featured_snippet.html").read_text()


@pytest.fixture()
def google_knowledge_html() -> str:
    return (FIXTURES_DIR / "google" / "knowledge_panel.html").read_text()


@pytest.fixture()
def bing_organic_html() -> str:
    return (FIXTURES_DIR / "bing" / "organic_results.html").read_text()


@pytest.fixture()
def bing_github_repos_html() -> str:
    return (FIXTURES_DIR / "bing" / "search_github_repos.html").read_text()


@pytest.fixture()
def google_github_repos_html() -> str:
    return (FIXTURES_DIR / "google" / "search_github_repos.html").read_text()


@pytest.fixture()
def google_scheduling_app_html() -> str:
    return (FIXTURES_DIR / "google" / "search_best_employee_scheduling_app.html").read_text()


@pytest.fixture()
def duckduckgo_organic_html() -> str:
    return (FIXTURES_DIR / "duckduckgo" / "organic_results.html").read_text()


@pytest.fixture()
def google_need_javascript_html() -> str:
    return (FIXTURES_DIR / "google" / "need_turn_on_javascript.html").read_text()


@pytest.fixture()
def duckduckgo_github_repos_html() -> str:
    return (FIXTURES_DIR / "duckduckgo" / "search_github_repos.html").read_text()


@pytest.fixture()
def google_web_scraping_html() -> str:
    return (FIXTURES_DIR / "google" / "search_python_web_scraping.html").read_text()
