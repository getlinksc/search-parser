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


@pytest.fixture()
def google_supply_chain_jobs_html() -> str:
    return (FIXTURES_DIR / "google" / "supply-chain-director-jobs.html").read_text()


@pytest.fixture()
def google_weekly_contacts_mobile_html() -> str:
    return (FIXTURES_DIR / "google" / "weekly_contacts_with_mobile.html").read_text()


@pytest.fixture()
def google_seven_cloak_html() -> str:
    return (FIXTURES_DIR / "google" / "search_seven_cloak.html").read_text()


@pytest.fixture()
def google_news_tab_html() -> str:
    return (FIXTURES_DIR / "google" / "news_tab_search.html").read_text()


@pytest.fixture()
def google_personal_injury_lawyer_html() -> str:
    return (FIXTURES_DIR / "google" / "personal_injury_lawyer_20260528_203801.html").read_text()


@pytest.fixture()
def google_iphone_15_review_html() -> str:
    return (FIXTURES_DIR / "google" / "iphone_15_review_20260528_204042.html").read_text()


@pytest.fixture()
def google_opera_mini_html() -> str:
    return (FIXTURES_DIR / "google" / "opera_mini_claude.html").read_text()


@pytest.fixture()
def google_finance_quote_html() -> str:
    return (FIXTURES_DIR / "google_finance" / "quote.html").read_text()


@pytest.fixture()
def google_finance_crypto_html() -> str:
    return (FIXTURES_DIR / "google_finance" / "crypto.html").read_text()
