from __future__ import annotations
import sys

from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea

from tui_translator.config import AppConfig, ConfigError, default_config_path, load_config
from tui_translator.masking import mask_tokens, unmask_tokens
from tui_translator.state import UndoStack
from tui_translator.translator import TranslationError, rewrite_to_english


async def _do_translate(text: str, stack: UndoStack, status: dict, config: AppConfig) -> str:
    """Translate text; returns translated on success, original on failure."""
    status["msg"] = "Translating..."
    ctx = mask_tokens(text, enabled=config.preserve_backticks)
    try:
        masked_result = await rewrite_to_english(ctx.masked, config)
    except TranslationError as e:
        status["msg"] = f"[Error] {e}"
        return text
    result = unmask_tokens(masked_result, ctx.tokens)
    stack.push(text)
    status["msg"] = ""
    return result


def _do_undo(stack: UndoStack, status: dict) -> str | None:
    """Restore last pre-translation snapshot; returns None if nothing to undo."""
    if not stack.can_undo():
        status["msg"] = "[Info] Nothing to undo."
        return None
    restored = stack.pop()
    status["msg"] = ""
    return restored


def build_app(config: AppConfig) -> tuple[Application, TextArea]:
    stack = UndoStack()
    status: dict[str, str] = {"msg": ""}

    text_area = TextArea(text="", multiline=True, scrollbar=True,
                         focus_on_click=True, wrap_lines=True)

    def get_status_text() -> str:
        info = f"[{config.provider}/{config.model}]"
        msg = status["msg"]
        if msg:
            return f" {info}  {msg}"
        return f" {info}  Ready — Ctrl+T translate | Ctrl+Z undo | Ctrl+C quit"

    header = Window(height=1, content=FormattedTextControl(get_status_text), style="class:status")
    footer = Window(height=1,
                    content=FormattedTextControl(" Ctrl+T: translate  Ctrl+Z: undo  Ctrl+C: quit"),
                    style="class:status")

    layout = Layout(HSplit([header, text_area, footer]), focused_element=text_area)
    kb = KeyBindings()

    @kb.add("c-t")
    async def handle_translate(event) -> None:
        current = text_area.text
        if not current.strip():
            return
        translated = await _do_translate(current, stack, status, config)
        text_area.text = translated
        text_area.buffer.cursor_position = len(translated)
        event.app.invalidate()

    @kb.add("c-z")
    def handle_undo(event) -> None:
        restored = _do_undo(stack, status)
        if restored is not None:
            text_area.text = restored
            text_area.buffer.cursor_position = len(restored)
        event.app.invalidate()

    @kb.add("c-c")
    def handle_quit(event) -> None:
        event.app.exit(result=text_area.text)

    app: Application = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True,
        mouse_support=False,
        style=Style.from_dict({"status": "reverse"}),
    )
    return app, text_area


def main() -> None:
    config_path = default_config_path()
    try:
        config = load_config(config_path)
        config.resolve_api_key()
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print(f"\nCreate a config at: {config_path}", file=sys.stderr)
        print('\nExample:\n  provider = "openai"\n  model = "gpt-4.1-mini"\n  api_key_env = "OPENAI_API_KEY"',
              file=sys.stderr)
        sys.exit(1)

    app, _ = build_app(config)
    result = app.run()
    if result:
        print(result)


if __name__ == "__main__":
    main()
