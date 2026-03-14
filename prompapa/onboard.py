import sys
import getpass
import httpx
import questionary
from pathlib import Path
import textwrap

_GCP_HELP = """
How to get a Google Cloud Translation API key:
  1. Go to https://console.cloud.google.com/
  2. Create a project (or select an existing one)
  3. Enable "Cloud Translation API" from the API library
  4. Go to "APIs & Services" > "Credentials" > "Create Credentials" > "API key"
  5. Copy the generated key and paste it below
"""

_OPENAI_HELP = """
How to get an OpenAI API key:
  1. Go to https://platform.openai.com/api-keys
  2. Click "Create new secret key" and copy it

Recommended models: gpt-4.1-mini (fast, cheap), gpt-4o (best quality)
"""

_ANTHROPIC_HELP = """
How to get an Anthropic API key:
  1. Go to https://console.anthropic.com/settings/keys
  2. Click "Create Key" and copy it

Recommended models: claude-haiku-4-5 (fast, cheap), claude-sonnet-4-5 (best quality)
"""

_GOOGLE_URL = "https://translation.googleapis.com/language/translate/v2"
_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_TEST_TEXT = "Hello, how are you doing today?"


def _test_google(api_key: str) -> str:
    response = httpx.post(
        _GOOGLE_URL,
        params={"key": api_key},
        json={"q": _TEST_TEXT, "target": "fr", "format": "text"},
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()["data"]["translations"][0]["translatedText"]


def _test_openai(api_key: str, model: str) -> str:
    response = httpx.post(
        _OPENAI_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Reply with just: ok"}],
            "max_tokens": 5,
        },
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _test_anthropic(api_key: str, model: str) -> str:
    response = httpx.post(
        _ANTHROPIC_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Reply with just: ok"}],
            "max_tokens": 5,
        },
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"].strip()


def _pick_provider() -> str:
    choice = questionary.select(
        "Select translation provider:",
        choices=[
            questionary.Choice(
                "Google Cloud Translation  (fast, free tier 500k chars/month)",
                value="google",
            ),
            questionary.Choice(
                "OpenAI                    (LLM quality) — To be added!",
                value="openai",
                disabled="To be added!",
            ),
            questionary.Choice(
                "Anthropic                 (LLM quality) — To be added!",
                value="anthropic",
                disabled="To be added!",
            ),
        ],
    ).ask()
    if choice is None:
        sys.exit(0)
    return choice


def _pick_model(provider: str) -> str:
    defaults = {
        "openai": "gpt-4.1-mini",
        "anthropic": "claude-haiku-4-5",
    }
    default = defaults[provider]
    value = input(f"Model [{default}]: ").strip()
    return value if value else default


def run_onboard() -> None:
    print("prompapa setup\n")

    provider = _pick_provider()
    print()

    if provider == "google":
        print(_GCP_HELP)
        api_key = getpass.getpass("Google Cloud Translation API key: ").strip()
        if not api_key:
            print("\nAPI key cannot be empty. Onboarding cancelled.")
            sys.exit(1)

        print("\nTesting API key...", end=" ", flush=True)
        try:
            result = _test_google(api_key)
            print("ok")
            print(f"\n  Input  : {_TEST_TEXT}")
            print(f"  Output : {result}")
        except httpx.HTTPStatusError as e:
            print("failed")
            print(
                f"\nAPI call failed ({e.response.status_code}). Check your key and try again."
            )
            sys.exit(1)
        except Exception as e:
            print("failed")
            print(f"\nUnexpected error: {e}")
            sys.exit(1)

        toml_content = textwrap.dedent(f"""\
            provider = "google"
            api_key = "{api_key}"
            target_cmd = ["claude"]
            preserve_backticks = true
        """)

    else:
        help_text = _OPENAI_HELP if provider == "openai" else _ANTHROPIC_HELP
        print(help_text)

        api_key = getpass.getpass(f"{provider.capitalize()} API key: ").strip()
        if not api_key:
            print("\nAPI key cannot be empty. Onboarding cancelled.")
            sys.exit(1)

        model = _pick_model(provider)

        print("\nTesting API key...", end=" ", flush=True)
        try:
            if provider == "openai":
                _test_openai(api_key, model)
            else:
                _test_anthropic(api_key, model)
            print("ok")
        except httpx.HTTPStatusError as e:
            print("failed")
            print(
                f"\nAPI call failed ({e.response.status_code}). Check your key and try again."
            )
            sys.exit(1)
        except Exception as e:
            print("failed")
            print(f"\nUnexpected error: {e}")
            sys.exit(1)

        toml_content = textwrap.dedent(f"""\
            provider = "{provider}"
            model = "{model}"
            api_key = "{api_key}"
            target_cmd = ["claude"]
            preserve_backticks = true
        """)

    config_dir = Path.home() / ".config" / "prompapa"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.toml"

    config_path.write_text(toml_content, encoding="utf-8")
    print(f"\nConfiguration saved to {config_path}")
    print("Run `papa claude` to get started.")
    print()
    print("Tip: you can also edit the config manually:")
    print(f"  {config_path}")
    print()
    print("Manual config example (OpenAI with env var):")
    print('  provider = "openai"')
    print('  model = "gpt-4.1-mini"')
    print('  api_key_env = "OPENAI_API_KEY"')
    print('  target_cmd = ["claude"]')
