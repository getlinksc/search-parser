# Adding a New Search Engine Parser

This guide walks you through adding support for a new search engine.

## Step 1: Create the Parser

Create `src/search_engine_parser/parsers/myengine.py`:

```python
from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from search_engine_parser.core.models import SearchResult, SearchResults
from search_engine_parser.parsers.base import BaseParser
from search_engine_parser.utils import clean_text, make_soup


class MyEngineParser(BaseParser):
    @property
    def engine_name(self) -> str:
        return "myengine"

    def can_parse(self, soup: BeautifulSoup) -> float:
        # Return confidence 0.0-1.0 that this HTML is from your engine
        if soup.find("div", class_="myengine-results"):
            return 0.9
        return 0.0

    def parse(self, html: str) -> SearchResults:
        soup = make_soup(html)
        organic: list[SearchResult] = []
        position = 1

        for item in soup.find_all("div", class_="result"):
            if not isinstance(item, Tag):
                continue
            link = item.find("a")
            if not isinstance(link, Tag):
                continue
            title = clean_text(link.get_text())
            url = str(link.get("href", ""))
            if title and url:
                organic.append(
                    SearchResult(title=title, url=url, position=position, result_type="organic")
                )
                position += 1

        return SearchResults(
            search_engine=self.engine_name,
            query=self.extract_query(soup),
            results=organic,
            detection_confidence=self.can_parse(soup),
        )
```

**Key conventions:**

- `results` must contain **organic results only**. Sponsored ads go in `sponsored`, featured snippets in `featured_snippet`, etc.
- Return an empty `SearchResults` (with `results=[]`) on malformed HTML — never raise.
- Use `clean_text()` from `search_engine_parser.utils` to normalize whitespace.

## Step 2: Register the Parser

Add to `src/search_engine_parser/parsers/__init__.py`:

```python
from search_engine_parser.parsers.myengine import MyEngineParser

PARSER_REGISTRY: dict[str, type[BaseParser]] = {
    "google": GoogleParser,
    "bing": BingParser,
    "duckduckgo": DuckDuckGoParser,
    "myengine": MyEngineParser,  # Add this line
}
```

## Step 3: Add Test Fixtures

Create `tests/fixtures/myengine/organic_results.html` with sample HTML.

## Step 4: Write Tests

Create `tests/unit/test_myengine_parser.py`. Cover:

- `engine_name` property
- `can_parse()` returns a high score for matching HTML and `0.0` for non-matching
- `parse()` returns only organic results in `results`
- Edge cases: empty results, malformed HTML, missing fields
- Confirm non-organic types (if supported) appear in their dedicated fields, not in `results`

Example assertion pattern:

```python
def test_organic_results_only(self, myengine_html: str) -> None:
    results = self.parser.parse(myengine_html)
    for r in results.results:
        assert r.result_type == "organic"
```

## Step 5: Submit a PR

Run the full test suite and linting before submitting:

```bash
uv run pytest
uv run ruff check .
uv run mypy src/search_engine_parser
```
