# Decisions — Go Port

## D1: Skip buffer.py and state.py
Python runtime doesn't use them. Port only what's actually called.

## D2: Skip editor.py
Separate binary for editor IPC. Not part of core translate flow. Can add later.

## D3: Package structure
```
cmd/tui-translator/main.go     — entry point
internal/config/config.go       — AppConfig, load, defaults
internal/prompts/prompts.go     — SYSTEM_PROMPT, BuildUserMessage
internal/masking/masking.go     — mask/unmask backtick spans
internal/screen/screen.go       — ScreenTracker with vt10x
internal/translator/translator.go — HTTP translation clients
internal/adapters/adapter.go    — TargetAdapter interface
internal/adapters/claude.go     — ClaudeAdapter
internal/adapters/opencode.go   — OpenCodeAdapter
internal/app/app.go             — PTY proxy loop, translate/undo flow, display_width
```

## D4: Go module path
`github.com/seil/_projects/tui-translator` or just `tui-translator` — use simple module path.

## D5: Synchronous HTTP in Go
Python uses async httpx. Go's net/http is synchronous but runs in a goroutine anyway.
No need for async HTTP client — just call http.Post in the translate goroutine.
