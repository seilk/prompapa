from __future__ import annotations

import asyncio
import os

from prompapa.screen import ScreenTracker


class CodexAdapter:
    prompt_prefixes = ("› ", "›")

    async def clear_input(self, master_fd: int, captured: str) -> None:
        line_count = captured.count("\n") + 1
        os.write(master_fd, b"\x01")  # Ctrl+A: move to start of line
        await asyncio.sleep(0.05)
        for _ in range(line_count + 2):  # +2 safety margin
            os.write(master_fd, b"\x0b")  # Ctrl+K: kill to end of line
            await asyncio.sleep(0.02)

    def capture_text(self, screen: ScreenTracker) -> str:
        return screen.capture_near_cursor(prompt_prefixes=self.prompt_prefixes)

    def inject_text(self, master_fd: int, text: str) -> None:
        os.write(
            master_fd,
            b"\x1b[200~" + text.encode("utf-8") + b"\x1b[201~",
        )
