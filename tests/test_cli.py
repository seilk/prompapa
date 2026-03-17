"""Tests for the click CLI interface."""

from unittest.mock import patch

from click.testing import CliRunner

from prompapa import cli
from prompapa.adapters import get_adapter
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


def test_main_routes_ccr_code_to_proxy_command():
    with patch.object(cli, "_run_proxy") as run_proxy, patch.object(
        cli.sys, "argv", ["papa", "ccr", "code"]
    ):
        cli.main()

    _, kwargs = run_proxy.call_args
    assert kwargs == {"target": None, "command": ["ccr", "code"]}


def test_main_routes_ccr_code_with_trailing_args():
    with patch.object(cli, "_run_proxy") as run_proxy, patch.object(
        cli.sys, "argv", ["papa", "ccr", "code", "--help", "--print", "foo"]
    ):
        cli.main()

    _, kwargs = run_proxy.call_args
    assert kwargs == {
        "target": None,
        "command": ["ccr", "code", "--help", "--print", "foo"],
    }


def test_main_routes_unknown_single_arg_to_proxy_target():
    with patch.object(cli, "_run_proxy") as run_proxy, patch.object(
        cli.sys, "argv", ["papa", "claude"]
    ):
        cli.main()

    _, kwargs = run_proxy.call_args
    assert kwargs == {"target": "claude"}


def test_ccr_adapter_is_registered():
    adapter = get_adapter("ccr")
    assert adapter.__class__.__name__ == "CCRAdapter"
