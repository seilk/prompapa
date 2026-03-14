<p align="center">
  <img src="assets/prompapa-banner.png" alt="prompapa" width="800" />
</p>

<p align="center">
  <em>Type in your language. Hit <code>Ctrl+]</code> in <strong>Claude Code / Codex / Opencode</strong>. <br> Watch it become perfect English.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/install-uv-blueviolet" alt="uv" />
  <img src="https://img.shields.io/badge/translation-Google_Cloud-green" alt="Google Cloud Translation" />
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a> · <a href="README.zh.md">中文</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <a href="README.ru.md">Русский</a>
</p>

## Demo

<table>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-ko.gif" width="600" />
      <br/>🇰🇷 Korean
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-jp.gif" width="600" />
      <br/>🇯🇵 Japanese
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-cn.gif" width="600" />
      <br/>🇨🇳 Chinese
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-fr.gif" width="600" />
      <br/>🇫🇷 French
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-es.gif" width="600" />
      <br/>🇪🇸 Spanish
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-de.gif" width="600" />
      <br/>🇩🇪 German
    </td>
  </tr>
</table>

<p align="center"><em><strong>Type in <em>any language</em>. Press <code>Ctrl+]</code> to translate to English. Press <code>Ctrl+Q</code> to undo.</strong></em></p>

## Why This Exists

Language is not a neutral container for thought. The words we reach for first, the structure we impose before we even know what we mean, the instinct that precedes articulation: these are native. Forcing that process through a second language does not merely slow it down. It quietly reshapes it.

AI coding assistants carry an analogous constraint from the other direction. Research confirms what many have sensed: these models exhibit a structural English bias, where the same intent expressed in a non-English language yields measurably weaker responses [[1]](https://arxiv.org/abs/2504.11833). The bias runs deeper than surface vocabulary. Representational analyses of large reasoning models show that their internal reasoning pathways are English-centered by architecture, not just by training data. Regardless of the language a prompt arrives in, the model converges toward an English-shaped latent space before it begins to reason [[2]](https://arxiv.org/abs/2601.02996). Separating language representation from reasoning substrate reveals the same pattern: the reasoning engine performs best when the language layer presented to it is English [[3]](https://arxiv.org/abs/2505.15257). The consequence is not theoretical. Across eleven languages and four task domains, non-English prompts produce consistent degradation in both performance and robustness [[4]](https://arxiv.org/abs/2505.15935).

Two minds at cross-purposes. One that thinks clearest in its native tongue. One that reasons best in English.

Prompapa sits between them. Nothing more.

### References

1. Gao et al. (2025). *Could Thinking Multilingually Empower LLM Reasoning?* [arXiv:2504.11833](https://arxiv.org/abs/arXiv:2504.11833)
2. Liu et al. (2026). *Large Reasoning Models Are (Not Yet) Multilingual Latent Reasoners.* [arXiv:2601.02996](https://arxiv.org/abs/arXiv:2601.02996)
3. Zhao et al. (2025). *When Less Language is More: Language-Reasoning Disentanglement Makes LLMs Better Multilingual Reasoners.* NeurIPS 2025. [arXiv:2505.15257](https://arxiv.org/abs/arXiv:2505.15257)
4. Hofman et al. (2025). *MAPS: A Multilingual Benchmark for Agent Performance and Security.* EACL 2026. [arXiv:2505.15935](https://arxiv.org/abs/arXiv:2505.15935)

## Install

Requires [uv](https://docs.astral.sh/uv/). If you don't have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then install prompapa:

```bash
uv tool install git+https://github.com/seilk/prompapa
```

## Setup

Run the onboarding wizard to configure your API key:

```bash
papa onboard
```

This sets up `~/.config/prompapa/config.toml` with your Google Cloud Translation API key.

### Getting a Google Cloud Translation API key

> **Free tier:** Google Cloud Translation API (Basic) gives you **500,000 characters free every month**. Beyond that, it's $20 per million characters. A typical AI prompt is 100–300 characters, so the free tier covers roughly 1,500–5,000 translations per day before any cost kicks in.

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and sign in.
2. Create a new project (or select an existing one).
3. Navigate to **APIs & Services → Library**, search for **Cloud Translation API**, and click **Enable**.
4. You'll be prompted to enable billing. Google requires a credit card on file, but **you won't be charged within the free tier**. ([Pricing details](https://cloud.google.com/translate/pricing))
5. Go to **APIs & Services → Credentials → Create Credentials → API Key**.
6. Copy the generated key and paste it when `papa onboard` asks for it.

## Usage

> ⚠️ **OpenCode users:** Currently, Prompapa does not support OpenCode's sidebar view. Run OpenCode with the sidebar disabled. We'll fix it right away!


```bash
papa claude # for Claude-Code
papa codex # for Codex
papa opencode # for Opencode
```

> **Note:** When using `papa opencode`, disable the sidebar view first. Prompapa cannot correctly isolate the input area when the sidebar is open, which causes translation errors.

Your tool opens exactly as normal. Two new hotkeys:

| Hotkey | Action |
|--------|--------|
| `Ctrl+]` | Translate current input to English |
| `Ctrl+Q` | Undo translation, restore original text |

### One-shot translation

Translate text directly from the command line without launching a TUI:

```bash
papa -t "버그를 고쳐줘"          # Korean  → Fix the bug.
papa -t "バグを修正して"          # Japanese → Fix the bug.
papa -t "修复这个错误"            # Chinese  → Fix this error.
papa -t "Corrige el error"       # Spanish  → Fix the error.
papa -t "Corrige le bug"         # French   → Fix the bug.
papa -t "Behebe den Fehler"      # German   → Fix the bug.
```

The translated result is printed to stdout, making it easy to pipe into other tools:

```bash
papa -t "이 내용을 클립보드에 복사해줘" | pbcopy
```

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

Prompapa forks your target CLI into a **PTY (pseudo-terminal)**, sitting transparently between your keyboard and the process. Every keystroke passes through unchanged until you hit `Ctrl+]`.

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
uv run papa -t "테스트 문장"
```

## Update

```bash
papa update
```

Pulls and reinstalls the latest version from GitHub.

## Uninstall

```bash
papa uninstall
```

Your config at `~/.config/prompapa/` is kept. Remove it manually if needed.

## TODO
- [x] `codex` and `opencode` support
- [ ] OpenCode sidebar view support — currently throws an error when sidebar is enabled
- [ ] LLM API translation support (OpenAI, Gemini, Claude, ...)
- [ ] Configurable target (destination) language — currently English only
