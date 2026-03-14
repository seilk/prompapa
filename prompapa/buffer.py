from __future__ import annotations


class ShadowBuffer:
    """
    Tracks the current input line content by interpreting raw terminal bytes.
    Does not interact with the terminal itself — pure data structure.

    Handles:
    - Printable ASCII + multibyte UTF-8 (Korean etc.)
    - Backspace (0x7f, 0x08): remove last character
    - Ctrl+U (0x15): clear entire buffer
    - Ctrl+W (0x17): kill last word
    - Escape sequences (ESC[...): ignored
    - Bracketed paste (ESC[200~...ESC[201~): content appended
    """

    def __init__(self) -> None:
        self._chars: list[str] = []
        self._stale: bool = False

    @property
    def stale(self) -> bool:
        """Return whether the buffer is marked as stale."""
        return self._stale

    def mark_stale(self) -> None:
        """Mark the buffer as stale."""
        self._stale = True

    def mark_fresh(self) -> None:
        """Mark the buffer as fresh."""
        self._stale = False

    def feed(self, data: bytes) -> None:
        """Process raw bytes from stdin and update internal state."""
        i = 0
        while i < len(data):
            b = data[i]

            # Bracketed paste start: ESC[200~
            if data[i : i + 6] == b"\x1b[200~":
                end = data.find(b"\x1b[201~", i + 6)
                if end != -1:
                    paste = data[i + 6 : end].decode("utf-8", errors="replace")
                    self._chars.extend(paste)
                    i = end + 6
                else:
                    i += 6
                continue

            # Escape sequence: ESC followed by optional '[' and params, ending at final byte (0x40-0x7e)
            if b == 0x1B:
                j = i + 1
                # Skip optional '[' or 'O' introducer
                if j < len(data) and data[j] in (0x5B, 0x4F):  # '[' or 'O'
                    j += 1
                # Skip parameter bytes (0x20-0x3f) and intermediate bytes (0x20-0x2f)
                while j < len(data) and data[j] < 0x40:
                    j += 1
                # Skip final byte (0x40-0x7e)
                if j < len(data) and 0x40 <= data[j] <= 0x7E:
                    j += 1
                # Arrow keys (ESC[A/B/C/D) and other cursor movement
                # indicate history recall or mid-text editing — buffer
                # can no longer be trusted as the sole source of truth.
                seq = data[i:j]
                if len(seq) == 3 and seq[1:2] == b"[" and seq[2:3] in (b"A", b"B", b"C", b"D"):
                    self._stale = True
                i = j
                continue

            # Enter (0x0d): clear buffer and mark fresh (submission = new empty input)
            if b == 0x0D:
                self._chars.clear()
                self._stale = False
                i += 1
                continue

            # Ctrl+J (0x0a): append newline (multiline within input)
            if b == 0x0A:
                self._chars.append("\n")
                i += 1
                continue

            # Ctrl+U: clear all
            if b == 0x15:
                self._chars.clear()
                i += 1
                continue

            # Ctrl+W: kill last word
            if b == 0x17:
                # Remove trailing spaces
                while self._chars and self._chars[-1] == " ":
                    self._chars.pop()
                # Remove last word
                while self._chars and self._chars[-1] != " ":
                    self._chars.pop()
                i += 1
                continue

            # Backspace (DEL 0x7f or BS 0x08)
            if b in (0x7F, 0x08):
                if self._chars:
                    self._chars.pop()
                i += 1
                continue

            # Multibyte UTF-8
            if b >= 0x80:
                # Determine sequence length
                if b >= 0xF0:
                    seq_len = 4
                elif b >= 0xE0:
                    seq_len = 3
                elif b >= 0xC0:
                    seq_len = 2
                else:
                    # Continuation byte alone — skip
                    i += 1
                    continue
                raw = data[i : i + seq_len]
                try:
                    ch = raw.decode("utf-8")
                    self._chars.append(ch)
                except UnicodeDecodeError:
                    pass
                i += seq_len
                continue

            # Printable ASCII (0x20–0x7e)
            if 0x20 <= b <= 0x7E:
                self._chars.append(chr(b))
                i += 1
                continue

            # Everything else (control chars, etc.): skip
            i += 1

    def text(self) -> str:
        """Return current buffer content as a string."""
        return "".join(self._chars)

    def clear(self) -> None:
        """Clear the buffer."""
        self._chars.clear()
        self._stale = False

    def set_text(self, text: str) -> None:
        """Replace buffer content with given text."""
        self._chars = list(text)
        self._stale = False
