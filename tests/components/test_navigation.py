import pytest

from tui_z import Sidebar, Text, TwApp


class Toggles(TwApp):
    def __init__(self, **kw) -> None:
        super().__init__()
        self.kw = kw
        self.toggles: list[bool] = []

    def compose(self):
        with Sidebar(title="Menu", width="w-20", id="sb", **self.kw):  # compose-context children
            yield Text("inside", id="inner")

    def on_sidebar_toggled(self, event: Sidebar.Toggled) -> None:
        self.toggles.append(event.collapsed)


async def test_sidebar_collapses_and_expands():
    app = Toggles()
    async with app.run_test(size=(80, 20)) as pilot:
        sb = app.query_one("#sb", Sidebar)
        assert sb.outer_size.width == 20 and app.query_one("#inner").display
        assert str(sb.handle.render()) == "«"
        await pilot.click(sb.handle)
        await pilot.pause()
        assert sb.collapsed and sb.outer_size.width == 3
        assert not sb.body.display and str(sb.handle.render()) == "»"
        assert app.query_one("#inner").parent is sb.body
        sb.toggle()
        await pilot.pause()
        assert not sb.collapsed and sb.outer_size.width == 20
        assert app.toggles == [True, False]


async def test_sidebar_right_side_mirrors_and_starts_collapsed():
    app = Toggles(side="right", collapsed=True)
    async with app.run_test(size=(80, 20)):
        sb = app.query_one("#sb", Sidebar)
        assert sb.collapsed and sb.outer_size.width == 3
        assert str(sb.handle.render()) == "«"
        assert "border-l" in sb.applied_cls


async def test_sidebar_user_cls_survives_toggling():
    app = Toggles(cls="bg-panel")
    async with app.run_test(size=(80, 20)) as pilot:
        sb = app.query_one("#sb", Sidebar)
        sb.set_cls("bg-boost")
        sb.toggle()
        await pilot.pause()
        assert sb.cls == "bg-boost" and "bg-boost" in sb.applied_cls


def test_sidebar_rejects_unknown_side():
    with pytest.raises(ValueError, match="side"):
        Sidebar(side="top")
