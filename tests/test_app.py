"""
Tests for the PTY proxy helper functions.
The proxy loop itself requires a real PTY and is tested manually.
"""

import pytest
from unittest.mock import AsyncMock, patch
from prompapa.app import _display_width, _translate_text
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
