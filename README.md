# search-engine-parser

[![PyPI](https://img.shields.io/pypi/v/search-engine-parser)](https://pypi.org/project/search-engine-parser/)
[![Python Versions](https://img.shields.io/pypi/pyversions/search-engine-parser)](https://pypi.org/project/search-engine-parser/)
[![Tests](https://github.com/getlinksc/search-engine-parser/actions/workflows/test.yml/badge.svg)](https://github.com/getlinksc/search-engine-parser/actions/workflows/test.yml)
[![Lint](https://github.com/getlinksc/search-engine-parser/actions/workflows/lint.yml/badge.svg)](https://github.com/getlinksc/search-engine-parser/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/getlinksc/search-engine-parser/branch/main/graph/badge.svg)](https://codecov.io/gh/getlinksc/search-engine-parser)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Parse search engine HTML results into structured data (JSON, Markdown) with auto-detection.**

`search-engine-parser` takes raw HTML from popular search engines and extracts structured result data -- titles, URLs, snippets, and more -- into your preferred output format. It auto-detects the search engine from the HTML content, so you don't have to specify which parser to use.

---

## Quick Start

```python
from search_engine_parser import parse

html = open("google_results.html").read()

# JSON string
json_output = parse(html, output_format="json")
print(json_output)
# [{"title": "Example Result", "url": "https://example.com", "snippet": "An example result..."}, ...]

# Markdown string
md_output = parse(html, output_format="markdown")
print(md_output)
# ## Example Result
# **URL:** https://example.com
# An example result...

# Python list of dicts (default)
results = parse(html, output_format="dict")
for result in results:
    print(result["title"], result["url"])
```

---

## Installation

**With uv (recommended):**

```bash
uv add search-engine-parser
```

**With pip:**

```bash
pip install search-engine-parser
```

---

## Supported Search Engines

| Search Engine | Auto-Detect | Status |
|---------------|-------------|--------|
| Google        | Yes         | Stable |
| Bing          | Yes         | Stable |
| DuckDuckGo    | Yes         | Stable |

Each parser extracts the following fields (when available):

- `title` -- The result heading
- `url` -- The link to the result page
- `snippet` -- The text preview / description
- `position` -- The result's rank on the page

---

## Output Formats

### JSON

```json
[
  {
    "position": 1,
    "title": "Example Domain",
    "url": "https://example.com",
    "snippet": "This domain is for use in illustrative examples..."
  },
  {
    "position": 2,
    "title": "Another Result",
    "url": "https://another.example.com",
    "snippet": "Another example snippet text..."
  }
]
```

### Markdown

```markdown
## 1. Example Domain
**URL:** https://example.com
This domain is for use in illustrative examples...

---

## 2. Another Result
**URL:** https://another.example.com
Another example snippet text...
```

### Dict (Python)

```python
[
    {
        "position": 1,
        "title": "Example Domain",
        "url": "https://example.com",
        "snippet": "This domain is for use in illustrative examples...",
    },
    {
        "position": 2,
        "title": "Another Result",
        "url": "https://another.example.com",
        "snippet": "Another example snippet text...",
    },
]
```

---

## CLI Usage

`search-engine-parser` includes a command-line interface for quick parsing:

```bash
# Parse an HTML file to JSON (auto-detects search engine)
search-engine-parser parse results.html --format json

# Parse with explicit engine
search-engine-parser parse results.html --engine google --format markdown

# Read from stdin
cat results.html | search-engine-parser parse - --format json

# Output to a file
search-engine-parser parse results.html --format json --output results.json
```

---

## Documentation

Full documentation is available at [https://search-engine-parser.github.io/search-engine-parser/](https://search-engine-parser.github.io/search-engine-parser/).

- [Getting Started](https://search-engine-parser.github.io/search-engine-parser/getting_started/)
- [API Reference](https://search-engine-parser.github.io/search-engine-parser/api_reference/)
- [Adding a New Search Engine](https://search-engine-parser.github.io/search-engine-parser/adding_search_engine/)
- [Examples](https://search-engine-parser.github.io/search-engine-parser/examples/basic_usage/)

---

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on the development workflow, how to add new parsers, and how to submit pull requests.

---

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
