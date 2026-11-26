import pytest
from helpers import plain
from textual.binding import Binding

from tui_z import KeyHints, Sidebar, TabPane, Tabs, TabView, Text, TwApp


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


# -- Tabs / TabView -----------------------------------------------------------------

class Tabbed(TwApp):
    BINDINGS = [Binding("q", "quit", "Quit"), Binding("x", "noop", "Hidden", show=False)]

    def __init__(self) -> None:
        super().__init__()
        self.changes: list[str] = []

    def compose(self):
        with TabView(active="logs", id="tv"):
            with TabPane("Dashboard", id="dash"):
                yield Text("dash body", id="dash-body")
            with TabPane("Logs", id="logs"):
                yield Text("log body", id="log-body")
            yield TabPane("Auto id")
        yield KeyHints(id="hints")
        yield KeyHints([("[ ]", "theme")], key_cls="text-warning", id="fixed")

    def on_tab_view_changed(self, event: TabView.Changed) -> None:
        self.changes.append(event.pane.id or "")


async def test_tab_view_starts_on_active_and_switches():
    app = Tabbed()
    async with app.run_test(size=(80, 20)) as pilot:
        tv = app.query_one("#tv", TabView)
        assert tv.active == "logs" and tv.active_pane.title == "Logs"
        assert app.query_one("#logs").display
        assert not app.query_one("#dash").display
        assert [plain(t) for t in tv.tabs.items] == ["Dashboard", "Logs", "Auto id"]
        assert tv.panes[2].id.startswith("tw-pane-")
        await pilot.click(tv.tabs.items[0])
        await pilot.pause()
        assert tv.active == "dash" and app.query_one("#dash").display
        tv.tabs.focus()
        await pilot.press("left")  # wraps to the last tab
        await pilot.pause()
        tv.active = "logs"
        await pilot.pause()
        assert app.changes == ["dash", tv.panes[2].id, "logs"]
        with pytest.raises(ValueError, match="no pane"):
            tv.active = "missing"


def test_tab_view_only_takes_panes_and_tabs_need_labels():
    with pytest.raises(TypeError, match="TabPane"):
        TabView().compose_add_child(Text("x"))
    with pytest.raises(ValueError, match="label"):
        Tabs([])
    tv = TabView(TabPane("a", id="a"), TabPane("b", id="b"))
    tv.active = "b"  # before mount: remembered
    assert tv.active == "b"


async def test_tabs_highlight_active(mount):
    tabs = Tabs(["one", "two"], active=5)
    async with mount(tabs) as (app, pilot):
        assert tabs.active == 1
        assert "bg-primary/15" in tabs.items[1].cls and "bg-primary/15" not in tabs.items[0].cls


# -- KeyHints -------------------------------------------------------------------

async def test_key_hints_follow_bindings_and_take_a_fixed_list():
    app = Tabbed()
    async with app.run_test(size=(120, 20)) as pilot:
        hints = app.query_one("#hints", KeyHints)
        shown = dict(hints.current_hints())
        assert shown.get("q") == "Quit" and "Hidden" not in shown.values()
        app.query_one("#tv", TabView).tabs.focus()
        await pilot.pause()
        assert "Next tab" in dict(hints.current_hints()).values()  # the focused widget's bindings
        assert "q Quit" in plain(hints)
        fixed = app.query_one("#fixed", KeyHints)
        assert plain(fixed) == "[ ] theme"
