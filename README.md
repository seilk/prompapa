# tui-translator

A terminal TUI for rewriting Korean/mixed-language prompts into English,
optimized for AI coding assistants.

## What it does

Type Korean or mixed Korean/English instructions, press **Ctrl+T**, and the
buffer is replaced in-place with a clean English rewrite. Review, edit if
needed, then press **Ctrl+C** to exit and print the result to stdout.

## Install

    # From source with uv:
    git clone <repo>
    cd tui-translator
    uv sync
    uv run tui-translator

    # Or install as tool:
    uv tool install git+<repo>

## Config

Create `~/.config/tui-translator/config.toml`:

```toml
provider = "openai"
model = "gpt-4.1-mini"
api_key_env = "OPENAI_API_KEY"
hotkey_translate = "c-t"
hotkey_undo = "c-z"
preserve_backticks = true
```

## Environment variable

    export OPENAI_API_KEY=sk-...

For Anthropic:

```toml
provider = "anthropic"
model = "claude-3-haiku-20240307"
api_key_env = "ANTHROPIC_API_KEY"
```

    export ANTHROPIC_API_KEY=sk-ant-...

## Hotkeys

| Key    | Action                      |
|--------|-----------------------------|
| Ctrl+T | Translate buffer to English |
| Ctrl+Z | Undo last translation       |
| Ctrl+C | Quit and print to stdout    |

## Usage example

1. Run `tui-translator`
2. Type: `이 버그 원인 찾아서 고쳐줘. src/auth.ts 건드리지마.`
3. Press `Ctrl+T`
4. Buffer becomes: `Find the root cause of this bug and fix it. Do not touch src/auth.ts.`
5. Press `Ctrl+C` — English text printed to stdout

## Running tests

    uv run pytest -v

## Future extensions (not implemented)

- Selection-only translation
- Diff preview before replace
- Clipboard integration
- tmux pane wrapping
- Per-project glossary presets
- Session history
