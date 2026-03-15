"""
PTY proxy for prompapa.

Wraps a target CLI app (e.g. `claude`, `opencode`) in a PTY, forwarding all
input/output transparently.

Hotkeys (configurable via [hotkeys] in config.toml):
  Ctrl+]  --  Translate entire input text (default).
  Ctrl+Y  --  Undo last translation (default, stack depth: _UNDO_STACK_MAX).

Both raw control bytes and Kitty keyboard protocol (CSI u) sequences are
recognised, so hotkeys work on terminals like Ghostty that use the modern
key encoding.

Screen-capture-first translation flow (zero UI refresh):
  Capture:   pyte ScreenTracker reads the current input cell from the screen.
  Clear:     Ctrl+A + Ctrl+K per line (adapter-specific).
  Translate: API call while TUI stays live.
  Inject:    Bracketed paste (\\x1b[200~ ... \\x1b[201~) into child PTY.
  Undo:      Undo stack — cleared on Enter.
  Errors:    Written as a temporary status line below the prompt.
"""

from __future__ import annotations

import asyncio
import fcntl
import os
import shutil
import signal
import struct
import sys
import termios
import unicodedata

from prompapa.adapters import TargetAdapter
from prompapa.screen import ScreenTracker
from prompapa.config import (
    AppConfig,
    Hotkey,
    SystemConfig,
)
from prompapa.masking import mask_tokens, unmask_tokens
from prompapa.translator import TranslationError, rewrite_to_english

_UNDO_STACK_MAX = 1


def _find_hotkey(data: bytes, hotkey: Hotkey) -> tuple[int, int]:
    """Find a hotkey in *data*, checking both raw byte and Kitty CSI u forms.

    Returns ``(position, byte_length)`` of the earliest match,
    or ``(-1, 0)`` if not found.
    """
    raw_pos = data.find(hotkey.raw)
    csi_pos = data.find(hotkey.csi_u)
    if raw_pos == -1 and csi_pos == -1:
        return (-1, 0)
    if csi_pos == -1:
        return (raw_pos, len(hotkey.raw))
    if raw_pos == -1:
        return (csi_pos, len(hotkey.csi_u))
    if raw_pos <= csi_pos:
        return (raw_pos, len(hotkey.raw))
    return (csi_pos, len(hotkey.csi_u))


def _display_width(text: str) -> int:
    width = 0
    for ch in text:
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


async def _translate_text(text: str, config: AppConfig) -> str:
    ctx = mask_tokens(text, enabled=config.preserve_backticks)
    masked_result = await rewrite_to_english(ctx.masked, config)
    return unmask_tokens(masked_result, ctx.tokens)


def _set_winsize(fd: int) -> None:
    cols, rows = shutil.get_terminal_size()
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


async def _proxy_loop(
    master_fd: int,
    config: AppConfig,
    child_pid: int,
    adapter: TargetAdapter,
    sys_config: SystemConfig | None = None,
) -> None:
    loop = asyncio.get_running_loop()
    translating = False
    sc = sys_config or SystemConfig()
    undo_stack: list[tuple[str, str]] = []
    cols, rows = shutil.get_terminal_size()
    screen = ScreenTracker(cols, rows)

    def handle_child_output() -> None:
        try:
            data = os.read(master_fd, 4096)
            os.write(sys.stdout.fileno(), data)
            screen.feed(data)
        except OSError:
            loop.stop()

    def _forward_to_child(data: bytes) -> bool:
        nonlocal undo_stack
        try:
            os.write(master_fd, data)
        except OSError:
            loop.stop()
            return False
        if b"\r" in data:
            undo_stack.clear()
        return True

    def _bell() -> None:
        try:
            os.write(sys.stdout.fileno(), b"\x07")
        except OSError:
            pass

    def _show_error(msg: str) -> None:
        try:
            line = f"\r\n\x1b[31m[prompapa] {msg}\x1b[0m\r\n"
            os.write(sys.stdout.fileno(), line.encode())
        except OSError:
            pass

    async def _probe_edge(key: bytes) -> tuple[int, int]:
        """Send *key* repeatedly until the cursor stops moving.

        Returns the final cursor position.  For Ctrl+A this reaches the
        very start of the input area; for Ctrl+E the very end — even in
        multi-line inputs where a single press only moves within one line.

        Tunable via ``system.toml``: ``probe_max_repeats``, ``probe_settle_ms``.
        """
        pos = screen.cursor
        for _ in range(sc.probe_max_repeats):
            try:
                os.write(master_fd, key)
            except OSError:
                break
            await asyncio.sleep(sc.probe_settle_ms / 1000)
            new = screen.cursor
            if new == pos:
                break  # cursor stopped moving
            pos = new
        return pos

    async def _probe_capture() -> str:
        """Capture text by probing input boundaries with Home/End keys.

        Sends Ctrl+A repeatedly until the cursor stops → start of input.
        Sends Ctrl+E repeatedly until the cursor stops → end of input.
        Reads screen content between those two positions.
        """
        orig = screen.cursor

        home_x, home_y = await _probe_edge(b"\x01")  # Ctrl+A → Home
        end_x, end_y = await _probe_edge(b"\x05")    # Ctrl+E → End

        # If cursor didn't move at all, probing failed.
        if (home_x, home_y) == (end_x, end_y) == orig:
            return ""

        text = screen.capture_by_cursor_probe(
            home_y, home_x, end_y, end_x,
            prompt_prefixes=adapter.prompt_prefixes,
        )
        return text

    async def _poll_capture(max_ms: int = 300, stale_text: str | None = None) -> str:
        # Try cursor probe first (most accurate).
        probed = await _probe_capture()
        if probed.strip():
            return probed

        # Fallback: screen-based capture via adapter.
        for _ in range(max_ms // 20):
            await asyncio.sleep(0.02)
            text = adapter.capture_text(screen)
            if not text.strip():
                continue
            if stale_text is not None and text.strip() == stale_text.strip():
                continue
            return text
        return ""

    def _nudge_child() -> None:
        _set_winsize(master_fd)

    async def do_translate(stale_text: str | None = None) -> None:
        nonlocal translating, undo_stack
        if translating:
            return
        translating = True
        try:
            captured = await _poll_capture(stale_text=stale_text)
            if not captured.strip():
                _nudge_child()
                captured = await _poll_capture(max_ms=500)
            if not captured.strip():
                _bell()
                return

            await adapter.clear_input(master_fd, captured)

            try:
                result = await _translate_text(captured, config)
            except TranslationError as exc:
                adapter.inject_text(master_fd, captured)
                _show_error(str(exc))
                return
            except Exception as exc:
                adapter.inject_text(master_fd, captured)
                _show_error(str(exc))
                return

            result_text = result.strip()
            undo_stack.append((captured, result_text))
            if len(undo_stack) > _UNDO_STACK_MAX:
                undo_stack.pop(0)
            adapter.inject_text(master_fd, result_text)
        except OSError:
            pass
        finally:
            translating = False

    async def do_undo() -> None:
        nonlocal undo_stack
        if not undo_stack:
            return
        pre, post = undo_stack.pop()
        # Probe the actual editable area for accurate clearing.
        probed = await _probe_capture()
        text_to_clear = probed or post or adapter.capture_text(screen)
        await adapter.clear_input(master_fd, text_to_clear)
        adapter.inject_text(master_fd, pre.strip())

    def handle_stdin() -> None:
        try:
            data = os.read(sys.stdin.fileno(), 1024)
        except OSError:
            loop.stop()
            return

        if not data:
            loop.stop()
            return

        tr_pos, tr_len = _find_hotkey(data, config.hotkey_translate)
        un_pos, un_len = _find_hotkey(data, config.hotkey_undo)

        candidates: list[tuple[int, int, str]] = []
        if tr_pos != -1:
            candidates.append((tr_pos, tr_len, "translate"))
        if un_pos != -1:
            candidates.append((un_pos, un_len, "undo"))

        if not candidates:
            _forward_to_child(data)
            return

        candidates.sort()
        idx, hk_len, action = candidates[0]

        stale = adapter.capture_text(screen) if idx > 0 else None

        if idx > 0:
            if not _forward_to_child(data[:idx]):
                return

        if not translating:
            if action == "translate":
                asyncio.ensure_future(do_translate(stale_text=stale))
            else:
                asyncio.ensure_future(do_undo())

        after = data[idx + hk_len :]
        if after:
            _forward_to_child(after)

    loop.add_reader(master_fd, handle_child_output)
    loop.add_reader(sys.stdin.fileno(), handle_stdin)

    def _on_sigwinch() -> None:
        _set_winsize(master_fd)
        c, r = shutil.get_terminal_size()
        screen.resize(c, r)

    loop.add_signal_handler(signal.SIGWINCH, _on_sigwinch)

    try:
        while True:
            await asyncio.sleep(0.1)
            try:
                result = os.waitpid(-1, os.WNOHANG)
                if result[0] != 0:
                    break
            except ChildProcessError:
                break
    finally:
        loop.remove_reader(master_fd)
        loop.remove_reader(sys.stdin.fileno())


async def _run_translate_once(text: str, config: AppConfig) -> None:
    result = await _translate_text(text, config)
    print(result)


if __name__ == "__main__":
    from prompapa.cli import main

    main()
