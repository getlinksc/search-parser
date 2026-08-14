# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Documentation

- Expanded the Google Maps guide with the complete typed field contract,
  serialization, detection/error behavior, and monitoring guidance

---

## [0.5.8] - 2026-08-14

### Added

- `GoogleMapsParser` for the XSSI-prefixed JSON returned by Google's non-JavaScript
  `tbm=map` transport
- Typed `GoogleMapsPlace` and `GoogleMapsResults` models covering place IDs,
  direct websites, addresses, coordinates, ratings, categories, phones, photos,
  time zones, and displayed opening hours
- Positional-schema validation, duplicate suppression, redirect decoding, plain-JSON
  support, public exports, focused unit tests, and a Google Maps usage guide

---

## [0.5.7] - 2026-08-14

### Added

- No-JS mobile organic rich metadata: `display_url`, `rating`, `reviews`, `attributes`, `published_time`, and decoded `sitelinks` are now preserved in each result's `metadata`
- No-JS mobile text ads from `data-text-ad="1"` cards are parsed into `sponsored`, including display URL, advertiser rating, description, sitelinks, and phone number. Repeated top/bottom copies are merged without losing metadata that appears in only one placement
- AI Overview citation cards and expanded facts embedded in Google's inert `window.jsl.dh(...)` HTML strings are decoded without executing JavaScript. Citations are returned in `ai_overview.metadata["sources"]`, including source names, and expanded facts in `ai_overview.metadata["details"]`
- No-JS mobile "People also search for" cards are returned through `people_also_search`
- Page-level location, location source, next/previous page URLs, and result offsets are returned through `SearchResults.metadata`
- Compact no-JS mobile rich-results regression fixture based on a live proxy response, with seven focused tests for the new fields

### Fixed

- No-JS mobile organic descriptions no longer include rating, review, delivery, publication-date, or sitelink text rendered beside the actual snippet

### Documentation

- Added a complete Google metadata reference and updated the README, site home, getting-started guide, API guidance, parser-author guidance, and basic/advanced examples for rich organic results, sponsored ads, AI citations/details, related searches, location, and pagination

---

## [0.5.6] - 2026-08-14

### Added

- Google no-JS mobile layout support. The stripped page reuses the mobile `div.xpd` shell but puts the title in an `h3.zBAuLc` inside the result anchor instead of an `egMi0` block, so `parse()` returned zero organic results for it. `_find_no_js_mobile_organic_results` and `_parse_no_js_mobile_organic_result` handle that layout; `_find_organic_results` falls through to it only when the desktop and `egMi0` mobile selectors find nothing
- `tests/fixtures/google/no_js_mobile_claude.html` — a real no-JS mobile SERP (9 organic results), with tests covering count, positions, redirect decoding, titles, and detection confidence

### Fixed

- No-JS mobile snippets no longer swallow sitelink text: sitelinks are nested anchors inside the same `div.lQigmf` description block, so they are dropped from a copy of the tag before the snippet text is collected

---

## [0.5.5] - 2026-08-11

### Fixed

- Desktop organic results returned Google redirect hrefs (`/url?q=https%3A%2F%2F...`) raw instead of the destination URL — `_parse_organic_result` now runs both desktop branches through `_decode_google_redirect`, matching what the mobile path already did
- `__version__` was pinned at `0.5.3` while `pyproject.toml` shipped `0.5.4`, so `search_parser.__version__` reported the wrong release — both are now bumped together

### Changed

- `_decode_google_redirect` docstring documents that some Google buckets serve `/goto?url=<blob>` hrefs which are encrypted server-side; the destination is not present anywhere in the HTML, so those are returned unchanged for the caller to resolve over the network

### Chore

- Cleared all outstanding `ruff check` errors (unused `json`/`pytest` imports, `try`/`except`/`pass` → `contextlib.suppress`, lambda assignment → `def`) and applied `ruff format` to the four files that were failing `--check`, so the lint workflow passes
- Cleared the two `mypy` errors in `scrapers/google_finance.py` — the `requests` batchexecute payload list is annotated `list[dict[str, Any]]` so its element type is no longer joined down to `object`
- Raised the tooling Python target to match `requires-python = ">=3.10"` (mypy `python_version` and ruff `target-version` were both still on 3.9; mypy 1.x rejects `python_version = "3.9"` outright), and dropped the stale `markdownify.*` mypy override
- Dropped Python 3.9 from the test matrix and the trove classifiers — `requires-python` has been `>=3.10` since 0.5.3, so the 3.9 leg could only ever fail at `uv sync`
- CI hardening: the coverage badge step is skipped when `GIST_SECRET`/`GIST_ID` are unset and tolerated when the gist API rejects them (a cosmetic badge write to an external gist no longer reds the pipeline); the publish job declares `contents: read` explicitly (declaring any `permissions` key drops the defaults, which breaks `actions/checkout`) and fails fast if the release tag does not match the version in `pyproject.toml`

---

## [0.5.4] - 2026-06-06

### Added

- `local_businesses: list[SearchResult]` field on `SearchResults` for Google local business pack results
- `"local_business"` added to the `result_type` Literal in `SearchResult`
- `_extract_local_businesses` and `_parse_local_business` methods on `GoogleParser` — extracts name, rating, review count, category, location, hours, phone, and sponsored flag from `div.cXedhc` cards
- Markdown formatter renders `## Local Businesses` section with all available metadata fields
- New fixtures (`personal_injury_lawyer_20260528_203801.html`, `iphone_15_review_20260528_204042.html`) and 16 new unit tests

### Fixed

- `search_parser.parsers.google_finance` and `search_parser.scrapers` were missing from the built package because the source files had never been committed to git — any app importing `search_parser` crashed at startup with `ModuleNotFoundError`

---

## [0.5.2] - 2026-04-26

### Added

- **`GoogleFinanceParser`** — parses Google Finance HTML pages by extracting the
  embedded `AF_initDataCallback` data blocks (no network calls required).
  Supports stocks, ETFs, indices, crypto, and FX pairs.  Returns a
  `SearchResults` object with dedicated fields:
  - `stock_quote` — price, change, change %, previous close, currency, timezone,
    after-hours data
  - `company_info` — description, CEO, employees, market cap, P/E ratio,
    52-week range, sector, headquarters
  - `stock_chart` — time-series of date / price / volume points
  - `financial_news` — news items with title, URL, source, and Unix timestamp
  - `financial_statements` — income statement, balance sheet, and cash flow
    data (stocks only; uses recursive positional-array detection)

- **`GoogleFinanceScraper`** — standalone class that fetches live data from
  Google Finance's internal `batchexecute` RPC endpoint using only the Python
  standard library (`urllib`).  No API key required.  Returns typed dataclasses
  (`GoogleFinanceData`, `FinancialQuote`, `CompanyInfo`, `ChartData`,
  `ChartPoint`, `NewsItem`, `FinancialStatement`).

- **New `result_type` literals** — `stock_quote`, `company_info`, `stock_chart`,
  `financials`, `financial_news` added to `SearchResult.result_type`.

- **New `SearchResults` fields** — `stock_quote`, `company_info`, `stock_chart`,
  `financial_statements`, `financial_news` (all default to `None` / `[]` so
  existing code is unaffected).

- **Auto-detection** — `SearchEngineDetector` now recognises Google Finance
  pages (canonical URL or `AF_dataServiceRequests` script marker) before
  falling through to the generic Google check.

### Usage

```python
# Parse a saved Google Finance HTML page
from search_parser import GoogleFinanceParser

parser = GoogleFinanceParser()
results = parser.parse(html)

print(results.query)                          # "GOOGL:NASDAQ"
print(results.stock_quote.metadata["price"]) # 339.32
print(results.company_info.metadata["ceo"])  # "Sundar Pichai"
print(results.financial_news[0].title)

# Fetch live data (no API key needed)
from search_parser import GoogleFinanceScraper

scraper = GoogleFinanceScraper()
data = scraper.scrape("GOOGL:NASDAQ")   # stocks
data = scraper.scrape("BTC-USD")        # crypto
data = scraper.scrape("EUR-USD")        # FX

print(data.quote.price)
print(data.company.sector)
print(data.chart.points[0].date)
```

---

## [0.5.1] - 2026-04-08

### Fixed

- **JSON output: non-ASCII characters no longer escaped** — `JSONFormatter`, `SearchResults.to_json()`, and the `"dict"` output path in `SearchParser.parse()` all previously relied on Pydantic's `model_dump_json()` / `serde_json`, which escapes every non-ASCII character as `\uXXXX`. They now use `model_dump(mode="json")` + `json.dumps(..., ensure_ascii=False)`, so Korean, Japanese, Arabic, and all other non-Latin scripts are emitted as literal UTF-8 characters.

---

## [0.5.0] - 2026-04-08

### Added

- **Google parser: News Tab** — new `news` field on `SearchResults` containing articles from the Google News tab (`tbm=nws`). Each entry has `result_type="news"` with `metadata["source"]` (publisher name) and `metadata["published_time"]` (e.g. "2 days ago"). News articles are never included in the organic `results` list.
- New `result_type` value `"news"` is now backed by a dedicated `news` field on `SearchResults` (the type was previously defined in the Literal but had no dedicated field).
- Markdown formatter now renders a `## News Results` section with position, source, published time, description, and URL when `news` results are present, using the new `_format_news()` method.
- 13 new unit tests covering news tab parsing (count, result type, positions, titles, URLs, descriptions, source metadata, published time, isolation from organic, total results, detection confidence, and empty-page fallback).

---

## [0.4.1] - 2026-03-05

### Added

- **Google parser: Mobile HTML support** — organic results from mobile Google pages (using `div.xpd` / `egMi0` layout) are now parsed correctly. URLs are decoded from Google's `/url?q=...` redirect format to the actual destination. People Also Ask, People Also Search For, and AI Overview are also extracted from the mobile layout.
- **Google parser: Shopping Ads** — new `shopping_ads` field on `SearchResults` containing product cards from Google Shopping units (mobile `wywECb`/`qvfQJe` layout). Each entry has `result_type="shopping_ad"` with `metadata["price"]` and `metadata["merchant"]`. Shopping ads are never included in the organic `results` list.
- New `result_type` value `"shopping_ad"` added to the `SearchResult` model's Literal type.
- Markdown formatter now renders a `## Shopping Ads` section when `shopping_ads` are present.
- 14 new unit tests covering mobile organic results (count, positions, URL decoding, titles), mobile PAA, mobile PASF, mobile AI Overview, and shopping ads (count, titles, prices, merchants, isolation).

---

## [0.4.0] - 2026-03-05

### Added

- **Google parser: Jobs** — new `jobs` field on `SearchResults` containing job listings from the Google Jobs widget. Each entry has `result_type="job"` with `metadata["company"]` and `metadata["location"]` fields. Jobs are never included in the organic `results` list.
- **Google parser: Discussions and forums** — new `discussions` field on `SearchResults` containing entries from the "Discussions and forums" widget. Each entry has `result_type="discussion"` with a `description` excerpt and `metadata["source"]` (platform, forum, comment count, and date).
- New `result_type` values `"job"` and `"discussion"` added to the `SearchResult` model's Literal type.
- Markdown formatter now renders `## Jobs` and `## Discussions and Forums` sections when those fields are present.
- Unit tests for jobs and discussions parsing using the `supply-chain-director-jobs.html` fixture.

---

## [0.3.0] - 2026-02-21

### Changed

- Renamed all stale `search_engine_parser` references to `search_parser` across config, docs, and CI workflows.
- Fixed `pyproject.toml`: CLI entry point, hatch build target, and mypy `files` path all now point to `src/search_parser`.
- Synced `__version__.py` to match `pyproject.toml`.
- Added author and publisher metadata (`linksc`, `hello@link.sc`) to `pyproject.toml`.
- Updated package description with explicit search engine names and output formats for better discoverability.

---

## [0.2.0] - 2026-02-20

### Added

- `SearchResults.to_json(indent=2)` — serialize results directly to a JSON string without going through `SearchParser`.
- `SearchResults.to_markdown()` — render results directly to a Markdown string without going through `SearchParser`.
- `SearchResults.total_results` — Google parser now extracts the "About X results" count from `div#result-stats`.
- **Google parser: AI Overview** — new `ai_overview` field on `SearchResults` containing the summary text and a `metadata["sources"]` list of `{title, url}` citations.
- **Google parser: People Also Ask** — new `people_also_ask` field, a list of PAA questions extracted from `related-question-pair` elements.
- **Google parser: What People Are Saying** — new `people_saying` field, a list of social posts from the "What people are saying" carousel.
- **Google parser: People Also Search For** — new `people_also_search` field, a list of related-search carousel items.
- **Google parser: Find Related Products & Services** — new `related_products` field, a list of ad suggestion links.

### Changed

- **Breaking:** `SearchResults.results` now contains **organic results only**. All other result types have been moved to dedicated typed fields:
  - `SearchResults.sponsored: list[SearchResult]` — sponsored / ad results (was mixed into `results`)
  - `SearchResults.featured_snippet: SearchResult | None` — featured snippet (was mixed into `results`)
  - `SearchResults.ai_overview: SearchResult | None` — AI Overview (new)
  - `SearchResults.people_also_ask: list[SearchResult]` — PAA questions (new)
  - `SearchResults.people_saying: list[SearchResult]` — social posts (new)
  - `SearchResults.people_also_search: list[SearchResult]` — related search items (new)
  - `SearchResults.related_products: list[SearchResult]` — product ad suggestions (new)

### Fixed

- **Security:** `SearchEngineDetector._check_url_patterns` replaced substring `in href` checks with `urlparse` hostname parsing against an explicit allowlist (`_ALLOWED_HOSTS`), preventing false positives from URLs like `http://evil.com/google.com`.
- **Security:** `DuckDuckGoParser.can_parse` replaced `"duckduckgo.com" in href` substring check with `urlparse` hostname comparison (exact match or `.duckduckgo.com` subdomain).
- **CI:** Added explicit `permissions: contents: read` blocks to `test.yml`, `lint.yml`, and `coverage-badge.yml` workflows to follow least-privilege GITHUB_TOKEN scoping.

### Migration

If you were filtering `results.results` by `result_type`, update your code:

```python
# Before
featured = [r for r in results.results if r.result_type == "featured_snippet"]
sponsored = [r for r in results.results if r.result_type == "sponsored"]

# After
featured = results.featured_snippet  # SearchResult | None
sponsored = results.sponsored         # list[SearchResult]
```

---

## [0.1.0] - 2025-01-01

### Added

- Initial release of `search-parser`.
- Core parsing framework with `BaseParser` and `SearchResult` data model.
- Google search results parser with auto-detection.
- Bing search results parser with auto-detection.
- DuckDuckGo search results parser with auto-detection.
- Auto-detection of search engine from raw HTML content.
- Three output formats: JSON, Markdown, and Python dict.
- Command-line interface (`search-parser parse`).
- Comprehensive test suite with HTML fixtures.
- Documentation site using MkDocs with Material theme.
- CI/CD workflows for testing, linting, coverage, and publishing.
- Pre-commit hooks for ruff and mypy.

[Unreleased]: https://github.com/getlinksc/search-parser/compare/v0.5.7...HEAD
[0.5.7]: https://github.com/getlinksc/search-parser/compare/v0.5.6...v0.5.7
[0.5.6]: https://github.com/getlinksc/search-parser/compare/v0.5.5...v0.5.6
[0.5.5]: https://github.com/getlinksc/search-parser/compare/v0.5.4...v0.5.5
[0.5.4]: https://github.com/getlinksc/search-parser/compare/v0.5.3...v0.5.4
[0.5.3]: https://github.com/getlinksc/search-parser/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/getlinksc/search-parser/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/getlinksc/search-parser/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/getlinksc/search-parser/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/getlinksc/search-parser/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/getlinksc/search-parser/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/getlinksc/search-parser/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/getlinksc/search-parser/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/getlinksc/search-parser/releases/tag/v0.1.0
