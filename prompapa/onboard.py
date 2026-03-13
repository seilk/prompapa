import sys
import getpass
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


def run_onboard() -> None:
    print("prompapa setup\n")
    print("  Translation : Google Cloud Translation API")
    print("  Target CLI  : claude\n")

    print(_GCP_HELP)

    api_key = getpass.getpass("Google Cloud Translation API key: ").strip()

    if not api_key:
        print("\nAPI key cannot be empty. Onboarding cancelled.")
        sys.exit(1)

    config_dir = Path.home() / ".config" / "prompapa"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.toml"

    toml_content = textwrap.dedent(f"""\
        provider = "google"
        api_key = "{api_key}"
        target_cmd = ["claude"]
        hotkey_translate = "c-t"
        hotkey_undo = "c-z"
        preserve_backticks = true
    """)

    config_path.write_text(toml_content, encoding="utf-8")
    print(f"\nConfiguration saved to {config_path}")
    print("Run `papa claude` to get started.")
