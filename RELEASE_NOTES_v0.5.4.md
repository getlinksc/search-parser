# Release Notes — v0.5.4

**Released:** 2026-06-06

## What's New

### Google Local Business Pack Parsing

When Google displays a local business pack alongside search results (e.g. searching "personal injury lawyer near me"), those listings are now extracted into a dedicated `local_businesses` field on `SearchResults`. Local business results are **never mixed into organic results**.

Each entry includes:

| Field | Description |
|---|---|
| `title` | Business name |
| `metadata["rating"]` | Star rating (e.g. `"4.9"`) |
| `metadata["reviews"]` | Review count (e.g. `"813"`) |
| `metadata["category"]` | Business category (e.g. `"Personal injury attorney"`) |
| `metadata["location"]` | City and state (e.g. `"Alexandria, VA"`) |
| `metadata["hours"]` | Hours string (e.g. `"Open 24 hours"`) |
| `metadata["phone"]` | Phone number (e.g. `"(703) 884-1863"`) |
| `metadata["sponsored"]` | `True` when the listing is a paid placement |

```python
results = parser.parse(html)

for biz in results.local_businesses:
    print(biz.title)
    print(biz.metadata["rating"], f"({biz.metadata.get('reviews')} reviews)")
    print(biz.metadata.get("category"))
    print(biz.metadata.get("location"))
    print(biz.metadata.get("phone"))
    print(biz.metadata.get("hours"))

    if biz.metadata.get("sponsored"):
        print("  (sponsored)")
```

---

## Bug Fixes

### Startup crash: `ModuleNotFoundError: No module named 'search_parser.parsers.google_finance'`

Any application importing `search_parser` would crash at startup because `search_parser.parsers.google_finance` and the entire `search_parser.scrapers` module were missing from the built package. The source files existed but had never been committed to git, so they were excluded from the wheel. This release includes those files and the issue is resolved.

---

## Migration

No breaking changes. `local_businesses` is a new field that defaults to an empty list when no local pack is present on the page. `"local_business"` has been added to the `result_type` Literal, but existing comparisons against other types are unaffected.

---

## Full Changelog

- Added `local_businesses: list[SearchResult]` field to `SearchResults`
- Added `"local_business"` to the `result_type` Literal in `SearchResult`
- Added `_extract_local_businesses` and `_parse_local_business` methods to `GoogleParser`
- `_parse_local_business` extracts name, rating, review count, category, location, hours, phone, and sponsored flag from `div.cXedhc` cards
- Markdown formatter renders `## Local Businesses` section with all available metadata fields
- Added fixture `personal_injury_lawyer_20260528_203801.html` and `iphone_15_review_20260528_204042.html` to conftest
- Fixed `ModuleNotFoundError` on startup — `parsers/google_finance.py` and `scrapers/` were missing from the built package due to uncommitted source files

[Full diff](https://github.com/getlinksc/search-parser/compare/v0.5.3...v0.5.4)
