# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-03-14

### Fixed
- `ClaudeAdapter.clear_input` — replaced `→×N + BS×N` timing hack with `Ctrl+A / Ctrl+K` per line (consistent with Codex/OpenCode, faster and version-stable)
- `SYSTEM_PROMPT` — removed Korean hardcoding; now accepts input in any language or mix of languages
- `papa onboard` — replaced silent bell on translation error with a red status line below the prompt

### Changed
- `papa onboard` — provider selection is now an arrow-key menu (`questionary`) with Google pre-selected; OpenAI, Anthropic, and Gemini shown as grayed-out "To be added!" entries
- Undo slot kept at depth 1 (intentional single-slot design); internal refactor to stack type for future extensibility

### Added
- Codex and OpenCode support (`papa codex`, `papa opencode`)
- `papa -t "text"` one-shot translate mode — prints translation to stdout without launching a TUI
- `papa update` — checks GitHub tags and installs the latest release
- LLM translation backends (OpenAI, Anthropic) — wired up but not yet exposed in onboarding

## [0.1.0] - 2026-03-14

### Added
- PTY proxy for Claude Code — zero-refresh inline translation with `Ctrl+T` / `Ctrl+Y` undo
- Google Cloud Translation API backend
- `papa onboard` — interactive wizard to configure and verify the API key
- `papa update` — reinstalls the latest version from GitHub via `uv`
- `papa uninstall` — removes the package while preserving config
- `preserve_backticks` option — keeps backtick-wrapped tokens untranslated
- `api_key` direct config support alongside `api_key_env`
- Multilingual README: Korean, Japanese, Chinese, French, Spanish, German, Russian

### Notes
- Initial public release
- Currently supports `claude` as the target CLI; `opencode` support is planned
- Translation target is English only; configurable destination language is planned
