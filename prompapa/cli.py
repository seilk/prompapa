"""Click CLI interface for prompapa."""

from __future__ import annotations

import asyncio
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path

import click


def _get_version() -> str:
    try:
        return pkg_version("prompapa")
    except PackageNotFoundError:
        return "0.0.0-dev"


# Known subcommands — anything else is treated as a PTY target name.
_SUBCOMMANDS = {"onboard", "uninstall", "update", "hotkey", "translate"}


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(
    _get_version(),
    "-v", "--version",
    prog_name="prompapa",
)
@click.pass_context
def papa(ctx: click.Context) -> None:
    """Translate your prompts to English inside AI coding assistants."""
    if ctx.invoked_subcommand is None:
        _run_proxy(target=None)


@papa.command()
def onboard() -> None:
    """Run the interactive setup wizard."""
    from prompapa.onboard import run_onboard

    run_onboard()


@papa.command()
def uninstall() -> None:
    """Uninstall prompapa from your system."""
    from prompapa.uninstall import run_uninstall

    run_uninstall()


@papa.command()
def update() -> None:
    """Check for updates and install the latest version."""
    from prompapa.update import run_update

    run_update()


@papa.command()
@click.option("--setup", is_flag=True, help="Interactive hotkey configuration.")
def hotkey(setup: bool) -> None:
    """Show or configure hotkeys."""
    from prompapa.hotkey import run_hotkey_setup, run_hotkey_show

    if setup:
        run_hotkey_setup()
    else:
        run_hotkey_show()


@papa.command(name="translate")
@click.argument("text", nargs=-1, required=True)
def translate_cmd(text: tuple[str, ...]) -> None:
    """One-shot translation of the given text."""
    from prompapa.app import _run_translate_once
    from prompapa.config import ConfigError, default_config_path, load_config, _load_dotenv
    from prompapa.translator import TranslationError

    _load_dotenv(Path(".env"))
    config_path = default_config_path()
    try:
        config = load_config(config_path)
        config.resolve_api_key()
    except ConfigError as e:
        click.echo(f"prompapa: {e}", err=True)
        sys.exit(1)

    joined = " ".join(text)
    try:
        asyncio.run(_run_translate_once(joined, config))
    except TranslationError as e:
        click.echo(f"prompapa: translation failed: {e}", err=True)
        sys.exit(1)


def _run_proxy(target: str | None, command: list[str] | None = None) -> None:
    """Launch the PTY proxy (default command)."""
    import os
    import pty
    import shutil
    import termios
    import tty

    from prompapa.adapters import get_adapter
    from prompapa.app import _proxy_loop, _set_winsize
    from prompapa.config import ConfigError, default_config_path, load_config, load_system_config, _load_dotenv

    _load_dotenv(Path(".env"))
    config_path = default_config_path()
    try:
        config = load_config(config_path)
        config.resolve_api_key()
    except ConfigError as e:
        click.echo(f"prompapa: {e}", err=True)
        click.echo(f"\nCreate config at: {config_path}", err=True)
        click.echo(
            '\nExample:\n  provider = "openai"\n  model = "gpt-4.1-mini"'
            '\n  api_key_env = "OPENAI_API_KEY"\n  target_cmd = ["claude"]',
            err=True,
        )
        sys.exit(1)

    if not sys.stdin.isatty():
        click.echo(
            "prompapa: stdin is not a TTY. Run directly in a terminal, "
            "not inside a pipe or IDE shell.",
            err=True,
        )
        sys.exit(1)

    if command is not None:
        cmd = command
        target_name = cmd[0]
    elif target:
        cmd = [target]
        target_name = target
    else:
        cmd = config.target_cmd
        target_name = cmd[0]

    try:
        adapter = get_adapter(target_name)
    except ValueError as e:
        click.echo(f"prompapa: {e}", err=True)
        sys.exit(1)

    if not shutil.which(cmd[0]):
        click.echo(f"prompapa: command not found: {cmd[0]}", err=True)
        sys.exit(1)

    pid, master_fd = pty.fork()

    if pid == 0:
        os.environ["PROMPT_TOOLKIT_NO_CPR"] = "1"
        os.execvp(cmd[0], cmd)
        sys.exit(1)

    _set_winsize(master_fd)
    old_attrs = termios.tcgetattr(sys.stdin.fileno())
    tty.setraw(sys.stdin.fileno())

    sys_config = load_system_config()

    try:
        asyncio.run(_proxy_loop(master_fd, config, pid, adapter, sys_config))
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, old_attrs)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        os.close(master_fd)


def main() -> None:
    """Entry point that preprocesses sys.argv for backward compat.

    Handles two backward-compat cases before click sees the arguments:
    1. ``papa -t "text"`` → ``papa translate "text"``
    2. ``papa claude`` (unknown subcommand) → launch PTY proxy directly
    """
    args = sys.argv[1:]

    # Map `papa -t "text"` -> `papa translate "text"`
    if len(args) >= 2 and args[0] == "-t":
        sys.argv = [sys.argv[0], "translate"] + args[1:]
        papa(standalone_mode=True)
        return

    if len(args) >= 2 and args[0] == "ccr" and args[1] == "code":
        _run_proxy(target=None, command=["ccr", "code", *args[2:]])
        return

    # If the first arg looks like a target name (not a known subcommand
    # and not a flag), launch PTY proxy directly.
    if args and not args[0].startswith("-") and args[0] not in _SUBCOMMANDS:
        _run_proxy(target=args[0])
        return

    papa(standalone_mode=True)
