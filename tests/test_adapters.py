import pytest
from unittest.mock import patch, call, AsyncMock
import os

from prompapa.adapters import get_adapter
from prompapa.adapters.claude import ClaudeAdapter
from prompapa.adapters.codex import CodexAdapter
from prompapa.adapters.opencode import OpenCodeAdapter


# ── Registry tests ─────────────────────────────────────────────────────────────


class TestAdapterRegistry:
    def test_get_adapter_claude(self):
        adapter = get_adapter("claude")
        assert isinstance(adapter, ClaudeAdapter)

    def test_get_adapter_codex(self):
        adapter = get_adapter("codex")
        assert isinstance(adapter, CodexAdapter)

    def test_get_adapter_opencode(self):
        adapter = get_adapter("opencode")
        assert isinstance(adapter, OpenCodeAdapter)

    def test_get_adapter_unknown(self):
        with pytest.raises(ValueError, match="Unknown target"):
            get_adapter("vim")

    def test_get_adapter_unknown_lists_supported(self):
        with pytest.raises(ValueError, match="claude"):
            get_adapter("vim")


# ── Prompt prefixes ────────────────────────────────────────────────────────────


class TestPromptPrefixes:
    def test_claude_prompt_prefixes(self):
        assert ClaudeAdapter.prompt_prefixes == ("❯ ", "❯")

    def test_codex_prompt_prefixes(self):
        assert CodexAdapter.prompt_prefixes == ("› ", "›")

    def test_opencode_prompt_prefixes(self):
        assert OpenCodeAdapter.prompt_prefixes == ("> ", "  > ")


# ── Capture text tests ────────────────────────────────────────────────────────


class TestCaptureText:
    def test_claude_capture_strips_prompt(self):
        from prompapa.screen import ScreenTracker

        adapter = ClaudeAdapter()
        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("❯ hello world\r\n".encode("utf-8"))
        assert adapter.capture_text(screen) == "hello world"

    def test_codex_capture_strips_prompt(self):
        from prompapa.screen import ScreenTracker

        adapter = CodexAdapter()
        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("› hello world\r\n".encode("utf-8"))
        assert adapter.capture_text(screen) == "hello world"

    def test_opencode_capture_strips_prompt(self):
        from prompapa.screen import ScreenTracker

        adapter = OpenCodeAdapter()
        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("> hello world\r\n".encode("utf-8"))
        assert adapter.capture_text(screen) == "hello world"

    def test_opencode_capture_strips_indented_prompt(self):
        from prompapa.screen import ScreenTracker

        adapter = OpenCodeAdapter()
        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("  > hello world\r\n".encode("utf-8"))
        assert adapter.capture_text(screen) == "hello world"

    def test_codex_capture_with_box_decorations(self):
        from prompapa.screen import ScreenTracker

        adapter = CodexAdapter()
        screen = ScreenTracker(cols=80, rows=24)
        raw = (
            "╭─────────────────────╮\r\n"
            "│ >_ OpenAI Codex     │\r\n"
            "╰─────────────────────╯\r\n"
            "› 안녕하세요 테스트입니다\r\n"
        )
        screen.feed(raw.encode("utf-8"))
        assert adapter.capture_text(screen) == "안녕하세요 테스트입니다"

    def test_claude_capture_with_separator_lines(self):
        from prompapa.screen import ScreenTracker

        adapter = ClaudeAdapter()
        screen = ScreenTracker(cols=160, rows=24)
        raw = (
            "─" * 80 + "\r\n"
            "❯ 클로드 안녕\r\n"
            "─" * 80 + "\r\n"
            "  seil@host ~/path  |  Haiku\r\n"
        )
        screen.feed(raw.encode("utf-8"))
        assert "클로드 안녕" in adapter.capture_text(screen)

    def test_claude_does_not_capture_codex_prompt(self):
        """Claude adapter should NOT detect codex's › prompt."""
        from prompapa.screen import ScreenTracker

        adapter = ClaudeAdapter()
        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("› some codex text\r\n".encode("utf-8"))
        # Falls through to Phase 2 (fallback), which includes the ›
        captured = adapter.capture_text(screen)
        assert "›" in captured  # prompt not stripped since wrong adapter

    def test_codex_does_not_capture_claude_prompt(self):
        """Codex adapter should NOT detect claude's ❯ prompt."""
        from prompapa.screen import ScreenTracker

        adapter = CodexAdapter()
        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("❯ some claude text\r\n".encode("utf-8"))
        captured = adapter.capture_text(screen)
        assert "❯" in captured


# ── Inject text tests ─────────────────────────────────────────────────────────


class TestInjectText:
    def test_claude_inject_uses_bracketed_paste(self):
        adapter = ClaudeAdapter()
        with patch.object(os, "write") as mock_write:
            adapter.inject_text(99, "hello")
        mock_write.assert_called_once_with(99, b"\x1b[200~hello\x1b[201~")

    def test_codex_inject_uses_bracketed_paste(self):
        adapter = CodexAdapter()
        with patch.object(os, "write") as mock_write:
            adapter.inject_text(99, "hello")
        mock_write.assert_called_once_with(99, b"\x1b[200~hello\x1b[201~")

    def test_opencode_inject_uses_bracketed_paste(self):
        adapter = OpenCodeAdapter()
        with patch.object(os, "write") as mock_write:
            adapter.inject_text(99, "hello")
        mock_write.assert_called_once_with(99, b"\x1b[200~hello\x1b[201~")

    def test_inject_handles_unicode(self):
        adapter = ClaudeAdapter()
        with patch.object(os, "write") as mock_write:
            adapter.inject_text(99, "안녕하세요")
        expected = b"\x1b[200~" + "안녕하세요".encode("utf-8") + b"\x1b[201~"
        mock_write.assert_called_once_with(99, expected)


# ── Clear input tests ─────────────────────────────────────────────────────────


class TestClearInput:
    @pytest.mark.asyncio
    async def test_claude_clear_uses_right_arrow_and_backspace(self):
        adapter = ClaudeAdapter()
        writes = []
        with patch.object(
            os, "write", side_effect=lambda fd, data: writes.append(data)
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await adapter.clear_input(99, "hello")

        # "hello" is 5 chars wide + 20 safety = 25
        right_arrows = [w for w in writes if w == b"\x1b[C"]
        assert len(right_arrows) == 25

        # Should have one bulk backspace write
        backspaces = [w for w in writes if b"\x7f" in w and w != b"\x1b[C"]
        assert len(backspaces) == 1
        assert backspaces[0] == b"\x7f" * 25

    @pytest.mark.asyncio
    async def test_claude_clear_handles_korean(self):
        adapter = ClaudeAdapter()
        writes = []
        with patch.object(
            os, "write", side_effect=lambda fd, data: writes.append(data)
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await adapter.clear_input(99, "안녕")

        # "안녕" is 4 chars wide + 20 = 24
        right_arrows = [w for w in writes if w == b"\x1b[C"]
        assert len(right_arrows) == 24

    @pytest.mark.asyncio
    async def test_codex_clear_single_line(self):
        adapter = CodexAdapter()
        writes = []
        with patch.object(
            os, "write", side_effect=lambda fd, data: writes.append(data)
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await adapter.clear_input(99, "hello")

        assert writes[0] == b"\x01"
        assert writes[1] == b"\x0b"
        backspaces = [w for w in writes if w == b"\x7f"]
        assert len(backspaces) == 0

    @pytest.mark.asyncio
    async def test_codex_clear_multiline(self):
        adapter = CodexAdapter()
        writes = []
        with patch.object(
            os, "write", side_effect=lambda fd, data: writes.append(data)
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await adapter.clear_input(99, "line1\nline2\nline3")

        ctrl_a = [w for w in writes if w == b"\x01"]
        ctrl_k = [w for w in writes if w == b"\x0b"]
        backspaces = [w for w in writes if w == b"\x7f"]
        assert len(ctrl_a) == 3
        assert len(ctrl_k) == 3
        assert len(backspaces) == 2

    @pytest.mark.asyncio
    async def test_opencode_clear_single_line(self):
        adapter = OpenCodeAdapter()
        writes = []
        with patch.object(
            os, "write", side_effect=lambda fd, data: writes.append(data)
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await adapter.clear_input(99, "hello")

        assert writes[0] == b"\x01"
        assert writes[1] == b"\x0b"

    @pytest.mark.asyncio
    async def test_opencode_clear_multiline(self):
        adapter = OpenCodeAdapter()
        writes = []
        with patch.object(
            os, "write", side_effect=lambda fd, data: writes.append(data)
        ):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await adapter.clear_input(99, "line1\nline2")

        ctrl_a = [w for w in writes if w == b"\x01"]
        ctrl_k = [w for w in writes if w == b"\x0b"]
        backspaces = [w for w in writes if w == b"\x7f"]
        assert len(ctrl_a) == 2
        assert len(ctrl_k) == 2
        assert len(backspaces) == 1

    @pytest.mark.asyncio
    async def test_clear_empty_string(self):
        """All adapters should handle empty captured gracefully."""
        for AdapterCls in (ClaudeAdapter, CodexAdapter, OpenCodeAdapter):
            adapter = AdapterCls()
            with patch.object(os, "write"):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    await adapter.clear_input(99, "")
            # Should not raise


# ── Screen prompt_prefixes parameterization tests ─────────────────────────────


class TestScreenPromptPrefixes:
    def test_capture_with_codex_prompt(self):
        from prompapa.screen import ScreenTracker

        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("› test input\r\n".encode("utf-8"))
        captured = screen.capture_near_cursor(prompt_prefixes=("› ", "›"))
        assert captured == "test input"

    def test_capture_with_opencode_prompt(self):
        from prompapa.screen import ScreenTracker

        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("> test input\r\n".encode("utf-8"))
        captured = screen.capture_near_cursor(prompt_prefixes=("> ", "  > "))
        assert captured == "test input"

    def test_capture_with_opencode_indented_prompt(self):
        from prompapa.screen import ScreenTracker

        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("  > test input\r\n".encode("utf-8"))
        captured = screen.capture_near_cursor(prompt_prefixes=("> ", "  > "))
        assert captured == "test input"

    def test_default_prompt_prefixes_backwards_compatible(self):
        from prompapa.screen import ScreenTracker

        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("❯ hello world\r\n".encode("utf-8"))
        # Default prefixes should match claude's ❯
        captured = screen.capture_near_cursor()
        assert captured == "hello world"

    def test_strip_prompt_with_custom_prefixes(self):
        from prompapa.screen import ScreenTracker

        # "› test" starts with "› " (first prefix) -> returns "test"
        assert ScreenTracker._strip_prompt("› test", ("› ", "›")) == "test"
        # "›test" (no space) starts with "›" (second prefix) -> returns "test"
        assert ScreenTracker._strip_prompt("›test", ("› ", "›")) == "test"

    def test_strip_prompt_no_match(self):
        from prompapa.screen import ScreenTracker

        assert ScreenTracker._strip_prompt("hello", ("› ", "›")) == "hello"


class TestHeavyBoxChars:
    def test_strip_heavy_vertical(self):
        from prompapa.screen import ScreenTracker

        result = ScreenTracker._strip_decorations("┃ hello world ┃")
        assert result == "hello world"

    def test_strip_heavy_border(self):
        from prompapa.screen import ScreenTracker

        result = ScreenTracker._strip_decorations("┏━━━━━━━━━━━┓")
        assert result == ""

    def test_opencode_prompt_with_heavy_border(self):
        from prompapa.screen import ScreenTracker

        adapter = OpenCodeAdapter()
        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("┃ > 번역할 텍스트 ┃\r\n".encode("utf-8"))
        captured = adapter.capture_text(screen)
        assert "번역할 텍스트" in captured
        assert "┃" not in captured


class TestOpenCodeJunkFiltering:
    def test_filters_osc_color_queries(self):
        from prompapa.screen import ScreenTracker

        adapter = OpenCodeAdapter()
        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("> hello\r\n0;?]4;11;?]4;12;?tmux;\r\n".encode("utf-8"))
        captured = adapter.capture_text(screen)
        assert "hello" in captured
        assert "]4;" not in captured

    def test_filters_tmux_clipboard(self):
        from prompapa.screen import ScreenTracker

        adapter = OpenCodeAdapter()
        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("> test\r\nmux;]52;c;base64data\r\n".encode("utf-8"))
        captured = adapter.capture_text(screen)
        assert "test" in captured
        assert "]52;" not in captured

    def test_preserves_clean_multiline(self):
        from prompapa.screen import ScreenTracker

        adapter = OpenCodeAdapter()
        screen = ScreenTracker(cols=80, rows=24)
        screen.feed("> first line\r\nsecond line\r\n".encode("utf-8"))
        captured = adapter.capture_text(screen)
        assert "first line" in captured
        assert "second line" in captured


class TestPanelIsolation:
    def test_sidebar_excluded_from_capture(self):
        from prompapa.screen import ScreenTracker

        adapter = OpenCodeAdapter()
        screen = ScreenTracker(cols=120, rows=24)
        main = " > 번역할 텍스트" + " " * 40
        sidebar = " ~/projects/foo  "
        row = "┃" + main + "┃" + sidebar + "┃"
        screen.feed((row + "\r\n").encode("utf-8"))
        captured = adapter.capture_text(screen)
        assert "번역할 텍스트" in captured
        assert "projects" not in captured

    def test_strip_decorations_returns_widest_panel(self):
        from prompapa.screen import ScreenTracker

        main_panel = " > text" + " " * 50
        sidebar = " path "
        line = "┃" + main_panel + "┃" + sidebar + "┃"
        result = ScreenTracker._strip_decorations(line)
        assert result == "> text"
        assert "path" not in result

    def test_no_vertical_separators_unchanged(self):
        from prompapa.screen import ScreenTracker

        result = ScreenTracker._strip_decorations("─── hello world ───")
        assert result == "hello world"

    def test_empty_main_panel_returns_empty(self):
        from prompapa.screen import ScreenTracker

        main = " " * 40
        sidebar = " ~/path/to/project "
        line = "┃" + main + "┃" + sidebar + "┃"
        result = ScreenTracker._strip_decorations(line)
        assert result == ""

    def test_decoration_only_main_panel_excludes_sidebar(self):
        """When main panel has only decorations (e.g. horizontal rule),
        column-span should still pick main panel, not sidebar."""
        from prompapa.screen import ScreenTracker

        main_deco = "\u2500" * 60
        sidebar = " ~/projects/foo "
        line = "\u2503" + main_deco + "\u2503" + sidebar + "\u2503"
        result = ScreenTracker._strip_decorations(line)
        assert "projects" not in result
        assert result == ""

    def test_column_span_picks_wider_panel(self):
        """Even if sidebar has more text content, the wider column
        span of the main panel wins."""
        from prompapa.screen import ScreenTracker

        main = " short " + " " * 53
        sidebar = " this sidebar has much longer text content here "
        line = "\u2502" + main + "\u2502" + sidebar + "\u2502"
        result = ScreenTracker._strip_decorations(line)
        assert result == "short"
        assert "sidebar" not in result

    def test_full_block_separator_isolates_sidebar(self):
        """OpenCode uses \u2588 (Full Block) as sidebar separator."""
        from prompapa.screen import ScreenTracker

        main = "  \u2503  user typed text" + " " * 40
        sidebar_text = "    Context"
        line = main + "\u2588" + sidebar_text
        result = ScreenTracker._strip_decorations(line)
        assert "user typed text" in result
        assert "Context" not in result

    def test_single_separator_uses_simple_strip(self):
        """A single vertical separator (just a border) should not
        trigger panel isolation -- use simple strip instead."""
        from prompapa.screen import ScreenTracker

        line = " " * 80 + "\u2503  hello world" + " " * 30
        result = ScreenTracker._strip_decorations(line)
        assert result == "hello world"


class TestOpenCodeRealScreen:
    """Tests using layouts captured from actual opencode 1.2.25."""

    def test_first_screen_captures_input(self):
        from prompapa.screen import ScreenTracker

        adapter = OpenCodeAdapter()
        screen = ScreenTracker(cols=160, rows=40)
        rows = []
        rows.append(" " * 80 + "\u2503" + " " * 74)
        rows.append(
            " " * 80 + "\u2503  " + "\ud55c\uad6d\uc5b4 \ud14c\uc2a4\ud2b8" + " " * 50
        )
        rows.append(" " * 80 + "\u2503" + " " * 74)
        rows.append(
            " " * 80 + "\u2503  Sisyphus (Ultraworker)  Claude Opus 4.6" + " " * 30
        )
        rows.append(" " * 80 + "\u2559" + "\u2580" * 74)
        feed = "\r\n".join(rows) + "\r\n"
        screen.feed(feed.encode("utf-8"))
        # bubbletea positions cursor at the text input, not bottom of screen
        screen.feed(b"\x1b[2;96H")
        captured = adapter.capture_text(screen)
        assert "\ud55c\uad6d\uc5b4 \ud14c\uc2a4\ud2b8" in captured
        assert "Sisyphus" not in captured

    def test_on_session_sidebar_excluded(self):
        from prompapa.screen import ScreenTracker

        adapter = OpenCodeAdapter()
        screen = ScreenTracker(cols=200, rows=40)
        rows = []
        rows.append("  \u2503" + " " * 150 + "\u2588    Session title")
        rows.append(
            "  \u2503  \ud55c\uad6d\uc5b4 \uc785\ub825 \ud14c\uc2a4\ud2b8"
            + " " * 130
            + "\u2588"
        )
        rows.append("  \u2503" + " " * 150 + "\u2588    Context")
        feed = "\r\n".join(rows) + "\r\n"
        screen.feed(feed.encode("utf-8"))
        captured = adapter.capture_text(screen)
        assert "\ud55c\uad6d\uc5b4 \uc785\ub825 \ud14c\uc2a4\ud2b8" in captured
        assert "Session title" not in captured
        assert "Context" not in captured
