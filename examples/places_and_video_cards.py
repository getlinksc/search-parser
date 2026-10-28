"""Example: places-only pages and video-card results on Google.

Two layouts that need a little care when you consume the output:

* A no-JS (Opera Mini) page can hold nothing but a places pack. Its ``results`` is
  empty and the businesses are in ``local_businesses``, so "no results" should check both.
* Desktop pages can render organic results as video cards. They are ordinary entries in
  ``results``; their ``url`` may be a ``/goto?url=...`` redirect.

The HTML comes from the reduced, synthetic test fixtures in ``tests/fixtures/google``.
"""

from pathlib import Path

from search_parser.parsers.google import GoogleParser

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "google"
parser = GoogleParser()

# ── Places-only page (no-JS mobile) ────────────────────────────────────────

places = parser.parse((FIXTURES / "no_js_places_only.html").read_text())

print("=== Places-only page ===")
print(f"Organic results: {len(places.results)}")
print(f"Local businesses: {len(places.local_businesses)}")

if not places.results and not places.local_businesses:
    print("Nothing on this page")

for biz in places.local_businesses:
    meta = biz.metadata
    # Every key is optional: a gas station has no rating, a shop has no price.
    rating = (
        f"{meta['rating']} ({meta.get('reviews', '?')} reviews)"
        if "rating" in meta
        else "no rating"
    )
    print(f"{biz.position}. {biz.title} · {rating}")
    for key in ("category", "location", "hours", "price"):
        if key in meta:
            print(f"     {key}: {meta[key]}")
    # details keeps every line in page order, including ones that were not classified
    print(f"     details: {meta.get('details', [])}")

# ── Video-card results (desktop) ───────────────────────────────────────────

videos = parser.parse((FIXTURES / "video_card_results.html").read_text())

print()
print("=== Page with video-card results ===")
for result in videos.results:
    redirect = " (Google redirect)" if result.url.startswith("/goto?") else ""
    print(f"{result.position}. {result.title}")
    print(f"     {result.url}{redirect}")
    print(f"     {result.description}")
