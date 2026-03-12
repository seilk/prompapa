"""
Tests for the PTY proxy helper functions.
The proxy loop itself requires a real PTY and is tested manually.
"""
import pytest
from unittest.mock import AsyncMock, patch
from tui_translator.app import _do_translate, _do_undo
from tui_translator.buffer import ShadowBuffer
from tui_translator.state import UndoStack
from tui_translator.config import AppConfig


def _cfg(monkeypatch) -> AppConfig:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    return AppConfig(
        provider="openai",
        model="gpt-4.1-mini",
        api_key_env="OPENAI_API_KEY",
    )


async def test_do_translate_returns_translated_text(monkeypatch):
    cfg = _cfg(monkeypatch)
    stack = UndoStack()
    buf = ShadowBuffer()
    buf.set_text("이 버그 고쳐줘")
    status = {"msg": ""}

    with patch(
        "tui_translator.app.rewrite_to_english",
        new=AsyncMock(return_value="Fix this bug."),
    ):
        result = await _do_translate(buf, stack, status, cfg)

    assert result == "Fix this bug."
    assert buf.text() == "Fix this bug."


async def test_do_translate_pushes_original_to_undo_stack(monkeypatch):
    cfg = _cfg(monkeypatch)
    stack = UndoStack()
    buf = ShadowBuffer()
    buf.set_text("이 버그 고쳐줘")
    status = {"msg": ""}

    with patch(
        "tui_translator.app.rewrite_to_english",
        new=AsyncMock(return_value="Fix this bug."),
    ):
        await _do_translate(buf, stack, status, cfg)

    assert stack.can_undo()
    assert stack.pop() == "이 버그 고쳐줘"


async def test_do_translate_on_api_error_preserves_buffer(monkeypatch):
    from tui_translator.translator import TranslationError
    cfg = _cfg(monkeypatch)
    stack = UndoStack()
    buf = ShadowBuffer()
    buf.set_text("이 버그 고쳐줘")
    status = {"msg": ""}

    with patch(
        "tui_translator.app.rewrite_to_english",
        new=AsyncMock(side_effect=TranslationError("API error")),
    ):
        result = await _do_translate(buf, stack, status, cfg)

    assert result == "이 버그 고쳐줘"
    assert buf.text() == "이 버그 고쳐줘"
    assert not stack.can_undo()
    assert "error" in status["msg"].lower()


async def test_do_translate_with_backtick_masking(monkeypatch):
    cfg = _cfg(monkeypatch)
    cfg.preserve_backticks = True
    stack = UndoStack()
    buf = ShadowBuffer()
    buf.set_text("실행해줘 `npm test`")
    status = {"msg": ""}

    with patch(
        "tui_translator.app.rewrite_to_english",
        new=AsyncMock(return_value="Please run __MASK_0__"),
    ):
        result = await _do_translate(buf, stack, status, cfg)

    assert "`npm test`" in result
    assert "`npm test`" in buf.text()


async def test_do_translate_empty_buffer_is_noop(monkeypatch):
    cfg = _cfg(monkeypatch)
    stack = UndoStack()
    buf = ShadowBuffer()
    buf.set_text("")
    status = {"msg": ""}

    with patch("tui_translator.app.rewrite_to_english") as mock_api:
        result = await _do_translate(buf, stack, status, cfg)

    mock_api.assert_not_called()
    assert result == ""
    assert not stack.can_undo()


def test_do_undo_restores_previous_text():
    stack = UndoStack()
    buf = ShadowBuffer()
    buf.set_text("translated text")
    stack.push("original korean text")
    status = {"msg": ""}

    result = _do_undo(stack, buf, status)

    assert result == "original korean text"
    assert buf.text() == "original korean text"
    assert not stack.can_undo()


def test_do_undo_on_empty_stack_returns_none():
    stack = UndoStack()
    buf = ShadowBuffer()
    status = {"msg": ""}

    result = _do_undo(stack, buf, status)

    assert result is None
    assert "nothing" in status["msg"].lower()
