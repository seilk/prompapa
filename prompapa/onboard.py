import sys
import getpass
import httpx
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

_GOOGLE_URL = "https://translation.googleapis.com/language/translate/v2"
_TEST_TEXT = "안녕하세요, 잘 지내셨나요?"


def _test_api_key(api_key: str) -> str:
    response = httpx.post(
        _GOOGLE_URL,
        params={"key": api_key},
        json={"q": _TEST_TEXT, "target": "en", "format": "text"},
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()["data"]["translations"][0]["translatedText"]


def run_onboard() -> None:
    print("prompapa setup\n")
    print("  Translation : Google Cloud Translation API")
    print("  Target CLI  : claude\n")

    print(_GCP_HELP)

    api_key = getpass.getpass("Google Cloud Translation API key: ").strip()

    if not api_key:
        print("\nAPI key cannot be empty. Onboarding cancelled.")
        sys.exit(1)

    print("\nTesting API key...", end=" ", flush=True)
    try:
        result = _test_api_key(api_key)
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

    config_dir = Path.home() / ".config" / "prompapa"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.toml"

    toml_content = textwrap.dedent(f"""\
        provider = "google"
        api_key = "{api_key}"
        target_cmd = ["claude"]
        preserve_backticks = true
    """)

    config_path.write_text(toml_content, encoding="utf-8")
    print(f"\nConfiguration saved to {config_path}")
    print("Run `papa claude` to get started.")
