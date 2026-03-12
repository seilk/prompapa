"""
PTY proxy for tui-translator.

Wraps a target CLI app (e.g. `claude`, `opencode`) in a PTY, forwarding all
input/output transparently. Intercepts:
  Ctrl+T (0x14): translate current input line Korean→English in-place
  Ctrl+Z (0x1a): undo last translation

Architecture:
  pty.fork() → asyncio dual-reader loop
  Parent: raw stdin → forward to child PTY
  Child: exec target command with PROMPT_TOOLKIT_NO_CPR=1

Line capture strategy:
  Ctrl+U clears the line (saves to readline kill-ring).
  Ctrl+Y yanks it back — the yanked text appears in child stdout.
  We read that stdout to get the actual current line content.
"""
from __future__ import annotations

import asyncio
import fcntl
import os
import pty
import re
import shutil
import signal
import struct
import sys
import termios
import tty
from pathlib import Path

# Matches: CSI sequences (ESC[...X), OSC sequences (ESC]...BEL), DCS/PM/APC,
# private mode sequences (?2026h etc), and bare ESC + one char
_ANSI_RE = re.compile(
    rb'\x1b\[[\x30-\x3f]*[\x20-\x2f]*[\x40-\x7e]'  # CSI: ESC [ params intermediate final
    rb'|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)'          # OSC: ESC ] ... BEL or ST
    rb'|\x1b[PX^_][^\x1b]*\x1b\\'                   # DCS/SOS/PM/APC
    rb'|\x1b.'                                        # ESC + any single char
)


def _read_with_timeout(fd: int, size: int = 4096, timeout: float = 0.3) -> bytes:
    """Read from fd with timeout. Returns b'' if no data available within timeout."""
    import select
    try:
        r, _, _ = select.select([fd], [], [], timeout)
        if not r:
            return b""
        return os.read(fd, size)
    except OSError:
        return b""


def _strip_ansi(data: bytes) -> str:
    return _ANSI_RE.sub(b'', data).decode('utf-8', errors='replace').strip()

from tui_translator.buffer import ShadowBuffer
from tui_translator.config import AppConfig, ConfigError, default_config_path, load_config, _load_dotenv
from tui_translator.masking import mask_tokens, unmask_tokens
from tui_translator.state import UndoStack
from tui_translator.translator import TranslationError, rewrite_to_english

# ── Pure logic helpers (unit-testable) ────────────────────────────────────────

async def _do_translate(
    text: str,
    stack: UndoStack,
    buf: ShadowBuffer,
    status: dict,
    config: AppConfig,
) -> str:
    """
    Translate the given text. Updates buf and stack in-place.
    Returns translated text on success, original text on failure.
    No-op (returns "") if text is empty.
    """
    if not text.strip():
        return text

    status["msg"] = "translating"
    ctx = mask_tokens(text, enabled=config.preserve_backticks)

    try:
        masked_result = await rewrite_to_english(ctx.masked, config)
    except TranslationError as e:
        status["msg"] = f"[Error] {e}"
        return text

    result = unmask_tokens(masked_result, ctx.tokens)
    stack.push(text)
    buf.set_text(result)
    status["msg"] = ""
    return result


def _do_undo(
    stack: UndoStack,
    buf: ShadowBuffer,
    status: dict,
) -> str | None:
    """
    Restore last pre-translation snapshot.
    Updates buf in-place. Returns restored text or None if nothing to undo.
    """
    if not stack.can_undo():
        status["msg"] = "[Info] Nothing to undo."
        return None
    restored = stack.pop()
    buf.set_text(restored)
    status["msg"] = ""
    return restored


# ── PTY proxy loop ─────────────────────────────────────────────────────────────

def _set_winsize(fd: int) -> None:
    """Forward current terminal window size to PTY master fd."""
    cols, rows = shutil.get_terminal_size()
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


async def _proxy_loop(master_fd: int, config: AppConfig) -> None:
    """
    Asyncio event loop body for the PTY proxy.
    Reads from stdin and master_fd simultaneously.
    """
    loop = asyncio.get_running_loop()
    stack = UndoStack()
    buf = ShadowBuffer()
    status: dict[str, str] = {"msg": ""}
    translating = False
    waiting_chord = False  # True after Ctrl+T, waiting for T or L

    def handle_child_output() -> None:
        """Child PTY output → our stdout."""
        try:
            data = os.read(master_fd, 4096)
            os.write(sys.stdout.fileno(), data)
        except OSError:
            loop.stop()

    async def _capture_current_line() -> str:
        """Capture current line via Ctrl+E + Ctrl+U + Ctrl+Y. Returns stripped text."""
        # Drain stale data
        while _read_with_timeout(master_fd, timeout=0.02):
            pass

        # Ctrl+E: move to end of line
        os.write(master_fd, b"\x05")
        await asyncio.sleep(0.03)
        _read_with_timeout(master_fd, timeout=0.05)

        # Ctrl+U: kill line → kill-ring
        os.write(master_fd, b"\x15")
        await asyncio.sleep(0.05)
        _read_with_timeout(master_fd)  # discard backspaces

        # Ctrl+Y: yank back → appears in stdout
        os.write(master_fd, b"\x19")
        await asyncio.sleep(0.05)
        raw = _read_with_timeout(master_fd)
        captured = _strip_ansi(raw)

        if captured.strip():
            # Ctrl+U: clear the yanked text (we have it now)
            os.write(master_fd, b"\x15")
            await asyncio.sleep(0.03)
            _read_with_timeout(master_fd)

        return captured

    async def _capture_all_lines() -> str:
        """
        Capture entire multiline buffer by iterating upward line by line.
        Uses Up arrow to move to previous lines, captures each via Ctrl+U/Y.
        Returns lines joined with newline, in correct top-to-bottom order.
        """
        lines: list[str] = []

        # Capture current (last) line first
        line = await _capture_current_line()
        if not line.strip():
            return ""
        lines.append(line)

        # Walk upward collecting lines until Up arrow produces no new content
        MAX_LINES = 20
        for _ in range(MAX_LINES):
            # Move up one line
            os.write(master_fd, b"\x1b[A")  # Up arrow
            await asyncio.sleep(0.08)
            _read_with_timeout(master_fd, timeout=0.05)  # discard cursor movement

            line = await _capture_current_line()
            if not line.strip():
                break
            # Avoid collecting duplicate (Up arrow at top of buffer repeats last line)
            if line == lines[-1]:
                break
            lines.append(line)

        # lines are bottom-to-top; reverse for correct order
        lines.reverse()
        return "\n".join(lines)

    async def _run_translation(captured: str) -> None:
        """Translate captured text and inject result into child."""
        try:
            indicator = b"\r\x1b[2K[tui-translator: translating...]\r"
            os.write(sys.stdout.fileno(), indicator)

            result = await _do_translate(captured, stack, buf, status, config)

            os.write(sys.stdout.fileno(), b"\r\x1b[2K")

            if result:
                os.write(master_fd, result.encode("utf-8"))
        except OSError:
            pass

    async def do_translate_line() -> None:
        """Ctrl+T L — translate current line only."""
        nonlocal translating
        if translating:
            return
        translating = True
        loop.remove_reader(master_fd)
        captured = ""
        try:
            captured = await _capture_current_line()
        except OSError:
            captured = ""
        finally:
            loop.add_reader(master_fd, handle_child_output)

        if captured.strip():
            await _run_translation(captured)
        translating = False

    async def do_translate_all() -> None:
        """Ctrl+T T — translate entire multiline buffer."""
        nonlocal translating
        if translating:
            return
        translating = True
        loop.remove_reader(master_fd)
        captured = ""
        try:
            captured = await _capture_all_lines()
        except OSError:
            captured = ""
        finally:
            loop.add_reader(master_fd, handle_child_output)

        if captured.strip():
            await _run_translation(captured)
        translating = False

    def do_undo() -> None:
        restored = _do_undo(stack, buf, status)
        if restored is not None:
            try:
                os.write(master_fd, b"\x05")   # Ctrl+E: move to end of line
                os.write(master_fd, b"\x15")   # Ctrl+U: kill whole line
                os.write(master_fd, restored.encode("utf-8"))
            except OSError:
                pass

    def handle_stdin() -> None:
        """Our stdin → forward to child PTY (with hotkey interception)."""
        nonlocal translating, waiting_chord
        try:
            data = os.read(sys.stdin.fileno(), 1024)
        except OSError:
            loop.stop()
            return

        if not data:
            loop.stop()
            return

        # Chord: waiting for second key after Ctrl+T
        if waiting_chord:
            waiting_chord = False
            key = data[0:1]
            if key in (b"t", b"T") and not translating:
                asyncio.ensure_future(do_translate_all())
            elif key in (b"l", b"L") and not translating:
                asyncio.ensure_future(do_translate_line())
            # anything else: discard (cancel chord)
            return

        # Ctrl+T: enter chord mode
        if b"\x14" in data:
            if not translating:
                waiting_chord = True
            return

        # Ctrl+Z: undo
        if b"\x1a" in data:
            if not translating:
                do_undo()
            return

        # Forward to child
        try:
            os.write(master_fd, data)
        except OSError:
            loop.stop()

    loop.add_reader(master_fd, handle_child_output)
    loop.add_reader(sys.stdin.fileno(), handle_stdin)
    loop.add_signal_handler(signal.SIGWINCH, lambda: _set_winsize(master_fd))

    # Run until child exits or loop stopped
    try:
        while True:
            await asyncio.sleep(0.1)
            # Check if child still alive
            try:
                result = os.waitpid(-1, os.WNOHANG)
                if result[0] != 0:
                    break
            except ChildProcessError:
                break
    finally:
        loop.remove_reader(master_fd)
        loop.remove_reader(sys.stdin.fileno())


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    _load_dotenv(Path(".env"))
    config_path = default_config_path()
    try:
        config = load_config(config_path)
        config.resolve_api_key()
    except ConfigError as e:
        print(f"tui-translator: {e}", file=sys.stderr)
        print(f"\nCreate config at: {config_path}", file=sys.stderr)
        print(
            '\nExample:\n  provider = "openai"\n  model = "gpt-4.1-mini"'
            '\n  api_key_env = "OPENAI_API_KEY"\n  target_cmd = ["claude"]',
            file=sys.stderr,
        )
        sys.exit(1)

    if not sys.stdin.isatty():
        print("tui-translator: stdin is not a TTY. Run directly in a terminal, not inside a pipe or IDE shell.", file=sys.stderr)
        sys.exit(1)

    cmd = config.target_cmd
    if not shutil.which(cmd[0]):
        print(f"tui-translator: command not found: {cmd[0]}", file=sys.stderr)
        sys.exit(1)

    # Fork with PTY
    pid, master_fd = pty.fork()

    if pid == 0:
        # Child: exec target command
        os.environ["PROMPT_TOOLKIT_NO_CPR"] = "1"
        os.execvp(cmd[0], cmd)
        # execvp never returns
        sys.exit(1)

    # Parent: set up raw mode and run proxy
    _set_winsize(master_fd)
    old_attrs = termios.tcgetattr(sys.stdin.fileno())
    tty.setraw(sys.stdin.fileno())

    try:
        asyncio.run(_proxy_loop(master_fd, config))
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, old_attrs)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        os.close(master_fd)


if __name__ == "__main__":
    main()
