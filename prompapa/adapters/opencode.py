from __future__ import annotations

import asyncio
import os

from prompapa.screen import ScreenTracker


class OpenCodeAdapter:
    async def clear_input(self, master_fd: int, n: int) -> None:
        # TODO: test whether OpenTUI needs individual right-arrow delays
        # or if bulk cursor movement works natively
        for _ in range(n):
            os.write(master_fd, b"\x1b[C")
            await asyncio.sleep(0.002)
        os.write(master_fd, b"\x7f" * n)
        await asyncio.sleep(0.05)

    def capture_text(self, screen: ScreenTracker) -> str:
        # TODO: OpenCode has no ❯ prompt — need custom capture logic
        # that identifies the textarea region from the screen layout
        return screen.capture_near_cursor()

    def inject_text(self, master_fd: int, text: str) -> None:
        # Bracketed paste works for text < 150 chars / < 3 lines.
        # Longer pastes get summarized by OpenCode's onPaste handler.
        os.write(
            master_fd,
            b"\x1b[200~" + text.encode("utf-8") + b"\x1b[201~",
        )
