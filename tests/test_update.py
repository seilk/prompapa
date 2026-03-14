import subprocess
import sys
from unittest.mock import patch, MagicMock

import pytest

from prompapa.update import run_update, _latest_tag, _current_version


def _make_proc(returncode: int, stderr: str = "") -> MagicMock:
    m = MagicMock()
    m.returncode = returncode
    m.stderr = stderr
    return m


def _make_http(tags: list[str]) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = [{"name": t} for t in tags]
    resp.raise_for_status = MagicMock()
    return resp


class TestLatestTag:
    def test_picks_latest_semver(self):
        with patch(
            "httpx.get", return_value=_make_http(["v0.1.0", "v1.0.0", "v0.9.0"])
        ):
            assert _latest_tag() == "v1.0.0"

    def test_ignores_non_v_tags(self):
        with patch(
            "httpx.get", return_value=_make_http(["release-1", "v0.2.0", "nightly"])
        ):
            assert _latest_tag() == "v0.2.0"

    def test_no_tags_raises(self):
        with patch("httpx.get", return_value=_make_http([])):
            with pytest.raises(RuntimeError, match="No release tags"):
                _latest_tag()

    def test_http_error_propagates(self):
        resp = MagicMock()
        resp.raise_for_status.side_effect = Exception("HTTP 403")
        with patch("httpx.get", return_value=resp):
            with pytest.raises(Exception, match="HTTP 403"):
                _latest_tag()


class TestRunUpdate:
    def test_already_up_to_date(self, capsys):
        with patch("prompapa.update._current_version", return_value="1.0.0"):
            with patch("prompapa.update._latest_tag", return_value="v1.0.0"):
                run_update()
        assert "up to date" in capsys.readouterr().out.lower()

    def test_updates_to_latest_tag(self, capsys):
        with patch("prompapa.update._current_version", return_value="0.1.0"):
            with patch("prompapa.update._latest_tag", return_value="v1.0.0"):
                with patch("subprocess.run", return_value=_make_proc(0)) as mock_run:
                    run_update()

        args = mock_run.call_args[0][0]
        assert "uv" in args
        assert "--force" in args
        assert any("@v1.0.0" in a for a in args)
        assert "updated" in capsys.readouterr().out.lower()

    def test_install_failure_exits(self):
        with patch("prompapa.update._current_version", return_value="0.1.0"):
            with patch("prompapa.update._latest_tag", return_value="v1.0.0"):
                with patch("subprocess.run", return_value=_make_proc(1, "error")):
                    with pytest.raises(SystemExit) as exc_info:
                        run_update()
        assert exc_info.value.code == 1

    def test_fetch_failure_exits(self):
        with patch(
            "prompapa.update._latest_tag", side_effect=Exception("network error")
        ):
            with pytest.raises(SystemExit) as exc_info:
                run_update()
        assert exc_info.value.code == 1
