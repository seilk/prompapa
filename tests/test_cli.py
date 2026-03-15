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


def test_help_flag():
    runner = CliRunner()
    result = runner.invoke(papa, ["--help"])
    assert result.exit_code == 0
    assert "Translate your prompts" in result.output
    assert "onboard" in result.output
    assert "update" in result.output
    assert "hotkey" in result.output


def test_help_short_flag():
    runner = CliRunner()
    result = runner.invoke(papa, ["-h"])
    assert result.exit_code == 0
    assert "Translate your prompts" in result.output


def test_onboard_help():
    runner = CliRunner()
    result = runner.invoke(papa, ["onboard", "--help"])
    assert result.exit_code == 0


def test_uninstall_help():
    runner = CliRunner()
    result = runner.invoke(papa, ["uninstall", "--help"])
    assert result.exit_code == 0


def test_update_help():
    runner = CliRunner()
    result = runner.invoke(papa, ["update", "--help"])
    assert result.exit_code == 0


def test_hotkey_help():
    runner = CliRunner()
    result = runner.invoke(papa, ["hotkey", "--help"])
    assert result.exit_code == 0
    assert "--setup" in result.output


def test_translate_help():
    runner = CliRunner()
    result = runner.invoke(papa, ["translate", "--help"])
    assert result.exit_code == 0
