from __future__ import annotations

import asyncio
import os
import unicodedata

from prompapa.screen import ScreenTracker


def _display_width(text: str) -> int:
    width = 0
    for ch in text:
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


class ClaudeAdapter:
    prompt_prefixes = ("❯ ", "❯")

    async def clear_input(self, master_fd: int, captured: str) -> None:
        n = _display_width(captured) + 20
        for _ in range(n):
            os.write(master_fd, b"\x1b[C")
            await asyncio.sleep(0.002)
        os.write(master_fd, b"\x7f" * n)
        await asyncio.sleep(0.05)

    def capture_text(self, screen: ScreenTracker) -> str:
        return screen.capture_near_cursor(prompt_prefixes=self.prompt_prefixes)

    def inject_text(self, master_fd: int, text: str) -> None:
        os.write(
            master_fd,
            b"\x1b[200~" + text.encode("utf-8") + b"\x1b[201~",
        )
