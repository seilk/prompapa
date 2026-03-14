"""
Tests for cursor-anchored capture_by_marker in ScreenTracker.

These verify the generic marker-based expansion logic, independent
of any specific adapter.
"""

from prompapa.screen import ScreenTracker


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
