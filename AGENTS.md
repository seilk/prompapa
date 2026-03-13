# AGENTS.md — tui-translator Development Guidelines

## Commit Discipline

**After every feature implementation or bug fix, once verification passes, create a git commit immediately.**

- One logical change = one commit. Do not batch unrelated changes.
- Do NOT commit unrelated dirty files (e.g. scratch files, unrelated module edits).
- Commit message format: `type(scope): short description`
  - `feat(config): support direct api_key in config.toml`
  - `fix: strip leading/trailing whitespace from translation result`
- Commits serve as snapshots — they make rollback, bisect, and review safe and fast.
- If a task spans multiple files, verify all changed files are clean (`lsp_diagnostics`) before committing.

## Verification Before Commit

1. Run `uv run pytest -v` — all tests must pass.
2. Run `lsp_diagnostics` on changed files — no errors.
3. Only then commit.

## Project Context

- **Language**: Python (mainline). Go/Rust spikes exist as git worktrees but are NOT the active path.
- **Entry point**: `uv run tui-translator <cmd>` (e.g. `tui-translator claude`)
- **Config**: `~/.config/tui-translator/config.toml` — supports `api_key` directly or `api_key_env` as fallback.
- **Key files**:
  - `tui_translator/app.py` — PTY proxy, hotkey handling, translation flow
  - `tui_translator/config.py` — config loading and API key resolution
  - `tui_translator/translator.py` — LLM API calls
  - `tui_translator/buffer.py` — input buffer management
- **Tests**: `uv run pytest -v`
- **Zero-refresh UX is a hard requirement** — no terminal flicker or screen refresh during translation.
