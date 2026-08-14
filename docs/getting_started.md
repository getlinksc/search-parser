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
    # Optional Google rich-result fields
    print("   Display URL:", result["metadata"].get("display_url"))
    print("   Rating:", result["metadata"].get("rating"))
    print("   Reviews:", result["metadata"].get("reviews"))
    for sitelink in result["metadata"].get("sitelinks", []):
        print("   Sitelink:", sitelink["title"], sitelink["url"])

# Featured snippet (dict or None)
if data["featured_snippet"]:
    print("Featured:", data["featured_snippet"]["title"])

# AI Overview (dict or None) — Google only
if data["ai_overview"]:
    print("AI Overview:", data["ai_overview"]["description"][:200])
    for source in data["ai_overview"]["metadata"]["sources"]:
        print(f"  Source: {source.get('source', source['title'])} — {source['url']}")
    for detail in data["ai_overview"]["metadata"].get("details", []):
        print("  Detail:", detail)

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
    print("  Display URL:", ad["metadata"].get("display_url"))
    print("  Rating:", ad["metadata"].get("rating"))
    print("  Phone:", ad["metadata"].get("phone"))
    for sitelink in ad["metadata"].get("sitelinks", []):
        print("  Sitelink:", sitelink["title"], sitelink["url"])

# Related Products & Services (list) — Google only
for product in data["related_products"]:
    print("Product:", product["title"])

# Jobs (list) — Google only
# Each job has metadata: company, location, salary (optional), employment_type, benefits
for job in data["jobs"]:
    print("Job:", job["title"])
    print("  Company:", job["metadata"]["company"])
    print("  Location:", job["metadata"]["location"])
    print("  Salary:", job["metadata"].get("salary"))          # None if not listed
    print("  Type:", job["metadata"].get("employment_type"))
    print("  Benefits:", job["metadata"].get("benefits", []))

# Discussions and forums (list) — Google only
# Each entry has a url, description excerpt, and metadata["source"]
for disc in data["discussions"]:
    print("Discussion:", disc["title"])
    print("  URL:", disc["url"])
    print("  Source:", disc["metadata"]["source"])

# Shopping ads (list) — Google only
# Each entry has metadata["price"] and metadata["merchant"]
for ad in data["shopping_ads"]:
    print("Ad:", ad["title"])
    print("  Price:", ad["metadata"]["price"])
    print("  Merchant:", ad["metadata"]["merchant"])

# News tab articles (list) — Google only (tbm=nws pages)
# Each entry has metadata["source"] (publisher) and metadata["published_time"]
for article in data["news"]:
    print("News:", article["title"])
    print("  URL:", article["url"])
    print("  Source:", article["metadata"]["source"])
    print("  Published:", article["metadata"]["published_time"])

# Metadata
print(data["query"])           # "python web scraping"
print(data["total_results"])   # 26200000 or None
print(data["search_engine"])   # "google"
print(data["metadata"].get("location"))
print(data["metadata"].get("location_source"))
print(data["metadata"].get("pagination", {}).get("next_url"))
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
    print(r.metadata.get("display_url"), r.metadata.get("rating"))

if results.featured_snippet:
    print(results.featured_snippet.title)

if results.ai_overview:
    print(results.ai_overview.description)
    print(results.ai_overview.metadata.get("details", []))

for ad in results.sponsored:
    print(ad.title, ad.metadata.get("display_url"), ad.metadata.get("phone"))

for q in results.people_also_ask:
    print(q.title)

for job in results.jobs:
    print(job.title, job.metadata["company"], job.metadata.get("salary"))

for disc in results.discussions:
    print(disc.title, disc.url)

for ad in results.shopping_ads:
    print(ad.title, ad.metadata["price"], ad.metadata["merchant"])

for article in results.news:
    print(article.title, article.url)
    print(article.metadata["source"], article.metadata["published_time"])

# Serialize without going through SearchParser
json_str = results.to_json()  # JSON string, indent=2 by default
json_str = results.to_json(indent=4)  # custom indent
md_str = results.to_markdown()  # Markdown string
```

Google only emits rich metadata when the corresponding markup exists. See
[Google Parsing](google.md) for every organic, sponsored, AI Overview, location,
and pagination field.

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
