from __future__ import annotations

import asyncio
import os

from prompapa.screen import ScreenTracker


class ClaudeAdapter:
    async def clear_input(self, master_fd: int, n: int) -> None:
        for _ in range(n):
            os.write(master_fd, b"\x1b[C")
            await asyncio.sleep(0.002)
        os.write(master_fd, b"\x7f" * n)
        await asyncio.sleep(0.05)

    def capture_text(self, screen: ScreenTracker) -> str:
        return screen.capture_near_cursor()

    def inject_text(self, master_fd: int, text: str) -> None:
        os.write(
            master_fd,
            b"\x1b[200~" + text.encode("utf-8") + b"\x1b[201~",
        )
