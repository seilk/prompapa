# Go Port Plan — tui-translator

Port the Python tui-translator to Go as a single static binary.
Working directory: `.gitworktrees/go-port/`

## Phase 0: Infrastructure
- [x] T0: Create git worktree and initialize Go module

## Phase 1: Leaf Packages (no internal dependencies — PARALLEL)
- [x] T1a: Implement `internal/config` — TOML config loading, AppConfig struct, ConfigError
- [x] T1b: Implement `internal/prompts` — SYSTEM_PROMPT constant, BuildUserMessage function (fixed backslash issue)
- [x] T1c: Implement `internal/masking` — backtick mask/unmask with regex
- [x] T1d: Implement `internal/screen` — VT100 ScreenTracker using vt10x, capture_near_cursor

## Phase 2: Depends on Phase 1 (PARALLEL after Phase 1)
- [x] T2a: Implement `internal/translator` — HTTP translation clients (Google, OpenAI, Anthropic)
- [x] T2b: Implement `internal/adapters` — TargetAdapter interface, ClaudeAdapter, OpenCodeAdapter

## Phase 3: Main app (depends on all above)
- [x] T3: Implement `cmd/tui-translator/main.go` — PTY proxy loop, hotkey interception, translate/undo flow

## Phase 4: Tests (PARALLEL)
- [x] T4a: Tests for `internal/config`
- [x] T4b: Tests for `internal/prompts`
- [x] T4c: Tests for `internal/masking`
- [x] T4d: Tests for `internal/screen`
- [x] T4e: Tests for `internal/translator`
- [x] T4f: Tests for `internal/adapters`
- [x] T4g: Tests for display_width and translate_text helpers in app package

## Phase 5: Build and Integration
- [x] T5: Build verification — `go build`, `go vet`, `go test ./...` all pass (63 tests, 9.7MB binary)

## Final Verification Wave
- [x] F1: Code review — all Go code follows conventions, matches Python behavior
- [x] F2: Test parity — 63 Go tests covering all Python test scenarios (config 11, prompts 5, masking 8, screen 17, translator 9, adapters 5, app 8)
- [x] F3: Build verification — 9.3MB static binary, go build + go vet + go test all pass
- [x] F4: Architecture review — clean package structure, proper interfaces, idiomatic error handling
