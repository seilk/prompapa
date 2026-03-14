from prompapa.prompts import SYSTEM_PROMPT, build_user_message


def test_system_prompt_is_nonempty_string():
    assert isinstance(SYSTEM_PROMPT, str) and len(SYSTEM_PROMPT) > 50


def test_system_prompt_contains_key_instructions():
    assert "English" in SYSTEM_PROMPT
    assert "technical" in SYSTEM_PROMPT.lower()
    assert "Korean" not in SYSTEM_PROMPT
    assert "any language" in SYSTEM_PROMPT.lower()


def test_build_user_message_wraps_text():
    msg = build_user_message("이 버그 고쳐줘")
    assert "이 버그 고쳐줘" in msg


def test_build_user_message_preserves_backtick_context():
    text = "이 함수 리팩토링해줘 but keep `npm test` passing"
    assert "`npm test`" in build_user_message(text)


def test_build_user_message_not_empty_for_empty_input():
    assert isinstance(build_user_message(""), str)
