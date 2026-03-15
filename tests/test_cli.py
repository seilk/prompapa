"""Tests for the click CLI interface."""

from click.testing import CliRunner
from prompapa.cli import papa


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(papa, ["--version"])
    assert result.exit_code == 0
    assert "prompapa" in result.output
    # Version should be a semver-like string
    parts = result.output.strip().split()
    version_str = parts[-1]
    assert "." in version_str


def test_version_short_flag():
    runner = CliRunner()
    result = runner.invoke(papa, ["-v"])
    assert result.exit_code == 0
    assert "prompapa" in result.output
