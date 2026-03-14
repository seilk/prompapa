import os, tempfile, textwrap
from pathlib import Path
import pytest
from prompapa.config import load_config, ConfigError, AppConfig, Hotkey, parse_hotkey


def _write_toml(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", delete=False, encoding="utf-8"
    )
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
    assert cfg.api_key == ""
    assert cfg.preserve_backticks is True


def test_load_config_with_direct_api_key():
    p = _write_toml("""
        provider = "google"
        api_key = "google-direct-key"
    """)
    cfg = load_config(p)
    assert cfg.provider == "google"
    assert cfg.api_key == "google-direct-key"
    assert cfg.api_key_env == ""


def test_load_config_with_overrides():
    p = _write_toml("""
        provider = "anthropic"
        model = "claude-3-haiku-20240307"
        api_key_env = "ANTHROPIC_API_KEY"
        preserve_backticks = false
    """)
    cfg = load_config(p)
    assert cfg.preserve_backticks is False


def test_missing_required_field_raises():
    p = _write_toml('provider = "openai"')
    with pytest.raises(ConfigError, match="api_key"):
        load_config(p)


def test_missing_model_for_llm_raises():
    p = _write_toml("""
        provider = "openai"
        api_key_env = "OPENAI_API_KEY"
    """)
    with pytest.raises(ConfigError, match="model"):
        load_config(p)


def test_google_provider_no_model_required():
    p = _write_toml("""
        provider = "google"
        api_key_env = "GOOGLE_API_KEY"
    """)
    cfg = load_config(p)
    assert cfg.provider == "google"
    assert cfg.model == ""


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


def test_resolve_api_key_prefers_direct_value(monkeypatch):
    monkeypatch.setenv("MY_TEST_KEY", "sk-env")
    p = _write_toml("""
        provider = "google"
        api_key = "sk-direct"
        api_key_env = "MY_TEST_KEY"
    """)
    cfg = load_config(p)
    assert cfg.resolve_api_key() == "sk-direct"


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


# ── Hotkey parsing tests ────────────────────────────────────────────────────


class TestParseHotkey:
    def test_ctrl_bracket(self):
        hk = parse_hotkey("Ctrl+]")
        assert hk.raw == b"\x1d"
        assert hk.csi_u == b"\x1b[93;5u"

    def test_ctrl_q(self):
        hk = parse_hotkey("Ctrl+Q")
        assert hk.raw == b"\x11"
        assert hk.csi_u == b"\x1b[113;5u"

    def test_ctrl_t(self):
        hk = parse_hotkey("Ctrl+T")
        assert hk.raw == b"\x14"
        assert hk.csi_u == b"\x1b[116;5u"

    def test_case_insensitive(self):
        assert parse_hotkey("Ctrl+q").raw == parse_hotkey("Ctrl+Q").raw
        assert parse_hotkey("ctrl+t").raw == parse_hotkey("Ctrl+T").raw

    def test_ctrl_backslash(self):
        hk = parse_hotkey("Ctrl+\\")
        assert hk.raw == b"\x1c"

    def test_ctrl_caret(self):
        hk = parse_hotkey("Ctrl+^")
        assert hk.raw == b"\x1e"

    def test_ctrl_underscore(self):
        hk = parse_hotkey("Ctrl+_")
        assert hk.raw == b"\x1f"

    def test_reserved_ctrl_c_raises(self):
        with pytest.raises(ConfigError, match="reserved"):
            parse_hotkey("Ctrl+C")

    def test_reserved_ctrl_z_raises(self):
        with pytest.raises(ConfigError, match="reserved"):
            parse_hotkey("Ctrl+Z")

    def test_reserved_esc_raises(self):
        with pytest.raises(ConfigError, match="reserved"):
            parse_hotkey("Ctrl+[")

    def test_reserved_ctrl_u_raises(self):
        with pytest.raises(ConfigError, match="reserved"):
            parse_hotkey("Ctrl+U")

    def test_reserved_ctrl_w_raises(self):
        with pytest.raises(ConfigError, match="reserved"):
            parse_hotkey("Ctrl+W")

    def test_reserved_ctrl_m_raises(self):
        with pytest.raises(ConfigError, match="reserved"):
            parse_hotkey("Ctrl+M")

    def test_reserved_ctrl_j_raises(self):
        with pytest.raises(ConfigError, match="reserved"):
            parse_hotkey("Ctrl+J")

    def test_alt_x_is_valid(self):
        hk = parse_hotkey("Alt+X")
        assert hk.raw == b"\x1bx"

    def test_invalid_format_bare_key_raises(self):
        with pytest.raises(ConfigError, match="Invalid hotkey format"):
            parse_hotkey("X")

    def test_invalid_format_empty_raises(self):
        with pytest.raises(ConfigError, match="Must be a single character"):
            parse_hotkey("Ctrl+")

    def test_invalid_key_digit_raises(self):
        with pytest.raises(ConfigError, match="Invalid hotkey key"):
            parse_hotkey("Ctrl+1")

    def test_whitespace_stripped(self):
        hk = parse_hotkey("  Ctrl+T  ")
        assert hk.raw == b"\x14"

    def test_label_ctrl(self):
        assert parse_hotkey("Ctrl+T").label == "Ctrl+T"
        assert parse_hotkey("Ctrl+]").label == "Ctrl+]"

    # ── Alt+key tests ───────────────────────────────────────────────────

    def test_alt_t(self):
        hk = parse_hotkey("Alt+T")
        assert hk.raw == b"\x1bt"
        assert hk.csi_u == b"\x1b[116;3u"
        assert hk.label == "Alt+T"

    def test_alt_case_insensitive(self):
        assert parse_hotkey("Alt+t").raw == parse_hotkey("Alt+T").raw
        assert parse_hotkey("alt+a").raw == parse_hotkey("Alt+A").raw

    def test_alt_reserved_c_raises(self):
        with pytest.raises(ConfigError, match="reserved"):
            parse_hotkey("Alt+C")

    def test_alt_reserved_n_raises(self):
        with pytest.raises(ConfigError, match="reserved"):
            parse_hotkey("Alt+N")

    def test_alt_reserved_o_raises(self):
        with pytest.raises(ConfigError, match="reserved"):
            parse_hotkey("Alt+O")

    def test_alt_punctuation_raises(self):
        with pytest.raises(ConfigError, match="Must be A-Z"):
            parse_hotkey("Alt+]")

    def test_alt_digit_raises(self):
        with pytest.raises(ConfigError, match="Must be A-Z"):
            parse_hotkey("Alt+1")

    # ── Ctrl+Alt+key tests ──────────────────────────────────────────────

    def test_ctrl_alt_t(self):
        hk = parse_hotkey("Ctrl+Alt+T")
        assert hk.raw == b"\x1b\x14"
        assert hk.csi_u == b"\x1b[116;7u"
        assert hk.label == "Ctrl+Alt+T"

    def test_alt_ctrl_order_accepted(self):
        hk = parse_hotkey("Alt+Ctrl+T")
        assert hk.label == "Ctrl+Alt+T"
        assert hk.raw == parse_hotkey("Ctrl+Alt+T").raw

    def test_ctrl_alt_reserved_c_raises(self):
        with pytest.raises(ConfigError, match="reserved"):
            parse_hotkey("Ctrl+Alt+C")

    def test_ctrl_alt_punctuation_raises(self):
        with pytest.raises(ConfigError, match="Must be A-Z"):
            parse_hotkey("Ctrl+Alt+]")

    # ── Invalid modifier tests ──────────────────────────────────────────

    def test_shift_only_raises(self):
        with pytest.raises(ConfigError, match="modifier"):
            parse_hotkey("Shift+T")

    def test_super_raises(self):
        with pytest.raises(ConfigError, match="modifier"):
            parse_hotkey("Super+T")


# ── Hotkey config loading tests ─────────────────────────────────────────────


class TestHotkeyConfigLoading:
    def test_default_hotkeys_when_no_section(self):
        p = _write_toml("""
            provider = "openai"
            model = "gpt-4.1-mini"
            api_key_env = "OPENAI_API_KEY"
        """)
        cfg = load_config(p)
        assert cfg.hotkey_translate.raw == b"\x1d"
        assert cfg.hotkey_undo.raw == b"\x19"

    def test_custom_hotkeys(self):
        p = _write_toml("""
            provider = "openai"
            model = "gpt-4.1-mini"
            api_key_env = "OPENAI_API_KEY"

            [hotkeys]
            translate = "Ctrl+T"
            undo = "Ctrl+R"
        """)
        cfg = load_config(p)
        assert cfg.hotkey_translate.raw == b"\x14"
        assert cfg.hotkey_undo.raw == b"\x12"

    def test_partial_hotkeys_translate_only(self):
        p = _write_toml("""
            provider = "openai"
            model = "gpt-4.1-mini"
            api_key_env = "OPENAI_API_KEY"

            [hotkeys]
            translate = "Ctrl+T"
        """)
        cfg = load_config(p)
        assert cfg.hotkey_translate.raw == b"\x14"
        assert cfg.hotkey_undo.raw == b"\x19"  # default

    def test_partial_hotkeys_undo_only(self):
        p = _write_toml("""
            provider = "openai"
            model = "gpt-4.1-mini"
            api_key_env = "OPENAI_API_KEY"

            [hotkeys]
            undo = "Ctrl+R"
        """)
        cfg = load_config(p)
        assert cfg.hotkey_translate.raw == b"\x1d"  # default
        assert cfg.hotkey_undo.raw == b"\x12"

    def test_conflicting_hotkeys_raises(self):
        p = _write_toml("""
            provider = "openai"
            model = "gpt-4.1-mini"
            api_key_env = "OPENAI_API_KEY"

            [hotkeys]
            translate = "Ctrl+T"
            undo = "Ctrl+T"
        """)
        with pytest.raises(ConfigError, match="conflict"):
            load_config(p)

    def test_custom_hotkeys_have_csi_u(self):
        p = _write_toml("""
            provider = "openai"
            model = "gpt-4.1-mini"
            api_key_env = "OPENAI_API_KEY"

            [hotkeys]
            translate = "Ctrl+T"
            undo = "Ctrl+R"
        """)
        cfg = load_config(p)
        assert cfg.hotkey_translate.csi_u == b"\x1b[116;5u"
        assert cfg.hotkey_undo.csi_u == b"\x1b[114;5u"
