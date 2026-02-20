"""Example: creating a custom output formatter."""

from __future__ import annotations

import csv
import io

from search_engine_parser import SearchParser
from search_engine_parser.core.models import SearchResults
from search_engine_parser.formatters.base import BaseFormatter


class CSVFormatter(BaseFormatter):
    """Custom formatter that outputs results as CSV."""

    def format(self, results: SearchResults) -> str:
        """Format results as CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["position", "title", "url", "description", "type"])

        # Write results
        for result in results.results:
            writer.writerow(
                [
                    result.position,
                    result.title,
                    result.url,
                    result.description or "",
                    result.result_type,
                ]
            )

        return output.getvalue()


# Usage
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

# First, get the parsed results as a dict
parser = SearchParser()
dict_output = parser.parse(SAMPLE_HTML, output_format="dict")

# Then use the custom formatter with the model directly

results = SearchResults(**dict_output)  # type: ignore[arg-type]
csv_formatter = CSVFormatter()
csv_output = csv_formatter.format(results)

print("=== CSV Output ===")
print(csv_output)
