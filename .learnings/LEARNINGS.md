# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice
**Areas**: frontend | backend | infra | tests | docs | config
**Statuses**: pending | in_progress | resolved | wont_fix | promoted | promoted_to_skill

---

## [LRN-20260314-001] best_practice

**Logged**: 2026-03-14T12:45:00Z
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
Use tmux capture-pane to reverse-engineer TUI layouts before implementing screen parsing

### Details
When building a PTY proxy that needs to capture text from different TUI apps (Claude Code, Codex, OpenCode), each app has a unique screen layout with different markers, decorations, and panel structures. Running each app in a tmux session and capturing the raw screen output with `tmux capture-pane -p` gives ground truth for boundary detection, eliminating guesswork.

### Suggested Action
Always capture real screen data from target apps before designing screen parsing algorithms.

### Metadata
- Source: conversation
- Related Files: prompapa/screen.py, prompapa/adapters/
- Tags: tui, pty, screen-capture, tmux, reverse-engineering

---

## [LRN-20260314-002] knowledge_gap

**Logged**: 2026-03-14T10:30:00Z
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
Kitty keyboard protocol (CSI u) causes Ctrl+key hotkeys to fail silently on modern terminals

### Details
Ghostty and other terminals implementing the Kitty keyboard protocol encode Ctrl+key as CSI u escape sequences (e.g. Ctrl+] = `ESC[93;5u`) instead of raw control bytes (0x1D). A PTY proxy scanning only for raw bytes will never detect the hotkey. The CSI u modifier value is `1 + modifier_bits` where Ctrl=4, Alt=2, Shift=1.

### Suggested Action
Any PTY proxy intercepting keyboard shortcuts must check both legacy raw bytes and Kitty CSI u encodings.

### Metadata
- Source: user_feedback
- Tags: kitty-protocol, csi-u, ghostty, terminal, keybinding

---

## [LRN-20260314-003] best_practice

**Logged**: 2026-03-14T13:00:00Z
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
Adapter-specific input area markers are more reliable than generic prompt prefix detection

### Details
Different TUI coding assistants mark their input areas differently: Claude Code uses ──── decoration lines, Codex uses ▌ (U+258C) prefix on every input line, OpenCode uses ┃ (U+2503) vertical column. A generic "find the prompt prefix" approach fails for apps without standard prompts. Cursor-anchored expansion with per-adapter marker detection is more robust.

### Suggested Action
When parsing TUI output, prefer adapter-specific boundary detection over generic heuristics.

### Metadata
- Source: conversation
- Tags: adapter-pattern, tui, cursor-expansion, capture

---

## [LRN-20260314-004] correction

**Logged**: 2026-03-14T11:00:00Z
**Priority**: medium
**Status**: resolved
**Area**: config

### Summary
No single Ctrl+key default works across all terminals and TUI apps

### Details
Ctrl+Q (0x11) is XON flow control — eaten by Ghostty. Ctrl+Y (0x19) is readline yank — intercepted by Claude Code. The solution is configurable hotkeys with documented per-terminal workarounds, not hunting for a universal default.

### Suggested Action
Always make PTY proxy hotkeys configurable. Document known conflicts per terminal.

### Metadata
- Source: user_feedback
- Tags: keybinding, terminal-compatibility, ghostty, xon-xoff

---

## [LRN-20260314-005] best_practice

**Logged**: 2026-03-14T22:00:00Z
**Priority**: critical
**Status**: resolved
**Area**: backend

### Summary
Cursor probing with Ctrl+A/Ctrl+E is the most reliable input capture method for PTY proxies

### Details
Sending Ctrl+A (Home) and Ctrl+E (End) to the child TUI app and observing where the cursor lands gives the exact editable region — as defined by the app itself. Repeating until the cursor stops moving handles multiline input where a single Ctrl+A only moves to the start of the current line. This eliminates all heuristics: no prompt prefix detection, no decoration boundary parsing, no per-line marker matching. No visible TUI refresh was observed on Claude Code, Codex, or OpenCode.

### Suggested Action
Use cursor probing as the primary capture method. Keep adapter-specific screen capture as fallback only. Make probe parameters (max_repeats, settle_ms) configurable via system.toml.

### Metadata
- Source: conversation
- Related Files: prompapa/app.py, prompapa/screen.py, prompapa/config.py
- Tags: cursor-probe, ctrl-a, ctrl-e, capture, universal

---
