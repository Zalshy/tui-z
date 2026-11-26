from helpers import plain

from tui_z import Badge, Box, Col, Divider, Grid, Panel, Row, Scroll, Spacer, Text


async def test_row_lays_out_horizontally_and_col_vertically(mount):
    row = Row(Text("ab", id="a"), Text("cd", id="b"))
    col = Col(Text("ef", id="c"), Text("gh", id="d"))
    async with mount(row, col) as (app, pilot):
        a, b = app.query_one("#a"), app.query_one("#b")
        assert a.region.y == b.region.y and b.region.x == a.region.right
        c, d = app.query_one("#c"), app.query_one("#d")
        assert c.region.x == d.region.x and d.region.y == c.region.bottom


async def test_box_is_vertical_by_default(mount):
    async with mount(Box(Text("1", id="a"), Text("2", id="b"))) as (app, pilot):
        assert app.query_one("#b").region.y == app.query_one("#a").region.bottom


async def test_grid_columns(mount):
    grid = Grid(*[Text(str(i), "w-full", id=f"g{i}") for i in range(4)], cls="grid-cols-2 w-20")
    async with mount(grid) as (app, pilot):
        g = [app.query_one(f"#g{i}").region for i in range(4)]
        assert g[0].y == g[1].y and g[2].y == g[0].bottom
        assert g[0].width == g[1].width == 10


async def test_spacer_pushes_to_the_right_edge(mount):
    row = Row(Text("L", id="l"), Spacer(), Text("R", id="r"), cls="w-30")
    async with mount(row) as (app, pilot):
        assert app.query_one("#r").region.right == 30


async def test_scroll_scrolls(mount):
    scroll = Scroll(*[Text(f"line {i}") for i in range(50)], cls="h-5")
    async with mount(scroll) as (app, pilot):
        assert scroll.max_scroll_y > 0
        scroll.scroll_end(animate=False)
        await pilot.pause()
        assert scroll.scroll_offset.y == scroll.max_scroll_y


async def test_divider_fills_its_width_with_char(mount):
    plain_div, heavy = Divider("w-12"), Divider("w-5", char="━")
    async with mount(plain_div, heavy):
        assert plain(plain_div) == "─" * 12
        assert plain(heavy) == "━" * 5


async def test_panel_header_has_prefix_title_subtitle_and_badge(mount):
    badge = Badge("new", id="badge")
    panel = Panel(Text("body", id="body"), title="Markets", subtitle="live", badge=badge, cls="w-40")
    async with mount(panel) as (app, pilot):
        header = panel.children[0]
        texts = [plain(w) for w in header.children if isinstance(w, Text)]
        assert texts[:3] == ["// ", "M A R K E T S", "  live"]  # uppercase tracking-wide title
        assert badge.parent is header and badge.region.right == panel.content_region.right
        assert app.query_one("#body").region.y > header.region.y


async def test_panel_without_title_has_no_header(mount):
    panel = Panel(Text("only", id="only"))
    async with mount(panel) as (app, pilot):
        assert list(panel.children) == [app.query_one("#only")]


async def test_panel_prefix_and_title_cls_are_customizable(mount):
    class Plain(Panel):
        PREFIX = ""

    panel = Plain(title="Stats", title_cls="normal-case tracking-normal")
    async with mount(panel):
        texts = [plain(w) for w in panel.children[0].children if isinstance(w, Text)]
        assert texts[0] == "Stats"  # normal-case undoes the default uppercase
