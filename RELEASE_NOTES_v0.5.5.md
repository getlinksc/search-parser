# Release Notes — v0.5.5

**Released:** 2026-08-11

A maintenance release: one parser correctness fix, a version-reporting fix, and a clean lint/type slate.

---

## Bug Fixes

### Desktop organic results returned undecoded redirect URLs

Google wraps result links in a redirect of the form `/url?q=<percent-encoded destination>`. `_parse_mobile_organic_result` already unwrapped these through `_decode_google_redirect`, but `_parse_organic_result` did not — so on desktop pages, `SearchResult.url` came back as the raw relative redirect instead of the destination:

```python
# before — desktop
result.url
'/url?q=https%3A%2F%2Fexample.com%2Fpage%3Fid%3D1&sa=U&ved=...'

# after
result.url
'https://example.com/page?id=1'
```

Both desktop branches (the `div.yuRUbf` container path and the direct `<a>` + `<h3>` fallback) now decode. Pages that already carry absolute `href`s are unaffected — `_decode_google_redirect` returns non-matching hrefs untouched.

### `search_parser.__version__` reported the wrong release

`src/search_parser/__version__.py` was left at `0.5.3` when `pyproject.toml` went to `0.5.4`, so anything reading `search_parser.__version__` — logs, telemetry, bug reports — saw a stale version. Both are bumped together in this release, and `__version__` now reads `0.5.5`.

---

## Known Limitation: encrypted `/goto?url=` hrefs

Some Google response buckets serve organic hrefs as opaque, server-side encrypted redirects rather than the destination:

```html
<a class="zReHs" href="/goto?url=CAESaAHuR6pN8ugNbKPGvPmn_leeyAs0Ofgl7Uia...">
```

The blob decodes to a protobuf whose payload is ciphertext. **The destination URL is not present anywhere in the HTML** — not in the `href`, not in `ping=`, not in any data attribute. The `<cite>` breadcrumb shown on the page is lossy (it drops and truncates path segments), so it is not a reliable substitute.

The parser therefore returns these hrefs **unchanged** rather than guessing. This is deliberate and is now documented on `_decode_google_redirect`. Resolving them requires a network call the parser will not make on your behalf — a `GET` to `https://www.google.com<href>` with redirects disabled returns a `302` whose `Location` header is the destination:

```python
# note: HEAD does not work — Google answers 200 with no Location header
async with session.get(f"https://www.google.com{result.url}", allow_redirects=False) as resp:
    destination = resp.headers.get("location")
```

Callers that need absolute URLs should check for a leading `/` on `result.url` and resolve as above, ideally in parallel across a page's results.

---

## Chore

`ruff check`, `ruff format --check` and `mypy` all failed on `main` before this release; the lint workflow now passes clean.

- Removed unused `json` import from `core/parser.py` and unused `pytest` import from `tests/unit/test_google_finance_parser.py` (`F401`)
- `parsers/google_finance.py`: `try`/`except json.JSONDecodeError`/`pass` → `contextlib.suppress` (`SIM105`)
- `scrapers/google_finance.py`: the `get` lambda assignment is now a nested `def` (`E731`)
- Applied `ruff format` to the four files failing `--check` — `parsers/google.py`, `parsers/google_finance.py`, `scrapers/google_finance.py`, `tests/unit/test_google_parser.py`. Formatting only; no behavior change.

### Type checking

`uv run mypy src/search_parser` reported two errors and a config error:

```
pyproject.toml: [mypy]: python_version: Python 3.9 is not supported (must be 3.10 or higher)
scrapers/google_finance.py:178: error: Value of type "object" is not indexable  [index]
scrapers/google_finance.py:181: error: Argument 1 to "_build_body" has incompatible type "list[object]"; expected "list[dict[str, Any]]"  [arg-type]
```

The batchexecute payload list mixes `str` and nested-`list` values, so mypy joined the dict value types down to `object` and inferred the list as `list[object]`. It is now annotated explicitly:

```python
requests: list[dict[str, Any]] = [
    {"id": "xh8wxf", "req": [[t], 1]},
    ...
]
```

Annotation only — no runtime change.

### CI

- Dropped the `3.9` leg from the test matrix and the `Programming Language :: Python :: 3.9` classifier. `requires-python` has been `>=3.10` since 0.5.3, so that matrix job could only ever fail at `uv sync`.
- The coverage badge writes to a gist outside this repo. It is now skipped when `GIST_SECRET`/`GIST_ID` are unset and marked `continue-on-error`, so an expired token can no longer take the whole pipeline red over a cosmetic badge.
- The publish job now declares `contents: read` alongside `id-token: write`. Declaring any `permissions` key replaces the entire default set, so `actions/checkout` was running with a token that had no repository access.
- The publish job fails fast when the release tag does not match `version` in `pyproject.toml`, so a release cut on the wrong commit can't ship a mislabeled artifact.

Tooling Python targets were also brought in line with `requires-python = ">=3.10"`: mypy `python_version` and ruff `target-version` were both still on 3.9, and current mypy rejects `python_version = "3.9"` as a config error. The stale `markdownify.*` mypy override (flagged by `warn_unused_configs`) was dropped; `markdownify` remains a declared dependency.

---

## Migration

No breaking changes and no API surface changes. The only behavioral difference is that desktop organic `SearchResult.url` values that previously came back as `/url?q=...` strings are now the decoded destination URLs. If you were unwrapping those yourself downstream, that step is now a no-op and can be removed — decoding is idempotent, so leaving it in place is harmless.

---

## Verification

- 287 tests pass (`uv run pytest`)
- `uv run ruff check .` — all checks passed
- `uv run ruff format --check .` — 36 files already formatted
- `uv run mypy src/search_parser` — success, no issues found in 21 source files

---

## Full Changelog

- Fixed desktop organic results returning raw `/url?q=` redirect hrefs — both desktop branches of `_parse_organic_result` now call `_decode_google_redirect`
- Fixed `__version__` being out of sync with `pyproject.toml` (`0.5.3` vs `0.5.4`); both now `0.5.5`
- Documented on `_decode_google_redirect` that `/goto?url=` blobs are encrypted server-side and are returned unchanged for the caller to resolve
- Fixed all outstanding `ruff check` errors (`F401` ×2, `SIM105`, `E731`)
- Applied `ruff format` to four files that were failing `ruff format --check`
- Fixed both `mypy` errors in `scrapers/google_finance.py` by annotating the batchexecute payload as `list[dict[str, Any]]`
- Raised mypy `python_version` and ruff `target-version` to 3.10 to match `requires-python`, and removed the unused `markdownify.*` mypy override

[Full diff](https://github.com/getlinksc/search-parser/compare/v0.5.4...v0.5.5)
