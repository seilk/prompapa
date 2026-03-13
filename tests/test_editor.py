import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from prompapa.editor import main

NONCE = "test-nonce-abc123"


def _execvp_guard(*args, **kwargs):
    raise AssertionError(f"Unexpected os.execvp call: {args}")


@pytest.fixture
def ipc_env(monkeypatch):
    pid = str(os.getpid())
    monkeypatch.setenv("TUI_TRANSLATOR_PID", pid)
    monkeypatch.setattr("os.execvp", _execvp_guard)
    base = Path(tempfile.gettempdir())
    yield base, pid
    for suffix in (".request", ".claimed", ".capture", ".result", ".done"):
        (base / f"prompapa-{pid}{suffix}").unlink(missing_ok=True)


def test_capture_mode_saves_text(ipc_env, monkeypatch, tmp_path):
    base, pid = ipc_env
    (base / f"prompapa-{pid}.request").write_text(f"capture:{NONCE}")

    f = tmp_path / "input.txt"
    f.write_text("번역해줘", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", str(f)])

    main()

    assert f.read_text() == "번역해줘"
    capture = base / f"prompapa-{pid}.capture"
    assert capture.read_text() == "번역해줘"
    done = base / f"prompapa-{pid}.done"
    assert done.read_text() == NONCE
    assert not (base / f"prompapa-{pid}.request").exists()
    assert not (base / f"prompapa-{pid}.claimed").exists()


def test_capture_mode_no_file_arg(ipc_env, monkeypatch):
    base, pid = ipc_env
    (base / f"prompapa-{pid}.request").write_text(f"capture:{NONCE}")
    monkeypatch.setattr("sys.argv", ["prompapa-edit"])

    main()

    assert not (base / f"prompapa-{pid}.capture").exists()
    assert (base / f"prompapa-{pid}.done").read_text() == NONCE


def test_capture_mode_missing_file(ipc_env, monkeypatch, tmp_path):
    base, pid = ipc_env
    (base / f"prompapa-{pid}.request").write_text(f"capture:{NONCE}")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", str(tmp_path / "nope.txt")])

    main()

    assert not (base / f"prompapa-{pid}.capture").exists()
    assert (base / f"prompapa-{pid}.done").read_text() == NONCE


def test_inject_mode_writes_result(ipc_env, monkeypatch, tmp_path):
    base, pid = ipc_env
    (base / f"prompapa-{pid}.request").write_text(f"inject:{NONCE}")
    (base / f"prompapa-{pid}.result").write_text(
        "Translated text.", encoding="utf-8"
    )

    f = tmp_path / "input.txt"
    f.write_text("원본 텍스트", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", str(f)])

    main()

    assert f.read_text() == "Translated text."
    assert not (base / f"prompapa-{pid}.result").exists()
    assert (base / f"prompapa-{pid}.done").read_text() == NONCE
    assert not (base / f"prompapa-{pid}.request").exists()


def test_inject_mode_no_result_file(ipc_env, monkeypatch, tmp_path):
    base, pid = ipc_env
    (base / f"prompapa-{pid}.request").write_text(f"inject:{NONCE}")

    f = tmp_path / "input.txt"
    f.write_text("원본 텍스트", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", str(f)])

    main()

    assert f.read_text() == "원본 텍스트"
    assert (base / f"prompapa-{pid}.done").read_text() == NONCE


def test_no_request_passes_through(ipc_env, monkeypatch):
    _base, _pid = ipc_env
    monkeypatch.setenv("TUI_TRANSLATOR_REAL_EDITOR", "/usr/bin/vi")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", "/tmp/test.txt"])
    mock_exec = patch("os.execvp").start()

    main()

    mock_exec.assert_called_once_with("/usr/bin/vi", ["/usr/bin/vi", "/tmp/test.txt"])
    patch.stopall()


def test_passthrough_splits_editor_with_args(ipc_env, monkeypatch):
    _base, _pid = ipc_env
    monkeypatch.setenv("TUI_TRANSLATOR_REAL_EDITOR", "code --wait")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", "/tmp/test.txt"])
    mock_exec = patch("os.execvp").start()

    main()

    mock_exec.assert_called_once_with("code", ["code", "--wait", "/tmp/test.txt"])
    patch.stopall()


def test_inject_mode_atomic_write(ipc_env, monkeypatch, tmp_path):
    base, pid = ipc_env
    (base / f"prompapa-{pid}.request").write_text(f"inject:{NONCE}")
    (base / f"prompapa-{pid}.result").write_text(
        "Atomically written.", encoding="utf-8"
    )

    f = tmp_path / "input.txt"
    f.write_text("original", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", str(f)])

    main()

    assert f.read_text() == "Atomically written."
    assert not list(tmp_path.glob("*.tui-tmp"))
    assert (base / f"prompapa-{pid}.done").read_text() == NONCE


def test_atomic_claim_prevents_double_processing(ipc_env, monkeypatch, tmp_path):
    base, pid = ipc_env
    (base / f"prompapa-{pid}.request").write_text(f"capture:{NONCE}")

    f = tmp_path / "input.txt"
    f.write_text("테스트", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", str(f)])

    main()

    assert (base / f"prompapa-{pid}.done").read_text() == NONCE
    assert not (base / f"prompapa-{pid}.request").exists()
    assert not (base / f"prompapa-{pid}.claimed").exists()

    monkeypatch.setenv("TUI_TRANSLATOR_REAL_EDITOR", "echo")
    with patch("os.execvp") as mock_exec:
        main()

    mock_exec.assert_called_once()


def test_passthrough_empty_editor_falls_back_to_vi(ipc_env, monkeypatch):
    _base, _pid = ipc_env
    monkeypatch.setenv("TUI_TRANSLATOR_REAL_EDITOR", "")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", "/tmp/test.txt"])

    with patch("os.execvp") as mock_exec:
        main()

    mock_exec.assert_called_once_with("vi", ["vi", "/tmp/test.txt"])


def test_passthrough_malformed_editor_falls_back_to_vi(ipc_env, monkeypatch):
    _base, _pid = ipc_env
    monkeypatch.setenv("TUI_TRANSLATOR_REAL_EDITOR", "editor 'unmatched")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", "/tmp/test.txt"])

    with patch("os.execvp") as mock_exec:
        main()

    mock_exec.assert_called_once_with("vi", ["vi", "/tmp/test.txt"])


def test_passthrough_unset_editor_falls_back_to_vi(ipc_env, monkeypatch):
    _base, _pid = ipc_env
    monkeypatch.delenv("TUI_TRANSLATOR_REAL_EDITOR", raising=False)
    monkeypatch.setattr("sys.argv", ["prompapa-edit", "/tmp/test.txt"])

    with patch("os.execvp") as mock_exec:
        main()

    mock_exec.assert_called_once_with("vi", ["vi", "/tmp/test.txt"])


def test_malformed_request_content_passes_through(ipc_env, monkeypatch):
    """When .request content has no colon, wrapper claims it but falls through to passthrough."""
    base, pid = ipc_env
    (base / f"prompapa-{pid}.request").write_text("garbage-no-colon")
    monkeypatch.setenv("TUI_TRANSLATOR_REAL_EDITOR", "/usr/bin/vi")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", "/tmp/test.txt"])

    with patch("os.execvp") as mock_exec:
        main()

    mock_exec.assert_called_once_with("/usr/bin/vi", ["/usr/bin/vi", "/tmp/test.txt"])
    assert not (base / f"prompapa-{pid}.request").exists()
    assert not (base / f"prompapa-{pid}.claimed").exists()
    assert not (base / f"prompapa-{pid}.done").exists()


def test_unknown_mode_passes_through(ipc_env, monkeypatch):
    """When .request has a colon but unknown mode, wrapper passes through."""
    base, pid = ipc_env
    (base / f"prompapa-{pid}.request").write_text(f"unknown:{NONCE}")
    monkeypatch.setenv("TUI_TRANSLATOR_REAL_EDITOR", "/usr/bin/vi")
    monkeypatch.setattr("sys.argv", ["prompapa-edit", "/tmp/test.txt"])

    with patch("os.execvp") as mock_exec:
        main()

    mock_exec.assert_called_once_with("/usr/bin/vi", ["/usr/bin/vi", "/tmp/test.txt"])
    assert not (base / f"prompapa-{pid}.done").exists()
