from __future__ import annotations
import os, tomllib
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Load key=value pairs from a .env file into os.environ (no-op if missing)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ[key] = value


class ConfigError(Exception):
    pass


@dataclass
class Hotkey:
    """A terminal hotkey with both raw byte(s) and Kitty CSI u representations."""

    raw: bytes
    csi_u: bytes
    label: str


# ── Reserved keys ────────────────────────────────────────────────────────────

_RESERVED_CTRL_BYTES: frozenset[int] = frozenset(
    {
        0x03,  # Ctrl+C  (SIGINT)
        0x0A,  # Ctrl+J  (LF / newline — used by buffer.py)
        0x0D,  # Ctrl+M  (CR / Enter — clears undo stack)
        0x15,  # Ctrl+U  (line clear — used by buffer.py)
        0x17,  # Ctrl+W  (word kill — used by buffer.py)
        0x1A,  # Ctrl+Z  (SIGTSTP)
        0x1B,  # Ctrl+[  (ESC — breaks escape sequences)
    }
)

# Alt+key sends ESC + char in legacy mode.  Some ESC + char sequences are
# standard terminal controls (ECMA-48 Fs range) and must not be used.
_RESERVED_ALT_CHARS: frozenset[str] = frozenset(
    {
        "c",  # ESC c = RIS (full terminal reset)
        "n",  # ESC n = LS2 (locking shift 2)
        "o",  # ESC o = LS3 (locking shift 3)
    }
)

# Kitty keyboard protocol modifier values (1 + modifier bits).
_CSI_MOD_ALT = 3  # 1 + Alt(2)
_CSI_MOD_CTRL = 5  # 1 + Ctrl(4)
_CSI_MOD_CTRL_ALT = 7  # 1 + Ctrl(4) + Alt(2)


def parse_hotkey(name: str) -> Hotkey:
    """Parse a human-readable hotkey into a :class:`Hotkey`.

    Supported formats::

        Ctrl+<key>       e.g. Ctrl+], Ctrl+T
        Alt+<key>        e.g. Alt+T
        Ctrl+Alt+<key>   e.g. Ctrl+Alt+T

    Key is A-Z (case-insensitive).  Ctrl also accepts ``[\\ ] ^ _``.
    """
    name = name.strip()
    parts = [p.strip() for p in name.split("+")]
    if len(parts) < 2:
        raise ConfigError(
            f"Invalid hotkey format: '{name}'. "
            "Expected 'Ctrl+<key>', 'Alt+<key>', or 'Ctrl+Alt+<key>'."
        )
    key_char = parts[-1]
    mods = frozenset(p.lower() for p in parts[:-1])

    if len(key_char) != 1:
        raise ConfigError(
            f"Invalid hotkey key: '{key_char}'. Must be a single character."
        )

    _VALID_MODS = {
        frozenset({"ctrl"}),
        frozenset({"alt"}),
        frozenset({"ctrl", "alt"}),
    }
    if mods not in _VALID_MODS:
        raise ConfigError(
            f"Invalid modifier combination in '{name}'. "
            "Supported: Ctrl, Alt, Ctrl+Alt."
        )

    has_ctrl = "ctrl" in mods
    has_alt = "alt" in mods
    upper = key_char.upper()
    code = ord(upper)

    if has_ctrl and not has_alt:
        # ── Ctrl+key ────────────────────────────────────────────────────
        # Valid: A-Z (0x41-0x5A) and [\]^_ (0x5B-0x5F)
        if not (0x41 <= code <= 0x5F):
            raise ConfigError(
                f"Invalid hotkey key: '{key_char}'. Must be A-Z or one of [\\]^_."
            )
        raw_byte = code & 0x1F
        if raw_byte in _RESERVED_CTRL_BYTES:
            raise ConfigError(
                f"Hotkey Ctrl+{upper} (0x{raw_byte:02x}) is reserved "
                "and cannot be used."
            )
        base_cp = ord(key_char.lower()) if key_char.isalpha() else ord(key_char)
        raw = bytes([raw_byte])
        csi_u = f"\x1b[{base_cp};{_CSI_MOD_CTRL}u".encode("ascii")
        label = f"Ctrl+{upper}" if key_char.isalpha() else f"Ctrl+{key_char}"

    elif has_alt and not has_ctrl:
        # ── Alt+key ─────────────────────────────────────────────────────
        # Valid: A-Z only (punctuation after ESC is ambiguous)
        if not (0x41 <= code <= 0x5A):
            raise ConfigError(
                f"Invalid hotkey key for Alt: '{key_char}'. Must be A-Z."
            )
        lower = key_char.lower()
        if lower in _RESERVED_ALT_CHARS:
            raise ConfigError(
                f"Hotkey Alt+{upper} is reserved (ESC {lower} is a terminal "
                "control sequence) and cannot be used."
            )
        raw = b"\x1b" + lower.encode("ascii")
        csi_u = f"\x1b[{ord(lower)};{_CSI_MOD_ALT}u".encode("ascii")
        label = f"Alt+{upper}"

    else:
        # ── Ctrl+Alt+key ────────────────────────────────────────────────
        # Valid: A-Z only
        if not (0x41 <= code <= 0x5A):
            raise ConfigError(
                f"Invalid hotkey key for Ctrl+Alt: '{key_char}'. Must be A-Z."
            )
        ctrl_byte = code & 0x1F
        if ctrl_byte in _RESERVED_CTRL_BYTES:
            raise ConfigError(
                f"Hotkey Ctrl+Alt+{upper} is reserved (Ctrl+{upper} byte "
                f"0x{ctrl_byte:02x} conflicts) and cannot be used."
            )
        raw = b"\x1b" + bytes([ctrl_byte])
        csi_u = (
            f"\x1b[{ord(key_char.lower())};{_CSI_MOD_CTRL_ALT}u".encode("ascii")
        )
        label = f"Ctrl+Alt+{upper}"

    return Hotkey(raw=raw, csi_u=csi_u, label=label)


# ── Default hotkeys ─────────────────────────────────────────────────────────

_DEFAULT_TRANSLATE = Hotkey(raw=b"\x1d", csi_u=b"\x1b[93;5u", label="Ctrl+]")
_DEFAULT_UNDO = Hotkey(raw=b"\x19", csi_u=b"\x1b[121;5u", label="Ctrl+Y")


@dataclass
class AppConfig:
    provider: str
    api_key_env: str = ""
    api_key: str = ""
    model: str = ""
    preserve_backticks: bool = True
    target_cmd: list[str] = field(default_factory=lambda: ["claude"])
    hotkey_translate: Hotkey = field(default_factory=lambda: _DEFAULT_TRANSLATE)
    hotkey_undo: Hotkey = field(default_factory=lambda: _DEFAULT_UNDO)

    def resolve_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        key = os.environ.get(self.api_key_env)
        if not key:
            if self.api_key_env:
                raise ConfigError(
                    f"Environment variable '{self.api_key_env}' is not set."
                )
            raise ConfigError("Either 'api_key' or 'api_key_env' must be set.")
        return key


_REQUIRED = ("provider",)


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with open(path, "rb") as f:
        data = tomllib.load(f)
    for key in _REQUIRED:
        if key not in data:
            raise ConfigError(f"Missing required config field '{key}' in {path}")
    if not data.get("api_key") and not data.get("api_key_env"):
        raise ConfigError(
            f"Missing required config field 'api_key' or 'api_key_env' in {path}"
        )
    provider = data["provider"]
    # model is required for LLM providers, optional for google
    if provider != "google" and "model" not in data:
        raise ConfigError(f"Missing required config field 'model' in {path}")
    # ── Parse optional [hotkeys] table ──────────────────────────────────────
    hotkeys_data = data.get("hotkeys", {})
    hotkey_translate = _DEFAULT_TRANSLATE
    hotkey_undo = _DEFAULT_UNDO

    if "translate" in hotkeys_data:
        hotkey_translate = parse_hotkey(hotkeys_data["translate"])
    if "undo" in hotkeys_data:
        hotkey_undo = parse_hotkey(hotkeys_data["undo"])
    if hotkey_translate.raw == hotkey_undo.raw:
        raise ConfigError(
            "Hotkey conflict: 'translate' and 'undo' cannot be the same key."
        )

    return AppConfig(
        provider=provider,
        api_key_env=data.get("api_key_env", ""),
        api_key=data.get("api_key", ""),
        model=data.get("model", ""),
        preserve_backticks=data.get("preserve_backticks", True),
        target_cmd=data.get("target_cmd", ["claude"]),
        hotkey_translate=hotkey_translate,
        hotkey_undo=hotkey_undo,
    )


def default_config_path() -> Path:
    return Path.home() / ".config" / "prompapa" / "config.toml"


def default_system_config_path() -> Path:
    return Path.home() / ".config" / "prompapa" / "system.toml"


# ── System tuning (system.toml) ─────────────────────────────────────────────


@dataclass
class SystemConfig:
    probe_max_repeats: int = 30
    probe_settle_ms: int = 40


_SYSTEM_TOML_TEMPLATE = """\
# Prompapa system tuning — adjust if needed, defaults work for most setups.

# Cursor probe: how many times to repeat Ctrl+A/Ctrl+E to find input edges.
probe_max_repeats = 30

# Milliseconds to wait after each probe keystroke for cursor to settle.
probe_settle_ms = 40
"""


def ensure_system_config(path: Path | None = None) -> Path:
    """Create ``system.toml`` with defaults if it does not exist."""
    if path is None:
        path = default_system_config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_SYSTEM_TOML_TEMPLATE, encoding="utf-8")
    return path


def load_system_config(path: Path | None = None) -> SystemConfig:
    """Load ``system.toml`` from ``~/.config/prompapa/``.

    Missing file or missing keys silently fall back to defaults.
    """
    if path is None:
        path = default_system_config_path()
    if not path.exists():
        return SystemConfig()
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return SystemConfig(
        probe_max_repeats=data.get("probe_max_repeats", 30),
        probe_settle_ms=data.get("probe_settle_ms", 40),
    )
