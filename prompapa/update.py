from __future__ import annotations

import subprocess
import sys
from importlib.metadata import version as pkg_version, PackageNotFoundError

import httpx


REPO = "seilk/prompapa"
TAGS_API = f"https://api.github.com/repos/{REPO}/tags"
INSTALL_BASE = f"git+https://github.com/{REPO}"


def _current_version() -> str:
    try:
        return pkg_version("prompapa")
    except PackageNotFoundError:
        return "0.0.0"


def _latest_tag() -> str:
    resp = httpx.get(
        TAGS_API, timeout=10, headers={"Accept": "application/vnd.github+json"}
    )
    resp.raise_for_status()
    tags = resp.json()
    release_tags = [t["name"] for t in tags if t["name"].startswith("v")]
    if not release_tags:
        raise RuntimeError("No release tags found on GitHub.")

    def _version_key(tag: str) -> tuple[int, ...]:
        return tuple(int(x) for x in tag.lstrip("v").split(".") if x.isdigit())

    return max(release_tags, key=_version_key)


def run_update() -> None:
    print("Checking for updates...")

    try:
        latest = _latest_tag()
    except Exception as e:
        print(f"Failed to fetch latest version: {e}", file=sys.stderr)
        sys.exit(1)

    current = _current_version()
    print(f"Current: v{current}  Latest: {latest}")

    def _ver(s: str) -> tuple[int, ...]:
        return tuple(int(x) for x in s.lstrip("v").split(".") if x.isdigit())

    if _ver(current) >= _ver(latest):
        print("Already up to date.")
        return

    print(f"Updating to {latest}...")
    result = subprocess.run(
        ["uv", "tool", "install", "--force", f"{INSTALL_BASE}@{latest}"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        from prompapa.config import ensure_system_config

        ensure_system_config()
        print(f"Updated to {latest}.")
    else:
        print(f"Update failed:\n{result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
