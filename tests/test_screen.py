import pytest
from prompapa.screen import ScreenTracker


class TestScreenTrackerInitialization:
    def test_initial_screen_size(self):
        tracker = ScreenTracker(cols=80, rows=24)
        assert len(tracker.display) == 24
        assert all(len(line) == 80 for line in tracker.display)


class TestScreenTrackerFeed:
    def test_feed_simple_text(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(b"hello")
        display_text = tracker.display[0]
        assert "hello" in display_text

    def test_cursor_position_after_write(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(b"hello")
        x, y = tracker.cursor
        assert x == 5
        assert y == 0

    def test_feed_with_newline(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(b"line1\r\nline2")
        assert "line1" in tracker.display[0]
        assert "line2" in tracker.display[1]


class TestScreenTrackerResize:
    def test_resize(self):
        tracker = ScreenTracker(cols=80, rows=24)
        initial_rows = len(tracker.display)
        tracker.resize(cols=100, rows=30)
        assert len(tracker.display) == 30
        assert all(len(line) == 100 for line in tracker.display)


class TestCaptureNearCursor:
    def test_capture_near_cursor_single_line(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(b"hello world")
        captured = tracker.capture_near_cursor()
        assert "hello world" in captured

    def test_capture_near_cursor_multiline(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(b"line1\r\nline2\r\nline3")
        captured = tracker.capture_near_cursor()
        assert "line1" in captured
        assert "line2" in captured
        assert "line3" in captured

    def test_capture_stops_at_empty_line(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(b"line1\r\nline2\r\n\r\nline4")
        captured = tracker.capture_near_cursor()
        assert "line4" in captured
        assert "line2" not in captured

    def test_capture_skips_empty_lines_at_cursor(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(b"some text\r\n\r\n")
        _, cy = tracker.cursor
        assert cy == 2
        captured = tracker.capture_near_cursor()
        assert "some text" in captured

    def test_capture_stops_at_prompt_and_strips_chrome(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(
            "user@host ~/path\r\nclaude-opus code\r\n❯ input text\r\n".encode("utf-8")
        )
        captured = tracker.capture_near_cursor()
        assert captured == "input text"
        assert "user@host" not in captured
        assert "claude-opus" not in captured

    def test_capture_multiline_input_with_prompt(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed("status info\r\n❯ first line\r\nsecond line\r\n".encode("utf-8"))
        captured = tracker.capture_near_cursor()
        assert "first line" in captured
        assert "second line" in captured
        assert "status" not in captured

    def test_capture_prompt_above_status_bar(self):
        tracker = ScreenTracker(cols=160, rows=24)
        raw = (
            "─" * 80 + "\r\n"
            "❯ 클로드 안녕\r\n"
            "─" * 80 + "\r\n"
            "  seil@host ~/path  |  Haiku\r\n"
            "  ⏵⏵ accept edits on\r\n"
        )
        tracker.feed(raw.encode("utf-8"))
        captured = tracker.capture_near_cursor()
        assert "클로드 안녕" in captured
        assert "seil@host" not in captured
        assert "⏵⏵" not in captured

    def test_capture_with_ansi_styled_prompt(self):
        tracker = ScreenTracker(cols=160, rows=24)
        raw = (
            "─" * 80 + "\r\n"
            "\x1b[1;38;2;100;200;50m❯\x1b[0m 한국어 텍스트\r\n"
            "─" * 80 + "\r\n"
            "\x1b[90m  seil@host ~/path  |  Haiku\x1b[0m\r\n"
            "  ⏵⏵ accept edits on\r\n"
        )
        tracker.feed(raw.encode("utf-8"))
        captured = tracker.capture_near_cursor()
        assert "한국어 텍스트" in captured
        assert "seil@host" not in captured

    def test_capture_cursor_on_prompt_line(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed("❯ test input".encode("utf-8"))
        captured = tracker.capture_near_cursor()
        assert captured == "test input"


class TestStripDecorations:
    def test_strip_decorations_removes_box_chars(self):
        result = ScreenTracker._strip_decorations("┌─────┐")
        assert result == ""

    def test_strip_decorations_removes_heavy_box_chars(self):
        result = ScreenTracker._strip_decorations("┏━━━━━┓")
        assert result == ""

    def test_strip_decorations_removes_heavy_vertical(self):
        result = ScreenTracker._strip_decorations("┃ text ┃")
        assert result == "text"

    def test_strip_decorations_preserves_text(self):
        result = ScreenTracker._strip_decorations("  hello world  ")
        assert result == "hello world"

    def test_capture_near_cursor_with_decorations(self):
        tracker = ScreenTracker(cols=80, rows=24)
        text = "┌─────────────┐\r\n│ hello world │\r\n│ more text   │"
        tracker.feed(text.encode("utf-8"))
        captured = tracker.capture_near_cursor()
        assert "hello world" in captured
        assert "more text" in captured
        assert "┌" not in captured
        assert "│" not in captured

    def test_capture_near_cursor_with_heavy_decorations(self):
        tracker = ScreenTracker(cols=80, rows=24)
        text = "┏━━━━━━━━━━━━━┓\r\n┃ hello world ┃\r\n┃ more text   ┃"
        tracker.feed(text.encode("utf-8"))
        captured = tracker.capture_near_cursor()
        assert "hello world" in captured
        assert "more text" in captured
        assert "┃" not in captured
        assert "━" not in captured
