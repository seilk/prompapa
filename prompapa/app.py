"""
PTY proxy for prompapa.

Wraps a target CLI app (e.g. `claude`, `opencode`) in a PTY, forwarding all
input/output transparently.

Hotkeys:
  Ctrl+T  —  Translate entire input text.
  Ctrl+Y  —  Undo last translation.

Screen-capture-first translation flow (zero UI refresh):
  Capture:   pyte ScreenTracker reads the current input cell from the screen.
  Clear:     Right-arrow × N (individual writes, cursor to end) + BS × N.
  Translate: API call while TUI stays live.
  Inject:    Bracketed paste (\\x1b[200~ ... \\x1b[201~) into child PTY.
  Undo:      Single `pre_translation` slot — cleared on Enter.
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
from .onboard import run_onboard
from .uninstall import run_uninstall
from .update import run_update
import termios
import tty
import unicodedata
from pathlib import Path

from prompapa.adapters import TargetAdapter, get_adapter
from prompapa.screen import ScreenTracker
from prompapa.config import (
    AppConfig,
    ConfigError,
    default_config_path,
    load_config,
    _load_dotenv,
)
from prompapa.masking import mask_tokens, unmask_tokens
from prompapa.translator import TranslationError, rewrite_to_english

# ── Pure logic helpers (unit-testable) ────────────────────────────────────────


def _display_width(text: str) -> int:
    width = 0
    for ch in text:
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


async def _translate_text(text: str, config: AppConfig) -> str:
    """
    Translate text via the configured API with backtick masking.
    Returns translated text. Raises TranslationError on failure.
    """
    ctx = mask_tokens(text, enabled=config.preserve_backticks)
    masked_result = await rewrite_to_english(ctx.masked, config)
    return unmask_tokens(masked_result, ctx.tokens)


# ── PTY proxy loop ─────────────────────────────────────────────────────────────


def _set_winsize(fd: int) -> None:
    cols, rows = shutil.get_terminal_size()
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


async def _proxy_loop(
    master_fd: int,
    config: AppConfig,
    child_pid: int,
    adapter: TargetAdapter,
) -> None:
    loop = asyncio.get_running_loop()
    translating = False
    pre_translation: str | None = None
    cols, rows = shutil.get_terminal_size()
    screen = ScreenTracker(cols, rows)

    # ── Child output handling ──────────────────────────────────────────────

    def handle_child_output() -> None:
        try:
            data = os.read(master_fd, 4096)
            os.write(sys.stdout.fileno(), data)
            screen.feed(data)
        except OSError:
            loop.stop()

    # ── Forward helper ────────────────────────────────────────────────────

    def _forward_to_child(data: bytes) -> bool:
        nonlocal pre_translation
        try:
            os.write(master_fd, data)
        except OSError:
            loop.stop()
            return False
        # Enter clears the undo snapshot
        if b"\r" in data:
            pre_translation = None
        return True

    # ── Translate ─────────────────────────────────────────────────────────

    def _bell() -> None:
        try:
            os.write(sys.stdout.fileno(), b"\x07")
        except OSError:
            pass

    async def _poll_capture(max_ms: int = 300) -> str:
        # Poll pyte screen every 20ms until non-empty or deadline.
        # Ink batches renders, so yielding lets the event loop
        # process queued handle_child_output callbacks first.
        for _ in range(max_ms // 20):
            await asyncio.sleep(0.02)
            text = adapter.capture_text(screen)
            if text.strip():
                return text
        return ""

    async def do_translate() -> None:
        nonlocal translating, pre_translation
        if translating:
            return
        translating = True
        try:
            captured = await _poll_capture()
            if not captured.strip():
                _bell()
                return

            await adapter.clear_input(master_fd, captured)

            try:
                result = await _translate_text(captured, config)
            except TranslationError:
                adapter.inject_text(master_fd, captured)
                _bell()
                return
            except Exception:
                adapter.inject_text(master_fd, captured)
                _bell()
                return

            pre_translation = captured
            adapter.inject_text(master_fd, result.strip())
        except OSError:
            pass
        finally:
            translating = False

    # ── Undo ───────────────────────────────────────────────────────────────

    async def do_undo() -> None:
        nonlocal pre_translation
        if pre_translation is None:
            return
        captured = adapter.capture_text(screen)
        await adapter.clear_input(master_fd, captured)
        adapter.inject_text(master_fd, pre_translation.strip())
        pre_translation = None

    # ── Stdin handling (Ctrl+T = translate, Ctrl+Y = undo) ────────────────

    def handle_stdin() -> None:
        try:
            data = os.read(sys.stdin.fileno(), 1024)
        except OSError:
            loop.stop()
            return

        if not data:
            loop.stop()
            return

        ctrl_t = data.find(b"\x14")
        ctrl_y = data.find(b"\x19")

        candidates: list[tuple[int, str]] = []
        if ctrl_t != -1:
            candidates.append((ctrl_t, "translate"))
        if ctrl_y != -1:
            candidates.append((ctrl_y, "undo"))

        if not candidates:
            _forward_to_child(data)
            return

        candidates.sort()
        idx, action = candidates[0]

        if idx > 0:
            if not _forward_to_child(data[:idx]):
                return

        if not translating:
            if action == "translate":
                asyncio.ensure_future(do_translate())
            else:
                asyncio.ensure_future(do_undo())

        after = data[idx + 1 :]
        if after:
            _forward_to_child(after)

    # ── Wire up readers and run ────────────────────────────────────────────

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


# ── Entry point ────────────────────────────────────────────────────────────────


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "onboard":
        run_onboard()
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        run_uninstall()
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "update":
        run_update()
        sys.exit(0)

    _load_dotenv(Path(".env"))
    config_path = default_config_path()
    try:
        config = load_config(config_path)
        config.resolve_api_key()
    except ConfigError as e:
        print(f"prompapa: {e}", file=sys.stderr)
        print(f"\nCreate config at: {config_path}", file=sys.stderr)
        print(
            '\nExample:\n  provider = "openai"\n  model = "gpt-4.1-mini"'
            '\n  api_key_env = "OPENAI_API_KEY"\n  target_cmd = ["claude"]',
            file=sys.stderr,
        )
        sys.exit(1)

    if not sys.stdin.isatty():
        print(
            "prompapa: stdin is not a TTY. Run directly in a terminal, not inside a pipe or IDE shell.",
            file=sys.stderr,
        )
        sys.exit(1)

    args = sys.argv[1:]
    if args:
        target_name = args[0]
        cmd = args
    else:
        cmd = config.target_cmd
        target_name = cmd[0]

    try:
        adapter = get_adapter(target_name)
    except ValueError as e:
        print(f"prompapa: {e}", file=sys.stderr)
        sys.exit(1)

    if not shutil.which(cmd[0]):
        print(f"prompapa: command not found: {cmd[0]}", file=sys.stderr)
        sys.exit(1)

    pid, master_fd = pty.fork()

    if pid == 0:
        os.environ["PROMPT_TOOLKIT_NO_CPR"] = "1"
        os.execvp(cmd[0], cmd)
        sys.exit(1)

    _set_winsize(master_fd)
    old_attrs = termios.tcgetattr(sys.stdin.fileno())
    tty.setraw(sys.stdin.fileno())

    try:
        asyncio.run(_proxy_loop(master_fd, config, pid, adapter))
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, old_attrs)
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        os.close(master_fd)


if __name__ == "__main__":
    main()
