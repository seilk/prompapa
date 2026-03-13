<p align="center">
  <img src="assets/prompapa-banner.png" alt="Prompapa" width="800" />
</p>

<p align="center">
  <em>Type in your language. Hit Ctrl+T in Claude Code. Watch it become perfect English.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/install-uv-blueviolet" alt="uv" />
  <img src="https://img.shields.io/badge/translation-Google_Cloud-green" alt="Google Cloud Translation" />
</p>

## Demo Video
To be announced

## Why This Exists

Language is not a neutral container for thought. The words we reach for first, the structure we impose before we even know what we mean, the instinct that precedes articulation: these are native. Forcing that process through a second language does not merely slow it down. It quietly reshapes it.

AI coding assistants carry an analogous constraint from the other direction. Research confirms what many have sensed: these models exhibit a structural English bias, where the same intent expressed in a non-English language yields measurably weaker responses [[1]](https://arxiv.org/abs/2504.11833). The bias runs deeper than surface vocabulary. Representational analyses of large reasoning models show that their internal reasoning pathways are English-centered by architecture, not just by training data. Regardless of the language a prompt arrives in, the model converges toward an English-shaped latent space before it begins to reason [[2]](https://arxiv.org/abs/2601.02996). Separating language representation from reasoning substrate reveals the same pattern: the reasoning engine performs best when the language layer presented to it is English [[3]](https://arxiv.org/abs/2505.15257). The consequence is not theoretical. Across eleven languages and four task domains, non-English prompts produce consistent degradation in both performance and robustness [[4]](https://arxiv.org/abs/2505.15935).

Two minds at cross-purposes. One that thinks clearest in its native tongue. One that reasons best in English.

Prompapa sits between them. Nothing more.

### References

1. Gao et al. (2025). *Could Thinking Multilingually Empower LLM Reasoning?* arXiv:2504.11833
2. Liu et al. (2026). *Large Reasoning Models Are (Not Yet) Multilingual Latent Reasoners.* arXiv:2601.02996
3. Zhao et al. (2025). *When Less Language is More: Language-Reasoning Disentanglement Makes LLMs Better Multilingual Reasoners.* NeurIPS 2025. arXiv:2505.15257
4. Hofman et al. (2025). *MAPS: A Multilingual Benchmark for Agent Performance and Security.* EACL 2026. arXiv:2505.15935

## Install

Requires [uv](https://docs.astral.sh/uv/). Install it once, then:

```bash
uv tool install git+https://github.com/seilk/prompapa
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

Prompapa forks your target CLI into a **PTY (pseudo-terminal)**, sitting transparently between your keyboard and the process. Every keystroke passes through unchanged — until you hit `Ctrl+T`.

At that point:

1. Reads current input off the terminal screen via a `pyte` screen tracker
2. Fires an async call to Google Cloud Translation API
3. Erases the original text with precisely-counted backspaces (no screen refresh)
4. Injects the English result via bracketed paste

The child process never pauses. The UI never redraws. The text just... changes.

## Development

```bash
git clone https://github.com/seilk/prompapa
cd prompapa
uv sync
uv run pytest -v
```

Run locally without installing:

```bash
uv run papa claude
```

## Uninstall

```bash
papa uninstall
```

Your config at `~/.config/prompapa/` is kept. Remove it manually if needed.

## TODO
- [ ] `opencode` support
- [ ] LLM API translation support (OpenAI, Gemini, Claude, ...)
