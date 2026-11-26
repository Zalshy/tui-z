import pytest
from textual.app import ComposeResult
from textual.color import Color

from tui_z import THEME_NAMES, THEMES, Box, TailError, Text, TwApp
from tui_z.styling.themes import EXTRA_TOKENS


def make_app(*widgets_factory):
    class App(TwApp):
        def compose(self) -> ComposeResult:
            yield from widgets_factory[0]()

    return App()


async def test_styles_applied_on_first_frame_and_in_every_app():
    # Two apps in one process must both get the utility stylesheet.
    for _ in range(2):
        app = make_app(lambda: [Text("hi", "text-[#ff0000] w-10 p-1", id="t")])
        async with app.run_test(size=(80, 24)):
            t = app.query_one("#t")
            assert t.styles.color == Color.parse("#ff0000")
            assert t.outer_size.width == 10


async def test_theme_color_resolves():
    app = make_app(lambda: [Text("hi", "text-success bg-panel", id="t")])
    async with app.run_test():
        t = app.query_one("#t")
        assert t.styles.color == Color.parse(app.theme_variables["success"])


async def test_set_cls_at_runtime():
    app = make_app(lambda: [Text("hi", "text-success", id="t")])
    async with app.run_test() as pilot:
        t = app.query_one("#t", Text)
        t.set_cls("text-[#123456] uppercase")
        await pilot.pause()
        assert t.styles.color == Color.parse("#123456")
        assert str(t.render()) == "HI"


async def test_unknown_theme_color_raises():
    app = make_app(lambda: [Text("x", "text-sucess")])
    with pytest.raises(TailError, match="sucess"):
        async with app.run_test():
            pass


async def test_breakpoints():
    def ui():
        return [Box(cls="grid-cols-1 md:grid-cols-3", id="g")]

    app = make_app(ui)
    async with app.run_test(size=(100, 24)):
        assert app.query_one("#g").styles.grid_size_columns == 1
    app = make_app(ui)
    async with app.run_test(size=(130, 24)):
        assert app.query_one("#g").styles.grid_size_columns == 3


async def test_every_theme_applies_every_token(mount):
    async with mount(Text("x", "text-purple bg-panel border border-line", id="t")) as (app, pilot):
        for name in THEME_NAMES:
            app.theme = name
            await pilot.pause()
            for token in EXTRA_TOKENS:
                assert token in app.theme_variables, (name, token)
            assert app.query_one("#t").styles.color == Color.parse(app.theme_variables["purple"])


async def test_builtin_textual_themes_get_fallback_tokens(mount):
    async with mount(Text("x")) as (app, pilot):
        app.theme = "nord"
        await pilot.pause()
        for token in EXTRA_TOKENS:
            assert token in app.theme_variables


async def test_exact_palette_values_survive_textual(mount):
    async with mount(Text("x")) as (app, pilot):
        for t in THEMES:
            app.theme = t.name
            await pilot.pause()
            for key in ("primary", "accent", "warning", "error", "background", "foreground"):
                assert Color.parse(app.theme_variables[key]) == Color.parse(getattr(t, key)), (t.name, key)


async def test_cycle_theme_wraps_and_handles_foreign_themes(mount):
    async with mount(Text("x")) as (app, pilot):
        assert app.theme == "terminal"
        app.action_next_theme()
        assert app.theme == THEME_NAMES[1]
        app.action_prev_theme()
        app.action_prev_theme()
        assert app.theme == THEME_NAMES[-1]
        app.theme = "nord"  # not in TW_THEMES: next goes to the first
        assert app.cycle_theme() == THEME_NAMES[0]
