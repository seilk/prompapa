<p align="center">
  <img src="assets/prompapa-banner.png" alt="prompapa" width="800" />
</p>

<p align="center">
  <em>Schreibe in deiner Sprache. Drücke <code>Ctrl+]</code> in <strong>Claude Code / Codex / Opencode</strong>. Sieh, wie es zu perfektem Englisch wird.</em>
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
      <br/>🇰🇷 Koreanisch
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-jp.gif" width="600" />
      <br/>🇯🇵 Japanisch
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-cn.gif" width="600" />
      <br/>🇨🇳 Chinesisch
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-fr.gif" width="600" />
      <br/>🇫🇷 Französisch
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-es.gif" width="600" />
      <br/>🇪🇸 Spanisch
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-de.gif" width="600" />
      <br/>🇩🇪 Deutsch
    </td>
  </tr>
</table>

<p align="center"><em><strong>Tippe in <em>jeder Sprache</em>. Drücke <code>Ctrl+]</code> zum Übersetzen ins Englische. Drücke <code>Ctrl+Q</code> zum Rückgängigmachen.</strong></em></p>

## Warum das existiert

Sprache ist kein neutrales Behältnis für Gedanken. Die Wörter, auf die wir als erstes zurückgreifen, die Struktur, die wir auferlegen, bevor wir überhaupt wissen, was wir meinen, der Instinkt, der der Artikulation vorausgeht. All das ist muttersprachlich. Diesen Prozess durch eine Zweitsprache zu zwingen, verlangsamt ihn nicht nur. Es formt ihn still um.

KI-Coding-Assistenten tragen eine analoge Einschränkung aus der entgegengesetzten Richtung. Die Forschung bestätigt, was viele gespürt haben: Diese Modelle weisen einen strukturellen Englisch-Bias auf, bei dem die gleiche Absicht in einer nicht-englischen Sprache ausgedrückt messbar schwächere Antworten erzeugt [[1]](https://arxiv.org/abs/2504.11833). Der Bias reicht tiefer als das Oberflächenvokabular. Repräsentationale Analysen großer Reasoning-Modelle zeigen, dass ihre internen Reasoning-Pfade architektonisch englischzentriert sind, nicht nur durch Trainingsdaten. Unabhängig davon, in welcher Sprache ein Prompt ankommt, konvergiert das Modell zu einem englischförmigen latenten Raum, bevor es mit dem Schlussfolgern beginnt [[2]](https://arxiv.org/abs/2601.02996). Die Trennung von Sprachrepräsentation und Reasoning-Substrat zeigt dasselbe Muster: Das Reasoning-System funktioniert am besten, wenn die ihm präsentierte Sprachschicht Englisch ist [[3]](https://arxiv.org/abs/2505.15257). Die Konsequenz ist nicht theoretisch. Über elf Sprachen und vier Aufgabendomänen hinweg produzieren nicht-englische Prompts eine konsistente Verschlechterung sowohl der Leistung als auch der Robustheit [[4]](https://arxiv.org/abs/2505.15935).

Zwei Geister mit widerstreitenden Zwecken. Einer, der in seiner Muttersprache am klarsten denkt. Einer, der auf Englisch am besten schlussfolgert.

Prompapa steht zwischen ihnen. Nichts mehr.

### Referenzen

1. Gao et al. (2025). *Could Thinking Multilingually Empower LLM Reasoning?* [arXiv:2504.11833](https://arxiv.org/abs/2504.11833)
2. Liu et al. (2026). *Large Reasoning Models Are (Not Yet) Multilingual Latent Reasoners.* [arXiv:2601.02996](https://arxiv.org/abs/2601.02996)
3. Zhao et al. (2025). *When Less Language is More: Language-Reasoning Disentanglement Makes LLMs Better Multilingual Reasoners.* NeurIPS 2025. [arXiv:2505.15257](https://arxiv.org/abs/2505.15257)
4. Hofman et al. (2025). *MAPS: A Multilingual Benchmark for Agent Performance and Security.* EACL 2026. [arXiv:2505.15935](https://arxiv.org/abs/2505.15935)

## Installation

Benötigt [uv](https://docs.astral.sh/uv/). Einmal installieren, dann:

```bash
uv tool install git+https://github.com/seilk/prompapa
```

## Einrichtung

Führe den Onboarding-Assistenten aus, um deinen API-Schlüssel zu konfigurieren:

```bash
papa onboard
```

Dies richtet `~/.config/prompapa/config.toml` mit deinem Google Cloud Translation API-Schlüssel ein.

Noch keinen Schlüssel? Der Assistent führt dich durch den Erhalt eines solchen.

## Verwendung

```bash
papa claude
```

Dein Tool öffnet sich genau wie gewohnt. Zwei neue Hotkeys:

| Hotkey | Aktion |
|--------|--------|
| `Ctrl+]` | Aktuelle Eingabe ins Englische übersetzen |
| `Ctrl+Q` | Übersetzung rückgängig machen, Originaltext wiederherstellen |

## Konfiguration

`~/.config/prompapa/config.toml`:

```toml
provider = "google"
api_key = "your-gcp-translation-api-key"
target_cmd = ["claude"]
preserve_backticks = true
```

`api_key_env` wird ebenfalls unterstützt, wenn du den Schlüssel lieber in einer Umgebungsvariable speicherst:

```toml
provider = "google"
api_key_env = "GOOGLE_API_KEY"
target_cmd = ["claude"]
```

### preserve_backticks

Hält in Backticks eingeschlossene Token unübersetzt:

```toml
preserve_backticks = true
```

`` `src/auth.ts` `` bleibt nach der Übersetzung genau so, wie es ist.

## Wie es funktioniert

Prompapa forkt dein Ziel-CLI in ein **PTY (Pseudo-Terminal)** und sitzt transparent zwischen deiner Tastatur und dem Prozess. Jeder Tastendruck wird unverändert weitergeleitet bis du `Ctrl+]` drückst.

Zu diesem Zeitpunkt:

1. Liest die aktuelle Eingabe vom Terminalbildschirm über einen `pyte`-Bildschirm-Tracker
2. Löst einen asynchronen Aufruf an die Google Cloud Translation API aus
3. Löscht den Originaltext mit präzise gezählten Rückwärtsschritten (keine Bildschirmaktualisierung)
4. Injiziert das englische Ergebnis über Bracket-Paste

Der Kindprozess pausiert nie. Die Benutzeroberfläche wird nie neu gezeichnet. Der Text... ändert sich einfach.

## Entwicklung

```bash
git clone https://github.com/seilk/prompapa
cd prompapa
uv sync
uv run pytest -v
```

Lokal ohne Installation ausführen:

```bash
uv run papa claude
```

## Aktualisierung

```bash
papa update
```

Lädt die neueste Version von GitHub herunter und installiert sie neu.

## Deinstallation

```bash
papa uninstall
```

Deine Konfiguration unter `~/.config/prompapa/` bleibt erhalten. Lösche sie manuell, wenn nötig.

## TODO
- [x] `codex`- und `opencode`-Unterstützung
- [ ] LLM API Übersetzungsunterstützung (OpenAI, Gemini, Claude, ...)
- [ ] Konfigurierbare Zielsprache und Erweiterung (aktuell nur Englisch)
