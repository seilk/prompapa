from __future__ import annotations
from collections import deque

class UndoStack:
    def __init__(self, max_depth: int = 20) -> None:
        self._stack: deque[str] = deque(maxlen=max_depth)

    def push(self, text: str) -> None:
        self._stack.append(text)

    def pop(self) -> str | None:
        return self._stack.pop() if self._stack else None

    def can_undo(self) -> bool:
        return bool(self._stack)

    def clear(self) -> None:
        self._stack.clear()
