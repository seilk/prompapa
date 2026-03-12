"""
PTY proxy for tui-translator.

Wraps a target CLI app (e.g. `claude`, `opencode`) in a PTY, forwarding all
input/output transparently. Intercepts:
  Ctrl+T (0x14): translate current input line Korean→English in-place
  Ctrl+Z (0x1a): undo last translation

Architecture:
  pty.fork() → asyncio dual-reader loop
  Parent: raw stdin → shadow buffer tracking + forward to child PTY
  Child: exec target command with PROMPT_TOOLKIT_NO_CPR=1
"""
from __future__ import annotations

import asyncio
import fcntl
import os
import pty
import shutil
import signal
import struct
import sys
import termios
import tty
from pathlib import Path

from tui_translator.buffer import ShadowBuffer
from tui_translator.config import AppConfig, ConfigError, default_config_path, load_config, _load_dotenv
from tui_translator.masking import mask_tokens, unmask_tokens
from tui_translator.state import UndoStack
from tui_translator.translator import TranslationError, rewrite_to_english

# ── Pure logic helpers (unit-testable) ────────────────────────────────────────

async def _do_translate(
    buf: ShadowBuffer,
    stack: UndoStack,
    status: dict,
    config: AppConfig,
) -> str:
    """
    Translate current buffer content. Updates buf and stack in-place.
    Returns translated text on success, original text on failure.
    No-op (returns "") if buffer is empty.
    """
    text = buf.text()
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

    def handle_child_output() -> None:
        """Child PTY output → our stdout."""
        try:
            data = os.read(master_fd, 4096)
            os.write(sys.stdout.fileno(), data)
        except OSError:
            loop.stop()

    async def do_translate() -> None:
        nonlocal translating
        translating = True
        text = buf.text()

        # Tell child to clear its line
        try:
            os.write(master_fd, b"\x15")  # Ctrl+U
        except OSError:
            translating = False
            return

        # Show indicator on our stdout
        indicator = b"\r\x1b[2K[tui-translator: translating...]\r"
        os.write(sys.stdout.fileno(), indicator)

        await asyncio.sleep(0.03)  # let child process Ctrl+U

        result = await _do_translate(buf, stack, status, config)

        # Clear indicator
        os.write(sys.stdout.fileno(), b"\r\x1b[2K")

        if result:
            try:
                os.write(master_fd, result.encode("utf-8"))
            except OSError:
                pass

        translating = False

    def do_undo() -> None:
        restored = _do_undo(stack, buf, status)
        if restored is not None:
            try:
                os.write(master_fd, b"\x15")  # Ctrl+U
                os.write(master_fd, restored.encode("utf-8"))
            except OSError:
                pass

    def handle_stdin() -> None:
        """Our stdin → forward to child PTY (with hotkey interception)."""
        nonlocal translating
        try:
            data = os.read(sys.stdin.fileno(), 1024)
        except OSError:
            loop.stop()
            return

        if not data:
            loop.stop()
            return

        # Ctrl+T: translate
        if b"\x14" in data:
            if not translating:
                asyncio.ensure_future(do_translate())
            return

        # Ctrl+Z: undo
        if b"\x1a" in data:
            if not translating:
                do_undo()
            return

        # Update shadow buffer (only when not translating)
        if not translating:
            buf.feed(data)

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
