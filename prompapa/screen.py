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
                    if not cleaned2:
                        break
                    lines.append(cleaned2)
                return "\n".join(lines)

        lines = []
        found = False
        for y in range(cy, max(cy - max_lines, -1), -1):
            row = self._screen.display[y].rstrip()
            cleaned = self._strip_decorations(row)
            if not cleaned:
                if found:
                    break
                continue
            found = True
            lines.append(cleaned)
        lines.reverse()
        return "\n".join(lines)

    @staticmethod
    def _strip_decorations(line: str) -> str:
        # Split at vertical box separators to isolate TUI panels,
        # then return the widest panel (main content area).
        # Prevents sidebar content from contaminating capture.
        panels: list[str] = [""]
        for ch in line:
            if ch in ("│", "┃", "║"):
                panels.append("")
            elif _is_decoration(ch):
                continue
            else:
                panels[-1] += ch

        if len(panels) <= 1:
            return panels[0].strip()

        widest = max(panels, key=len)
        return widest.strip()

    @staticmethod
    def _strip_prompt(line: str, prompt_prefixes: tuple[str, ...] = ("❯ ", "❯")) -> str:
        for prefix in prompt_prefixes:
            if line.startswith(prefix):
                return line[len(prefix) :]
        return line
