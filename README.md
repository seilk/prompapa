<p align="center">
  <img src="assets/prompapa-banner.png" alt="prompapa" width="600" />
</p>

<p align="center">
  <em>Type in any language. Hit Ctrl+T. Watch it become perfect English.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/install-uv-blueviolet" alt="uv" />
  <img src="https://img.shields.io/badge/translation-Google_Cloud-green" alt="Google Cloud Translation" />
</p>

# prompapa

## Install

Requires [uv](https://docs.astral.sh/uv/). Install it once, then:

```bash
uv tool install git+https://github.com/your-org/prompapa
```

## Setup

Run the onboarding wizard to configure your API key:

```bash
papa onboard
```

This sets up `~/.config/prompapa/config.toml` with your Google Cloud Translation API key.

Don't have a key yet? The wizard walks you through getting one.

## Usage

```bash
papa claude
```

Your tool opens exactly as normal. Two new hotkeys:

| Hotkey | Action |
|--------|--------|
| `Ctrl+T` | Translate current input to English |
| `Ctrl+Y` | Undo — restore original text |

## Configuration

`~/.config/prompapa/config.toml`:

```toml
provider = "google"
api_key = "your-gcp-translation-api-key"
target_cmd = ["claude"]
preserve_backticks = true
```

`api_key_env` is also supported if you prefer to keep the key in an environment variable:

```toml
provider = "google"
api_key_env = "GOOGLE_API_KEY"
target_cmd = ["claude"]
```

### preserve_backticks

Keeps backtick-wrapped tokens untranslated:

```toml
preserve_backticks = true
```

`` `src/auth.ts` `` stays exactly as-is after translation.

## How it works

prompapa forks your target CLI into a **PTY (pseudo-terminal)**, sitting transparently between your keyboard and the process. Every keystroke passes through unchanged — until you hit `Ctrl+T`.

At that point:

1. Reads current input off the terminal screen via a `pyte` screen tracker
2. Fires an async call to Google Cloud Translation API
3. Erases the original text with precisely-counted backspaces (no screen refresh)
4. Injects the English result via bracketed paste

The child process never pauses. The UI never redraws. The text just... changes.

## Development

```bash
git clone https://github.com/your-org/prompapa
cd prompapa
uv sync
uv run pytest -v
```

Run locally without installing:

```bash
uv run papa claude
```

## TODO

- `opencode` support
- LLM API translation support
