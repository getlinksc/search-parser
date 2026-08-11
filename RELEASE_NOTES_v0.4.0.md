# Release Notes — v0.4.0

**Released:** 2026-03-05

## What's New

### Google Jobs Widget Parsing

When Google displays a Jobs widget alongside search results (e.g. searching "supply chain director jobs"), those listings are now extracted into a dedicated `jobs` field on `SearchResults`. Job listings are **never mixed into organic results**.

Each job entry includes:

| Field | Description |
|---|---|
| `title` | Job title |
| `metadata["company"]` | Hiring company |
| `metadata["location"]` | Location and source platform (e.g. "San Jose, CA · via Ladders") |
| `metadata["salary"]` | Salary range when shown (e.g. `"150K–200K a year"`) |
| `metadata["employment_type"]` | e.g. `"Full-time"` |
| `metadata["benefits"]` | List of benefits when shown (e.g. `["Health insurance", "Dental insurance"]`) |

```python
results = parser.parse(html)

for job in results.jobs:
    print(job.title)
    print(job.metadata["company"])
    print(job.metadata["location"])
    print(job.metadata.get("salary"))        # None if not listed
    print(job.metadata.get("employment_type"))
    print(job.metadata.get("benefits", []))
```

### Google Discussions and Forums Parsing

Google's "Discussions and forums" widget (Reddit threads, Quora answers, etc.) is now extracted into a dedicated `discussions` field.

Each discussion entry includes:

| Field | Description |
|---|---|
| `title` | Thread or post title |
| `url` | Direct link to the forum post |
| `description` | Excerpt from the post body |
| `metadata["source"]` | Platform, forum, comment count, and age (e.g. `"Reddit · r/supplychain · 10+ comments · 1 year ago"`) |

```python
for disc in results.discussions:
    print(disc.title)
    print(disc.url)
    print(disc.description)
    print(disc.metadata["source"])
```

---

## Migration

No breaking changes. Both `jobs` and `discussions` are new fields that default to an empty list when not present on the page.

---

## Full Changelog

- Added `jobs: list[SearchResult]` field to `SearchResults`
- Added `discussions: list[SearchResult]` field to `SearchResults`
- Added `"job"` and `"discussion"` to the `result_type` Literal in `SearchResult`
- Markdown formatter renders `## Jobs` and `## Discussions and Forums` sections
- 11 new unit tests covering both result types (count, titles, metadata, URLs, descriptions, not-in-organic, empty-when-absent)

[Full diff](https://github.com/getlinksc/search-parser/compare/v0.3.0...v0.4.0)
