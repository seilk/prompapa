import sys
import getpass
from pathlib import Path
import textwrap

def run_onboard() -> None:
    print("🐼 Welcome to prompapa onboarding!\n")
    print("Target CLI  : claude (opencode support coming soon!)")
    print("Translation : Claude (Anthropic)\n")
    
    api_key = getpass.getpass("Enter your Anthropic API Key (sk-ant-...): ").strip()
    
    if not api_key:
        print("\n❌ API Key cannot be empty. Onboarding cancelled.")
        sys.exit(1)
        
    config_dir = Path.home() / ".config" / "prompapa"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.toml"
    
    toml_content = textwrap.dedent(f"""\
        provider = "anthropic"
        model = "claude-3-haiku-20240307"
        api_key = "{api_key}"
        target_cmd = ["claude"]
        hotkey_translate = "c-t"
        hotkey_undo = "c-z"
        preserve_backticks = true
    """)
    
    config_path.write_text(toml_content, encoding="utf-8")
    print(f"\n✅ Configuration successfully saved to {config_path}")
    print("🎉 You're all set! Run `papa claude` to begin.")
