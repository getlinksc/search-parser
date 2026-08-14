# Google Parsing

The Google parser supports desktop results, standard mobile results, and the
stripped no-JavaScript layout Google serves to Opera Mini rendering proxies.
Every layout uses the same `SearchResults` and `SearchResult` models. Fields that
are not present in the HTML are omitted from `metadata` rather than filled with
placeholder values.

## Organic result metadata

Opera Mini rich organic cards can provide these optional `SearchResult.metadata`
keys:

| Key | Type | Meaning |
|---|---|---|
| `display_url` | `str` | Display domain or breadcrumb shown above the result |
| `rating` | `str` | Rating exactly as displayed by Google |
| `reviews` | `str` | Review count, preserving abbreviations such as `1K` |
| `attributes` | `list[str]` | Extra labels such as delivery or return information |
| `published_time` | `str` | Displayed date or relative publication time |
| `sitelinks` | `list[dict]` | Decoded `{title, url}` links nested under the result |

```python
from search_parser.parsers.google import GoogleParser

results = GoogleParser().parse(html)

for result in results.results:
    print(result.title, result.url)
    print("Display URL:", result.metadata.get("display_url"))
    print("Rating:", result.metadata.get("rating"))
    print("Reviews:", result.metadata.get("reviews"))
    print("Attributes:", result.metadata.get("attributes", []))
    print("Published:", result.metadata.get("published_time"))
    for sitelink in result.metadata.get("sitelinks", []):
        print("Sitelink:", sitelink["title"], sitelink["url"])
```

Rich labels, dates, and sitelink text are kept out of `description`; the
description contains only the result snippet.

## Sponsored results

Opera Mini text ads are returned in `SearchResults.sponsored`. Their optional
metadata includes `display_url`, `rating`, `phone`, and `sitelinks`. Google often
renders the same advertiser above and below the organic results. Those copies are
merged by advertiser, including metadata such as a phone number that occurs only
in the lower placement.

```python
for ad in results.sponsored:
    print(ad.title, ad.description)
    print(ad.metadata.get("display_url"))
    print(ad.metadata.get("rating"), ad.metadata.get("phone"))
    for sitelink in ad.metadata.get("sitelinks", []):
        print(sitelink["title"], sitelink["url"])
```

An Opera Mini ad's `url` and sitelink URLs may remain Google `aclk` tracking URLs
when the destination URL is not included in the page markup.

## AI Overview metadata

AI Overviews are returned as one `SearchResult` in `SearchResults.ai_overview`.
The visible summary is in `description`. Metadata contains:

| Key | Type | Meaning |
|---|---|---|
| `sources` | `list[dict]` | Citations with `title`, decoded `url`, and optional `source` name |
| `details` | `list[str]` | Expanded facts that Google initially keeps outside the visible summary |

```python
overview = results.ai_overview
if overview:
    print(overview.description)
    for source in overview.metadata.get("sources", []):
        print(source.get("source", source["title"]), source["url"])
    for detail in overview.metadata.get("details", []):
        print(detail)
```

In Opera Mini pages, Google sometimes stores citation cards and expanded facts as
escaped HTML passed to `window.jsl.dh(...)`. The parser decodes that inert string
as HTML; it never executes the JavaScript.

## Related searches

Opera Mini "People also search for" links are returned in
`SearchResults.people_also_search`, consistent with desktop and standard mobile
layouts:

```python
for related in results.people_also_search:
    print(related.title, related.url)
```

## Page metadata

Location and pagination describe the page rather than a single result, so they
are returned in `SearchResults.metadata`:

```python
{
    "location": "Washington DC (Hagerstown MD), Virginia",
    "location_source": "From your IP address",
    "pagination": {
        "next_url": "https://www.google.com/search?q=contact+lens+weekly&start=10&sa=N",
        "next_start": 10,
    },
}
```

Depending on the page, `pagination` can contain `next_url`, `next_start`,
`previous_url`, and `previous_start`.
