"""
Tests for the PTY proxy helper functions.
The proxy loop itself requires a real PTY and is tested manually.
"""

import pytest
import sys
from unittest.mock import AsyncMock, patch
from prompapa.app import (
    _display_width,
    _translate_text,
    _run_translate_once,
)
from prompapa.config import AppConfig
from prompapa.translator import TranslationError


def _cfg(monkeypatch) -> AppConfig:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    return AppConfig(
        provider="openai",
        model="gpt-4.1-mini",
        api_key_env="OPENAI_API_KEY",
    )


def test_display_width_ascii():
    assert _display_width("hello") == 5


def test_display_width_korean():
    assert _display_width("안녕하세요") == 10


def test_display_width_mixed():
    assert _display_width("hello 안녕") == 10


def test_display_width_empty():
    assert _display_width("") == 0


def test_display_width_cjk_fullwidth():
    # Fullwidth Latin: Ａ (U+FF21) = width 2 each
    assert _display_width("Ａ") == 2
    assert _display_width("ＡＢＣ") == 6


def test_display_width_japanese():
    assert _display_width("日本語") == 6


def test_display_width_multiline():
    assert _display_width("abc\ndef") == 7


async def test_translate_text_returns_translated(monkeypatch):
    cfg = _cfg(monkeypatch)
    with patch(
        "prompapa.app.rewrite_to_english",
        new=AsyncMock(return_value="Fix this bug."),
    ):
        result = await _translate_text("이 버그 고쳐줘", cfg)
    assert result == "Fix this bug."


async def test_translate_text_raises_on_api_error(monkeypatch):
    cfg = _cfg(monkeypatch)
    with patch(
        "prompapa.app.rewrite_to_english",
        new=AsyncMock(side_effect=TranslationError("API error")),
    ):
        with pytest.raises(TranslationError):
            await _translate_text("이 버그 고쳐줘", cfg)


async def test_translate_text_preserves_backticks(monkeypatch):
    cfg = _cfg(monkeypatch)
    cfg.preserve_backticks = True
    with patch(
        "prompapa.app.rewrite_to_english",
        new=AsyncMock(return_value="Please run __MASK_0__"),
    ):
        result = await _translate_text("실행해줘 `npm test`", cfg)
    assert "`npm test`" in result


async def test_translate_text_without_masking(monkeypatch):
    cfg = _cfg(monkeypatch)
    cfg.preserve_backticks = False
    with patch(
        "prompapa.app.rewrite_to_english",
        new=AsyncMock(return_value="Run npm test"),
    ):
        result = await _translate_text("실행해줘 `npm test`", cfg)
    assert result == "Run npm test"


# ── Hotkey byte parsing tests ─────────────────────────────────────────────────
# These test the handle_stdin hotkey detection logic from app.py:
#   Ctrl+] (0x1D) = translate, Ctrl+Q (0x11) = undo
# The actual handle_stdin is a closure inside _proxy_loop, so we test
# the byte-level parsing patterns it depends on.


class TestHotkeyByteParsing:
    def test_ctrl_bracket_byte_value(self):
        # Ctrl+] = 0x1D (ASCII GS, Group Separator)
        assert b"\x1d" == bytes([0x1D])

    def test_ctrl_q_byte_value(self):
        # Ctrl+Q = 0x11 (ASCII DC1, XON)
        assert b"\x11" == bytes([0x11])

    def test_find_translate_hotkey_in_pure_data(self):
        data = b"\x1d"
        idx = data.find(b"\x1d")
        assert idx == 0

    def test_find_undo_hotkey_in_pure_data(self):
        data = b"\x11"
        idx = data.find(b"\x11")
        assert idx == 0

    def test_hotkey_not_present(self):
        data = b"normal text typing"
        assert data.find(b"\x1d") == -1
        assert data.find(b"\x11") == -1

    def test_text_before_hotkey_is_forwarded(self):
        # When user types "abc" then Ctrl+], data arrives as b"abc\x1d"
        data = b"abc\x1d"
        idx = data.find(b"\x1d")
        assert idx == 3
        prefix = data[:idx]
        assert prefix == b"abc"

    def test_text_after_hotkey_is_forwarded(self):
        data = b"\x1ddef"
        idx = data.find(b"\x1d")
        assert idx == 0
        suffix = data[idx + 1 :]
        assert suffix == b"def"

    def test_combined_text_and_hotkey_chunk(self):
        # Real scenario: fast typing + hotkey arrives in single read()
        data = b"typed text\x1d"
        idx = data.find(b"\x1d")
        assert idx == 10
        # idx > 0 means stale_text should be computed
        assert idx > 0

    def test_dual_hotkeys_first_wins(self):
        # Both Ctrl+] and Ctrl+Q in same chunk: leftmost wins
        data = b"\x1d\x11"
        candidates = []
        ctrl_bracket = data.find(b"\x1d")
        ctrl_q = data.find(b"\x11")
        if ctrl_bracket != -1:
            candidates.append((ctrl_bracket, "translate"))
        if ctrl_q != -1:
            candidates.append((ctrl_q, "undo"))
        candidates.sort()
        assert candidates[0] == (0, "translate")

    def test_undo_before_translate_undo_wins(self):
        data = b"\x11\x1d"
        candidates = []
        ctrl_bracket = data.find(b"\x1d")
        ctrl_q = data.find(b"\x11")
        if ctrl_bracket != -1:
            candidates.append((ctrl_bracket, "translate"))
        if ctrl_q != -1:
            candidates.append((ctrl_q, "undo"))
        candidates.sort()
        assert candidates[0] == (0, "undo")

    def test_hotkey_at_end_of_large_chunk(self):
        data = b"a" * 500 + b"\x1d"
        idx = data.find(b"\x1d")
        assert idx == 500

    def test_multiple_same_hotkeys_first_wins(self):
        data = b"\x1d\x1d\x1d"
        idx = data.find(b"\x1d")
        assert idx == 0

    def test_no_candidates_means_forward_all(self):
        data = b"hello world"
        ctrl_bracket = data.find(b"\x1d")
        ctrl_q = data.find(b"\x11")
        candidates = []
        if ctrl_bracket != -1:
            candidates.append((ctrl_bracket, "translate"))
        if ctrl_q != -1:
            candidates.append((ctrl_q, "undo"))
        assert len(candidates) == 0

    def test_stale_detection_only_when_prefix_exists(self):
        # idx > 0 means text was typed before hotkey -> capture is stale
        # idx == 0 means hotkey alone -> no stale detection needed
        data_with_prefix = b"text\x1d"
        data_without_prefix = b"\x1d"
        assert data_with_prefix.find(b"\x1d") > 0
        assert data_without_prefix.find(b"\x1d") == 0


# ── One-shot translate mode ───────────────────────────────────────────────────


async def test_run_translate_once_prints_result(monkeypatch, capsys):
    cfg = _cfg(monkeypatch)
    with patch(
        "prompapa.app.rewrite_to_english",
        new=AsyncMock(return_value="Fix this bug."),
    ):
        await _run_translate_once("이 버그 고쳐줘", cfg)
    captured = capsys.readouterr()
    assert captured.out.strip() == "Fix this bug."


async def test_run_translate_once_propagates_error(monkeypatch):
    cfg = _cfg(monkeypatch)
    with patch(
        "prompapa.app.rewrite_to_english",
        new=AsyncMock(side_effect=TranslationError("API error")),
    ):
        with pytest.raises(TranslationError):
            await _run_translate_once("이 버그 고쳐줘", cfg)
