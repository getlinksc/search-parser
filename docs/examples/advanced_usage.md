# Advanced Usage

## Batch Processing

```python
import json
from pathlib import Path
from search_parser import SearchParser

parser = SearchParser()

for html_file in Path("html_files").glob("*.html"):
    html = html_file.read_text()
    data = parser.parse(html, output_format="dict")
    output = html_file.with_suffix(".json")
    output.write_text(json.dumps(data, indent=2, default=str))
    print(f"{html_file.name}: {len(data['results'])} organic results")
```

## Custom Formatters

```python
import csv
import io
from search_parser.core.models import SearchResults
from search_parser.formatters.base import BaseFormatter


class CSVFormatter(BaseFormatter):
    def format(self, results: SearchResults) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["position", "title", "url", "description"])
        for r in results.results:
            writer.writerow([r.position, r.title, r.url, r.description or ""])
        return output.getvalue()
```

Use it with the engine parser directly (which returns a `SearchResults` object):

```python
from search_parser.parsers.google import GoogleParser

results = GoogleParser().parse(html)
csv_output = CSVFormatter().format(results)
```

## Accessing Dedicated Fields

Each result type has its own field on `SearchResults` — no filtering by `result_type` needed:

```python
from search_parser.parsers.google import GoogleParser

results = GoogleParser().parse(html)

# Organic results
print(f"{len(results.results)} organic results")

# Featured snippet
if results.featured_snippet:
    print(results.featured_snippet.title)
    print(results.featured_snippet.description)

# AI Overview
if results.ai_overview:
    print(results.ai_overview.description[:300])
    for source in results.ai_overview.metadata["sources"]:
        print(f"  {source['title']}: {source['url']}")

# People Also Ask
for q in results.people_also_ask:
    print(q.title)

# Sponsored ads
for ad in results.sponsored:
    print(ad.title, ad.url)

# Social posts
for post in results.people_saying:
    print(post.title, post.url)

# Related search terms
for item in results.people_also_search:
    print(item.title)

# Product / service suggestions
for product in results.related_products:
    print(product.title, product.url)

# Jobs — metadata includes company, location, salary, employment_type, benefits
for job in results.jobs:
    print(job.title)
    print(f"  {job.metadata['company']} — {job.metadata['location']}")
    if job.metadata.get("salary"):
        print(f"  Salary: {job.metadata['salary']}")

# Discussions and forums — metadata["source"] has platform + comment count + age
for disc in results.discussions:
    print(disc.title)
    print(f"  {disc.url}")
    print(f"  {disc.metadata['source']}")

# Shopping ads — metadata["price"] and metadata["merchant"]
for ad in results.shopping_ads:
    print(ad.title)
    print(f"  {ad.metadata['price']} from {ad.metadata['merchant']}")
    print(f"  {ad.url}")

# News tab articles — metadata["source"] (publisher) and metadata["published_time"]
for article in results.news:
    print(article.title)
    print(f"  {article.metadata['source']} · {article.metadata['published_time']}")
    print(f"  {article.url}")
```

## Using to_json() and to_markdown()

The `SearchResults` model exposes `to_json()` and `to_markdown()` so you can format
results without going through `SearchParser`:

```python
results = GoogleParser().parse(html)

# Write JSON to a file
Path("output.json").write_text(results.to_json())

# Write Markdown to a file
Path("output.md").write_text(results.to_markdown())

# Feed Markdown directly to an LLM prompt
prompt = f"Summarize these search results:\n\n{results.to_markdown()}"
```

## Error Handling

```python
from search_parser import SearchParser
from search_parser.exceptions import (
    SearchEngineDetectionError,
    ParserNotFoundError,
    ParseError,
)

parser = SearchParser()
try:
    result = parser.parse(html)
except SearchEngineDetectionError:
    # Auto-detection failed — specify the engine manually
    result = parser.parse(html, engine="google")
except ParserNotFoundError as e:
    print(f"No parser available: {e}")
except ParseError as e:
    print(f"Parsing failed: {e}")
```
