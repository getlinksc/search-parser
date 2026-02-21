# search-parser

[![PyPI](https://img.shields.io/pypi/v/search-parser)](https://pypi.org/project/search-parser/)
[![Python Versions](https://img.shields.io/pypi/pyversions/search-parser)](https://pypi.org/project/search-parser/)
[![Tests](https://github.com/getlinksc/search-parser/actions/workflows/test.yml/badge.svg)](https://github.com/getlinksc/search-parser/actions/workflows/test.yml)
[![Lint](https://github.com/getlinksc/search-parser/actions/workflows/lint.yml/badge.svg)](https://github.com/getlinksc/search-parser/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/getlinksc/search-parser/branch/main/graph/badge.svg)](https://codecov.io/gh/getlinksc/search-parser)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Parse search engine HTML results into structured data (JSON, Markdown) with auto-detection.**

`search-parser` takes raw HTML from Google, Bing, and DuckDuckGo and extracts every result type — organic results, featured snippets, AI Overviews, People Also Ask, sponsored ads, and more — into clean, typed Python objects. It auto-detects the search engine from the HTML, so you never have to specify which parser to use.

---

## Quick Start

```python
from search_engine_parser import SearchParser

parser = SearchParser()
html = open("google_results.html").read()

# JSON string (default)
json_output = parser.parse(html)

# Markdown string — great for feeding to an LLM
md_output = parser.parse(html, output_format="markdown")

# Python dict — for programmatic access
data = parser.parse(html, output_format="dict")

# Organic results are in data["results"]
for result in data["results"]:
    print(f"{result['position']}. {result['title']}")
    print(f"   {result['url']}")

# Every other result type has its own dedicated key
if data["featured_snippet"]:
    print("Featured:", data["featured_snippet"]["title"])

if data["ai_overview"]:
    print("AI Overview:", data["ai_overview"]["description"][:100])

for question in data["people_also_ask"]:
    print("PAA:", question["title"])
```

---

## Installation

**With uv (recommended):**

```bash
uv add search-parser
```

**With pip:**

```bash
pip install search-parser
```

---

## Supported Result Types

| Result Type | Field | Google | Bing | DuckDuckGo |
|---|---|:-:|:-:|:-:|
| Organic results | `results` | ✓ | ✓ | ✓ |
| Featured snippet | `featured_snippet` | ✓ | ✓ | — |
| Sponsored / ads | `sponsored` | ✓ | — | — |
| AI Overview | `ai_overview` | ✓ | — | — |
| People Also Ask | `people_also_ask` | ✓ | — | — |
| What People Are Saying | `people_saying` | ✓ | — | — |
| People Also Search For | `people_also_search` | ✓ | — | — |
| Related Products & Services | `related_products` | ✓ | — | — |

---

## Working with Results

`SearchParser.parse()` with `output_format="dict"` returns the full `SearchResults` structure:

```python
data = parser.parse(html, output_format="dict")

# Always a list (organic results only)
for r in data["results"]:
    print(r["title"], r["url"], r["description"])

# None or a single object
if data["featured_snippet"]:
    print(data["featured_snippet"]["title"])

# None or a single object with description + sources list
if data["ai_overview"]:
    overview = data["ai_overview"]
    print(overview["description"])
    for source in overview["metadata"]["sources"]:
        print(f"  - {source['title']}: {source['url']}")

# Always a list (empty when not present)
for q in data["people_also_ask"]:
    print(q["title"])

for post in data["people_saying"]:
    print(post["title"], post["url"])

for item in data["people_also_search"]:
    print(item["title"])

for ad in data["sponsored"]:
    print(ad["title"], ad["url"])

for product in data["related_products"]:
    print(product["title"])

# Metadata
print(data["search_engine"])        # "google"
print(data["query"])                # "python web scraping"
print(data["total_results"])        # 26200000 or None
print(data["detection_confidence"]) # 0.95
```

### Using the model directly

When you need the typed `SearchResults` object instead of a dict, call the engine parser directly. The model exposes `to_json()` and `to_markdown()` convenience methods:

```python
from search_engine_parser.parsers.google import GoogleParser

parser = GoogleParser()
results = parser.parse(html)  # returns SearchResults

# Typed access — no dict key lookups
print(results.query)
print(results.total_results)
print(len(results.results))          # organic count

if results.featured_snippet:
    print(results.featured_snippet.title)

if results.ai_overview:
    print(results.ai_overview.description)
    sources = results.ai_overview.metadata["sources"]

for q in results.people_also_ask:
    print(q.title)

for post in results.people_saying:
    print(post.title, post.url)

# Convert to JSON or Markdown directly on the model
json_str  = results.to_json()
json_str  = results.to_json(indent=4)  # custom indent
md_str    = results.to_markdown()
```

---

## Output Formats

### JSON (`output_format="json"` or `results.to_json()`)

```json
{
  "search_engine": "google",
  "query": "python web scraping",
  "total_results": 26200000,
  "results": [
    {
      "title": "Web Scraping with Python - Real Python",
      "url": "https://realpython.com/python-web-scraping/",
      "description": "Learn how to scrape websites with Python...",
      "position": 1,
      "result_type": "organic",
      "metadata": {}
    }
  ],
  "featured_snippet": null,
  "ai_overview": {
    "title": "AI Overview",
    "url": "",
    "description": "Python is a widely used language for web scraping...",
    "position": 0,
    "result_type": "ai_overview",
    "metadata": {
      "sources": [
        {"title": "Beautiful Soup", "url": "https://www.crummy.com/software/BeautifulSoup/"},
        {"title": "Requests", "url": "https://requests.readthedocs.io/"}
      ]
    }
  },
  "people_also_ask": [
    {"title": "Is Python good for web scraping?", "url": "", "position": 0, "result_type": "people_also_ask", "metadata": {}}
  ],
  "sponsored": [],
  "people_saying": [],
  "people_also_search": [],
  "related_products": [],
  "detection_confidence": 0.95,
  "parsed_at": "2026-02-21T00:00:00Z",
  "metadata": {}
}
```

### Markdown (`output_format="markdown"` or `results.to_markdown()`)

```markdown
# Search Results: python web scraping

**Search Engine:** Google
**Total Results:** ~26,200,000
**Parsed:** 2026-02-21 00:00:00 UTC

---

## Featured Snippet

### What is Web Scraping?
Web scraping is the process of extracting data from websites...

**Source:** [https://example.com](https://example.com)

---

## Organic Results

### 1. Web Scraping with Python - Real Python
Learn how to scrape websites with Python...

**URL:** https://realpython.com/python-web-scraping/
```

---

## CLI Usage

```bash
# Parse an HTML file (auto-detects search engine, outputs JSON)
search-parser parse results.html

# Markdown output
search-parser parse results.html --format markdown

# Specify engine manually
search-parser parse results.html --engine google --format json

# Read from stdin
cat results.html | search-parser parse - --format json

# Save to file
search-parser parse results.html --output results.json
```

---

## Documentation

Full documentation: [https://search-parser.github.io/search-parser/](https://search-parser.github.io/search-parser/)

- [Getting Started](https://search-parser.github.io/search-parser/getting_started/)
- [API Reference](https://search-parser.github.io/search-parser/api_reference/)
- [Adding a New Search Engine](https://search-parser.github.io/search-parser/adding_search_engine/)
- [Examples](https://search-parser.github.io/search-parser/examples/basic_usage/)

---

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on the development workflow, how to add new parsers, and how to submit pull requests.

---

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
