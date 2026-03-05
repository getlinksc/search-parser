# Basic Usage

## Parsing Search Results

```python
from search_parser import SearchParser

parser = SearchParser()

with open("results.html") as f:
    json_output = parser.parse(f.read())
```

## Output Formats via SearchParser

```python
# JSON string (default)
json_str = parser.parse(html)

# Markdown string (LLM-friendly)
markdown_str = parser.parse(html, output_format="markdown")

# Python dictionary
data = parser.parse(html, output_format="dict")
```

## Convenience Methods on the Model

When you use an engine parser directly, the returned `SearchResults` object has
`to_json()` and `to_markdown()` methods:

```python
from search_parser.parsers.google import GoogleParser

results = GoogleParser().parse(html)

json_str = results.to_json()  # same as JSONFormatter().format(results)
json_str = results.to_json(indent=4)  # custom indentation
md_str = results.to_markdown()  # same as MarkdownFormatter().format(results)
```

## Accessing Result Types

Every result type lives in its own dedicated field — never mixed into `results`:

```python
data = parser.parse(html, output_format="dict")

# Organic results (always a list)
for r in data["results"]:
    print(f"{r['position']}. {r['title']} — {r['url']}")

# Featured snippet (dict or None)
if data["featured_snippet"]:
    print(data["featured_snippet"]["title"])

# AI Overview with sources (Google only)
if data["ai_overview"]:
    print(data["ai_overview"]["description"])
    for s in data["ai_overview"]["metadata"]["sources"]:
        print(f"  {s['title']}: {s['url']}")

# People Also Ask (Google only)
for q in data["people_also_ask"]:
    print(q["title"])

# Sponsored ads
for ad in data["sponsored"]:
    print(ad["title"], ad["url"])

# What People Are Saying (Google only)
for post in data["people_saying"]:
    print(post["title"], post["url"])

# People Also Search For (Google only)
for item in data["people_also_search"]:
    print(item["title"])

# Related Products & Services (Google only)
for product in data["related_products"]:
    print(product["title"])

# Jobs (Google only)
for job in data["jobs"]:
    print(job["title"], "at", job["metadata"]["company"])
    print("  Location:", job["metadata"]["location"])
    if job["metadata"].get("salary"):
        print("  Salary:", job["metadata"]["salary"])
    if job["metadata"].get("employment_type"):
        print("  Type:", job["metadata"]["employment_type"])

# Discussions and forums (Google only)
for disc in data["discussions"]:
    print(disc["title"])
    print("  URL:", disc["url"])
    print("  Source:", disc["metadata"]["source"])
    if disc["description"]:
        print("  Excerpt:", disc["description"][:100])
```

## Specifying the Engine

```python
# Skip auto-detection
result = parser.parse(html, engine="google")
result = parser.parse(html, engine="bing")
result = parser.parse(html, engine="duckduckgo")
```
