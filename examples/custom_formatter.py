"""Example: creating a custom output formatter."""

from __future__ import annotations

import csv
import io

from search_engine_parser.core.models import SearchResults
from search_engine_parser.formatters.base import BaseFormatter
from search_engine_parser.parsers.google import GoogleParser


class CSVFormatter(BaseFormatter):
    """Custom formatter that outputs organic results as CSV."""

    def format(self, results: SearchResults) -> str:
        """Format organic results as a CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["position", "title", "url", "description"])
        for result in results.results:
            writer.writerow(
                [
                    result.position,
                    result.title,
                    result.url,
                    result.description or "",
                ]
            )
        return output.getvalue()


SAMPLE_HTML = """
<html>
<head><meta property="og:site_name" content="Google"></head>
<body>
    <div id="search">
        <div class="g">
            <div class="yuRUbf">
                <a href="https://example.com/1"><h3>First Result</h3></a>
            </div>
            <div class="VwiC3b">Description of the first result.</div>
        </div>
        <div class="g">
            <div class="yuRUbf">
                <a href="https://example.com/2"><h3>Second Result</h3></a>
            </div>
            <div class="VwiC3b">Description of the second result.</div>
        </div>
    </div>
</body>
</html>
"""

# Get a typed SearchResults object directly from the engine parser
results = GoogleParser().parse(SAMPLE_HTML)

# Use the custom formatter
csv_output = CSVFormatter().format(results)
print("=== CSV Output ===")
print(csv_output)

# The model's built-in methods are also available
print("=== JSON Output ===")
print(results.to_json())

print("=== Markdown Output ===")
print(results.to_markdown())
