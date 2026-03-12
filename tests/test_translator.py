import pytest, httpx
from unittest.mock import AsyncMock, MagicMock, patch
from tui_translator.translator import rewrite_to_english, TranslationError
from tui_translator.config import AppConfig

def _cfg(**kw) -> AppConfig:
    defaults = {"provider": "openai", "model": "gpt-4.1-mini", "api_key_env": "OPENAI_API_KEY"}
    defaults.update(kw)
    return AppConfig(**defaults)

def _mock_resp(content: str) -> MagicMock:
    m = MagicMock(spec=httpx.Response)
    m.raise_for_status = MagicMock()
    m.json.return_value = {"choices": [{"message": {"content": content}}]}
    return m

def _patch_client(mock_post):
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = mock_post
    return mock_client

async def test_korean_text_returns_english(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    expected = "Fix this bug."
    with patch("httpx.AsyncClient", return_value=_patch_client(
        AsyncMock(return_value=_mock_resp(expected)))):
        result = await rewrite_to_english("이 함수 버그 고쳐줘", _cfg())
    assert result == expected

async def test_api_error_raises_translation_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    with patch("httpx.AsyncClient", return_value=_patch_client(
        AsyncMock(side_effect=httpx.HTTPStatusError(
            "401", request=MagicMock(), response=MagicMock(status_code=401))))):
        with pytest.raises(TranslationError, match="401"):
            await rewrite_to_english("테스트", _cfg())

async def test_network_timeout_raises_translation_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    with patch("httpx.AsyncClient", return_value=_patch_client(
        AsyncMock(side_effect=httpx.TimeoutException("timed out")))):
        with pytest.raises(TranslationError, match="timed out"):
            await rewrite_to_english("테스트", _cfg())

async def test_strips_whitespace_from_response(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    with patch("httpx.AsyncClient", return_value=_patch_client(
        AsyncMock(return_value=_mock_resp("  Fix this bug.  \n")))):
        result = await rewrite_to_english("버그 고쳐줘", _cfg())
    assert result == "Fix this bug."

async def test_anthropic_provider_uses_correct_endpoint(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    cfg = _cfg(provider="anthropic", api_key_env="ANTHROPIC_API_KEY")
    mock_post = AsyncMock(return_value=_mock_resp("Fix the bug."))
    with patch("httpx.AsyncClient", return_value=_patch_client(mock_post)):
        result = await rewrite_to_english("버그 고쳐줘", cfg)
    url_called = mock_post.call_args[0][0]
    assert "anthropic" in url_called
    assert result == "Fix the bug."
