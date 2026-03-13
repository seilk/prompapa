# Changelog

All notable changes to this project will be documented in this file.

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
