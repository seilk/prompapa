import sys
import shutil
import subprocess
from pathlib import Path


def run_uninstall() -> None:
    print("This will remove the prompapa package.")
    print("Your config at ~/.config/prompapa/ will NOT be touched.\n")

    answer = input("Continue? [y/N] ").strip().lower()
    if answer != "y":
        print("Uninstall cancelled.")
        sys.exit(0)

    result = subprocess.run(
        ["uv", "tool", "uninstall", "prompapa"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("prompapa uninstalled.")
        print("Config kept at ~/.config/prompapa/ — remove manually if needed.")
    else:
        print(f"Uninstall failed:\n{result.stderr.strip()}")
        sys.exit(1)
