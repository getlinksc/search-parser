"""Example: batch processing multiple HTML files."""

import json
from pathlib import Path

from search_engine_parser import SearchParser

parser = SearchParser()


def process_directory(input_dir: str, output_dir: str) -> None:
    """Process all HTML files in a directory and save JSON results."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    html_files = list(input_path.glob("*.html"))
    print(f"Found {len(html_files)} HTML files to process")

    for html_file in html_files:
        print(f"Processing: {html_file.name}")
        html = html_file.read_text(encoding="utf-8")

        try:
            result = parser.parse(html, output_format="dict")
            output_file = output_path / f"{html_file.stem}.json"
            output_file.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
            print(f"  -> Saved {len(result['results'])} results to {output_file.name}")
        except Exception as e:
            print(f"  -> Error: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python batch_processing.py <input_dir> <output_dir>")
        sys.exit(1)

    process_directory(sys.argv[1], sys.argv[2])
