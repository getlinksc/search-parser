
# Search Engine HTML Parser - Claude Code Build Prompt

## Project Overview
**Project Name:** SearchEngineParser (or `search-parser`)

**Project Type:** Open-source Python library for parsing search engine HTML results

**Primary Goal:** Create a production-ready, extensible Python library that parses HTML from various search engines (Google, Bing, DuckDuckGo) and outputs structured data in multiple formats (JSON, Markdown) for both programmatic use and LLM consumption.

**Target Users:** 
- Developers building web scraping tools
- Data scientists analyzing search results
- AI/LLM application developers needing search data
- Open-source contributors wanting to add support for more search engines

**Quick Example:**
```python
from search_engine_parser import SearchParser

parser = SearchParser()

# Get JSON (default)
json_output = parser.parse(html_string)
# Returns: '{"search_engine": "google", "results": [...]}'

# Get Markdown (LLM-friendly)
markdown_output = parser.parse(html_string, output_format="markdown")
# Returns: '# Search Results\n\n## Organic Results\n\n### 1. Title...'

# Get Python dict (for programmatic access)
results_dict = parser.parse(html_string, output_format="dict")
# Returns: {"search_engine": "google", "results": [...]}
```

---

## Core Requirements

### Functional Requirements

1. **HTML Parsing:**
   - Accept HTML as string or file path input
   - Automatically detect which search engine the HTML came from (Google, Bing, DuckDuckGo)
   - Extract search results with high accuracy
   - Handle various search result types: organic results, featured snippets, knowledge panels, image results, news results
   - Gracefully handle malformed HTML or unexpected structures

2. **Search Engine Support:**
   - **Google:** Organic results, featured snippets, people also ask, knowledge graph, image packs, news results
   - **Bing:** Organic results, featured snippets, related searches, image results, news results
   - **DuckDuckGo:** Organic results, instant answers, related searches
   - Extensible architecture for contributors to add new search engines

3. **Output Formats:**
   - **JSON:** Structured data with fields: title, url, description, position, metadata
   - **Markdown:** Human/LLM-readable format with clear sections and formatting
   - **Python objects:** Pydantic models for type safety and validation
   - Allow custom formatters via plugin system

4. **Auto-Detection:**
   - Detect search engine from HTML meta tags, DOM structure, or URL patterns
   - Confidence scoring for detection (high/medium/low)
   - Fallback handling when detection fails

### Non-Functional Requirements

- **Performance:** Parse typical search page (<500KB) in under 100ms
- **Reliability:** Handle edge cases gracefully, never crash on malformed input
- **Maintainability:** Clear separation of concerns, easy to add new search engines
- **Extensibility:** Plugin architecture for custom parsers and formatters
- **Documentation:** Comprehensive docs for users and contributors
- **Testing:** High test coverage (>90%), including real HTML fixtures from each search engine

---

## Technical Specifications

### Tech Stack
- **Python Version:** 3.9+ (for better type hints and modern features)
- **Package Manager:** `uv` - Modern, fast Python package manager (https://github.com/astral-sh/uv)
- **Core Libraries:**
  - `beautifulsoup4` - HTML parsing (flexible and robust)
  - `lxml` - Fast HTML parser backend for BeautifulSoup
  - `markdownify` - Convert HTML to Markdown for LLM-friendly output
  - `pydantic` v2 - Data validation and settings
  - `click` - Optional CLI interface
  - `rich` - Beautiful CLI output (optional)
  
### Architecture Pattern
- **Pattern:** Strategy Pattern + Plugin Architecture
- **Justification:** 
  - Strategy pattern allows swapping parser implementations per search engine
  - Plugin architecture enables contributors to add new search engines without modifying core
  - Clear separation between detection, parsing, and formatting layers

### Project Structure
```
search-parser/
├── src/
│   └── search_engine_parser/
│       ├── __init__.py              # Public API exports
│       ├── __version__.py           # Version info
│       ├── core/
│       │   ├── __init__.py
│       │   ├── parser.py            # Main SearchParser class
│       │   ├── detector.py          # Search engine auto-detection
│       │   └── models.py            # Pydantic data models
│       ├── parsers/                 # Parser implementations
│       │   ├── __init__.py
│       │   ├── base.py              # Abstract base parser
│       │   ├── google.py            # Google parser
│       │   ├── bing.py              # Bing parser
│       │   └── duckduckgo.py        # DuckDuckGo parser
│       ├── formatters/              # Output formatters
│       │   ├── __init__.py
│       │   ├── base.py              # Abstract base formatter
│       │   ├── json_formatter.py    # JSON output (using Pydantic .model_dump_json())
│       │   └── markdown_formatter.py # Markdown output (using markdownify)
│       ├── exceptions.py            # Custom exceptions
│       ├── utils.py                 # Utility functions
│       └── cli.py                   # Optional CLI interface
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── fixtures/                    # HTML test fixtures
│   │   ├── google/
│   │   │   ├── organic_results.html
│   │   │   ├── featured_snippet.html
│   │   │   └── knowledge_panel.html
│   │   ├── bing/
│   │   │   └── organic_results.html
│   │   └── duckduckgo/
│   │       └── organic_results.html
│   ├── unit/
│   │   ├── test_detector.py
│   │   ├── test_google_parser.py
│   │   ├── test_bing_parser.py
│   │   └── test_duckduckgo_parser.py
│   ├── integration/
│   │   └── test_end_to_end.py
│   └── test_formatters.py
├── docs/
│   ├── index.md
│   ├── getting_started.md
│   ├── api_reference.md
│   ├── contributing.md
│   ├── adding_search_engine.md   # Guide for contributors
│   └── examples/
│       ├── basic_usage.md
│       └── advanced_usage.md
├── examples/
│   ├── basic_parsing.py
│   ├── batch_processing.py
│   └── custom_formatter.py
├── .github/
│   └── workflows/
│       ├── test.yml              # Run tests on PR/push
│       ├── publish.yml           # Publish to PyPI on release
│       ├── docs.yml              # Build and deploy docs
│       ├── lint.yml              # Code quality checks
│       └── coverage-badge.yml    # Update coverage badge
├── scripts/
│   └── update_fixtures.py        # Helper to capture new test fixtures
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml                # Project metadata and dependencies
├── uv.lock                       # Lock file for reproducible builds
├── README.md
├── LICENSE                       # MIT or Apache 2.0
├── CONTRIBUTING.md
├── CHANGELOG.md
└── CODE_OF_CONDUCT.md
```

---

## Installation & Development Setup

### For Users

**Using uv (recommended):**
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the package
uv pip install search-parser

# Or with CLI extras
uv pip install "search-parser[cli]"
```

**Using pip:**
```bash
pip install search-parser

# Or with CLI extras
pip install "search-parser[cli]"
```

### For Contributors

**Using uv (recommended):**
```bash
# Clone the repository
git clone https://github.com/getlinksc/search-parser.git
cd search-parser

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with all dev dependencies
uv pip install -e ".[dev,cli,docs]"

# Or use uv sync for locked dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

**Using traditional tools:**
```bash
# Clone the repository
git clone https://github.com/getlinksc/search-parser.git
cd search-parser

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev,cli,docs]"

# Install pre-commit hooks
pre-commit install
```

---

## Development Guidelines

### Code Quality Standards
- **Type Hints:** Full type hints for all functions and methods (use `mypy --strict`)
- **Docstrings:** Google-style docstrings for all public APIs
- **Linting:** 
  - `ruff` for fast linting and auto-fixing
  - `ruff format` for code formatting (replaces black, line length 100)
  - `mypy` for type checking with strict mode
- **Complexity:** Keep functions under 15 lines when possible, max cyclomatic complexity of 10

### Testing Requirements
- **Coverage Target:** Minimum 90% code coverage
- **Test Framework:** pytest with pytest-cov
- **Test Types:**
  - Unit tests for each parser with real HTML fixtures
  - Integration tests for full parse workflows
  - Edge case tests for malformed HTML
  - Performance benchmarks for parsing speed
- **Test Fixtures:** Capture real HTML from search engines (anonymized/minimal)

### Error Handling
- Custom exceptions:
  - `SearchEngineDetectionError` - Cannot determine search engine
  - `ParserNotFoundError` - No parser available for detected engine
  - `ParseError` - Failed to parse HTML
  - `InvalidHTMLError` - HTML structure is invalid
- Never crash on bad input - return empty results with warnings
- Comprehensive logging with appropriate levels

### Documentation Requirements
- **README.md** with:
  - **Badges section at the top:**
    ```markdown
    # Search Parser
    
    [![PyPI version](https://badge.fury.io/py/search-parser.svg)](https://badge.fury.io/py/search-parser)
    [![Python Support](https://img.shields.io/pypi/pyversions/search-parser.svg)](https://pypi.org/project/search-parser/)
    [![Tests](https://github.com/getlinksc/search-parser/workflows/Tests/badge.svg)](https://github.com/getlinksc/search-parser/actions?query=workflow%3ATests)
    [![Lint](https://github.com/getlinksc/search-parser/workflows/Lint/badge.svg)](https://github.com/getlinksc/search-parser/actions?query=workflow%3ALint)
    [![codecov](https://codecov.io/gh/getlinksc/search-parser/branch/main/graph/badge.svg)](https://codecov.io/gh/getlinksc/search-parser)
    [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
    [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
    [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
    [![Downloads](https://pepy.tech/badge/search-parser/month)](https://pepy.tech/project/search-parser)
    
    Parse search engine HTML results into structured data (JSON, Markdown) with auto-detection.
    ```
  - Quick start example
  - Installation instructions (using `uv` and `pip`)
  - Basic usage examples
  - Links to full documentation
- **API Documentation:** Auto-generated with Sphinx or mkdocs-material
- **Contributing Guide:** How to add new search engines, run tests, submit PRs
- **Examples:** Working code examples in examples/ directory
- **Changelog:** Keep updated following Keep a Changelog format

---

## Specific Implementation Details

### Auto-Detection Algorithm

The detector should check in this order:

1. **HTML Meta Tags:**
   ```python
   # Google: <meta content="Google" property="og:site_name">
   # Bing: <meta name="ms.application" content="Bing">
   # DuckDuckGo: Check for specific DDG meta tags or classes
   ```

2. **DOM Structure Patterns:**
   ```python
   # Google: div with id="search" or class="g"
   # Bing: div with class="b_algo"
   # DuckDuckGo: div with class="result" or "web-result"
   ```

3. **URL Patterns (if present in HTML):**
   ```python
   # Check for canonical URLs, links, or meta referrers
   ```

4. **Fallback:** If confidence < 80%, return None and let user specify manually

### Data Models

```python
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Literal
from datetime import datetime

class SearchResult(BaseModel):
    """Single search result item."""
    title: str
    url: HttpUrl
    description: Optional[str] = None
    position: int
    result_type: Literal["organic", "featured_snippet", "knowledge_panel", "news", "image"] = "organic"
    metadata: dict = Field(default_factory=dict)  # Engine-specific extra data

class SearchResults(BaseModel):
    """Collection of search results from a page."""
    search_engine: str  # "google", "bing", "duckduckgo"
    query: Optional[str] = None  # Extracted if possible
    total_results: Optional[int] = None  # If available
    results: List[SearchResult]
    detection_confidence: float = Field(ge=0.0, le=1.0)  # 0-1 confidence score
    parsed_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)  # Additional engine-specific data
```

### Parser Interface

```python
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

class BaseParser(ABC):
    """Abstract base class for search engine parsers."""
    
    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of the search engine (e.g., 'google')."""
        pass
    
    @abstractmethod
    def parse(self, html: str) -> SearchResults:
        """Parse HTML and extract search results."""
        pass
    
    @abstractmethod
    def can_parse(self, soup: BeautifulSoup) -> float:
        """
        Check if this parser can handle the HTML.
        Returns confidence score 0.0-1.0.
        """
        pass
    
    def extract_query(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract search query from HTML if possible."""
        pass
```

### Output Format Examples

**JSON Output:**
```json
{
  "search_engine": "google",
  "query": "python web scraping",
  "total_results": 1250000,
  "results": [
    {
      "title": "Web Scraping with Python - Real Python",
      "url": "https://realpython.com/python-web-scraping/",
      "description": "Learn how to scrape websites with Python...",
      "position": 1,
      "result_type": "organic",
      "metadata": {}
    },
    {
      "title": "What is Web Scraping?",
      "url": "https://example.com",
      "description": "Featured snippet content...",
      "position": 0,
      "result_type": "featured_snippet",
      "metadata": {
        "snippet_type": "paragraph"
      }
    }
  ],
  "detection_confidence": 0.95,
  "parsed_at": "2026-02-20T15:30:00Z",
  "metadata": {}
}
```

**Markdown Output (LLM-Friendly):**

The Markdown formatter should use `markdownify` to convert HTML snippets to clean Markdown, then structure the output in a clear, hierarchical format that's easy for both humans and LLMs to read.

```markdown
# Search Results: python web scraping

**Search Engine:** Google  
**Total Results:** ~1,250,000  
**Parsed:** 2026-02-20 15:30:00 UTC

---

## Featured Snippet

### What is Web Scraping?
Featured snippet content...

**Source:** [example.com](https://example.com)

---

## Organic Results

### 1. Web Scraping with Python - Real Python
Learn how to scrape websites with Python...

**URL:** https://realpython.com/python-web-scraping/

### 2. Beautiful Soup Tutorial
A comprehensive guide...

**URL:** https://example.com/bs4

---

*Parsed with search-parser v0.1.0*
```

**Implementation Note for Markdown Formatter:**
- Use `markdownify` library to convert HTML descriptions to clean Markdown
- Preserve links and basic formatting from search result descriptions
- Strip ads, JavaScript, and other non-content elements before conversion
- Example usage:
  ```python
  from markdownify import markdownify as md
  
  # Convert HTML description to Markdown
  clean_description = md(
      html_description,
      heading_style="ATX",  # Use # for headings
      bullets="-",           # Use - for lists
      strip=['script', 'style', 'nav']  # Remove these tags
  )
  ```

### API Usage Examples

```python
from search_engine_parser import SearchParser

# Basic usage - auto-detect engine, returns JSON string by default
parser = SearchParser()
with open("google_results.html") as f:
    results_json = parser.parse(f.read())  # Returns JSON string

# Get results as Markdown (uses markdownify internally)
markdown_output = parser.parse(html_string, output_format="markdown")

# Get results as Python dict for programmatic access
results_dict = parser.parse(html_string, output_format="dict")

# Access structured data from dict
for result in results_dict["results"]:
    print(f"{result['position']}. {result['title']}")
    print(f"   {result['url']}")

# Specify engine manually if detection fails
results = parser.parse(html_string, engine="google", output_format="json")

# Parse from file with different formats
with open("bing_results.html") as f:
    markdown = parser.parse(f.read(), output_format="markdown")
    
# Pretty print JSON
import json
results_json = parser.parse(html_string)
print(json.dumps(json.loads(results_json), indent=2))

# Filter results from dict output
results_dict = parser.parse(html_string, output_format="dict")
organic = [r for r in results_dict["results"] if r["result_type"] == "organic"]
featured = [r for r in results_dict["results"] if r["result_type"] == "featured_snippet"]
```

**Function Signature:**
```python
def parse(
    self,
    html: str,
    engine: Optional[str] = None,
    output_format: Literal["json", "markdown", "dict"] = "json"
) -> Union[str, dict]:
    """
    Parse search engine HTML and return results.
    
    Args:
        html: HTML string to parse
        engine: Optionally specify engine ("google", "bing", "duckduckgo")
                If None, will auto-detect
        output_format: Output format - "json" (default), "markdown", or "dict"
                      - "json": Returns JSON string
                      - "markdown": Returns Markdown string (uses markdownify)
                      - "dict": Returns Python dictionary
    
    Returns:
        str: JSON or Markdown string (depending on output_format)
        dict: Python dictionary (if output_format="dict")
        
    Raises:
        SearchEngineDetectionError: If engine cannot be detected and not specified
        ParserNotFoundError: If no parser available for the detected/specified engine
        ParseError: If parsing fails
    """
    pass
```

---

## Constraints & Considerations

### What to AVOID
- ❌ Don't use Selenium or browser automation - this library only parses HTML
- ❌ Avoid making actual HTTP requests - users provide HTML
- ❌ Don't include scraped HTML in git repo (copyright issues)
- ❌ Avoid tight coupling between parsers
- ❌ Don't use regex for complex HTML parsing (use BeautifulSoup)

### Known Challenges

**Challenge 1:** Search engines frequently change their HTML structure
- **Approach:** 
  - Version parsers (e.g., GoogleParserV1, GoogleParserV2)
  - Include HTML structure tests that fail when structure changes
  - Accept community contributions to update parsers

**Challenge 2:** Different locales/languages have different HTML structures
- **Approach:** 
  - Start with English/US results
  - Add locale detection and handling in future versions
  - Document limitations clearly

**Challenge 3:** Determining result position with ads and different result types
- **Approach:**
  - Featured snippets get position 0
  - Ads are excluded (or marked as type="ad")
  - Organic results numbered 1, 2, 3...

### Dependencies
- **System Dependencies:** None (pure Python)
- **External Services:** None (offline parsing only)

---

## Development Workflow

### Phase 1: Foundation (PRIORITY)
1. Set up project structure with pyproject.toml
2. Create base models (SearchResult, SearchResults) with Pydantic
3. Implement BaseParser abstract class
4. Create Detector class for auto-detection
5. Set up pytest with coverage
6. Configure ruff, black, mypy in pyproject.toml
7. Create initial README with project vision

### Phase 2: Google Parser (MVP)
1. Collect Google HTML test fixtures (organic results, featured snippet)
2. Implement GoogleParser with basic organic result extraction
3. Write unit tests for GoogleParser
4. Implement JSON formatter (using Pydantic's .model_dump_json())
5. Implement Markdown formatter (using markdownify library)
6. Add output_format parameter to parse() method (default: "json")
7. Test end-to-end: HTML → parse → JSON/Markdown/dict output

### Phase 3: Additional Search Engines
1. Implement BingParser with tests
2. Implement DuckDuckGoParser with tests
3. Enhance detector to distinguish between engines
4. Add integration tests for all engines

### Phase 4: CLI and Polish
1. Implement optional CLI with Click
2. Add --format flag for choosing output (json/markdown, default: json)
3. Add rich output for terminal display (when using CLI)
4. Create examples/ directory with working examples
5. Write comprehensive documentation

### Phase 5: Open Source Preparation
1. Write CONTRIBUTING.md with clear guidelines
2. Create issue templates (.github/ISSUE_TEMPLATE/)
3. Create PR template (.github/pull_request_template.md)
4. Add CODE_OF_CONDUCT.md
5. Set up GitHub workflows (test, publish, docs, lint, coverage)
6. Configure pre-commit hooks
7. **Set up Codecov:**
   - Sign up at https://codecov.io with GitHub account
   - Enable the repository in Codecov
   - Add `CODECOV_TOKEN` to GitHub repository secrets
   - Codecov will automatically comment on PRs with coverage reports
8. **Optional: Set up coverage badge using dynamic badge:**
   - Create a GitHub Gist for badge data
   - Generate a GitHub token with gist permissions
   - Add `GIST_SECRET` to repository secrets
   - Update gist ID in coverage-badge.yml workflow
9. Create v0.1.0 release

### Git Workflow
- Commit message convention: Conventional Commits (feat:, fix:, docs:, test:)
- Branch naming: feature/google-parser, fix/detection-bug
- Protected main branch requiring PR reviews
- Semantic versioning (SemVer)

---

## GitHub Workflows

### Test Workflow (.github/workflows/test.yml)
```yaml
name: Tests

on: 
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          uv sync --all-extras
      
      - name: Run tests with coverage
        run: |
          uv run pytest --cov=search_engine_parser --cov-report=xml --cov-report=term --cov-report=html
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.11'
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
          token: ${{ secrets.CODECOV_TOKEN }}
      
      - name: Upload coverage HTML artifact
        uses: actions/upload-artifact@v4
        if: matrix.python-version == '3.11'
        with:
          name: coverage-report
          path: htmlcov/
          retention-days: 30
```

### Publish to PyPI Workflow (.github/workflows/publish.yml)
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # For trusted publishing
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Set up Python
        run: uv python install 3.11
      
      - name: Build package
        run: uv build
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

### Lint Workflow (.github/workflows/lint.yml)
```yaml
name: Lint

on: 
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Set up Python
        run: uv python install 3.11
      
      - name: Install dependencies
        run: uv sync --all-extras
      
      - name: Run ruff check
        run: uv run ruff check .
      
      - name: Run ruff format check
        run: uv run ruff format --check .
      
      - name: Run mypy
        run: uv run mypy src/search_engine_parser
```

### Coverage Badge Workflow (.github/workflows/coverage-badge.yml)
```yaml
name: Coverage Badge

on:
  push:
    branches: [main]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Set up Python
        run: uv python install 3.11
      
      - name: Install dependencies
        run: uv sync --all-extras
      
      - name: Run tests with coverage
        run: |
          uv run pytest --cov=search_engine_parser --cov-report=term --cov-report=json
      
      - name: Create coverage badge
        uses: schneegans/dynamic-badges-action@v1.7.0
        with:
          auth: ${{ secrets.GIST_SECRET }}
          gistID: your-gist-id-here
          filename: search-parser-coverage.json
          label: coverage
          message: ${{ env.COVERAGE }}
          color: ${{ env.COVERAGE_COLOR }}
          namedLogo: python
```

---

## pyproject.toml Configuration

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "search-parser"
version = "0.1.0"
description = "Parse search engine HTML results into structured data"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
keywords = ["search", "parser", "scraping", "google", "bing", "duckduckgo"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
    "markdownify>=0.11.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
cli = [
    "click>=8.1.0",
    "rich>=13.0.0",
]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.7.0",
    "ruff>=0.1.0",
    "pre-commit>=3.5.0",
    "types-beautifulsoup4",
]
docs = [
    "mkdocs-material>=9.4.0",
    "mkdocstrings[python]>=0.24.0",
]

[project.urls]
Homepage = "https://github.com/getlinksc/search-parser"
Documentation = "https://search-parser.readthedocs.io"
Repository = "https://github.com/getlinksc/search-parser"
Issues = "https://github.com/getlinksc/search-parser/issues"
Changelog = "https://github.com/getlinksc/search-parser/blob/main/CHANGELOG.md"

[project.scripts]
search-parser = "search_engine_parser.cli:main"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.7.0",
    "ruff>=0.1.0",
    "pre-commit>=3.5.0",
    "types-beautifulsoup4",
]

[tool.ruff]
line-length = 100
target-version = "py39"
src = ["src"]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "W",   # pycodestyle warnings
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "SIM", # flake8-simplify
]
ignore = [
    "E501",  # Line too long (handled by formatter)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.9"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
files = ["src/search_engine_parser"]

[[tool.mypy.overrides]]
module = "bs4.*"
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "-v",
    "--strict-markers",
    "--strict-config",
    "--cov=search_engine_parser",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html",
    "--cov-report=xml",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/test_*.py",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if TYPE_CHECKING:",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]

[tool.coverage.html]
directory = "htmlcov"
```

---

## Additional Context

### Example Use Cases

**Use Case 1: LLM Application**
```
Given: User's LLM app performs web search via API that returns HTML
When: User passes HTML to search-parser
Then: Parser extracts results in markdown format that LLM can understand and process
```

**Use Case 2: Data Analysis**
```
Given: Researcher has 1000 saved Google search result pages
When: Batch process all HTML files with search-parser
Then: Generate JSON dataset for analysis of ranking changes over time
```

**Use Case 3: Contributing New Engine**
```
Given: Developer wants to add Yandex search support
When: Follow CONTRIBUTING.md guide to create YandexParser
Then: Submit PR with parser implementation, tests, and fixtures
```

### Sample HTML Fixtures

Create minimal, anonymized HTML fixtures like:

```html
<!-- tests/fixtures/google/organic_results.html -->
<!DOCTYPE html>
<html>
<head>
    <meta property="og:site_name" content="Google">
</head>
<body>
    <div id="search">
        <div class="g">
            <div class="yuRUbf">
                <a href="https://example.com/result1">
                    <h3>First Result Title</h3>
                </a>
            </div>
            <div class="VwiC3b">First result description here.</div>
        </div>
        <div class="g">
            <div class="yuRUbf">
                <a href="https://example.com/result2">
                    <h3>Second Result Title</h3>
                </a>
            </div>
            <div class="VwiC3b">Second result description.</div>
        </div>
    </div>
</body>
</html>
```

### Setting Up Badges and Code Coverage

**Codecov Setup (Automatic Coverage Reports):**
1. Go to https://codecov.io and sign in with GitHub
2. Click "Add Repository" and enable your `search-parser` repository
3. Go to repository settings → Secrets and add:
   - `CODECOV_TOKEN` (get from Codecov dashboard)
4. The test workflow will automatically upload coverage to Codecov
5. Codecov will comment on PRs with coverage changes
6. Badge will show current coverage percentage

**Badge URLs for README:**
```markdown
# Main Badges
[![Tests](https://github.com/USERNAME/search-parser/workflows/Tests/badge.svg)](https://github.com/USERNAME/search-parser/actions?query=workflow%3ATests)
[![Lint](https://github.com/USERNAME/search-parser/workflows/Lint/badge.svg)](https://github.com/USERNAME/search-parser/actions?query=workflow%3ALint)
[![codecov](https://codecov.io/gh/USERNAME/search-parser/branch/main/graph/badge.svg)](https://codecov.io/gh/USERNAME/search-parser)

# Package Badges
[![PyPI version](https://badge.fury.io/py/search-parser.svg)](https://badge.fury.io/py/search-parser)
[![Python Support](https://img.shields.io/pypi/pyversions/search-parser.svg)](https://pypi.org/project/search-parser/)
[![Downloads](https://pepy.tech/badge/search-parser/month)](https://pepy.tech/project/search-parser)

# Code Quality Badges
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

**What Each Badge Shows:**
- **Tests Badge**: Green if tests pass, red if failing
- **Lint Badge**: Green if linting passes
- **Codecov Badge**: Shows exact coverage percentage with color coding
- **PyPI Version**: Current version published to PyPI
- **Python Support**: Shows supported Python versions
- **Downloads**: Monthly download count from PyPI
- **Code Style**: Shows you use Ruff for linting/formatting
- **Type Checked**: Shows you use mypy for type safety
- **License**: Shows your license type

---

## Development Instructions for Claude Code

### CLAUDE.md Setup
Please create a `CLAUDE.md` file that includes:
- Project architecture (Strategy pattern for parsers, plugin system)
- Coding standards (type hints, docstrings, ruff check + ruff format, mypy)
- Package manager: Using `uv` for fast, modern Python package management
- How to add a new search engine parser
- Testing philosophy and fixture management
- Common development commands:
  - `uv sync` - Install/sync dependencies from lock file
  - `uv run pytest` - Run tests
  - `uv run ruff check .` - Lint code
  - `uv run ruff format .` - Format code
  - `uv run mypy src/search_engine_parser` - Type check
  - `uv run pre-commit run --all-files` - Run all pre-commit hooks
- Release process and versioning

### Execution Mode
- **Preferred Mode:** `/auto` for:
  - Creating project structure
  - Implementing parsers based on defined interfaces
  - Running tests and linters
  - Generating documentation
- Use `/normal` for:
  - Designing the plugin architecture
  - Creating the auto-detection algorithm
  - Deciding on data model structures

### Permissions
Please ask before:
- Publishing to PyPI (even test PyPI)
- Creating GitHub releases
- Modifying .github/workflows that affect CI/CD

### Validation Steps
After implementation, please:
1. ✅ Run `pytest -v --cov=search_engine_parser --cov-report=term` and confirm >90% coverage
2. ✅ Verify `ruff check .` passes with no errors
3. ✅ Verify `black --check .` passes
4. ✅ Run `mypy src/search_engine_parser --strict` and confirm no type errors
5. ✅ Test parsing actual Google, Bing, and DuckDuckGo HTML (use test fixtures)
6. ✅ Verify JSON output is valid JSON with `json.loads()`
7. ✅ Verify Markdown output is well-formatted and readable
8. ✅ Test all three output formats (json, markdown, dict) with same HTML
9. ✅ Test CLI if implemented: 
   - `search-parser examples/google.html` (default JSON)
   - `search-parser examples/google.html --format markdown`
   - `search-parser examples/google.html --format json --pretty`
10. ✅ Verify package can be installed: `pip install -e .`
11. ✅ Check that README examples actually work
12. ✅ Test markdownify properly converts HTML to clean Markdown

### Documentation Deliverables
Please include:
1. **README.md** with:
   - Project description and motivation
   - Quick start (install and basic example)
   - Supported search engines
   - Output format examples
   - Installation instructions
   - Badges (GitHub Actions status, coverage, PyPI)
   - Links to full documentation and contributing guide
2. **CONTRIBUTING.md** with:
   - How to set up development environment
   - How to add a new search engine parser
   - Code style guide
   - How to run tests
   - How to submit PRs
3. **API Documentation:** 
   - mkdocs-material site with API reference
   - Examples for common use cases
4. **docs/adding_search_engine.md:**
   - Step-by-step tutorial for contributors
   - Example of creating a new parser

---

## Questions for Claude Code

Before starting, please help me decide:

1. **License:** MIT or Apache 2.0? (MIT is simpler, Apache has patent protection)
2. **CLI:** Should the CLI be in the main package or optional? (Suggest: optional via extras)
3. **Parser versioning:** Should we version parsers (GoogleParserV1) from the start?
4. **Documentation hosting:** GitHub Pages, Read the Docs, or both?

If anything is unclear or you need more information about search engine HTML structures, please ask before beginning implementation.

---

## Success Criteria

The project is complete when:
- ✅ Can parse Google, Bing, and DuckDuckGo HTML correctly
- ✅ Auto-detection works with >90% accuracy on test fixtures
- ✅ parse() method accepts output_format parameter (json/markdown/dict)
- ✅ JSON output (default) is valid and properly formatted
- ✅ Markdown output uses markdownify and is clean/readable for LLMs
- ✅ Dict output returns proper Python dictionaries for programmatic access
- ✅ Test coverage exceeds 90%
- ✅ All tests pass on Python 3.9, 3.10, 3.11, 3.12
- ✅ Code passes ruff and black checks with no errors
- ✅ Code passes mypy strict with no type errors
- ✅ README includes working examples for all three output formats
- ✅ CONTRIBUTING.md has clear instructions for adding parsers
- ✅ GitHub workflows are configured and passing
- ✅ Package structure supports PyPI publication
- ✅ Documentation site is generated and complete
- ✅ At least 3 working examples in examples/ directory
- ✅ CLI works with --format flag (if included)
- ✅ Project is ready for first contributors

---

## Final Notes

**Development Philosophy:**
- **"Library first, CLI second"** - Core library should work perfectly without CLI
- **"Extensibility over completeness"** - Better to have a great plugin system than support every search engine
- **"Fail gracefully"** - Never crash, return empty results with clear errors
- **"Documentation is code"** - Treat docs as seriously as implementation
- **"Welcome contributors"** - Make it EASY for others to add search engines

**For Open Source Success:**
- Clear, friendly README
- Good first issue labels
- Responsive to PRs and issues
- Comprehensive contributing guide
- Welcoming community

**Communication:** Please provide updates after each phase and highlight any architectural decisions that need input.

**Working Mode:** Please use `/auto` for implementation following the defined interfaces, but pause for architectural decisions like the plugin system design.

**Testing Priority:** Parsers are the core value - they should have the highest test coverage and quality.
