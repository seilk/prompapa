from __future__ import annotations
import re
from dataclasses import dataclass, field

_BACKTICK_RE = re.compile(r"`[^`]+`")
_PLACEHOLDER_FMT = "__MASK_{i}__"

@dataclass
class MaskContext:
    masked: str
    tokens: list[str] = field(default_factory=list)

def mask_tokens(text: str, enabled: bool = True) -> MaskContext:
    if not enabled:
        return MaskContext(masked=text, tokens=[])
    tokens: list[str] = []
    def replacer(m: re.Match) -> str:
        idx = len(tokens)
        tokens.append(m.group(0))
        return _PLACEHOLDER_FMT.format(i=idx)
    result = _BACKTICK_RE.sub(replacer, text)
    return MaskContext(masked=result, tokens=tokens)

def unmask_tokens(text: str, tokens: list[str]) -> str:
    result = text
    for i, token in enumerate(tokens):
        result = result.replace(_PLACEHOLDER_FMT.format(i=i), token)
    return result
