from helpers import plain

from tui_z import Badge, Label, Stat, Text, compile_cls


async def test_text_markup_and_transforms_skip_tags(mount):
    t = Text("hello [b]world[/b]", "uppercase", id="t")
    raw = Text("[not markup]", markup=False, id="raw")
    async with mount(t, raw):
        assert plain(t) == "HELLO WORLD"
        assert plain(raw) == "[not markup]"


async def test_text_update_skips_unchanged_values(mount):
    t = Text("a", "w-10")
    async with mount(t) as (app, pilot):
        t.update("b")
        assert t.text == "b" and plain(t) == "b"
        calls = []
        t._render_text = lambda: calls.append(1)  # type: ignore[method-assign]
        t.update("b")
        assert not calls


async def test_text_auto_size_follows_content(mount):
    t = Text("abc")
    async with mount(t) as (app, pilot):
        assert t.outer_size.width == 3
        t.update("abcdef")
        await pilot.pause()
        assert t.outer_size.width == 6


async def test_badge_and_label_defaults(mount):
    badge, label = Badge("live"), Label("fair value")
    async with mount(badge, label):
        assert plain(badge) == "LIVE" and badge.outer_size.height == 1
        assert plain(label) == "FAIR VALUE"
        assert Label("Fair value", cls="normal-case").transforms == ()


async def test_stat_update_value_and_color(mount):
    stat = Stat("pnl", "+1", value_cls="text-success")
    async with mount(stat) as (app, pilot):
        assert plain(stat.label) == "PNL" and plain(stat.value) == "+1"
        success = app.theme_variables["success"]
        stat.update("-2", "text-error")
        await pilot.pause()
        assert plain(stat.value) == "-2"
        assert stat.value.styles.color.hex.lower() == app.theme_variables["error"].lower()
        assert stat.value.styles.color.hex.lower() != success.lower()
        stat.update("-3")  # value only: keeps the color
        await pilot.pause()
        assert stat.value.tw_class == compile_cls(stat.value.applied_cls).name
        assert "text-error" in stat.value.cls
