# Basic Usage

## Parsing Search Results

```python
from search_engine_parser import SearchParser

parser = SearchParser()

# Auto-detect engine and get JSON
with open("results.html") as f:
    json_output = parser.parse(f.read())
```

## Output Formats

```python
# JSON string (default)
json_str = parser.parse(html)

# Markdown string (LLM-friendly)
markdown_str = parser.parse(html, output_format="markdown")

# Python dictionary
result_dict = parser.parse(html, output_format="dict")
```

## Specifying the Engine

```python
# Skip auto-detection
result = parser.parse(html, engine="google")
result = parser.parse(html, engine="bing")
result = parser.parse(html, engine="duckduckgo")
```

## Working with Dict Output

```python
result = parser.parse(html, output_format="dict")

for item in result["results"]:
    print(f"{item['position']}. {item['title']}")
    print(f"   URL: {item['url']}")
    print(f"   Type: {item['result_type']}")
```
