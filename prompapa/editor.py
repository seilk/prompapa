"""Editor wrapper for prompapa's two-phase translation.

Installed as $EDITOR/$VISUAL before the child process is forked.
When the child app opens an external editor, this script runs instead
of the user's real editor.

IPC protocol:
  1. Proxy creates .request file with "mode:nonce" (capture or inject).
  2. Wrapper atomically claims .request via os.rename → .claimed.
     Only one wrapper can succeed; losers fall through to passthrough.
  3. Wrapper processes the request, writes nonce to .done.
  4. If no .request exists, wrapper execs the user's real editor.
"""

from __future__ import annotations

import os
import shlex
import sys
import tempfile
from pathlib import Path


def _passthrough() -> None:
    real_editor = os.environ.get("TUI_TRANSLATOR_REAL_EDITOR", "") or "vi"
    try:
        parts = shlex.split(real_editor)
    except ValueError:
        parts = []
    if not parts:
        parts = ["vi"]
    os.execvp(parts[0], parts + sys.argv[1:])


def main() -> None:
    pid = os.environ.get("TUI_TRANSLATOR_PID", "")
    base = Path(tempfile.gettempdir())
    request_path = base / f"prompapa-{pid}.request"
    claimed_path = base / f"prompapa-{pid}.claimed"
    capture_path = base / f"prompapa-{pid}.capture"
    result_path = base / f"prompapa-{pid}.result"
    done_path = base / f"prompapa-{pid}.done"

    try:
        os.rename(str(request_path), str(claimed_path))
    except (FileNotFoundError, OSError):
        _passthrough()
        return

    content = claimed_path.read_text(encoding="utf-8").strip()
    claimed_path.unlink(missing_ok=True)

    if ":" not in content:
        _passthrough()
        return

    mode, nonce = content.split(":", 1)

    if mode == "inject":
        if result_path.exists() and len(sys.argv) >= 2:
            result = result_path.read_text(encoding="utf-8")
            result_path.unlink(missing_ok=True)
            target = Path(sys.argv[-1])
            tmp_fd, tmp_name = tempfile.mkstemp(dir=target.parent, suffix=".tui-tmp")
            try:
                with os.fdopen(tmp_fd, "wb") as f:
                    f.write(result.encode("utf-8"))
                os.replace(tmp_name, str(target))
            except Exception:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
                raise
        done_path.write_text(nonce, encoding="utf-8")

    elif mode == "capture":
        if len(sys.argv) >= 2:
            filepath = Path(sys.argv[-1])
            if filepath.exists():
                text = filepath.read_text(encoding="utf-8")
                capture_path.write_text(text, encoding="utf-8")
        done_path.write_text(nonce, encoding="utf-8")

    else:
        _passthrough()


if __name__ == "__main__":
    main()
