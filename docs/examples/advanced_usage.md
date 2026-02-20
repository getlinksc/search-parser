# Advanced Usage

## Batch Processing

```python
import json
from pathlib import Path
from search_engine_parser import SearchParser

parser = SearchParser()

for html_file in Path("html_files").glob("*.html"):
    html = html_file.read_text()
    result = parser.parse(html, output_format="dict")
    output = html_file.with_suffix(".json")
    output.write_text(json.dumps(result, indent=2, default=str))
```

## Custom Formatters

```python
import csv
import io
from search_engine_parser.core.models import SearchResults
from search_engine_parser.formatters.base import BaseFormatter


class CSVFormatter(BaseFormatter):
    def format(self, results: SearchResults) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["position", "title", "url", "description", "type"])
        for r in results.results:
            writer.writerow([r.position, r.title, r.url, r.description, r.result_type])
        return output.getvalue()
```

## Filtering Results

```python
result = parser.parse(html, output_format="dict")

organic = [r for r in result["results"] if r["result_type"] == "organic"]
featured = [r for r in result["results"] if r["result_type"] == "featured_snippet"]
```

## Error Handling

```python
from search_engine_parser import SearchParser
from search_engine_parser.exceptions import (
    SearchEngineDetectionError,
    ParserNotFoundError,
    ParseError,
)

parser = SearchParser()
try:
    result = parser.parse(html)
except SearchEngineDetectionError:
    # Try specifying the engine manually
    result = parser.parse(html, engine="google")
except ParserNotFoundError as e:
    print(f"No parser available: {e}")
except ParseError as e:
    print(f"Parsing failed: {e}")
```
