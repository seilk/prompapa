from __future__ import annotations

import asyncio
import os

from prompapa.screen import ScreenTracker


class CodexAdapter:
    prompt_prefixes = ("› ", "›")

    async def clear_input(self, master_fd: int, captured: str) -> None:
        line_count = captured.count("\n") + 1
        for i in range(line_count):
            os.write(master_fd, b"\x01")  # Ctrl+A: start of line
            await asyncio.sleep(0.02)
            os.write(master_fd, b"\x0b")  # Ctrl+K: kill to end of line
            await asyncio.sleep(0.02)
            if i < line_count - 1:
                os.write(master_fd, b"\x7f")  # Backspace: delete preceding newline
                await asyncio.sleep(0.02)

    # Codex marks every input line with ▌ (U+258C, left half block).
    _INPUT_MARKER = "\u258c"

    def capture_text(self, screen: ScreenTracker) -> str:
        result = screen.capture_by_marker(
            self._INPUT_MARKER, prompt_prefixes=self.prompt_prefixes,
        )
        if result:
            return result
        # Fallback to prompt-based capture.
        return screen.capture_near_cursor(prompt_prefixes=self.prompt_prefixes)

    def inject_text(self, master_fd: int, text: str) -> None:
        os.write(
            master_fd,
            b"\x1b[200~" + text.encode("utf-8") + b"\x1b[201~",
        )
