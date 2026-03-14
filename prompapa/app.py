"""
PTY proxy for prompapa.

Wraps a target CLI app (e.g. `claude`, `opencode`) in a PTY, forwarding all
input/output transparently.

Hotkeys:
  Ctrl+]  --  Translate entire input text.
  Ctrl+Q  --  Undo last translation (stack depth: _UNDO_STACK_MAX).

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

_UNDO_STACK_MAX = 10


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
) -> None:
    loop = asyncio.get_running_loop()
    translating = False
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

    async def _poll_capture(max_ms: int = 300, stale_text: str | None = None) -> str:
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
        text_to_clear = post or adapter.capture_text(screen)
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

        ctrl_bracket = data.find(b"\x1d")
        ctrl_q = data.find(b"\x11")

        candidates: list[tuple[int, str]] = []
        if ctrl_bracket != -1:
            candidates.append((ctrl_bracket, "translate"))
        if ctrl_q != -1:
            candidates.append((ctrl_q, "undo"))

        if not candidates:
            _forward_to_child(data)
            return

        candidates.sort()
        idx, action = candidates[0]

        stale = adapter.capture_text(screen) if idx > 0 else None

        if idx > 0:
            if not _forward_to_child(data[:idx]):
                return

        if not translating:
            if action == "translate":
                asyncio.ensure_future(do_translate(stale_text=stale))
            else:
                asyncio.ensure_future(do_undo())

        after = data[idx + 1 :]
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

    if len(sys.argv) >= 3 and sys.argv[1] == "-t":
        text = " ".join(sys.argv[2:])
        try:
            asyncio.run(_run_translate_once(text, config))
        except TranslationError as e:
            print(f"prompapa: translation failed: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

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
