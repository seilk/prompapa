# 🐼 prompapa

## 🚀 Install

Requires [uv](https://docs.astral.sh/uv/). Install it once, then:

```bash
uv tool install git+https://github.com/your-org/prompapa
```

That's it. The `papa` command is now globally available.

## 🎮 Usage

Instead of running `claude` directly, run it through `papa`:

```bash
papa claude
```

Your tool opens exactly as normal. Same UI, same features, same everything. Now you just have two new hotkeys.

| Hotkey | Action |
|--------|--------|
| `Ctrl+T` | Translate your current input to English |
| `Ctrl+Y` | Undo — restore original text immediately |

That's the entire interface. Two keys.

## ⚙️ Configuration

Create `~/.config/prompapa/config.toml`:

```toml
provider = "openai"
model = "gpt-4.1-mini"
api_key_env = "OPENAI_API_KEY"
target_cmd = ["claude"]
```

### Supported providers

**OpenAI**
```toml
provider = "openai"
model = "gpt-4.1-mini"
api_key_env = "OPENAI_API_KEY"
```

**Anthropic**
```toml
provider = "anthropic"
model = "claude-3-haiku-20240307"
api_key_env = "ANTHROPIC_API_KEY"
```

**Google**
```toml
provider = "google"
model = "gemini-2.0-flash"
api_key_env = "GOOGLE_API_KEY"
```

Prefer to hardcode the key? Use `api_key = "sk-..."` instead of `api_key_env`. Your call.

### Preserve backtick tokens

Got code paths or variables mixed into your prompt? This keeps them untouched:

```toml
preserve_backticks = true
```

`` `src/auth.ts` `` stays exactly as-is after translation.

## 🔧 How it works

prompapa forks your target CLI into a **PTY (pseudo-terminal)**, then sits between your keyboard and that process. Every keystroke flows through transparently — until you hit `Ctrl+T`.

At that point:

1. It reads your current input directly off the terminal screen using a `pyte` screen tracker
2. Fires an async API call to your LLM of choice
3. Erases the old text with precisely-counted backspaces (no screen refresh)
4. Injects the English result via bracketed paste

The child process never pauses. The UI never redraws. You never see a flash. The text just... changes.

## 📦 Full config reference

```toml
# Provider: "openai" | "anthropic" | "google"
provider = "openai"

# Model for translation (pick something fast — this runs on every Ctrl+T)
model = "gpt-4.1-mini"

# API key — one of these two:
api_key = "sk-..."           # hardcoded
api_key_env = "OPENAI_API_KEY"  # from environment (recommended)

# The CLI tool to wrap
target_cmd = ["claude"]

# Keep backtick-wrapped tokens untranslated
preserve_backticks = true
```

## 🧪 Development

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

## 📝 TODO

- `opencode` support
- Full LLM API translation proxy support (LLM API를 통한 번역 지원)
