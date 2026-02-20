# Getting Started

## Installation

**Using uv (recommended):**
```bash
uv pip install search-parser
```

**Using pip:**
```bash
pip install search-parser
```

**With CLI extras:**
```bash
pip install "search-parser[cli]"
```

## Basic Usage

```python
from search_engine_parser import SearchParser

parser = SearchParser()

# Load HTML from a file
with open("google_results.html") as f:
    html = f.read()

# Get JSON output (default)
json_output = parser.parse(html)

# Get Markdown output
markdown_output = parser.parse(html, output_format="markdown")

# Get dict output
dict_output = parser.parse(html, output_format="dict")
for result in dict_output["results"]:
    print(f"{result['position']}. {result['title']}")
```

## CLI Usage

```bash
# JSON output (default)
search-parser results.html

# Markdown output
search-parser results.html --format markdown

# Specify engine manually
search-parser results.html --engine google
```
