"""Shared test helpers.

`mount` runs widgets in a headless `TwApp`:

    async def test_badge(mount):
        async with mount(Badge("live", id="b")) as (app, pilot):
            assert app.query_one("#b").render() ...

Pass widgets, or a zero-argument factory that returns them when they must be
created inside the app (e.g. ones that read `app` in `__init__`).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterable
from contextlib import asynccontextmanager

import pytest
from textual.app import ComposeResult
from textual.widget import Widget

from tui_z import TwApp

type Widgets = Widget | Callable[[], Iterable[Widget]]


@pytest.fixture
def mount():
    @asynccontextmanager
    async def _mount(*widgets: Widgets, size: tuple[int, int] = (80, 24),
                     app_class: type[TwApp] = TwApp, **app_attrs) -> AsyncIterator:
        class TestApp(app_class):  # type: ignore[valid-type, misc]
            def compose(self) -> ComposeResult:
                for item in widgets:
                    if isinstance(item, Widget):
                        yield item
                    else:
                        yield from item()

        for name, value in app_attrs.items():
            setattr(TestApp, name, value)
        app = TestApp()
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            yield app, pilot

    return _mount

