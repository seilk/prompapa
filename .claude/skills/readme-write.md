# Skill: readme-write

## When to use
Use this skill whenever updating or creating any README file for this project (README.md or any README.{lang}.md).

---

## Workflow

### Step 1 — Update English first
**README.md is the source of truth.** All changes start here.
- Write and verify the English version completely before touching any translated file.
- Commit the English update as its own commit before proceeding.

### Step 2 — Propagate to all language files
After README.md is finalized, apply the equivalent changes to all language files:
- `README.ko.md` — Korean
- `README.ja.md` — Japanese
- `README.zh.md` — Chinese (Simplified)
- `README.fr.md` — French
- `README.es.md` — Spanish
- `README.de.md` — German
- `README.ru.md` — Russian

Do not paraphrase or deviate. Match the structure, section order, and content exactly. Translate faithfully.

---

## Writing Rules

### No em dashes (—)
Em dashes are a hallmark of LLM-generated text and sound unnatural in most languages.
- **Wrong**: `Every keystroke passes through unchanged — until you hit Ctrl+T.`
- **Right**: `Every keystroke passes through unchanged until you hit Ctrl+T.`
- **Wrong**: `Undo — restore original text`
- **Right**: `Undo translation, restore original text`

Replace em dashes with:
- A period and new sentence (when the second clause is independent)
- A comma (when the clauses are tightly linked)
- Simple removal (when the dash is purely decorative)

### No hollow filler
Avoid: "It's worth noting that...", "In conclusion...", "This means that...", "In other words..."
Just say the thing.

### Short sentences over long ones
The "Why This Exists" section is intentionally philosophical and dense — that's deliberate style, not a template for other sections. Keep all other sections tight and direct.

### Code tokens stay untranslated
`Ctrl+T`, `Ctrl+Y`, `papa onboard`, `papa claude`, `~/.config/prompapa/config.toml`, `preserve_backticks`, `api_key`, `api_key_env` — never translate these. They appear verbatim in all language files.

### Language switcher block
Every README.{lang}.md must include the language switcher immediately after the badges block:

```html
<p align="center">
  <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a> · <a href="README.zh.md">中文</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <a href="README.ru.md">Русский</a>
</p>
```

README.md (English) also includes this block in the same position.

### Philosophical tone (Why This Exists only)
The "Why This Exists" section cites 4 academic papers and uses a deliberately dense, philosophical register. When translating:
- Preserve the logical flow and argument structure
- Do not simplify or paraphrase the academic content
- Maintain formal register appropriate to each language

---

## Adding a new language

1. Create `README.{lang}.md` by translating README.md fully
2. Add the new language to the switcher block in **all existing files** (README.md and all README.{lang}.md)
3. Add a demo table entry if a demo GIF exists for that language

---

## Section structure (must match across all files)

1. Banner image
2. Tagline (em)
3. Badges
4. Language switcher
5. Demo (GIF table + hotkey hint)
6. Why This Exists (+ References)
7. Install
8. Setup
9. Usage (hotkey table)
10. Configuration (+ preserve_backticks)
11. How it works
12. Development
13. Update
14. Uninstall
15. TODO

Do not reorder, rename, or skip sections between language files.

---

## Commit convention

- English update: `docs: <description>`
- Language files update: `docs: propagate <description> to all language READMEs`
- New language: `docs: add README.{lang}.md ({Language})`
