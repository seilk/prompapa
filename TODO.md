# TODO

## Priority: Stability First

Core functionality must be solid before expanding scope.

---

## Backlog

### Multi-target CLI support (ccr, code, opencode variants)
Currently `target_cmd` in config already supports any CLI wrapper (e.g. `["ccr"]`, `["code"]`).
However, proper multi-target support requires:
- Verified smoke tests against each known target (claude, ccr, opencode)
- Target-specific quirks documented (e.g. different readline behavior, bracketed paste handling)
- README examples for each target

**Not starting until:** basic translation flow is stable and smoke-tested end-to-end.

### ShadowBuffer sync (history navigation, paste, mid-line cursor)
Current Ctrl+U/Y capture pattern works for readline apps but has edge cases:
- Cursor not at end of line when Ctrl+T pressed
- Multiline input (only current physical line captured)
- Apps that don't use readline kill-ring (unlikely given target set)

### English input detection → skip translation
If input is already English, skip the API call entirely.
Simple heuristic: if >80% of chars are ASCII printable, skip.

### Visual feedback improvement
Current "translating..." indicator overwrites the line then disappears.
Consider a less disruptive status (e.g. brief flash in terminal title).

### Go 포팅 (배포 단순화)
현재 Python + uv 조합은 개발/iterate에 최적이지만 최종 사용자 경험은 아님.
안정화 후 Go로 포팅하면:
- 단일 바이너리 배포 (`brew install`, `apt install`, `scoop install`)
- 런타임 의존성 없음 — 그냥 `tui-translator` 실행
- `pty`, `syscall` 패키지로 현재 Python 로직 1:1 포팅 가능
- 크로스 컴파일 쉬움 (macOS/Linux/Windows)

중간 단계: `uv tool install git+https://...` 로 배포하면 `tui-translator` 한 줄 실행 가능 (Python 사용자 대상).

**Not starting until:** 핵심 로직(캡처, 번역, undo) 완전히 안정화 후.

### Translation quality post-processing
Google Translate is fast but loses "AI coding assistant" context.
Option: lightweight post-processing rules for common patterns
(e.g. ensure imperative mood, preserve file paths/commands).
