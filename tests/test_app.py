import pytest
from unittest.mock import AsyncMock, patch
from tui_translator.app import _do_translate, _do_undo
from tui_translator.state import UndoStack
from tui_translator.config import AppConfig

def _cfg(monkeypatch) -> AppConfig:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    return AppConfig(provider="openai", model="gpt-4.1-mini", api_key_env="OPENAI_API_KEY")

async def test_do_translate_replaces_text_and_pushes_undo(monkeypatch):
    cfg = _cfg(monkeypatch); stack = UndoStack(); status = {"msg": ""}
    original = "이 버그 고쳐줘"; translated = "Fix this bug."
    with patch("tui_translator.app.rewrite_to_english", new=AsyncMock(return_value=translated)):
        result = await _do_translate(original, stack, status, cfg)
    assert result == translated
    assert stack.can_undo() and stack.pop() == original
    assert status["msg"] == ""

async def test_do_translate_on_api_error_returns_original(monkeypatch):
    from tui_translator.translator import TranslationError
    cfg = _cfg(monkeypatch); stack = UndoStack(); status = {"msg": ""}
    original = "이 버그 고쳐줘"
    with patch("tui_translator.app.rewrite_to_english",
               new=AsyncMock(side_effect=TranslationError("API error"))):
        result = await _do_translate(original, stack, status, cfg)
    assert result == original
    assert not stack.can_undo()
    assert "error" in status["msg"].lower()

async def test_do_translate_with_masking(monkeypatch):
    cfg = _cfg(monkeypatch); cfg.preserve_backticks = True
    stack = UndoStack(); status = {"msg": ""}
    original = "실행해줘 `npm test`"
    with patch("tui_translator.app.rewrite_to_english",
               new=AsyncMock(return_value="Please run __MASK_0__")):
        result = await _do_translate(original, stack, status, cfg)
    assert "`npm test`" in result

async def test_do_undo_restores_previous():
    stack = UndoStack(); status = {"msg": ""}
    stack.push("original korean text")
    result = _do_undo(stack, status)
    assert result == "original korean text" and not stack.can_undo()

def test_do_undo_on_empty_stack_returns_none():
    stack = UndoStack(); status = {"msg": ""}
    result = _do_undo(stack, status)
    assert result is None
    assert "nothing" in status["msg"].lower()
