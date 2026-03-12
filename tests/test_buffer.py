from tui_translator.buffer import ShadowBuffer


def test_empty_buffer():
    b = ShadowBuffer()
    assert b.text() == ""


def test_printable_ascii_accumulates():
    b = ShadowBuffer()
    b.feed(b"hello")
    assert b.text() == "hello"


def test_backspace_removes_last_char():
    b = ShadowBuffer()
    b.feed(b"hello")
    b.feed(b"\x7f")  # DEL/backspace
    assert b.text() == "hell"


def test_backspace_on_empty_is_noop():
    b = ShadowBuffer()
    b.feed(b"\x7f")
    assert b.text() == ""


def test_ctrl_u_clears_all():
    b = ShadowBuffer()
    b.feed(b"hello world")
    b.feed(b"\x15")  # Ctrl+U
    assert b.text() == ""


def test_ctrl_w_kills_last_word():
    b = ShadowBuffer()
    b.feed(b"hello world")
    b.feed(b"\x17")  # Ctrl+W
    assert b.text() == "hello "


def test_ctrl_w_kills_trailing_spaces_then_word():
    b = ShadowBuffer()
    b.feed(b"hello   ")
    b.feed(b"\x17")
    assert b.text() == ""


def test_arrow_keys_ignored():
    b = ShadowBuffer()
    b.feed(b"hello")
    b.feed(b"\x1b[A")  # Up arrow
    b.feed(b"\x1b[B")  # Down arrow
    b.feed(b"\x1b[C")  # Right arrow
    b.feed(b"\x1b[D")  # Left arrow
    assert b.text() == "hello"


def test_escape_sequences_ignored():
    b = ShadowBuffer()
    b.feed(b"hi")
    b.feed(b"\x1b[1;5C")  # Ctrl+Right
    assert b.text() == "hi"


def test_korean_multibyte_utf8():
    b = ShadowBuffer()
    # "안녕" in UTF-8
    b.feed("안녕".encode("utf-8"))
    assert b.text() == "안녕"


def test_korean_backspace_removes_char():
    b = ShadowBuffer()
    b.feed("안녕".encode("utf-8"))
    # Each Korean char is 3 bytes; backspace removes one char
    b.feed(b"\x7f")
    assert b.text() == "안"


def test_bracketed_paste_appended():
    b = ShadowBuffer()
    b.feed(b"hello")
    # Bracketed paste: ESC[200~ ... ESC[201~
    b.feed(b"\x1b[200~pasted text\x1b[201~")
    assert b.text() == "hellopasted text"


def test_clear():
    b = ShadowBuffer()
    b.feed(b"hello")
    b.clear()
    assert b.text() == ""


def test_set_text():
    b = ShadowBuffer()
    b.feed(b"old")
    b.set_text("new translated text")
    assert b.text() == "new translated text"


def test_mixed_korean_english():
    b = ShadowBuffer()
    b.feed("이 버그 fix해줘".encode("utf-8"))
    assert b.text() == "이 버그 fix해줘"
