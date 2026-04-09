# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/getlinksc/search-parser/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/getlinksc/search-parser/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/getlinksc/search-parser/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/getlinksc/search-parser/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/getlinksc/search-parser/releases/tag/v0.1.0
