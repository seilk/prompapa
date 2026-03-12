from tui_translator.masking import mask_tokens, unmask_tokens, MaskContext

def test_no_backticks_unchanged():
    ctx = mask_tokens("hello world")
    assert ctx.masked == "hello world" and ctx.tokens == []

def test_single_backtick_span_replaced():
    ctx = mask_tokens("run `npm test` now")
    assert "`npm test`" not in ctx.masked
    assert "__MASK_0__" in ctx.masked
    assert ctx.tokens == ["`npm test`"]

def test_multiple_backtick_spans():
    ctx = mask_tokens("edit `src/app.py` and run `pytest`")
    assert ctx.tokens == ["`src/app.py`", "`pytest`"]
    assert "__MASK_0__" in ctx.masked and "__MASK_1__" in ctx.masked

def test_unmask_restores_original():
    original = "run `npm test` and check `src/auth.ts`"
    ctx = mask_tokens(original)
    assert unmask_tokens(ctx.masked, ctx.tokens) == original

def test_unmask_with_translated_text():
    ctx = mask_tokens("실행해줘 `npm test`")
    restored = unmask_tokens("Please run __MASK_0__", ctx.tokens)
    assert restored == "Please run `npm test`"

def test_unmask_missing_placeholder_returns_as_is():
    ctx = mask_tokens("check `file.py`")
    restored = unmask_tokens("check something else", ctx.tokens)
    assert isinstance(restored, str)

def test_empty_input():
    ctx = mask_tokens("")
    assert ctx.masked == "" and ctx.tokens == []
    assert unmask_tokens("", []) == ""

def test_preserve_backticks_false_does_not_mask():
    ctx = mask_tokens("`npm test`", enabled=False)
    assert ctx.masked == "`npm test`" and ctx.tokens == []
