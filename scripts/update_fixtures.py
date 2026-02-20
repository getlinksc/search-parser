"""Helper script to capture new test fixtures from HTML files.

Usage:
    python scripts/update_fixtures.py <engine> <input_file> <fixture_name>

Example:
    python scripts/update_fixtures.py google ~/downloads/google_results.html organic_results
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 4:
        print("Usage: python scripts/update_fixtures.py <engine> <input_file> <fixture_name>")
        print("Example: python scripts/update_fixtures.py google results.html organic_results")
        sys.exit(1)

    engine = sys.argv[1]
    input_file = Path(sys.argv[2])
    fixture_name = sys.argv[3]

    if not input_file.exists():
        print(f"Error: {input_file} does not exist")
        sys.exit(1)

    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / engine
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    output_file = fixtures_dir / f"{fixture_name}.html"
    html = input_file.read_text(encoding="utf-8")
    output_file.write_text(html, encoding="utf-8")
    print(f"Saved fixture to {output_file}")


if __name__ == "__main__":
    main()
