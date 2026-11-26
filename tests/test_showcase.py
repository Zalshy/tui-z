"""The showcase demo runs, and shows every exported component."""

import importlib.util
from pathlib import Path

import pytest
from components.examples import ABSTRACT, exported_components

from tui_z import Dialog, NotificationCenter, Sidebar, TabView, Toast, ToastStack

SHOWCASE = Path(__file__).parent.parent / "demos" / "showcase.py"


@pytest.fixture(scope="module")
def showcase_module():
    spec = importlib.util.spec_from_file_location("showcase", SHOWCASE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_showcase_uses_every_component(showcase_module):
    app = showcase_module.Showcase()
    async with app.run_test(size=(200, 60)) as pilot:
        await pilot.pause(0.5)
        await pilot.press("t")  # a toast: Toast + ToastStack
        await pilot.press("d")  # a dialog
        await pilot.pause()
        seen = {type(w) for w in app.query("*")} | {type(w) for w in app.screen.query("*")} | {type(app.screen)}
        missing = {c for c in exported_components() | (ABSTRACT - {app.__class__}) if not any(
            issubclass(s, c) for s in seen)}
        assert not missing, f"add these to demos/showcase.py: {sorted(c.__name__ for c in missing)}"
        assert isinstance(app.screen, Dialog)
        await pilot.press("escape")
        await pilot.pause()


async def test_showcase_interactions(showcase_module):
    app = showcase_module.Showcase()
    async with app.run_test(size=(200, 60)) as pilot:
        await pilot.pause(0.3)
        tabs = app.query_one("#tabs", TabView)
        for key, tab in zip("1234567", [t[0] for t in showcase_module.TABS]):
            await pilot.press(key)
            assert tabs.active == tab
        assert not app.on_dashboard  # live updates pause off the dashboard

        await pilot.press("4")
        app._press_toast_burst()  # 5 toasts, at most TW_TOAST_MAX on screen
        await pilot.pause()
        stack = app.screen.query_one(ToastStack)
        assert len(stack.toasts) == app.TW_TOAST_MAX
        app._toast_from_form()
        app._press_toast_repeat()
        await pilot.pause()
        assert stack.toasts[-1].count == 2  # the repeat merged into the newest toast

        inbox = app.query_one("#inbox", Sidebar)
        await pilot.press("i")
        await pilot.pause()
        assert not inbox.collapsed and app.query_one("#center", NotificationCenter).unread == 0

        app._press_dialog_delete()
        await pilot.pause()
        await pilot.press("enter")  # the focused button is "Delete"
        await pilot.pause()
        assert any(t.title == "Deleted" for t in app.screen.query(Toast))
