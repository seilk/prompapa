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

### Translation quality post-processing
Google Translate is fast but loses "AI coding assistant" context.
Option: lightweight post-processing rules for common patterns
(e.g. ensure imperative mood, preserve file paths/commands).
