from __future__ import annotations

import asyncio
import os
from typing import Protocol

from prompapa.screen import ScreenTracker


class TargetAdapter(Protocol):
    async def clear_input(self, master_fd: int, n: int) -> None: ...
    def capture_text(self, screen: ScreenTracker) -> str: ...
    def inject_text(self, master_fd: int, text: str) -> None: ...


_ADAPTERS: dict[str, type[TargetAdapter]] = {}


def _register() -> None:
    from prompapa.adapters.claude import ClaudeAdapter
    from prompapa.adapters.opencode import OpenCodeAdapter

    _ADAPTERS["claude"] = ClaudeAdapter
    _ADAPTERS["opencode"] = OpenCodeAdapter


def get_adapter(target: str) -> TargetAdapter:
    if not _ADAPTERS:
        _register()
    cls = _ADAPTERS.get(target)
    if cls is None:
        supported = ", ".join(sorted(_ADAPTERS))
        raise ValueError(f"Unknown target '{target}'. Supported targets: {supported}")
    return cls()
