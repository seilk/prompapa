import os, tempfile, textwrap
from pathlib import Path
import pytest
from tui_translator.config import load_config, ConfigError, AppConfig

def _write_toml(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False, encoding="utf-8")
    f.write(textwrap.dedent(content))
    f.close()
    return Path(f.name)

def test_load_minimal_config():
    p = _write_toml("""
        provider = "openai"
        model = "gpt-4.1-mini"
        api_key_env = "OPENAI_API_KEY"
    """)
    cfg = load_config(p)
    assert cfg.provider == "openai"
    assert cfg.model == "gpt-4.1-mini"
    assert cfg.hotkey_translate == "c-t"
    assert cfg.hotkey_undo == "c-z"
    assert cfg.preserve_backticks is True

def test_load_config_with_overrides():
    p = _write_toml("""
        provider = "anthropic"
        model = "claude-3-haiku-20240307"
        api_key_env = "ANTHROPIC_API_KEY"
        hotkey_translate = "c-r"
        preserve_backticks = false
    """)
    cfg = load_config(p)
    assert cfg.hotkey_translate == "c-r"
    assert cfg.preserve_backticks is False

def test_missing_required_field_raises():
    p = _write_toml('provider = "openai"')
    with pytest.raises(ConfigError, match="model"):
        load_config(p)

def test_file_not_found_raises():
    with pytest.raises(ConfigError, match="not found"):
        load_config(Path("/nonexistent/config.toml"))

def test_resolve_api_key(monkeypatch):
    monkeypatch.setenv("MY_TEST_KEY", "sk-test-123")
    p = _write_toml("""
        provider = "openai"
        model = "gpt-4.1-mini"
        api_key_env = "MY_TEST_KEY"
    """)
    cfg = load_config(p)
    assert cfg.resolve_api_key() == "sk-test-123"

def test_missing_api_key_env_raises(monkeypatch):
    monkeypatch.delenv("MISSING_KEY_XYZ", raising=False)
    p = _write_toml("""
        provider = "openai"
        model = "gpt-4.1-mini"
        api_key_env = "MISSING_KEY_XYZ"
    """)
    cfg = load_config(p)
    with pytest.raises(ConfigError, match="MISSING_KEY_XYZ"):
        cfg.resolve_api_key()

def test_target_cmd_default():
    p = _write_toml("""
        provider = "openai"
        model = "gpt-4.1-mini"
        api_key_env = "OPENAI_API_KEY"
    """)
    cfg = load_config(p)
    assert cfg.target_cmd == ["claude"]

def test_target_cmd_custom():
    p = _write_toml("""
        provider = "openai"
        model = "gpt-4.1-mini"
        api_key_env = "OPENAI_API_KEY"
        target_cmd = ["opencode"]
    """)
    cfg = load_config(p)
    assert cfg.target_cmd == ["opencode"]

def test_target_cmd_with_args():
    p = _write_toml("""
        provider = "openai"
        model = "gpt-4.1-mini"
        api_key_env = "OPENAI_API_KEY"
        target_cmd = ["claude", "--no-color"]
    """)
    cfg = load_config(p)
    assert cfg.target_cmd == ["claude", "--no-color"]
