# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-01-01

### Added

- Initial release of `search-engine-parser`.
- Core parsing framework with `BaseParser` and `SearchResult` data model.
- Google search results parser with auto-detection.
- Bing search results parser with auto-detection.
- DuckDuckGo search results parser with auto-detection.
- Auto-detection of search engine from raw HTML content.
- Three output formats: JSON, Markdown, and Python dict.
- Command-line interface (`search-engine-parser parse`).
- Comprehensive test suite with HTML fixtures.
- Documentation site using MkDocs with Material theme.
- CI/CD workflows for testing, linting, coverage, and publishing.
- Pre-commit hooks for ruff and mypy.

[Unreleased]: https://github.com/search-engine-parser/search-engine-parser/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/search-engine-parser/search-engine-parser/releases/tag/v0.1.0
