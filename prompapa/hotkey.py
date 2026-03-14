"""Hotkey display and interactive setup for prompapa."""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

import questionary

from prompapa.config import (
    ConfigError,
    default_config_path,
    load_config,
    parse_hotkey,
    _DEFAULT_TRANSLATE,
    _DEFAULT_UNDO,
)

_SELECT_STYLE = questionary.Style(
    [
        ("pointer", "fg:#00d7ff bold"),
        ("selected", "fg:#00d7ff bold"),
        ("highlighted", "fg:#00d7ff bold"),
    ]
)


def _validate_hotkey(value: str) -> bool | str:
    """Questionary validator for hotkey input."""
    if not value.strip():
        return True  # empty = use default
    try:
        parse_hotkey(value)
        return True
    except ConfigError as e:
        return str(e)


def _ask_hotkey(label: str, default: str) -> str:
    """Prompt the user for a hotkey, validating the input."""
    value = questionary.text(
        f"{label}:",
        default=default,
        validate=_validate_hotkey,
        style=_SELECT_STYLE,
    ).ask()
    if value is None:
        sys.exit(0)
    return value.strip() if value.strip() else default


def run_hotkey_show() -> None:
    """Display current hotkey configuration."""
    config_path = default_config_path()
    try:
        config = load_config(config_path)
    except ConfigError:
        print(f"  Translate : {_DEFAULT_TRANSLATE.label}  (default)")
        print(f"  Undo      : {_DEFAULT_UNDO.label}  (default)")
        print(f"\nNo config found at {config_path}")
        return

    tr = config.hotkey_translate
    un = config.hotkey_undo
    tr_default = " (default)" if tr.raw == _DEFAULT_TRANSLATE.raw else ""
    un_default = " (default)" if un.raw == _DEFAULT_UNDO.raw else ""

    print(f"  Translate : {tr.label}{tr_default}")
    print(f"  Undo      : {un.label}{un_default}")
    print(f"\nConfig: {config_path}")


def run_hotkey_setup() -> None:
    """Interactive hotkey setup — updates [hotkeys] in config.toml."""
    config_path = default_config_path()
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        print("Run `papa onboard` first.")
        sys.exit(1)

    try:
        config = load_config(config_path)
    except ConfigError as e:
        print(f"prompapa: {e}", file=sys.stderr)
        sys.exit(1)

    # Show current hotkeys
    tr_label = config.hotkey_translate.label
    un_label = config.hotkey_undo.label
    print(f"Current hotkeys:")
    print(f"  Translate : {tr_label}")
    print(f"  Undo      : {un_label}")

    print(
        "\nFormat: Ctrl+<key>, Alt+<key>, or Ctrl+Alt+<key>"
        "\n  e.g. Ctrl+], Ctrl+T, Alt+T, Ctrl+Alt+T"
    )
    print()

    translate_key = _ask_hotkey("Translate hotkey", tr_label)
    undo_key = _ask_hotkey("Undo hotkey", un_label)

    if translate_key == undo_key:
        print("\nError: translate and undo cannot be the same key.")
        sys.exit(1)

    # Show confirmation
    print(f"\n  Translate : {translate_key}")
    print(f"  Undo      : {undo_key}")
    confirm = questionary.confirm(
        "Use these hotkeys?", default=True, style=_SELECT_STYLE
    ).ask()
    if confirm is None or not confirm:
        print("Hotkey setup cancelled.")
        sys.exit(0)

    # Update config file — read existing content, replace/add [hotkeys] section
    content = config_path.read_text(encoding="utf-8")

    hotkeys_block = textwrap.dedent(f"""\
        [hotkeys]
        translate = "{translate_key}"
        undo = "{undo_key}"
    """)

    # Remove existing [hotkeys] section if present
    content = re.sub(
        r"\[hotkeys\]\s*\n(?:(?!\[)[^\n]*\n)*",
        "",
        content,
    )
    content = content.rstrip() + "\n\n" + hotkeys_block

    config_path.write_text(content, encoding="utf-8")
    print(f"\nSaved to {config_path}")
