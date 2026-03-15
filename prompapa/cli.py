"""Click CLI interface for prompapa."""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

import click


def _get_version() -> str:
    try:
        return pkg_version("prompapa")
    except PackageNotFoundError:
        return "0.0.0-dev"


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
        # Default: run PTY proxy (wired in later tasks)
        pass
