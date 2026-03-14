import pytest
from prompapa.screen import ScreenTracker, _is_decoration


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

    def test_capture_preserves_blank_lines(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(b"line1\r\nline2\r\n\r\nline4")
        captured = tracker.capture_near_cursor()
        assert "line1" in captured
        assert "line2" in captured
        assert "line4" in captured

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


class TestIsDecoration:
    """_is_decoration covers U+2500-U+259F: Box Drawing + Block Elements."""

    def test_light_box_drawing(self):
        # U+2500 (─), U+2502 (│), U+250C (┌), U+2510 (┐), U+2514 (└), U+2518 (┘)
        for ch in "─│┌┐└┘":
            assert _is_decoration(ch), f"{ch!r} (U+{ord(ch):04X}) should be decoration"

    def test_heavy_box_drawing(self):
        # U+2501 (━), U+2503 (┃), U+250F (┏), U+2513 (┓), U+2517 (┗), U+251B (┛)
        for ch in "━┃┏┓┗┛":
            assert _is_decoration(ch), f"{ch!r} (U+{ord(ch):04X}) should be decoration"

    def test_double_line_box_drawing(self):
        # U+2550 (═), U+2551 (║), U+2554 (╔), U+2557 (╗), U+255A (╚), U+255D (╝)
        for ch in "═║╔╗╚╝":
            assert _is_decoration(ch), f"{ch!r} (U+{ord(ch):04X}) should be decoration"

    def test_block_elements(self):
        # U+2580 (▀), U+2584 (▄), U+2588 (█), U+258C (▌), U+2590 (▐), U+2591-2593 (░▒▓)
        for ch in "▀▄█▌▐░▒▓":
            assert _is_decoration(ch), f"{ch!r} (U+{ord(ch):04X}) should be decoration"

    def test_half_block_at_boundary(self):
        # U+2579 (╹) -- encountered in opencode rendering
        assert _is_decoration("\u2579")
        # U+259F (▟) -- last char in block elements range
        assert _is_decoration("\u259f")

    def test_normal_text_not_decoration(self):
        for ch in "abcABC123 !@#$%":
            assert not _is_decoration(ch), f"{ch!r} should NOT be decoration"

    def test_cjk_not_decoration(self):
        for ch in "한국어中文日本語":
            assert not _is_decoration(ch)

    def test_boundary_below_range(self):
        # U+24FF is just below the box drawing range
        assert not _is_decoration("\u24ff")

    def test_boundary_above_range(self):
        # U+25A0 (■) is just above block elements range
        assert not _is_decoration("\u25a0")


class TestPanelIsolationRobustness:
    def test_zero_separators_simple_strip(self):
        result = ScreenTracker._strip_decorations("  hello world  ")
        assert result == "hello world"

    def test_one_separator_simple_strip(self):
        # Single separator = just a border, not panel boundary
        result = ScreenTracker._strip_decorations("\u2503 hello world")
        assert result == "hello world"

    def test_two_separators_panel_isolation(self):
        main = " text " + " " * 40
        side = " path "
        line = "\u2502" + main + "\u2502" + side + "\u2502"
        result = ScreenTracker._strip_decorations(line)
        assert result == "text"
        assert "path" not in result

    def test_three_separators_picks_widest(self):
        panel1 = " A " + " " * 30
        panel2 = " B " + " " * 50
        panel3 = " C "
        line = "\u2502" + panel1 + "\u2502" + panel2 + "\u2502" + panel3 + "\u2502"
        result = ScreenTracker._strip_decorations(line)
        assert result == "B"

    def test_mixed_separator_types(self):
        # │ and █ both in _PANEL_SEPARATORS
        main = " user input text " + " " * 40
        sidebar = " context "
        line = "\u2502" + main + "\u2588" + sidebar
        result = ScreenTracker._strip_decorations(line)
        assert "user input text" in result
        assert "context" not in result

    def test_heavy_and_full_block_mixed(self):
        # ┃ and █ -- opencode session uses both
        main = "  \u2503  typed text" + " " * 40
        sidebar = "    sidebar"
        line = main + "\u2588" + sidebar
        result = ScreenTracker._strip_decorations(line)
        assert "typed text" in result
        assert "sidebar" not in result

    def test_all_separator_types_recognized(self):
        # │ (U+2502), ┃ (U+2503), ║ (U+2551), █ (U+2588)
        for sep in "\u2502\u2503\u2551\u2588":
            main = " text " + " " * 30
            side = " path "
            line = sep + main + sep + side + sep
            result = ScreenTracker._strip_decorations(line)
            assert result == "text", f"Failed for separator U+{ord(sep):04X}"
            assert "path" not in result

    def test_asymmetric_layout_wider_left(self):
        left = " wide content area " + " " * 60
        right = " x "
        line = "\u2502" + left + "\u2502" + right + "\u2502"
        result = ScreenTracker._strip_decorations(line)
        assert "wide content area" in result
        assert "x" not in result

    def test_asymmetric_layout_wider_right(self):
        left = " y "
        right = " wide content area " + " " * 60
        line = "\u2502" + left + "\u2502" + right + "\u2502"
        result = ScreenTracker._strip_decorations(line)
        assert "wide content area" in result

    def test_edge_only_separators_at_start_and_end(self):
        # Two seps at edges = panel isolation with one panel
        line = "\u2502" + " hello " + " " * 40 + "\u2502"
        result = ScreenTracker._strip_decorations(line)
        assert result == "hello"

    def test_empty_panels(self):
        line = "\u2502" + " " * 40 + "\u2502" + " " * 20 + "\u2502"
        result = ScreenTracker._strip_decorations(line)
        assert result == ""


class TestCaptureEdgeCases:
    def test_cursor_at_top_of_screen(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(b"hello")
        assert tracker.cursor[1] == 0
        captured = tracker.capture_near_cursor()
        assert "hello" in captured

    def test_all_empty_lines_returns_empty(self):
        tracker = ScreenTracker(cols=80, rows=24)
        captured = tracker.capture_near_cursor()
        assert captured == ""

    def test_prompt_on_cursor_line_no_continuation(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed("\u276f single line only".encode("utf-8"))
        captured = tracker.capture_near_cursor()
        assert captured == "single line only"

    def test_multiline_input_with_blank_lines_and_prompt(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(
            "❯ 사과\r\n\r\n바나나\r\n\r\n수박".encode("utf-8")
        )
        captured = tracker.capture_near_cursor()
        assert "사과" in captured
        assert "바나나" in captured
        assert "수박" in captured

    def test_prompt_with_blank_lines_stops_at_decoration(self):
        tracker = ScreenTracker(cols=160, rows=24)
        raw = (
            "❯ input text\r\n"
            "\r\n"
            "more text\r\n"
            "─" * 80 + "\r\n"
            "  status bar\r\n"
        )
        tracker.feed(raw.encode("utf-8"))
        captured = tracker.capture_near_cursor()
        assert "input text" in captured
        assert "more text" in captured
        assert "status bar" not in captured

    def test_fallback_multiline_with_single_blank_preserves_all(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(b"line1\r\n\r\nline2\r\n\r\nline3")
        captured = tracker.capture_near_cursor()
        assert "line1" in captured
        assert "line2" in captured
        assert "line3" in captured

    def test_fallback_stops_at_decoration_boundary(self):
        tracker = ScreenTracker(cols=80, rows=24)
        raw = "old output\r\n" + "─" * 40 + "\r\nnew text"
        tracker.feed(raw.encode("utf-8"))
        captured = tracker.capture_near_cursor()
        assert "new text" in captured
        assert "old output" not in captured

    def test_cjk_text_capture(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed("\u276f \ud55c\uad6d\uc5b4 \ud14c\uc2a4\ud2b8\r\n".encode("utf-8"))
        captured = tracker.capture_near_cursor()
        assert captured == "\ud55c\uad6d\uc5b4 \ud14c\uc2a4\ud2b8"

    def test_mixed_cjk_ascii_capture(self):
        tracker = ScreenTracker(cols=80, rows=24)
        tracker.feed(
            "\u276f fix `src/auth.ts` \ud30c\uc77c\uc744 \uc218\uc815\ud574\uc918\r\n".encode(
                "utf-8"
            )
        )
        captured = tracker.capture_near_cursor()
        assert "fix" in captured
        assert "`src/auth.ts`" in captured
        assert "\ud30c\uc77c\uc744" in captured
