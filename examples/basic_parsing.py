"""Basic example: parse search engine HTML into different formats."""

from search_engine_parser import SearchParser

# Sample Google HTML (in real usage, you'd load from a file or API response)
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

parser = SearchParser()

# Get JSON output (default)
print("=== JSON Output ===")
json_output = parser.parse(SAMPLE_HTML)
print(json_output)
print()

# Get Markdown output (LLM-friendly)
print("=== Markdown Output ===")
markdown_output = parser.parse(SAMPLE_HTML, output_format="markdown")
print(markdown_output)

# Get Python dict for programmatic access
print("=== Dict Output ===")
dict_output = parser.parse(SAMPLE_HTML, output_format="dict")
for result in dict_output["results"]:
    print(f"  {result['position']}. {result['title']}")
    print(f"     {result['url']}")
