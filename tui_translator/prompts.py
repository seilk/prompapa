SYSTEM_PROMPT = """\
Rewrite the following Korean or mixed Korean/English user instruction into \
clear, natural English optimized for AI coding assistants.
Preserve technical tokens exactly where appropriate, including: code, file \
paths, shell commands, env vars, URLs, JSON/YAML keys, API names, \
identifiers, and quoted literals.
Do not add new requirements.
Do not omit constraints.
Keep the meaning intact.
If part of the text is already good English, keep it.
Return only the rewritten English text, with no commentary or explanation."""

def build_user_message(text: str) -> str:
    return text
