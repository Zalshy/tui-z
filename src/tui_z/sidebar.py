"""Collapsible side panel."""

from __future__ import annotations

from typing import ClassVar

from textual import events
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget

from .engine import merge
from .widgets import Box, Row, Text, Tw


class _Handle(Text):
    """The clickable « / » toggle."""

    def on_click(self, event: events.Click) -> None:
        event.stop()
        sidebar = next((a for a in self.ancestors if isinstance(a, Sidebar)), None)
        if sidebar is not None:
            sidebar.toggle()


class Sidebar(Tw, Widget):
    """A side panel that collapses to a thin rail.

    Sidebar(ThemeSwitcher(), title="Themes", width="w-26")
    sidebar.toggle() / sidebar.collapsed = True       # or click the « handle

    `width` is used when expanded, `rail` when collapsed (both class strings,
    so `md:w-30` etc. work). Posts `Sidebar.Toggled(collapsed)`.
    `side="right"` mirrors the border and arrows.
    """

    DEFAULT_CLS = "h-full col bg-surface"
    HEADER_CLS: ClassVar[str] = "h-1 mt-1 mb-1"
    TITLE_CLS: ClassVar[str] = "text-muted bold uppercase tracking-wide px-1 w-fr truncate"
    HANDLE_CLS: ClassVar[str] = "w-3 text-muted text-center cursor-pointer hover:text-primary hover:bg-boost"

    collapsed: reactive[bool] = reactive(False, init=False)

    class Toggled(Message):
        def __init__(self, sidebar: Sidebar, collapsed: bool) -> None:
            super().__init__()
            self.sidebar = sidebar
            self.collapsed = collapsed

        @property
        def control(self) -> Sidebar:
            return self.sidebar

    def __init__(self, *children: Widget, title: str = "", cls: str = "", width: str = "w-26",
                 rail: str = "w-3", side: str = "left", collapsed: bool = False,
                 id: str | None = None) -> None:
        if side not in ("left", "right"):
            raise ValueError("side must be 'left' or 'right'")
        self.side = side
        self.user_cls = cls
        self.width_cls = width
        self.rail_cls = rail
        self.title = Text(title, self.TITLE_CLS, markup=False)
        self.handle = _Handle("", self.HANDLE_CLS, markup=False)
        header = [self.title, self.handle] if side == "left" else [self.handle, self.title]
        self.body = Box(*children, cls="h-fr col")
        super().__init__(Row(*header, cls=self.HEADER_CLS), self.body, id=id)
        self._tw_init(self._cls_for(collapsed))
        self.set_reactive(Sidebar.collapsed, collapsed)
        self._apply(collapsed)

    def _cls_for(self, collapsed: bool) -> str:
        border = "border-r border-line" if self.side == "left" else "border-l border-line"
        return merge(border, self.user_cls, self.rail_cls if collapsed else self.width_cls)

    def _apply(self, collapsed: bool) -> None:
        self.set_cls(self._cls_for(collapsed))
        self.body.set_cls("h-fr col hidden" if collapsed else "h-fr col")
        self.title.set_cls(merge(self.TITLE_CLS, "hidden") if collapsed else self.TITLE_CLS)
        expand, collapse = ("»", "«") if self.side == "left" else ("«", "»")
        self.handle.update(expand if collapsed else collapse)
        self.handle.tooltip = "Expand" if collapsed else "Collapse"

    def watch_collapsed(self, collapsed: bool) -> None:
        self._apply(collapsed)
        self.post_message(self.Toggled(self, collapsed))

    def toggle(self) -> None:
        self.collapsed = not self.collapsed

    def compose_add_child(self, widget: Widget) -> None:
        # `with Sidebar(...): yield X` -> X goes in the collapsible body
        self.body.compose_add_child(widget)
