"""Command-line interface for search engine parser."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import click
    from rich.console import Console
    from rich.syntax import Syntax
except ImportError:
    print(
        'CLI dependencies not installed. Install with: pip install "search-engine-parser[cli]"',
        file=sys.stderr,
    )
    sys.exit(1)

from search_parser.core.parser import SearchParser
from search_parser.exceptions import SearchEngineParserError


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "markdown", "dict"]),
    default="json",
    help="Output format (default: json).",
)
@click.option(
    "--engine",
    type=click.Choice(["google", "bing", "duckduckgo"]),
    default=None,
    help="Manually specify the search engine.",
)
@click.option(
    "--pretty/--no-pretty",
    default=True,
    help="Pretty-print JSON output (default: true).",
)
def main(
    input_file: Path,
    output_format: str,
    engine: str | None,
    pretty: bool,
) -> None:
    """Parse search engine HTML results into structured data.

    INPUT_FILE is the path to an HTML file containing search results.
    """
    console = Console()
    html = input_file.read_text(encoding="utf-8")

    parser = SearchParser()
    try:
        # dict format is not useful for CLI, convert to json for display
        fmt = output_format if output_format != "dict" else "json"
        result = parser.parse(html, engine=engine, output_format=fmt)  # type: ignore[arg-type]
    except SearchEngineParserError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if isinstance(result, str):
        if output_format == "json" and pretty:
            import json

            formatted = json.dumps(json.loads(result), indent=2)
            syntax = Syntax(formatted, "json", theme="monokai")
            console.print(syntax)
        elif output_format == "markdown":
            from rich.markdown import Markdown

            console.print(Markdown(result))
        else:
            console.print(result)
    else:
        console.print(result)
