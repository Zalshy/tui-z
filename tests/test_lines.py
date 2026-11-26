import pytest
from textual.app import ComposeResult

from tui_z import LogView, Table, TailError, TwApp
from tui_z.styling.inline import column, inline, layout_columns, row_variants


def test_inline_styles():
    assert inline("bold text-success bg-panel/40").style == "bold $success on $panel 40%"
    assert inline("uppercase text-[#ff0000]").transforms == ("uppercase",)
    with pytest.raises(TailError):
        inline("border")  # not a text-level utility


def test_column_spec_and_layout():
    a, b, c = column("w-4 text-muted"), column("w-fr text-right bold"), column("w-2fr")
    assert (a.width, b.width, b.align, c.fr) == (4, None, "right", 2)
    widths = layout_columns([a, b, c], 40, gap=1)
    assert widths[0] == 4
    assert sum(widths) + 2 == 40  # columns + 2 gaps fill the width exactly
    assert abs(widths[2] - 2 * widths[1]) <= 1  # 2fr is twice 1fr


def test_row_variants():
    v = row_variants("odd:bg-panel hover:bg-boost text-muted")
    assert set(v) == {"", "odd", "hover"}
    with pytest.raises(TailError):
        row_variants("focus:bg-panel")


class App(TwApp):
    def compose(self) -> ComposeResult:
        yield Table([("#", "w-3"), ("Name", "w-fr"), ("PnL", "w-8 text-right text-success")],
                    [[str(i), f"row {i}", f"{i}.0"] for i in range(5)],
                    row_cls="odd:bg-panel hover:bg-boost", max_rows=50, id="t", cls="h-auto")
        yield LogView(cls="h-5", max_lines=100, id="log")


def plain(widget, y):
    return "".join(seg.text for seg in widget.render_line(y))


async def test_table_renders_aligned_rows_and_limits():
    app = App()
    async with app.run_test(size=(60, 30)) as pilot:
        t = app.query_one("#t", Table)
        assert t.size.height == 2 + 5  # header + rule + rows (h-auto)
        assert plain(t, 0).startswith("#   NAME")
        assert plain(t, 1).startswith("────")
        assert plain(t, 2).rstrip().endswith("0.0")  # right-aligned last column
        for i in range(100):
            t.add_row([str(i), "x", "1"], top=True)
        await pilot.pause()
        assert t.row_count == 50


async def test_table_hover_and_theme_switch_invalidate_cache():
    app = App()
    async with app.run_test(size=(60, 30)) as pilot:
        t = app.query_one("#t", Table)
        before = t.render_line(3)
        await pilot.hover(t, offset=(2, 3))
        await pilot.pause()
        assert t._hover == 1
        app.theme = "catppuccin-latte"
        await pilot.pause()
        after = t.render_line(3)
        assert [s.style for s in before] != [s.style for s in after]


async def test_logview_virtualized_and_trimmed():
    app = App()
    async with app.run_test(size=(60, 30)) as pilot:
        log = app.query_one("#log", LogView)
        for i in range(500):
            log.write(f"message {i}", tag="BUY", tag_cls="bg-success/20 text-success")
        await pilot.pause()
        assert log.line_count() == 100  # max_lines
        assert "message 499" in plain(log, 4)  # tail follows the end
        # only visible lines were rendered/cached, not all 500
        assert len(log._strips) <= 20


async def test_logview_unknown_color_raises():
    app = App()
    async with app.run_test():
        with pytest.raises(TailError, match="nope"):
            app.query_one("#log", LogView).write("x", tag="T", tag_cls="text-nope")
