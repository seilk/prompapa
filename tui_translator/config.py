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
class AppConfig:
    provider: str
    api_key_env: str = ""
    api_key: str = ""
    model: str = ""
    hotkey_translate: str = "c-t"
    hotkey_undo: str = "c-z"
    preserve_backticks: bool = True
    target_cmd: list[str] = field(default_factory=lambda: ["claude"])

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
    return AppConfig(
        provider=provider,
        api_key_env=data.get("api_key_env", ""),
        api_key=data.get("api_key", ""),
        model=data.get("model", ""),
        hotkey_translate=data.get("hotkey_translate", "c-t"),
        hotkey_undo=data.get("hotkey_undo", "c-z"),
        preserve_backticks=data.get("preserve_backticks", True),
        target_cmd=data.get("target_cmd", ["claude"]),
    )


def default_config_path() -> Path:
    return Path.home() / ".config" / "tui-translator" / "config.toml"
