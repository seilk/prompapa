"""
Tests for cursor-anchored capture_by_marker in ScreenTracker,
plus adapter-specific capture tests based on real tmux captures.
"""

from prompapa.screen import ScreenTracker
from prompapa.adapters.codex import CodexAdapter
from prompapa.adapters.opencode import OpenCodeAdapter


def _make_screen(
    lines: list[str], cols: int = 120, rows: int = 30, cursor_y: int | None = None,
) -> ScreenTracker:
    """Build a ScreenTracker pre-loaded with the given lines."""
    tracker = ScreenTracker(cols=cols, rows=rows)
    raw = "\r\n".join(lines)
    tracker.feed(raw.encode("utf-8"))
    if cursor_y is not None:
        tracker.feed(f"\x1b[{cursor_y + 1};1H".encode("ascii"))
    return tracker


class TestCaptureByMarker:
    def test_basic_marker_expansion(self):
        screen = _make_screen([
            "header",
            "\u258c line1",
            "\u258c line2",
            "\u258c line3",
            "footer",
        ], cursor_y=2)
        result = screen.capture_by_marker("\u258c")
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result
        assert "header" not in result
        assert "footer" not in result

    def test_marker_with_blank_lines(self):
        screen = _make_screen([
            "\u258c text1",
            "\u258c",
            "\u258c text2",
            "\u258c",
            "\u258c text3",
        ], cursor_y=2)
        result = screen.capture_by_marker("\u258c")
        assert "text1" in result
        assert "text2" in result
        assert "text3" in result

    def test_no_marker_returns_empty(self):
        screen = _make_screen([
            "no markers here",
            "just plain text",
        ], cursor_y=0)
        result = screen.capture_by_marker("\u258c")
        assert result == ""

    def test_prompt_prefix_stripped(self):
        screen = _make_screen([
            "\u2503  > hello",
            "\u2503  world",
        ], cursor_y=0)
        result = screen.capture_by_marker("\u2503", prompt_prefixes=("> ",))
        assert "hello" in result
        assert ">" not in result

    def test_panel_isolation_with_marker(self):
        """Marker + sidebar separator → only widest panel captured."""
        screen = _make_screen([
            "\u2503  main text" + " " * 40 + "\u2588 sidebar",
            "\u2503  more text" + " " * 40 + "\u2588 info",
        ], cursor_y=0)
        result = screen.capture_by_marker("\u2503")
        assert "main text" in result
        assert "sidebar" not in result


# ── Codex adapter ───────────────────────────────────────────────────────────


class TestCodexCapture:
    def test_multiline_with_blanks(self):
        """From tmux: every input line prefixed with ▌ (U+258C)."""
        screen = _make_screen([
            "  instructions and tips...",
            "",
            "\u258c 사과",
            "\u258c",
            "\u258c 바나나",
            "\u258c",
            "\u258c 수박",
            "",
            "⏎ send   ⌃J newline",
        ], cursor_y=6)
        captured = CodexAdapter().capture_text(screen)
        assert "사과" in captured
        assert "바나나" in captured
        assert "수박" in captured
        assert "send" not in captured
        assert "instructions" not in captured

    def test_single_line(self):
        screen = _make_screen([
            "",
            "\u258c hello world",
            "",
            "⏎ send",
        ], cursor_y=1)
        captured = CodexAdapter().capture_text(screen)
        assert "hello" in captured

    def test_blank_lines_preserved(self):
        screen = _make_screen([
            "\u258c line1",
            "\u258c",
            "\u258c line2",
        ], cursor_y=2)
        captured = CodexAdapter().capture_text(screen)
        assert "line1" in captured
        assert "line2" in captured


# ── OpenCode adapter ────────────────────────────────────────────────────────


class TestOpenCodeCapture:
    def test_dashboard_multiline(self):
        """Dashboard: ┃ column, model info filtered."""
        screen = _make_screen([
            "                       \u2503",
            "                       \u2503  사과",
            "                       \u2503",
            "                       \u2503  바나나",
            "                       \u2503",
            "                       \u2503  수박",
            "                       \u2503",
            "                       \u2503  Sisyphus (Ultraworker)  GPT-5.4",
            "                       \u2579\u2580" * 37,
        ], cursor_y=5)
        captured = OpenCodeAdapter().capture_text(screen)
        assert "사과" in captured
        assert "바나나" in captured
        assert "수박" in captured
        assert "Sisyphus" not in captured

    def test_session_multiline(self):
        """In-session: chat history shares ┃ column, separated by gap."""
        screen = _make_screen([
            "  \u2503",
            "  \u2503  hello",
            "  \u2503  9:07 PM",
            "  \u2503",
            "  \u2503  Bot response here",
            "  \u2503",
            "     \u25a3  Sisyphus agent info",
            "",
            "  \u2503",
            "  \u2503  사과",
            "  \u2503",
            "  \u2503  바나나",
            "  \u2503",
            "  \u2503  수박",
            "  \u2503",
            "  \u2503  Sisyphus (Ultraworker)  GPT-5.4",
            "  \u2579\u2580" * 30,
        ], cursor_y=13)
        captured = OpenCodeAdapter().capture_text(screen)
        assert "사과" in captured
        assert "바나나" in captured
        assert "수박" in captured
        assert "hello" not in captured
        assert "Bot response" not in captured

    def test_single_line_dashboard(self):
        screen = _make_screen([
            "                       \u2503",
            "                       \u2503  테스트",
            "                       \u2503",
            "                       \u2503  Sisyphus (Ultraworker)  GPT-5.4 OpenAI · max",
            "                       \u2579\u2580" * 37,
        ], cursor_y=1)
        captured = OpenCodeAdapter().capture_text(screen)
        assert "테스트" in captured
        assert "Sisyphus" not in captured
