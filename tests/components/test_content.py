import pytest
from helpers import plain

from tui_z import Badge, Kbd, KeyValue, Label, Stat, TailError, Text, compile_cls


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


async def test_kbd_is_literal_text(mount):
    k = Kbd("[ctrl]")
    async with mount(k):
        assert plain(k) == "[ctrl]" and k.outer_size == (8, 1)


async def test_keyvalue_aligns_values_and_updates(mount):
    kv = KeyValue([("Status", "Live", "text-success"), ("Latency", "[b]12[/b] ms")], "w-30",
                  key_cls="uppercase")
    async with mount(kv) as (app, pilot):
        assert plain(kv).split("\n") == ["STATUS   Live", "LATENCY  12 ms"]
        kv.set("Latency", "18 ms", "text-warning")
        kv.set("Region", "eu-west")
        await pilot.pause()
        assert kv.get("Latency") == "18 ms" and kv.get("nope") is None
        assert kv.outer_size.height == 3
        kv.remove_key("Status")
        await pilot.pause()
        assert plain(kv).split("\n")[0].startswith("LATENCY")
        assert plain(KeyValue()) == ""


async def test_keyvalue_unknown_color_raises(mount):
    kv = KeyValue([("a", "b")])
    async with mount(kv):
        with pytest.raises(TailError, match="nope"):
            kv.set("a", "b", "text-nope")
