# CLAUDE.md - Search Engine Parser

## Project Overview
Python library for parsing search engine HTML results into structured data (JSON, Markdown, dict).

## Architecture
- **Strategy Pattern**: Each search engine has its own parser implementing `BaseParser`
- **Plugin Architecture**: New engines added by creating a parser class and registering it
- **Layers**: Detection → Parsing → Formatting

## Package Manager
Using `uv` for fast, modern Python package management.

## Common Commands
```bash
uv sync --all-extras          # Install/sync all dependencies
uv run pytest                 # Run tests
uv run pytest --cov=search_engine_parser --cov-report=term  # Tests with coverage
uv run ruff check .           # Lint code
uv run ruff format .          # Format code
uv run mypy src/search_engine_parser  # Type check
```

## Adding a New Search Engine Parser
1. Create `src/search_engine_parser/parsers/engine_name.py`
2. Implement class extending `BaseParser` with `engine_name`, `parse()`, and `can_parse()` methods
3. Register in `src/search_engine_parser/parsers/__init__.py`
4. Add HTML test fixtures in `tests/fixtures/engine_name/`
5. Write unit tests in `tests/unit/test_engine_name_parser.py`

## Coding Standards
- Full type hints on all functions (mypy --strict)
- Google-style docstrings on public APIs
- `ruff check` + `ruff format` (line-length 100)
- Functions under 15 lines when possible

## Testing
- pytest with pytest-cov, target >90% coverage
- HTML fixtures in tests/fixtures/ for each engine
- Unit tests per parser, integration tests for full workflows
