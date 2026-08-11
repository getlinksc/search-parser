# Release Notes — v0.4.1

**Released:** 2026-03-05

## What's New

### Mobile Google HTML Parsing

The parser now handles Google search result pages captured on mobile devices. Mobile pages use a completely different DOM layout (`div.xpd` / `egMi0`) compared to desktop (`div.g`). The following are all extracted from mobile pages:

| Feature | Details |
|---|---|
| Organic results | 10 results with correct positions (1–10) |
| URL decoding | `/url?q=...` redirects resolved to actual destination URLs |
| People Also Ask | Questions from `div.Lt3Tzc` containers |
| People Also Search For | Related searches from `a.Q71vJc` links |
| AI Overview | Summary text from `div.frRrnc` inside the AI Overview `xpd` block |

```python
results = parser.parse(mobile_html)

# Same API — mobile or desktop, no configuration needed
for r in results.results:
    print(r.position, r.title)
    print(r.url)  # already decoded, e.g. https://www.targetoptical.com/...

print(results.ai_overview.description)

for q in results.people_also_ask:
    print(q.title)  # "Is there a weekly contact lens?"
```

### Google Shopping Ads

Product cards from Google Shopping units are now extracted into a dedicated `shopping_ads` field. Shopping ads are **never mixed into organic results**.

Each shopping ad entry includes:

| Field | Description |
|---|---|
| `title` | Product name |
| `metadata["price"]` | Price string (e.g. `"$51.19"`) |
| `metadata["merchant"]` | Retailer name (e.g. `"Contacts Direct"`) |
| `url` | Ad click-through URL |

```python
results = parser.parse(html)

for ad in results.shopping_ads:
    print(ad.title)
    print(ad.metadata["price"])
    print(ad.metadata["merchant"])
    print(ad.url)
```

---

## Migration

No breaking changes. `shopping_ads` is a new field that defaults to an empty list when no shopping unit is present on the page. Mobile pages parse seamlessly alongside desktop pages with no configuration required.

---

## Full Changelog

- Added mobile organic result parsing via `div.xpd` / `egMi0` container detection
- Added `_decode_google_redirect` helper to resolve `/url?q=...` URLs
- Added mobile fallback for People Also Ask (`div.Lt3Tzc`)
- Added mobile fallback for People Also Search For (`a.Q71vJc`)
- Added mobile AI Overview detection via `div.gqwIMe` + `div.frRrnc`
- Added `shopping_ads: list[SearchResult]` field to `SearchResults`
- Added `_extract_shopping_ads` and `_parse_shopping_card` methods to `GoogleParser`
- Added `"shopping_ad"` to the `result_type` Literal in `SearchResult`
- `can_parse` now awards confidence for mobile-specific signals (`div.xpd`, `zBAuLc`)
- Markdown formatter renders `## Shopping Ads` section with price and merchant
- 14 new unit tests covering all new behaviour (fixture: `weekly_contacts_with_mobile.html`)

[Full diff](https://github.com/getlinksc/search-parser/compare/v0.4.0...v0.4.1)
