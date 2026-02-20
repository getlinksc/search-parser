# Contributing to search-parser

Thank you for your interest in contributing! This guide will help you get started.

---

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

### 1. Clone the repository

```bash
git clone https://github.com/getlinksc/search-parser.git
cd search-parser
```

### 2. Install dependencies

```bash
uv sync --all-extras
```

This installs all runtime and development dependencies, including test and documentation tools.

### 3. Install pre-commit hooks

```bash
uv run pre-commit install
```

### 4. Verify your setup

```bash
uv run pytest
uv run ruff check .
uv run mypy .
```

---

## How to Add a New Search Engine Parser

Adding support for a new search engine is straightforward. Follow these steps:

### Step 1: Create the parser module

Create a new file at `src/search_engine_parser/engines/<engine_name>.py`:

```python
"""Parser for <EngineName> search results."""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, Tag

from search_engine_parser.engines.base import BaseParser, SearchResult


class EnginNameParser(BaseParser):
    """Parse <EngineName> HTML search results."""

    name: str = "<engine_name>"

    @staticmethod
    def detect(html: str) -> bool:
        """Return True if the HTML is from <EngineName>."""
        soup = BeautifulSoup(html, "html.parser")
        # Add detection logic here, e.g. check for a unique element or meta tag.
        return False

    def parse_results(self, html: str) -> list[SearchResult]:
        """Extract search results from <EngineName> HTML."""
        soup = BeautifulSoup(html, "html.parser")
        results: list[SearchResult] = []

        # Locate result containers and extract title, url, snippet.
        # Append SearchResult objects to the results list.

        return results
```

### Step 2: Register the parser

Add your parser to the engine registry in `src/search_engine_parser/engines/__init__.py`:

```python
from search_engine_parser.engines.engine_name import EngineNameParser

ENGINES: list[type[BaseParser]] = [
    GoogleParser,
    BingParser,
    DuckDuckGoParser,
    EngineNameParser,  # Add your parser here
]
```

### Step 3: Add test fixtures

1. Save a sample HTML file at `tests/fixtures/<engine_name>/results.html`.
2. Save expected parsed output at `tests/fixtures/<engine_name>/expected.json`.

You can use the fixture helper script:

```bash
uv run python scripts/update_fixtures.py <engine_name> path/to/sample.html
```

### Step 4: Write tests

Create `tests/engines/test_<engine_name>.py`:

```python
"""Tests for <EngineName> parser."""

import json
from pathlib import Path

from search_engine_parser.engines.engine_name import EngineNameParser

FIXTURES = Path(__file__).parent.parent / "fixtures" / "<engine_name>"


def test_detect() -> None:
    html = (FIXTURES / "results.html").read_text()
    assert EngineNameParser.detect(html) is True


def test_parse_results() -> None:
    html = (FIXTURES / "results.html").read_text()
    expected = json.loads((FIXTURES / "expected.json").read_text())
    parser = EngineNameParser()
    results = parser.parse_results(html)
    assert len(results) == len(expected)
    for result, exp in zip(results, expected):
        assert result.title == exp["title"]
        assert result.url == exp["url"]
```

### Step 5: Update documentation

Add the new engine to the supported engines table in `README.md` and `docs/index.md`.

---

## Code Style

This project enforces consistent code style with automated tooling:

- **[Ruff](https://docs.astral.sh/ruff/)** for linting and formatting. Configuration lives in `pyproject.toml`.
- **[mypy](https://mypy-lang.org/)** in strict mode for type checking.

All code must pass the following before merging:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```

Key style rules:

- All functions and methods must have type annotations.
- Use `from __future__ import annotations` in every module.
- Write docstrings for all public classes, methods, and functions.
- Keep line length at 88 characters.

---

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=search_engine_parser --cov-report=term-missing

# Run a specific test file
uv run pytest tests/engines/test_google.py

# Run tests matching a pattern
uv run pytest -k "test_detect"
```

---

## Pull Request Guidelines

1. **Branch from `main`** -- Create a feature branch for your work (e.g. `feat/add-yahoo-parser`).
2. **Keep PRs focused** -- One logical change per pull request.
3. **Write tests** -- All new functionality must include tests. Aim for high coverage.
4. **Pass CI** -- Ensure all checks (tests, lint, type checking) pass before requesting review.
5. **Update documentation** -- If your change affects public APIs or supported features, update the relevant docs.
6. **Write a clear description** -- Use the PR template and explain *what* changed and *why*.
7. **Sign your commits** -- Use `git commit -s` to add a `Signed-off-by` line (DCO).

---

## Reporting Issues

- Use the [bug report template](https://github.com/getlinksc/search-parser/issues/new?template=bug_report.md) for bugs.
- Use the [feature request template](https://github.com/getlinksc/search-parser/issues/new?template=feature_request.md) for new ideas.

---

Thank you for helping make `search-parser` better!
