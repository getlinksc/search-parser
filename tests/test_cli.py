"""Tests for the CLI interface."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from search_parser.cli import main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


class TestCLI:
    def test_json_output(self, runner: CliRunner) -> None:
        result = runner.invoke(main, [str(FIXTURES_DIR / "google" / "organic_results.html")])
        assert result.exit_code == 0

    def test_markdown_output(self, runner: CliRunner) -> None:
        result = runner.invoke(
            main,
            [str(FIXTURES_DIR / "google" / "organic_results.html"), "--format", "markdown"],
        )
        assert result.exit_code == 0

    def test_dict_format_falls_back_to_json(self, runner: CliRunner) -> None:
        result = runner.invoke(
            main,
            [str(FIXTURES_DIR / "google" / "organic_results.html"), "--format", "dict"],
        )
        assert result.exit_code == 0

    def test_manual_engine(self, runner: CliRunner) -> None:
        result = runner.invoke(
            main,
            [str(FIXTURES_DIR / "bing" / "organic_results.html"), "--engine", "bing"],
        )
        assert result.exit_code == 0

    def test_no_pretty(self, runner: CliRunner) -> None:
        result = runner.invoke(
            main,
            [
                str(FIXTURES_DIR / "google" / "organic_results.html"),
                "--no-pretty",
            ],
        )
        assert result.exit_code == 0

    def test_invalid_file(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["/nonexistent/file.html"])
        assert result.exit_code != 0

    def test_detection_failure(self, runner: CliRunner, tmp_path: Path) -> None:
        bad_html = tmp_path / "bad.html"
        bad_html.write_text("<html><body>not a search page</body></html>")
        result = runner.invoke(main, [str(bad_html)])
        assert result.exit_code == 1
