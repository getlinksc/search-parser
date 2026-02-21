"""Basic example: parse search engine HTML into different formats."""

from search_parser import SearchParser
from search_parser.parsers.google import GoogleParser

# Sample Google HTML (in real usage, load from a file or API response)
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>python tutorial - Google Search</title>
    <meta property="og:site_name" content="Google">
</head>
<body>
    <div id="search">
        <div class="g">
            <div class="yuRUbf">
                <a href="https://docs.python.org/3/tutorial/">
                    <h3>The Python Tutorial - Python Documentation</h3>
                </a>
            </div>
            <div class="VwiC3b">The official Python tutorial covering all the basics.</div>
        </div>
        <div class="g">
            <div class="yuRUbf">
                <a href="https://realpython.com/">
                    <h3>Real Python - Python Tutorials</h3>
                </a>
            </div>
            <div class="VwiC3b">Tutorials, articles, and resources for Python developers.</div>
        </div>
    </div>
    <input name="q" value="python tutorial" type="hidden">
</body>
</html>
"""

# ── Via SearchParser (auto-detects engine) ─────────────────────────────────

parser = SearchParser()

print("=== JSON Output ===")
json_output = parser.parse(SAMPLE_HTML)
print(json_output)
print()

print("=== Markdown Output ===")
markdown_output = parser.parse(SAMPLE_HTML, output_format="markdown")
print(markdown_output)

print("=== Dict Output ===")
data = parser.parse(SAMPLE_HTML, output_format="dict")

# Organic results
for result in data["results"]:
    print(f"  {result['position']}. {result['title']}")
    print(f"     {result['url']}")

# Dedicated fields (None / empty list when not present)
if data["featured_snippet"]:
    print(f"  Featured: {data['featured_snippet']['title']}")

if data["ai_overview"]:
    print(f"  AI Overview: {data['ai_overview']['description'][:100]}")

for q in data["people_also_ask"]:
    print(f"  PAA: {q['title']}")

# ── Via engine parser directly (typed SearchResults + convenience methods) ──

print()
print("=== Using model methods ===")
results = GoogleParser().parse(SAMPLE_HTML)

print(f"Engine: {results.search_engine}")
print(f"Query: {results.query}")
print(f"Organic results: {len(results.results)}")

# to_json() and to_markdown() on the model itself
json_str = results.to_json()
md_str = results.to_markdown()
print(f"JSON length: {len(json_str)} chars")
print(f"Markdown length: {len(md_str)} chars")
