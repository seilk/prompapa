from __future__ import annotations

import asyncio
import os
import re

from prompapa.screen import ScreenTracker

_TERMINAL_JUNK = re.compile(r"\]4;\d|\]52;|tmux;|mux;|\d;\?\]")
_COLUMN_GAP = re.compile(r"\s{10,}")


class OpenCodeAdapter:
    prompt_prefixes = ("> ", "  > ")

    async def clear_input(self, master_fd: int, captured: str) -> None:
        line_count = captured.count("\n") + 1
        for i in range(line_count):
            os.write(master_fd, b"\x01")  # Ctrl+A
            await asyncio.sleep(0.02)
            os.write(master_fd, b"\x0b")  # Ctrl+K
            await asyncio.sleep(0.02)
            if i < line_count - 1:
                os.write(master_fd, b"\x7f")  # Backspace: delete newline
                await asyncio.sleep(0.02)

    @staticmethod
    def _truncate_at_gap(line: str) -> str:
        m = _COLUMN_GAP.search(line)
        if m:
            return line[: m.start()].rstrip()
        return line

    def capture_text(self, screen: ScreenTracker) -> str:
        raw = screen.capture_near_cursor(prompt_prefixes=self.prompt_prefixes)
        lines = []
        for line in raw.split("\n"):
            if not line.strip():
                continue
            if _TERMINAL_JUNK.search(line):
                continue
            line = self._truncate_at_gap(line)
            if line:
                lines.append(line)
        return "\n".join(lines)

    def inject_text(self, master_fd: int, text: str) -> None:
        os.write(
            master_fd,
            b"\x1b[200~" + text.encode("utf-8") + b"\x1b[201~",
        )
