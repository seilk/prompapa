from __future__ import annotations
import pyte
import shutil


def _is_decoration(ch: str) -> bool:
    cp = ord(ch)
    # U+2500-U+257F Box Drawing, U+2580-U+259F Block Elements
    return 0x2500 <= cp <= 0x259F


class ScreenTracker:
    def __init__(self, cols: int = 0, rows: int = 0) -> None:
        if cols <= 0 or rows <= 0:
            c, r = shutil.get_terminal_size()
            cols = cols or c
            rows = rows or r
        self._screen = pyte.Screen(cols, rows)
        self._stream = pyte.ByteStream(self._screen)

    def feed(self, data: bytes) -> None:
        self._stream.feed(data)

    def resize(self, cols: int, rows: int) -> None:
        self._screen.resize(lines=rows, columns=cols)

    @property
    def cursor(self) -> tuple[int, int]:
        return self._screen.cursor.x, self._screen.cursor.y

    @property
    def display(self) -> list[str]:
        return self._screen.display

    def capture_near_cursor(
        self,
        max_lines: int = 20,
        prompt_prefixes: tuple[str, ...] = ("❯ ", "❯"),
    ) -> str:
        cy = self._screen.cursor.y
        total = len(self._screen.display)

        for y in range(cy, max(cy - max_lines, -1), -1):
            row = self._screen.display[y].rstrip()
            cleaned = self._strip_decorations(row)
            stripped = self._strip_prompt(cleaned, prompt_prefixes)
            if stripped != cleaned:
                lines: list[str] = [stripped]
                for y2 in range(y + 1, min(y + max_lines, total)):
                    row2 = self._screen.display[y2].rstrip()
                    cleaned2 = self._strip_decorations(row2)
                    if not cleaned2 and row2:
                        # Non-empty row that became empty after stripping
                        # decorations = decoration boundary (e.g. ─── line).
                        break
                    if not cleaned2:
                        # Genuinely empty line — preserve as part of input.
                        lines.append("")
                        continue
                    lines.append(cleaned2)
                while lines and not lines[-1]:
                    lines.pop()
                return "\n".join(lines)

        lines = []
        found = False
        for y in range(cy, max(cy - max_lines, -1), -1):
            row = self._screen.display[y].rstrip()
            cleaned = self._strip_decorations(row)
            if not cleaned:
                if found:
                    if row:
                        # Decoration boundary — stop.
                        break
                    # Genuinely empty line — preserve.
                    lines.append("")
                continue
            found = True
            lines.append(cleaned)
        lines.reverse()
        while lines and not lines[-1]:
            lines.pop()
        while lines and not lines[0]:
            lines.pop(0)
        return "\n".join(lines)

    _PANEL_SEPARATORS = frozenset("\u2502\u2503\u2551\u2588")  # │ ┃ ║ █

    @staticmethod
    def _strip_decorations(line: str) -> str:
        # Find vertical separator positions.  Need 2+ separators to
        # define a panel boundary (single separator is just a border).
        seps: list[int] = []
        for i, ch in enumerate(line):
            if ch in ScreenTracker._PANEL_SEPARATORS:
                seps.append(i)

        if len(seps) < 2:
            result = "".join(ch for ch in line if not _is_decoration(ch))
            return result.strip()

        # Compare segments between consecutive separators by column span.
        # Ignores content before first and after last separator (leading/
        # trailing padding that would incorrectly win by span alone).
        best_span = -1
        best_text = ""
        for j in range(len(seps) - 1):
            start = seps[j] + 1
            end = seps[j + 1]
            span = end - start
            if span > best_span:
                segment = line[start:end]
                text = "".join(ch for ch in segment if not _is_decoration(ch))
                best_span = span
                best_text = text
        return best_text.strip()

    def capture_by_marker(
        self,
        marker: str,
        max_lines: int = 30,
        prompt_prefixes: tuple[str, ...] = (),
    ) -> str:
        """Capture input by expanding from cursor while lines contain *marker*.

        Scans backward from cursor to find the topmost contiguous run of
        lines containing *marker*, then collects all text from those lines.
        Stops at the first line that does NOT contain *marker* (the boundary).

        For in-session layouts where chat history shares the same marker,
        a gap (line without marker) separates chat from input.
        """
        cy = self._screen.cursor.y
        display = self._screen.display

        # Find the marker column from the cursor line (or nearby).
        marker_col: int | None = None
        for y in range(cy, max(cy - max_lines, -1), -1):
            row = display[y]
            col = row.find(marker)
            if col != -1:
                marker_col = col
                break
        if marker_col is None:
            return ""

        # Scan UP from cursor: find top of input area.
        # Stop at the first line that doesn't have the marker at the expected column.
        top = 0
        for y in range(cy - 1, max(cy - max_lines, -1), -1):
            row = display[y]
            if len(row) <= marker_col or row[marker_col] != marker:
                top = y + 1
                break

        # Scan DOWN from cursor: find bottom of input area.
        total = len(display)
        bottom = min(cy + 1, total)
        for y in range(cy + 1, min(cy + max_lines, total)):
            row = display[y]
            if len(row) <= marker_col or row[marker_col] != marker:
                bottom = y
                break
            bottom = y + 1

        # Collect lines, stripping decorations with panel isolation.
        # Pass the full row so separator count (┃ + █) enables panel isolation.
        lines: list[str] = []
        for y in range(top, bottom):
            row = display[y].rstrip()
            text = self._strip_decorations(row)
            lines.append(text)

        # Strip prompt prefix from first non-empty line.
        for i, line in enumerate(lines):
            for prefix in prompt_prefixes:
                if line.startswith(prefix):
                    lines[i] = line[len(prefix) :]
                    break

        # Trim leading/trailing empty lines.
        while lines and not lines[-1]:
            lines.pop()
        while lines and not lines[0]:
            lines.pop(0)
        return "\n".join(lines)

    @staticmethod
    def _strip_prompt(line: str, prompt_prefixes: tuple[str, ...] = ("❯ ", "❯")) -> str:
        for prefix in prompt_prefixes:
            if line.startswith(prefix):
                return line[len(prefix) :]
        return line
