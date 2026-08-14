# search-parser

[![PyPI](https://img.shields.io/pypi/v/search-parser)](https://pypi.org/project/search-parser/)
[![Python Versions](https://img.shields.io/pypi/pyversions/search-parser)](https://pypi.org/project/search-parser/)
[![Tests](https://github.com/getlinksc/search-parser/actions/workflows/test.yml/badge.svg)](https://github.com/getlinksc/search-parser/actions/workflows/test.yml)
[![Lint](https://github.com/getlinksc/search-parser/actions/workflows/lint.yml/badge.svg)](https://github.com/getlinksc/search-parser/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/getlinksc/search-parser/branch/main/graph/badge.svg)](https://codecov.io/gh/getlinksc/search-parser)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Parse Google, Bing, DuckDuckGo, and Google Maps search results into typed Python objects, JSON, Markdown, or dict output.**

`search-parser` takes raw HTML from Google, Bing, and DuckDuckGo — desktop, mobile, or Google's stripped no-JS layout — and extracts every result type — organic results, featured snippets, AI Overviews, People Also Ask, sponsored ads, shopping ads, and more — into clean, typed Python objects. It auto-detects the search engine from the HTML, so you never have to specify which parser to use.

---

## Quick Start

```python
from search_parser import SearchParser

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
    # Google rich fields are optional and live under metadata
    print(f"   {result['metadata'].get('rating', 'no rating')}")

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

### Structured Google Maps results

`GoogleMapsParser` handles the XSSI-prefixed JSON from Google's non-JavaScript
`tbm=map` transport. The request builder remains outside this parsing library.

```python
from search_parser import GoogleMapsParser

places = GoogleMapsParser().parse(response_text, query="coffee chicago")
for place in places.places:
    print(place.name, place.website, place.rating, place.latitude, place.longitude)
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
| Jobs | `jobs` | ✓ | — | — |
| Discussions and forums | `discussions` | ✓ | — | — |
| Shopping ads | `shopping_ads` | ✓ | — | — |
| News tab articles | `news` | ✓ | — | — |
| Local business pack | `local_businesses` | ✓ | — | — |

---

## Working with Results

`SearchParser.parse()` with `output_format="dict"` returns the full `SearchResults` structure:

```python
data = parser.parse(html, output_format="dict")

# Always a list (organic results only)
for r in data["results"]:
    print(r["title"], r["url"], r["description"])
    print(r["metadata"].get("display_url"))
    print(r["metadata"].get("rating"), r["metadata"].get("reviews"))
    for sitelink in r["metadata"].get("sitelinks", []):
        print("  Sitelink:", sitelink["title"], sitelink["url"])

# None or a single object
if data["featured_snippet"]:
    print(data["featured_snippet"]["title"])

# None or a single object with description + sources list
if data["ai_overview"]:
    overview = data["ai_overview"]
    print(overview["description"])
    for source in overview["metadata"]["sources"]:
        print(f"  - {source.get('source', source['title'])}: {source['url']}")
    for detail in overview["metadata"].get("details", []):
        print(f"  - {detail}")

# Always a list (empty when not present)
for q in data["people_also_ask"]:
    print(q["title"])

for post in data["people_saying"]:
    print(post["title"], post["url"])

for item in data["people_also_search"]:
    print(item["title"])

for ad in data["sponsored"]:
    print(ad["title"], ad["url"])
    print(ad["metadata"].get("display_url"), ad["metadata"].get("phone"))
    for sitelink in ad["metadata"].get("sitelinks", []):
        print("  Sitelink:", sitelink["title"])

for product in data["related_products"]:
    print(product["title"])

# Jobs (title, metadata["company"], metadata["location"])
for job in data["jobs"]:
    print(job["title"], job["metadata"]["company"], job["metadata"]["location"])

# Discussions (title, url, description, metadata["source"])
for disc in data["discussions"]:
    print(disc["title"], disc["url"])
    print(disc["metadata"]["source"])

# Shopping ads (title, metadata["price"], metadata["merchant"])
for ad in data["shopping_ads"]:
    print(ad["title"], ad["metadata"]["price"], ad["metadata"]["merchant"])

# News tab articles (Google News tab, tbm=nws) — metadata["source"] and metadata["published_time"]
for article in data["news"]:
    print(article["title"], article["url"])
    print(article["metadata"]["source"], article["metadata"]["published_time"])

# Metadata
print(data["search_engine"])        # "google"
print(data["query"])                # "python web scraping"
print(data["total_results"])        # 26200000 or None
print(data["detection_confidence"]) # 0.95
print(data["metadata"].get("location"))
print(data["metadata"].get("location_source"))
print(data["metadata"].get("pagination", {}).get("next_url"))
```

### Using the model directly

When you need the typed `SearchResults` object instead of a dict, call the engine parser directly. The model exposes `to_json()` and `to_markdown()` convenience methods:

```python
from search_parser.parsers.google import GoogleParser

parser = GoogleParser()
results = parser.parse(html)  # returns SearchResults

# Typed access — no dict key lookups
print(results.query)
print(results.total_results)
print(len(results.results))  # organic count

if results.featured_snippet:
    print(results.featured_snippet.title)

if results.ai_overview:
    print(results.ai_overview.description)
    sources = results.ai_overview.metadata["sources"]
    details = results.ai_overview.metadata.get("details", [])

for result in results.results:
    print(result.metadata.get("display_url"))
    print(result.metadata.get("rating"), result.metadata.get("reviews"))

for ad in results.sponsored:
    print(ad.title, ad.metadata.get("display_url"), ad.metadata.get("phone"))

for q in results.people_also_ask:
    print(q.title)

for post in results.people_saying:
    print(post.title, post.url)

for ad in results.shopping_ads:
    print(ad.title, ad.metadata["price"], ad.metadata["merchant"])

for article in results.news:
    print(article.title, article.url)
    print(article.metadata["source"], article.metadata["published_time"])

# Convert to JSON or Markdown directly on the model
json_str = results.to_json()
json_str = results.to_json(indent=4)  # custom indent
md_str = results.to_markdown()
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
      "metadata": {
        "display_url": "realpython.com › tutorials",
        "published_time": "Feb 26, 2024",
        "sitelinks": [
          {"title": "Python Tutorials", "url": "https://realpython.com/tutorials/python/"}
        ]
      }
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
        {"title": "Beautiful Soup", "url": "https://www.crummy.com/software/BeautifulSoup/", "source": "Beautiful Soup"},
        {"title": "Requests", "url": "https://requests.readthedocs.io/", "source": "Requests"}
      ],
      "details": ["HTML parsers turn result markup into a searchable tree."]
    }
  },
  "people_also_ask": [
    {"title": "Is Python good for web scraping?", "url": "", "position": 0, "result_type": "people_also_ask", "metadata": {}}
  ],
  "sponsored": [
    {
      "title": "Sponsored result",
      "url": "http://www.google.com/aclk?...",
      "description": "An advertiser description.",
      "position": 0,
      "result_type": "sponsored",
      "metadata": {
        "display_url": "www.example.com/",
        "rating": "4.7",
        "phone": "(800) 555-0100",
        "sitelinks": [{"title": "Current offers", "url": "http://www.google.com/aclk?..."}]
      }
    }
  ],
  "people_saying": [],
  "people_also_search": [],
  "related_products": [],
  "jobs": [
    {
      "title": "Global Supply Chain Director",
      "url": "https://www.google.com/search?q=%22Supply+Chain+Director&udm=8",
      "description": null,
      "position": 0,
      "result_type": "job",
      "metadata": {
        "company": "InterSources, Inc.",
        "location": "San Jose, CA  •  via Ladders"
      }
    }
  ],
  "discussions": [
    {
      "title": "Being considered for Director of Supply Chain",
      "url": "https://www.reddit.com/r/supplychain/comments/1ib0c1a/being_considered_for_director_of_supply_chain/",
      "description": "I work for a mid-sized company as a Procurement Manager...",
      "position": 0,
      "result_type": "discussion",
      "metadata": {
        "source": "Reddit · r/supplychain · 10+ comments · 1 year ago"
      }
    }
  ],
  "shopping_ads": [
    {
      "title": "ALCON - Precision7 , 12 Pack",
      "url": "http://www.google.com/aclk?sa=L&ai=...",
      "description": null,
      "position": 0,
      "result_type": "shopping_ad",
      "metadata": {
        "price": "$51.19",
        "merchant": "Contacts Direct"
      }
    }
  ],
  "news": [],
  "detection_confidence": 0.95,
  "parsed_at": "2026-02-21T00:00:00Z",
  "metadata": {
    "location": "Washington DC (Hagerstown MD), Virginia",
    "location_source": "From your IP address",
    "pagination": {
      "next_url": "https://www.google.com/search?q=python+web+scraping&start=10&sa=N",
      "next_start": 10
    }
  }
}
```

Google only returns rich fields when they are present in the source HTML. See the
[Google parser reference](https://getlinksc.github.io/search-parser/google/) for the
complete metadata schema and Google no-JS behavior.

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

---

## Jobs

### Global Supply Chain Director

**Company:** InterSources, Inc.
**Location:** San Jose, CA  •  via Ladders
**URL:** https://www.google.com/search?q=%22Supply+Chain+Director&udm=8

---

## Discussions and Forums

### Being considered for Director of Supply Chain

I work for a mid-sized company as a Procurement Manager...

**URL:** https://www.reddit.com/r/supplychain/comments/1ib0c1a/being_considered_for_director_of_supply_chain/

## Shopping Ads

### ALCON - Precision7 , 12 Pack

**Price:** $51.19
**Merchant:** Contacts Direct
**URL:** http://www.google.com/aclk?sa=L&ai=...

## News Results

### 1. Python web scraping tutorial released

**Source:** Real Python · 2 days ago

Learn how to scrape websites with Python using BeautifulSoup and Requests...

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
