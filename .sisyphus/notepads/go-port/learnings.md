# Learnings — Go Port

## Go Library Selections (confirmed)
- PTY: `github.com/creack/pty` — Start/StartWithSize, InheritSize, Setsize
- VT100 screen: `github.com/hinshun/vt10x` — New(WithSize), Write, Size, cursor tracking
- Terminal raw mode: `golang.org/x/term` — MakeRaw/Restore
- TOML: `github.com/BurntSushi/toml` — standard Go TOML
- Unicode width: `github.com/mattn/go-runewidth` — RuneWidth for CJK
- HTTP: stdlib `net/http` — no third-party needed

## Python Architecture Notes
- Runtime does NOT use buffer.py or state.py — skip these in Go port
- Undo is a single `pre_translation` slot, not the UndoStack
- Hotkeys are hardcoded: Ctrl+T (0x14) = translate, Ctrl+Y (0x19) = undo
- Config hotkey fields are parsed but NOT used at runtime
- `build_user_message()` is identity function — just returns input text
- `editor.py` is a separate binary — skip for initial Go port

## Screen Capture Algorithm
1. Scan upward from cursor for line starting with `❯` (after stripping box chars)
2. If found: return stripped prompt content + following non-empty lines
3. If not found: collect contiguous non-empty lines near cursor (fallback)
4. `_strip_decorations()` removes box-drawing chars from _BOX_CHARS set
5. `_strip_prompt()` strips `❯ ` or `❯` prefix

## Clear/Inject Mechanism
- clear_input: right-arrow × n (2ms delay each) + backspace × n + 50ms sleep
- inject_text: bracketed paste \x1b[200~ + text + \x1b[201~
- n = _display_width(captured) + 20 slack chars

## Go Concurrency Pattern (replaces Python asyncio)
- Two goroutines: stdin→child (with hotkey interception), child→stdout (with screen.feed)
- Translation triggered via goroutine, guarded by mutex/atomic flag
- SIGWINCH handler via signal.Notify channel

## translator package (2026-03-13)
- Used inline struct types for JSON request/response shapes — keeps them local to each function, avoids polluting package namespace
- `isTimeout` helper checks error string for "timeout"/"deadline exceeded" — Go's net/http wraps url.Error which contains these strings
- Google URL query param `key=` appended directly to URL string (simpler than url.Values for single param)
- Kept `llmTimeout` as separate const (30s) vs `timeout` (10s for Google) — matches Python's effective behavior
- Exported: `TranslationError`, `RewriteToEnglish`. Unexported: all helpers.

## adapters package (2026-03-13)
- `syscall.Write(fd, bytes)` is the Go equivalent of Python's `os.write(fd, bytes)` for raw fd writes
- `bytes.Repeat([]byte{0x7f}, n)` for bulk backspace bytes
- Interface methods return `error` (Go style) vs Python's bare writes with no return
- `append([]byte("\x1b[200~"), append([]byte(text), []byte("\x1b[201~")...)...)` for bracketed paste payload
- Stateless adapters: zero-value structs, no constructor needed
- `GetAdapter` uses a switch statement (cleaner than a map for small fixed sets)
