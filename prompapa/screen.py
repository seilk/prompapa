from __future__ import annotations
import pyte
import shutil

_BOX_CHARS = set("─│┌┐└┘├┤┬┴┼╭╮╰╯╴╵╶╷═║╔╗╚╝╠╣╦╩╬▀▄█▌▐░▒▓")


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

    def capture_near_cursor(self, max_lines: int = 20) -> str:
        cy = self._screen.cursor.y
        total = len(self._screen.display)

        for y in range(cy, max(cy - max_lines, -1), -1):
            row = self._screen.display[y].rstrip()
            cleaned = self._strip_decorations(row)
            stripped = self._strip_prompt(cleaned)
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
        result = "".join(ch for ch in line if ch not in _BOX_CHARS)
        return result.strip()

    @staticmethod
    def _strip_prompt(line: str) -> str:
        for prefix in ("❯ ", "❯"):
            if line.startswith(prefix):
                return line[len(prefix) :]
        return line
