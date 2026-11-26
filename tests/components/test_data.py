from datetime import datetime

import pytest
from helpers import plain, plain_line

from tui_z import LogView, Table, TailError, Ticker

COLUMNS = [("#", "w-3"), ("Name", "w-fr"), ("PnL", "w-8 text-right text-success")]


def table(**kw):
    return Table(COLUMNS, [[str(i), f"row {i}", f"{i}.0"] for i in range(5)],
                 row_cls="odd:bg-panel hover:bg-boost", id="t", **kw)


# -- Table ----------------------------------------------------------------------

async def test_table_renders_aligned_rows_and_limits(mount):
    async with mount(table(max_rows=50, cls="h-auto"), size=(60, 30)) as (app, pilot):
        t = app.query_one("#t", Table)
        assert t.size.height == 2 + 5  # header + rule + rows (h-auto)
        assert plain_line(t, 0).startswith("#   NAME")
        assert plain_line(t, 1).startswith("────")
        assert plain_line(t, 2).rstrip().endswith("0.0")  # right-aligned last column
        for i in range(100):
            t.add_row([str(i), "x", "1"], top=True)
        await pilot.pause()
        assert t.row_count == 50
        assert plain_line(t, 2).startswith("99")  # newest on top


async def test_table_max_rows_trims_oldest_when_appending(mount):
    async with mount(table(max_rows=3)) as (app, pilot):
        t = app.query_one("#t", Table)
        assert t.row_count == 3
        t.add_row(["9", "nine", "9.0"])
        assert t.row_count == 3 and plain_line(t, 4).startswith("9")


async def test_table_update_row_clear_and_headerless(mount):
    headless = Table(COLUMNS, [["1", ("styled", "bold text-warning"), "2"]], header=False, id="h")
    async with mount(table(), headless) as (app, pilot):
        t = app.query_one("#t", Table)
        t.update_row(0, ["0", "renamed", "0.0"])
        assert "renamed" in plain_line(t, 2)
        t.clear()
        assert t.row_count == 0 and t.line_count() == 2
        h = app.query_one("#h", Table)
        assert plain_line(h, 0).startswith("1   styled")


async def test_table_cell_overflow_truncates_with_ellipsis(mount):
    t = Table([("A", "w-4"), ("B", "w-fr")], [["abcdefgh", "x"]], header=False, cls="w-20", id="t")
    async with mount(t):
        assert plain_line(t, 0).startswith("abc…")


async def test_table_hover_and_theme_switch_invalidate_cache(mount):
    async with mount(table(cls="h-auto"), size=(60, 30)) as (app, pilot):
        t = app.query_one("#t", Table)
        before = t.render_line(3)
        await pilot.hover(t, offset=(2, 3))
        await pilot.pause()
        assert t._hover == 1
        app.theme = "catppuccin-latte"
        await pilot.pause()
        after = t.render_line(3)
        assert [s.style for s in before] != [s.style for s in after]
        await pilot.hover(t, offset=(2, 0))  # header: no row hovered
        await pilot.pause()
        assert t._hover is None


async def test_table_unknown_cell_color_raises(mount):
    async with mount(table()) as (app, pilot):
        with pytest.raises(TailError, match="nope"):
            app.query_one("#t", Table).add_row(["1", ("x", "text-nope"), "2"])


# -- LogView --------------------------------------------------------------------

async def test_logview_virtualized_and_trimmed(mount):
    async with mount(LogView(cls="h-5", max_lines=100, id="log"), size=(60, 30)) as (app, pilot):
        log = app.query_one("#log", LogView)
        for i in range(500):
            log.write(f"message {i}", tag="BUY", tag_cls="bg-success/20 text-success")
        await pilot.pause()
        assert log.line_count() == 100 and log.max_lines == 100
        assert "message 499" in plain_line(log, 4)  # tail follows the end
        assert len(log._strips) <= 20  # only visible lines were rendered/cached


async def test_logview_line_format_and_clear(mount):
    log = LogView(cls="h-5 w-50", id="log")
    async with mount(log) as (app, pilot):
        log.write("hello [b]world[/b]", tag="buy", msg_cls="uppercase", time=datetime(2026, 1, 2, 3, 4, 5))
        assert plain_line(log, 0).startswith("03:04:05   BUY   HELLO WORLD")
        log.clear()
        assert log.line_count() == 0


async def test_logview_stops_following_when_scrolled_up(mount):
    log = LogView(cls="h-3", id="log")
    async with mount(log) as (app, pilot):
        for i in range(20):
            log.write(f"m{i}")
        await pilot.pause()
        log.scroll_to(y=0, animate=False)
        await pilot.pause()
        log.write("new")
        await pilot.pause()
        assert log.scroll_offset.y == 0


async def test_logview_unknown_color_raises(mount):
    async with mount(LogView(id="log")) as (app, pilot):
        with pytest.raises(TailError, match="nope"):
            app.query_one("#log", LogView).write("x", tag="T", tag_cls="text-nope")


# -- Ticker ---------------------------------------------------------------------

async def test_ticker_scrolls_one_cell_per_step(mount):
    ticker = Ticker(["alpha", "beta"], "w-20", separator=" | ", speed=60)
    async with mount(ticker):
        first = plain(ticker)
        assert first.startswith("alpha | beta | alpha")
        ticker._advance()
        assert plain(ticker) == first[1:] + plain(ticker)[-1]


async def test_ticker_set_items_and_empty(mount):
    ticker = Ticker([], "w-10", speed=60)
    async with mount(ticker):
        assert plain(ticker) == ""
        ticker._advance()  # no items: nothing to do
        ticker.set_items(["x"])
        assert plain(ticker).startswith("x")
