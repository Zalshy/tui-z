"""Guards for the Textual internals tui-z relies on (see tui_z/_textual.py).

If one of these fails after a Textual upgrade, tui-z still works through the
public fallbacks, but slower: update `_textual.py` for the new internals.
"""

import threading

from textual.app import App

from tui_z import Text, TwApp, _textual


def test_named_color_table_is_available():
    assert _textual.NAMED_COLORS is not None
    assert _textual.is_named_color("ansi_bright_green")
    assert not _textual.is_named_color("success")


def test_app_register_hook_exists():
    # TwApp flushes classes in _register, just before Textual styles new widgets.
    assert callable(getattr(App, "_register", None))


async def test_fast_path_is_used_on_a_live_app(mount):
    async with mount(Text("x")) as (app, pilot):
        assert _textual.can_append_rules(app.stylesheet)


async def test_fallback_path_still_styles(mount, monkeypatch):
    async with mount(Text("x", id="t")) as (app, pilot):
        monkeypatch.setattr(_textual, "can_append_rules", lambda sheet: False)
        t = app.query_one("#t", Text)
        t.set_cls("text-[#abcdef]")
        await pilot.pause()
        assert str(t.styles.color.hex).lower() == "#abcdef"


async def test_on_app_thread():
    app = TwApp()
    assert _textual.on_app_thread(app)  # not running yet
    async with app.run_test():
        assert _textual.on_app_thread(app)
        result = []
        thread = threading.Thread(target=lambda: result.append(_textual.on_app_thread(app)))
        thread.start()
        thread.join()
        assert result == [False]
