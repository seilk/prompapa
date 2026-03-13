import subprocess
import sys


INSTALL_URL = "git+https://github.com/seilk/prompapa"


def run_update() -> None:
    print("Updating prompapa from GitHub...")
    result = subprocess.run(
        ["uv", "tool", "install", "--force", INSTALL_URL],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("prompapa updated successfully.")
    else:
        print(f"Update failed:\n{result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
