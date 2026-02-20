# Search Engine Parser

Parse search engine HTML results into structured data (JSON, Markdown) with auto-detection.

## Features

- **Auto-detection** of Google, Bing, and DuckDuckGo HTML
- **Multiple output formats**: JSON, Markdown, Python dict
- **Extensible** plugin architecture for adding new search engines
- **Type-safe** with Pydantic models and full type hints

## Quick Start

```python
from search_engine_parser import SearchParser

parser = SearchParser()

# Parse HTML and get JSON (default)
json_output = parser.parse(html_string)

# Get Markdown for LLM consumption
markdown_output = parser.parse(html_string, output_format="markdown")

# Get Python dict for programmatic access
dict_output = parser.parse(html_string, output_format="dict")
```

## Supported Search Engines

| Engine | Organic Results | Featured Snippets | Auto-Detection |
|--------|:-:|:-:|:-:|
| Google | Yes | Yes | Yes |
| Bing | Yes | Yes | Yes |
| DuckDuckGo | Yes | - | Yes |
