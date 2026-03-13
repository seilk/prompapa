import subprocess
import sys
from unittest.mock import patch, MagicMock

import pytest

from prompapa.update import run_update


def _make_result(returncode: int, stderr: str = "") -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stderr = stderr
    return result


def test_update_success(capsys):
    with patch("subprocess.run", return_value=_make_result(0)) as mock_run:
        run_update()

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "uv"
    assert "--force" in args
    assert any("github.com/seilk/prompapa" in a for a in args)

    captured = capsys.readouterr()
    assert "updated" in captured.out.lower()


def test_update_failure_exits(capsys):
    with patch("subprocess.run", return_value=_make_result(1, "some error")):
        with pytest.raises(SystemExit) as exc_info:
            run_update()
    assert exc_info.value.code == 1
