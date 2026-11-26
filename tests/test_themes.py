from textual.app import ComposeResult
from textual.color import Color

from tui_z import THEME_NAMES, Box, Row, Text, ThemeSwitcher, TwApp
from tui_z.styling.themes import EXTRA_TOKENS


class App(TwApp):
    def compose(self) -> ComposeResult:
        yield ThemeSwitcher(id="switcher")
        yield Text("x", "text-purple bg-panel border border-line", id="t")


async def test_every_theme_defines_every_token_and_applies():
    app = App()
    async with app.run_test() as pilot:
        for name in THEME_NAMES:
            app.theme = name
            await pilot.pause()
            for token in EXTRA_TOKENS:
                assert token in app.theme_variables, (name, token)
            t = app.query_one("#t")
            assert t.styles.color == Color.parse(app.theme_variables["purple"])


async def test_builtin_textual_themes_get_fallback_tokens():
    app = App()
    async with app.run_test() as pilot:
        app.theme = "nord"
        await pilot.pause()
        for token in EXTRA_TOKENS:
            assert token in app.theme_variables


async def test_cycle_and_switcher_highlight():
    app = App()
    async with app.run_test() as pilot:
        assert app.theme == "terminal"
        app.action_next_theme()
        await pilot.pause()
        assert app.theme == THEME_NAMES[1]
        app.action_prev_theme()
        app.action_prev_theme()
        await pilot.pause()
        assert app.theme == THEME_NAMES[-1]
        switcher = app.query_one(ThemeSwitcher)
        active = [i for i in switcher.items if "●" in str(i.render())]
        assert [i.theme_name for i in active] == [THEME_NAMES[-1]]
        await pilot.click(switcher.items[2])
        await pilot.pause()
        assert app.theme == THEME_NAMES[2]


def test_default_cls_accumulates_down_the_hierarchy():
    class Card(Row):
        DEFAULT_CLS = "border h-3"

    assert Card.base_cls() == "w-full h-auto row w-full h-auto border h-3"
    assert Box.base_cls() == "w-full h-auto"


async def test_linechart_stream_scrolls_without_reshaping():
    from tui_z import LineChart

    class A(TwApp):
        def compose(self):
            # step=2 -> one point per cell, so a push shifts by exactly one cell
            yield LineChart([float(i % 7) for i in range(100)], "w-40 h-4", axis=False,
                            step=2, lo=0, hi=6, id="c")

    app = A()
    async with app.run_test() as pilot:
        chart = app.query_one("#c", LineChart)
        before = [line.plain for line in chart.render().split("\n")]
        chart.push(3.0)
        await pilot.pause()
        after = [line.plain for line in chart.render().split("\n")]
        for b, a in zip(before, after):
            assert a[:-1] == b[1:]  # old part moved left one cell, unchanged


async def test_sparkline_stream_scrolls():
    from tui_z import Sparkline

    class A(TwApp):
        def compose(self):
            yield Sparkline([float(i % 5) for i in range(50)], "w-20 h-2", lo=0, hi=4, id="s")

    app = A()
    async with app.run_test() as pilot:
        s = app.query_one("#s", Sparkline)
        before = str(s.render()).split("\n")
        s.push(2.0)
        await pilot.pause()
        after = str(s.render()).split("\n")
        for b, a in zip(before, after):
            assert a[:-1] == b[1:]


def _contrast(a: str, b: str) -> float:
    def lum(c: Color) -> float:
        f = lambda v: (v / 255) / 12.92 if v / 255 <= 0.03928 else (((v / 255) + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b)
    x, y = sorted((lum(Color.parse(a)), lum(Color.parse(b))), reverse=True)
    return (x + 0.05) / (y + 0.05)


def test_theme_legibility():
    from tui_z import THEMES
    for t in THEMES:
        v = t.variables
        assert _contrast(t.foreground, t.background) >= 4.5, t.name
        assert _contrast(v["muted"], t.background) >= 3.4, t.name   # labels stay readable
        assert _contrast(v["line"], t.background) >= 1.3, t.name    # borders stay visible


async def test_exact_palette_values_survive_textual():
    app = App()
    async with app.run_test() as pilot:
        for t in __import__("tui_z").THEMES:
            app.theme = t.name
            await pilot.pause()
            for key in ("primary", "accent", "warning", "error", "background", "foreground"):
                assert Color.parse(app.theme_variables[key]) == Color.parse(getattr(t, key)), (t.name, key)


async def test_sidebar_collapses_and_expands():
    from tui_z import Sidebar

    class S(TwApp):
        def compose(self):
            with Sidebar(title="Menu", width="w-20", id="sb"):  # compose-context children
                yield Text("inside", id="inner")

    app = S()
    async with app.run_test(size=(80, 20)) as pilot:
        sb = app.query_one("#sb", Sidebar)
        assert sb.outer_size.width == 20 and app.query_one("#inner").display
        await pilot.click(sb.handle)
        await pilot.pause()
        assert sb.collapsed and sb.outer_size.width == 3
        assert not sb.body.display
        assert app.query_one("#inner").parent is sb.body
        sb.toggle()
        await pilot.pause()
        assert not sb.collapsed and sb.outer_size.width == 20
