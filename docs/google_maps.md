# Google Maps structured responses

`GoogleMapsParser` decodes the XSSI-prefixed JSON returned by Google's
`tbm=map` search transport. It does not execute JavaScript or fetch the page.
It was added in `search-parser` 0.5.8.

## Basic usage

```python
from search_parser import GoogleMapsParser

results = GoogleMapsParser().parse(response_text, query="coffee chicago")
for place in results.places:
    print(place.name, place.website, place.latitude, place.longitude)
```

`response_text` can be a `str` or UTF-8 `bytes`. The normal response begins with
Google's `)]}'` XSSI guard followed by a newline and JSON; plain JSON is also
accepted for stored fixtures and tests.

## Result model

`parse()` returns a typed `GoogleMapsResults` instance:

| Field | Type | Meaning |
|---|---|---|
| `search_engine` | `"google_maps"` | Stable parser identifier |
| `query` | `str \| None` | Query supplied by the caller |
| `places` | `list[GoogleMapsPlace]` | De-duplicated place records in result order |
| `result_count` | `int` | Number of parsed places |
| `parsed_at` | `datetime` | UTC parse timestamp |
| `metadata` | `dict` | XSSI and positional-schema information |

Each `GoogleMapsPlace` exposes:

- `position`, `name`, Google's hexadecimal `data_id`, optional `place_id`, and
  a generated `google_maps_url`
- `website`, `domain`, `address`, `address_lines`, and `district`
- `latitude` and `longitude`
- `rating`, `review_count`, and `review_url`
- `categories`, `category_ids`, `phone`, and normalized `phone_e164`
- `timezone`, `thumbnail`, and displayed `opening_hours`

Optional upstream fields are `None` or empty collections when Google omits them.
Use Pydantic's `model_dump(mode="json")` for a dictionary or `to_json()` for a
JSON string:

```python
payload = results.model_dump(mode="json")
json_text = results.to_json(indent=2)
```

## Detection and errors

```python
from search_parser import GoogleMapsParseError, GoogleMapsParser

parser = GoogleMapsParser()
if parser.can_parse(response_text) == 1.0:
    try:
        results = parser.parse(response_text, query="coffee shops in 60601")
    except GoogleMapsParseError as exc:
        # Log the upstream status/size, not credentials or the entire response.
        raise RuntimeError("Maps response schema was not parseable") from exc
```

`can_parse()` reports confidence `1.0` for an XSSI-prefixed response and `0.0`
otherwise. `parse()` raises `GoogleMapsParseError` when JSON is invalid or the
XSSI prefix is not followed by a payload. A valid response containing no matching
place records returns `result_count == 0` rather than raising.

## Operational caveats

The `tbm=map` transport and its positional schema are undocumented and can
change. Keep request construction outside this library, retain compact fixtures,
and alert on unexpected zero-result parses or a sustained drop in parsed fields.
This parser is for local/business results; it does not turn Maps into a general
web-search transport.
