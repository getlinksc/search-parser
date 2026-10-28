# Google Parsing

The Google parser supports desktop results, standard mobile results, and a
stripped no-JavaScript mobile layout.
Every layout uses the same `SearchResults` and `SearchResult` models. Fields that
are not present in the HTML are omitted from `metadata` rather than filled with
placeholder values.

## Organic result metadata

No-JS mobile rich organic cards can provide these optional `SearchResult.metadata`
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

On the desktop layout Google can render an organic result as a video card (a thumbnail
beside the title and snippet) instead of the usual title block. Those cards are ordinary
entries in `results`, at their position on the page, and a page can be made up of them
entirely. Their `url` can be a `/goto?url=...` redirect, like other desktop results; it is
an encrypted token the caller resolves.

## Local business pack

Places packs are returned in `SearchResults.local_businesses`, one `SearchResult` per
business with `result_type="local_business"`. They are not repeated in `results`. A page
that only holds a places pack has an empty `results` and a non-empty `local_businesses`.

| Key | Type | Meaning |
|---|---|---|
| `rating` | `str` | Rating exactly as displayed |
| `reviews` | `str` | Review count without parentheses, for example `1,577` |
| `category` | `str` | Business type, for example `Running store` |
| `location` | `str` | Town or street address shown beside the category |
| `hours` | `str` | Opening state as displayed, for example `Closed · Opens 11 AM Mon` |
| `price` | `str` | Price level, for example `$10–20` (no-JS restaurants) |
| `phone` | `str` | Phone number (desktop pack) |
| `sponsored` | `bool` | `True` for a sponsored listing (desktop pack) |
| `details` | `list[str]` | Every detail line of a no-JS card, in page order |

Every key is optional. On no-JS mobile pages the order of a card's lines depends on the
kind of business (shops, hotels, gas stations), so `category`, `location` and `hours` are
filled only when a line's shape makes it clear which it is. Everything else, such as a
hotel's street address or a gas price, is left in `details`. The `url` of a local business
is empty.

```python
for biz in results.local_businesses:
    meta = biz.metadata
    print(biz.title, meta.get("rating"), meta.get("reviews"), meta.get("category"))
    print(meta.get("location"), meta.get("hours"), meta.get("price"))
    print(meta.get("details", []))
```

## Sponsored results

No-JS mobile text ads are returned in `SearchResults.sponsored`. Their optional
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
        print(sitelink["title"], sitelink["tracking_url"])
```

No-JS mobile ad markup does not include the destination URL. An ad's `url` is the
advertiser's site built from its display URL (for example `https://www.example.com/`),
the Google `aclk` click URL is kept in `metadata["tracking_url"]`, and the advertiser
domain is in `metadata["domain"]`. Sitelinks carry `title` and `tracking_url`; their `url` is `None`.
Fetching a `tracking_url` registers an ad click.

## AI Overview metadata

AI Overviews are returned as one `SearchResult` in `SearchResults.ai_overview`.
The visible summary is in `description`. Metadata contains:

| Key | Type | Meaning |
|---|---|---|
| `present` | `bool` | Always `True` when an overview was found |
| `layout` | `str` | `"chrome"` (JavaScript layout) or `"opera"` (no-JS mobile layout) |
| `text` | `str` | The full overview text, including text behind "Show more" when the page contains it |
| `truncated` | `bool` | Google collapsed the overview behind "Show more" |
| `sources` | `list[dict]` | Cited sources in overview order, see below |
| `citations` | `list[dict]` | `{"sentence", "source_positions"}` pairs linking sentences to `sources[].position`. Chrome layout only; empty for no-JS pages |
| `details` | `list[str]` | Expanded facts that Google initially keeps outside the visible summary (no-JS pages) |

Each source has `position` (1-based order in the overview), `title`, `url`, `domain`
and optional `source` (site name). Chrome-layout sources may also carry `snippet` and
`redirect` (the original Google redirect). No-JS pages often link sources through
encrypted Google redirects (`/url?q=CAES...`); the `url` is then that redirect,
`domain` is `None`, and the caller must resolve the redirect. No-JS titles shortened
by Google are flagged with `title_truncated`.

```python
overview = results.ai_overview
if overview:
    print(overview.metadata["text"])
    for source in overview.metadata.get("sources", []):
        print(source["position"], source.get("source", source["title"]), source["url"])
    for detail in overview.metadata.get("details", []):
        print(detail)
```

In no-JS mobile pages, Google sometimes stores citation cards and expanded facts as
escaped HTML passed to `window.jsl.dh(...)`. The parser decodes that inert string
as HTML; it never executes the JavaScript.

## Related searches

No-JS mobile "People also search for" links are returned in
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

## Extras: videos, answers, knowledge panel, ads and more

Some page parts do not have a typed field on `SearchResults`. `GoogleParser.parse_extras(html)`
returns them as plain dicts and lists, and `parse()` also stores the same dict in
`SearchResults.metadata["extras"]` whenever at least one part was found.

```python
from search_parser import GoogleParser

extras = GoogleParser().parse_extras(html)
# or: GoogleParser().parse(html).metadata.get("extras", {})
```

Only the keys that were found are present. Every part is parsed independently, so a layout change
that breaks one selector costs only that key.

| Key | Type | Content |
| --- | --- | --- |
| `total` / `total_text` | `int` / `str` | Result count and the text it came from (for example `About 1,234 results`). Works on the raw document, where Google writes it as a JS string, and on rendered markup. The first non-zero figure wins over a placeholder `About 0 results`. |
| `videos` | `list[dict]` | `title`, `url`, `site`, `channel`, `stats`, `date`, `duration`, `position`. |
| `pagination` | `dict` | `next_start`, `prev_start`, `has_next` from the Next and Previous links. The older `metadata["pagination"]` (URLs) is unchanged. |
| `answers` | `list[dict]` | Outermost `data-attrid` blocks (up to 12): `attrid`, `text`, `url`. Hidden duplicate text (`aria-hidden`) is dropped. |
| `answer_box` | `dict` | The expanded answer box: `title`, `text`, `url`. |
| `knowledge_panel` | `dict` | The right-hand panel: `title`, `text`, and up to 25 deduplicated `links`. |
| `discussions` | `list[dict]` | "Discussions and forums" threads: `title`, `url`, `source`, `meta`, `position`. |
| `ads` | `list[dict]` | Ads in the Chrome (JS) layout: `title`, `link`, `display_url`, `advertiser`, `description`, `position`, `result_type`, `metadata.slot`. |

Notes:

* Relative links are made absolute (`https://www.google.com/...`). `/goto?url=CAES...` tokens are
  returned as they are, because resolving them needs a request; resolve them with your own HTTP
  client (a GET without following redirects answers 302 with the destination in `Location`).
* Ad destinations come from `data-pcu`. The `/aclk` click URL is never read or returned: requesting it
  is a billable ad click.
