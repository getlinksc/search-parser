# Google Maps structured responses

`GoogleMapsParser` decodes the XSSI-prefixed JSON returned by Google's
`tbm=map` search transport. It does not execute JavaScript or fetch the page.

```python
from search_parser import GoogleMapsParser

results = GoogleMapsParser().parse(response_text, query="coffee chicago")
for place in results.places:
    print(place.name, place.website, place.latitude, place.longitude)
```

The parser exposes place names, IDs, websites, addresses, coordinates, ratings,
review counts, categories, phone numbers, photos, time zones, and displayed
opening hours. The upstream positional schema is undocumented and can change;
keep the request builder separate and monitor empty or failed parses.
