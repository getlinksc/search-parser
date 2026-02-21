# Getting Started

## Installation

**Using uv (recommended):**
```bash
uv add search-parser
```

**Using pip:**
```bash
pip install search-parser
```

**With CLI extras:**
```bash
pip install "search-parser[cli]"
```

## Basic Usage

```python
from search_parser import SearchParser

parser = SearchParser()

with open("google_results.html") as f:
    html = f.read()

# JSON string (default)
json_output = parser.parse(html)

# Markdown string
markdown_output = parser.parse(html, output_format="markdown")

# Python dict
data = parser.parse(html, output_format="dict")
```

## Working with Dict Output

`output_format="dict"` returns the full `SearchResults` structure as a Python dictionary.
`results` contains **organic results only** — every other type has its own key:

```python
data = parser.parse(html, output_format="dict")

# Organic results (list, always present)
for result in data["results"]:
    print(f"{result['position']}. {result['title']}")
    print(f"   {result['url']}")
    print(f"   {result['description']}")

# Featured snippet (dict or None)
if data["featured_snippet"]:
    print("Featured:", data["featured_snippet"]["title"])

# AI Overview (dict or None) — Google only
if data["ai_overview"]:
    print("AI Overview:", data["ai_overview"]["description"][:200])
    for source in data["ai_overview"]["metadata"]["sources"]:
        print(f"  Source: {source['title']} — {source['url']}")

# People Also Ask (list) — Google only
for q in data["people_also_ask"]:
    print("PAA:", q["title"])

# What People Are Saying (list) — Google only
for post in data["people_saying"]:
    print("Post:", post["title"], post["url"])

# People Also Search For (list) — Google only
for item in data["people_also_search"]:
    print("Related:", item["title"])

# Sponsored / ads (list)
for ad in data["sponsored"]:
    print("Ad:", ad["title"], ad["url"])

# Related Products & Services (list) — Google only
for product in data["related_products"]:
    print("Product:", product["title"])

# Metadata
print(data["query"])           # "python web scraping"
print(data["total_results"])   # 26200000 or None
print(data["search_engine"])   # "google"
```

## Using the Model Directly

When you want typed access and the `to_json()` / `to_markdown()` convenience methods, call the engine parser directly to get a `SearchResults` object:

```python
from search_parser.parsers.google import GoogleParser

results = GoogleParser().parse(html)

# Typed fields — no dict key lookups, no filtering by result_type
print(results.query)
print(results.total_results)

for r in results.results:  # organic only
    print(r.title, r.url)

if results.featured_snippet:
    print(results.featured_snippet.title)

if results.ai_overview:
    print(results.ai_overview.description)

for q in results.people_also_ask:
    print(q.title)

# Serialize without going through SearchParser
json_str = results.to_json()  # JSON string, indent=2 by default
json_str = results.to_json(indent=4)  # custom indent
md_str = results.to_markdown()  # Markdown string
```

## Specifying the Engine

```python
# Skip auto-detection
result = parser.parse(html, engine="google")
result = parser.parse(html, engine="bing")
result = parser.parse(html, engine="duckduckgo")
```

## CLI Usage

```bash
# JSON output (default)
search-parser results.html

# Markdown output
search-parser results.html --format markdown

# Specify engine manually
search-parser results.html --engine google
```
