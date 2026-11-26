"""Checks every component must pass. Add new components to `examples.py`."""

import pytest
from examples import EXAMPLES, INVISIBLE, WIDTH_FROM_PARAMS, exported_components

from tui_z import THEME_NAMES, compile_cls

COMPONENTS = sorted(EXAMPLES, key=lambda c: c.__name__)


def test_every_exported_component_has_an_example():
    missing = exported_components() - set(EXAMPLES)
    assert not missing, f"add these to tests/components/examples.py: {sorted(c.__name__ for c in missing)}"


@pytest.mark.parametrize("component", COMPONENTS, ids=lambda c: c.__name__)
def test_default_cls_is_applied_under_the_user_cls(component):
    widget = EXAMPLES[component]("bold")
    assert widget.cls == "bold"
    applied = widget.applied_cls.split()
    base = component.base_cls().split()
    assert applied[: len(base)] == base  # defaults first, so the user's utilities win
    assert "bold" in applied[len(base):]
    assert widget.tw_class == compile_cls(widget.applied_cls).name
    assert widget.tw_class in widget.classes


@pytest.mark.parametrize("component", COMPONENTS, ids=lambda c: c.__name__)
async def test_user_size_wins_and_set_cls_restyles(component, mount):
    widget = EXAMPLES[component]("w-7 h-3")
    fixed_width = component in WIDTH_FROM_PARAMS

    def size() -> tuple[int, int]:
        if component in INVISIBLE:
            return int(widget.styles.width.value), int(widget.styles.height.value)
        return widget.outer_size.width, widget.outer_size.height

    async with mount(widget, size=(60, 20)) as (app, pilot):
        assert size() == (7, 3)
        widget.set_cls("w-9 h-4")
        await pilot.pause()
        assert widget.cls == "w-9 h-4"
        assert size() == (7 if fixed_width else 9, 4)
        widget.add_cls("h-5")
        await pilot.pause()
        assert widget.cls == "w-9 h-4 h-5" and size()[1] == 5


@pytest.mark.parametrize("component", COMPONENTS, ids=lambda c: c.__name__)
async def test_renders_under_every_theme(component, mount):
    widget = EXAMPLES[component]("")
    async with mount(widget, size=(60, 20)) as (app, pilot):
        for name in THEME_NAMES:
            app.theme = name
            await pilot.pause()
            assert app.export_screenshot()  # draws every widget; errors surface here
