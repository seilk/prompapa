from __future__ import annotations
import httpx
from tui_translator.config import AppConfig
from tui_translator.prompts import SYSTEM_PROMPT, build_user_message

_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_TIMEOUT = 30.0

class TranslationError(Exception):
    pass

async def rewrite_to_english(text: str, config: AppConfig) -> str:
    api_key = config.resolve_api_key()

    if config.provider == "anthropic":
        url = _ANTHROPIC_URL
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01",
                   "Content-Type": "application/json"}
        payload = {"model": config.model, "system": SYSTEM_PROMPT,
                   "messages": [{"role": "user", "content": build_user_message(text)}],
                   "max_tokens": 1024}
    else:
        url = _OPENAI_URL
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": config.model,
                   "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                                 {"role": "user", "content": build_user_message(text)}],
                   "temperature": 0.3, "max_tokens": 1024}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=_TIMEOUT)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        raise TranslationError(f"API returned {e.response.status_code}: {e}") from e
    except httpx.TimeoutException as e:
        raise TranslationError(f"Request timed out: {e}") from e
    except httpx.RequestError as e:
        raise TranslationError(f"Network error: {e}") from e
    except (KeyError, IndexError) as e:
        raise TranslationError(f"Unexpected response format: {e}") from e
