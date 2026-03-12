from __future__ import annotations
import os, tomllib
from dataclasses import dataclass, field
from pathlib import Path

class ConfigError(Exception):
    pass

@dataclass
class AppConfig:
    provider: str
    model: str
    api_key_env: str
    hotkey_translate: str = "c-t"
    hotkey_undo: str = "c-z"
    preserve_backticks: bool = True
    target_cmd: list[str] = field(default_factory=lambda: ["claude"])

    def resolve_api_key(self) -> str:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise ConfigError(
                f"Environment variable '{self.api_key_env}' is not set."
            )
        return key

_REQUIRED = ("provider", "model", "api_key_env")

def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with open(path, "rb") as f:
        data = tomllib.load(f)
    for key in _REQUIRED:
        if key not in data:
            raise ConfigError(f"Missing required config field '{key}' in {path}")
    return AppConfig(
        provider=data["provider"],
        model=data["model"],
        api_key_env=data["api_key_env"],
        hotkey_translate=data.get("hotkey_translate", "c-t"),
        hotkey_undo=data.get("hotkey_undo", "c-z"),
        preserve_backticks=data.get("preserve_backticks", True),
        target_cmd=data.get("target_cmd", ["claude"]),
    )

def default_config_path() -> Path:
    return Path.home() / ".config" / "tui-translator" / "config.toml"
