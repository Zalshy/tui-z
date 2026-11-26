from textual.color import Color
from textual.widgets import DataTable

from tui_z import Box, Row, Text, compile_cls, merge, tw


def test_default_cls_accumulates_down_the_hierarchy():
    class Card(Row):
        DEFAULT_CLS = "border h-3"

    assert Card.base_cls() == "w-full h-auto row w-full h-auto border h-3"
    assert Box.base_cls() == "w-full h-auto"


def test_class_is_attached_before_mount():
    t = Text("x", "bold")
    assert t.tw_class == compile_cls(merge(Text.base_cls(), "bold")).name
    assert t.tw_class in t.classes and t.cls == "bold"


async def test_tw_on_a_plain_textual_widget(mount):
    table = tw(DataTable(id="dt"), "h-5 bg-[#102030]")
    async with mount(table) as (app, pilot):
        assert table.outer_size.height == 5
        assert table.styles.background == Color.parse("#102030")
        tw(table, "h-7")  # re-applying swaps the class
        await pilot.pause()
        assert table.outer_size.height == 7
        assert len([c for c in table.classes if c.startswith("tw-")]) == 1


async def test_set_cls_and_add_cls(mount):
    t = Text("hi", "text-[#ff0000] w-10", id="t")
    async with mount(t) as (app, pilot):
        first = t.tw_class
        t.set_cls("text-[#ff0000] w-10")  # unchanged: no class churn
        assert t.tw_class == first
        t.add_cls("w-4")  # appended utilities win
        await pilot.pause()
        assert t.cls == "text-[#ff0000] w-10 w-4"
        assert t.outer_size.width == 4
        assert first not in t.classes and t.tw_class in t.classes
