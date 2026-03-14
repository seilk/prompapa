from __future__ import annotations

import asyncio
import os

from prompapa.screen import ScreenTracker


class ClaudeAdapter:
    prompt_prefixes = ("❯ ", "❯")

    async def clear_input(self, master_fd: int, captured: str) -> None:
        line_count = captured.count("\n") + 1
        for i in range(line_count):
            os.write(master_fd, b"\x01")
            await asyncio.sleep(0.02)
            os.write(master_fd, b"\x0b")
            await asyncio.sleep(0.02)
            if i < line_count - 1:
                os.write(master_fd, b"\x7f")
                await asyncio.sleep(0.02)

    def capture_text(self, screen: ScreenTracker) -> str:
        # Use cursor expansion with decoration boundaries (no prompt anchor).
        # This works for both normal input and amendment/selection modes
        # where ❯ is a menu cursor, not an input prompt.
        raw = screen.capture_near_cursor(prompt_prefixes=())
        if not raw:
            return raw
        # Strip ❯ prefix cosmetically from the first line.
        lines = raw.split("\n")
        for prefix in self.prompt_prefixes:
            if lines[0].startswith(prefix):
                lines[0] = lines[0][len(prefix):]
                break
        return "\n".join(lines)

    def inject_text(self, master_fd: int, text: str) -> None:
        os.write(
            master_fd,
            b"\x1b[200~" + text.encode("utf-8") + b"\x1b[201~",
        )
