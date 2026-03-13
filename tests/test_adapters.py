import pytest
from prompapa.adapters import get_adapter
from prompapa.adapters.claude import ClaudeAdapter
from prompapa.adapters.opencode import OpenCodeAdapter


def test_get_adapter_claude():
    adapter = get_adapter("claude")
    assert isinstance(adapter, ClaudeAdapter)


def test_get_adapter_opencode():
    adapter = get_adapter("opencode")
    assert isinstance(adapter, OpenCodeAdapter)


def test_get_adapter_unknown():
    with pytest.raises(ValueError, match="Unknown target"):
        get_adapter("vim")


def test_claude_capture_delegates_to_screen(tmp_path):
    from prompapa.screen import ScreenTracker

    adapter = ClaudeAdapter()
    screen = ScreenTracker(cols=80, rows=24)
    screen.feed("❯ hello world\r\n".encode("utf-8"))
    assert adapter.capture_text(screen) == "hello world"


def test_claude_inject_uses_bracketed_paste():
    import os
    from unittest.mock import patch

    adapter = ClaudeAdapter()
    with patch.object(os, "write") as mock_write:
        adapter.inject_text(99, "hello")
    mock_write.assert_called_once_with(99, b"\x1b[200~hello\x1b[201~")
