# Search Engine Parser

Parse search engine HTML results into structured data (JSON, Markdown) with auto-detection.

## Features

- **Auto-detection** of Google, Bing, and DuckDuckGo HTML — desktop and mobile layouts
- **Dedicated fields** for every result type — organic results, featured snippets, AI Overviews, People Also Ask, sponsored ads, shopping ads, and more
- **Multiple output formats**: JSON, Markdown, Python dict
- **Convenience methods**: `results.to_json()` and `results.to_markdown()` directly on the model
- **Extensible** plugin architecture for adding new search engines
- **Type-safe** with Pydantic models and full type hints

## Quick Start

```python
from search_parser import SearchParser

parser = SearchParser()

# Parse HTML and get JSON (default)
json_output = parser.parse(html_string)

# Get Markdown for LLM consumption
markdown_output = parser.parse(html_string, output_format="markdown")

# Get Python dict for programmatic access
data = parser.parse(html_string, output_format="dict")

# Organic results
for result in data["results"]:
    print(result["title"], result["url"])

# Dedicated fields — no filtering needed
if data["featured_snippet"]:
    print(data["featured_snippet"]["title"])

if data["ai_overview"]:
    print(data["ai_overview"]["description"])

for q in data["people_also_ask"]:
    print(q["title"])

# Shopping ads (Google only)
for ad in data["shopping_ads"]:
    print(ad["title"], ad["metadata"]["price"], ad["metadata"]["merchant"])

# Local business pack (Google only)
for biz in data["local_businesses"]:
    print(biz["title"], biz["metadata"].get("rating"), biz["metadata"].get("phone"))
```

Or work directly with the typed model and use `to_json()` / `to_markdown()`:

```python
from search_parser.parsers.google import GoogleParser

results = GoogleParser().parse(html_string)

print(results.query)
print(results.total_results)
print(results.featured_snippet.title if results.featured_snippet else "no snippet")

json_str = results.to_json()
md_str = results.to_markdown()
```

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
| Jobs | `jobs` | ✓ | — | — |
| Discussions and forums | `discussions` | ✓ | — | — |
| Shopping ads | `shopping_ads` | ✓ | — | — |
| Local business pack | `local_businesses` | ✓ | — | — |
