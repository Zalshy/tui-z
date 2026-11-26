"""Navigation components: tabs, the collapsible sidebar and key hints."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import count
from typing import ClassVar

from textual import events
from textual.app import ComposeResult, RenderResult
from textual.content import Content
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import ContentSwitcher

from ..core.tw import Tw, check_inline, tw
from ..styling.engine import apply_transforms, merge
from ..styling.inline import inline
from .content import Text
from .layout import Box, Row


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
        self.set_reactive(Sidebar.collapsed, collapsed)
        self._apply(collapsed)

    @property
    def cls(self) -> str:
        """The user class string (the border and width/rail are added to it)."""
        return self.user_cls

    def set_cls(self, cls: str) -> None:
        """Replace the user class string. Widths come from `width` / `rail`."""
        self.user_cls = cls
        super().set_cls(self._cls_for(self.collapsed))

    def _cls_for(self, collapsed: bool) -> str:
        border = "border-r border-line" if self.side == "left" else "border-l border-line"
        return merge(border, self.user_cls, self.rail_cls if collapsed else self.width_cls)

    def _apply(self, collapsed: bool) -> None:
        super().set_cls(self._cls_for(collapsed))
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


# --------------------------------------------------------------------------- #
# Tabs
# --------------------------------------------------------------------------- #

class _Tab(Text):
    def __init__(self, label: str, index: int, cls: str) -> None:
        self.index = index
        super().__init__(label, cls, markup=False)

    def on_click(self, event: events.Click) -> None:
        event.stop()
        tabs = next((a for a in self.ancestors if isinstance(a, Tabs)), None)
        if tabs is not None:
            tabs.active = self.index
            tabs.focus()


class Tabs(Tw, Widget, can_focus=True):
    """A row of tab labels; one is active. Left/right or a click switch.

    Tabs(["Dashboard", "Logs"], active=0)     # posts Tabs.Changed(index)

    Use `TabView` for tabs that switch content.
    """

    DEFAULT_CLS = "row w-full h-2 border-b border-line"
    ITEM_CLS: ClassVar[str] = "w-auto h-1 px-1 text-muted cursor-pointer hover:text-foreground"
    ACTIVE_CLS: ClassVar[str] = "text-primary bold bg-primary/15"

    BINDINGS = [("left", "move(-1)", "Previous tab"), ("right", "move(1)", "Next tab")]

    active: reactive[int] = reactive(0, init=False)

    class Changed(Message):
        def __init__(self, tabs: Tabs, index: int) -> None:
            super().__init__()
            self.tabs = tabs
            self.index = index

        @property
        def control(self) -> Tabs:
            return self.tabs

    def __init__(self, labels: Sequence[str], active: int = 0, cls: str = "", *, item_cls: str = "",
                 active_cls: str = "", id: str | None = None) -> None:
        if not labels:
            raise ValueError("Tabs needs at least one label")
        self.item_cls = merge(self.ITEM_CLS, item_cls)
        self.active_cls = merge(self.item_cls, self.ACTIVE_CLS, active_cls)
        self.items = [_Tab(label, i, self.item_cls) for i, label in enumerate(labels)]
        super().__init__(*self.items, id=id)
        self.set_reactive(Tabs.active, self.validate_active(active))
        self._highlight(self.active)
        self._tw_init(cls)

    def validate_active(self, index: int) -> int:
        return max(0, min(len(self.items) - 1, index))

    def watch_active(self, index: int) -> None:
        self._highlight(index)
        self.post_message(self.Changed(self, index))

    def _highlight(self, index: int) -> None:
        for item in self.items:
            item.set_cls(self.active_cls if item.index == index else self.item_cls)

    def action_move(self, step: int) -> None:
        self.active = (self.active + step) % len(self.items)


_pane_ids = count()


class TabPane(Box):
    """One page of a `TabView`: `TabPane("Logs", LogView(), id="logs")`."""

    DEFAULT_CLS = "w-full h-auto"

    def __init__(self, title: str, *children: Widget, cls: str = "", id: str | None = None) -> None:
        self.title = title
        super().__init__(*children, cls=cls, id=id or f"tw-pane-{next(_pane_ids)}")


class TabView(Tw, Widget):
    """Tabs that switch between `TabPane`s. Only the active pane is displayed.

    with TabView(id="tabs"):
        with TabPane("Dashboard", id="dashboard"):
            yield ...
    tab_view.active = "dashboard"            # posts TabView.Changed(pane)
    """

    DEFAULT_CLS = "col w-full h-fr"
    BODY_CLS: ClassVar[str] = "w-full h-fr"

    class Changed(Message):
        def __init__(self, tab_view: TabView, pane: TabPane) -> None:
            super().__init__()
            self.tab_view = tab_view
            self.pane = pane

        @property
        def control(self) -> TabView:
            return self.tab_view

    def __init__(self, *panes: TabPane, active: str | None = None, cls: str = "", tabs_cls: str = "",
                 body_cls: str = "", id: str | None = None) -> None:
        super().__init__(id=id)
        self.panes: list[TabPane] = list(panes)
        self._initial = active
        self.tabs_cls = tabs_cls
        self.body_cls = merge(self.BODY_CLS, body_cls)
        self.tabs: Tabs | None = None
        self.body: ContentSwitcher | None = None
        self._tw_init(cls)

    def compose_add_child(self, widget: Widget) -> None:
        # `with TabView(): with TabPane(...)` -> collect the panes
        if not isinstance(widget, TabPane):
            raise TypeError(f"TabView children must be TabPane, not {type(widget).__name__}")
        self.panes.append(widget)

    def compose(self) -> ComposeResult:
        ids = [pane.id for pane in self.panes]
        start = ids.index(self._initial) if self._initial in ids else 0
        self.tabs = Tabs([pane.title for pane in self.panes] or ["—"], start, self.tabs_cls)
        self.body = tw(ContentSwitcher(*self.panes, initial=ids[start] if ids else None), self.body_cls)
        yield self.tabs
        yield self.body

    @property
    def active(self) -> str | None:
        """The id of the active pane."""
        return self.body.current if self.body else self._initial

    @active.setter
    def active(self, pane_id: str) -> None:
        ids = [pane.id for pane in self.panes]
        if pane_id not in ids:
            raise ValueError(f"no pane with id {pane_id!r}; panes: {ids}")
        if self.tabs is None:
            self._initial = pane_id
        else:
            self.tabs.active = ids.index(pane_id)

    @property
    def active_pane(self) -> TabPane | None:
        return next((p for p in self.panes if p.id == self.active), None)

    def on_tabs_changed(self, event: Tabs.Changed) -> None:
        if event.tabs is not self.tabs or not self.panes or self.body is None:
            return
        event.stop()
        pane = self.panes[event.index]
        if self.body.current != pane.id:
            self.body.current = pane.id
            self.post_message(self.Changed(self, pane))


# --------------------------------------------------------------------------- #
# Key hints
# --------------------------------------------------------------------------- #

class KeyHints(Tw, Widget):
    """A one-line list of keys and what they do, like a footer.

    KeyHints()                                   # follows the screen's bindings
    KeyHints([("q", "quit"), ("[ ]", "theme")])  # or a fixed list

    With no list it shows every binding with `show=True` that is active for
    the focused widget, and updates as focus moves.
    """

    DEFAULT_CLS = "w-full h-1 px-1 bg-surface"
    KEY_CLS: ClassVar[str] = "text-primary bold"
    DESC_CLS: ClassVar[str] = "text-muted"
    SEPARATOR: ClassVar[str] = "   "

    def __init__(self, hints: Sequence[tuple[str, str]] | None = None, cls: str = "", *, key_cls: str = "",
                 desc_cls: str = "", id: str | None = None) -> None:
        super().__init__(id=id)
        self.hints = list(hints) if hints is not None else None
        self.key_style = inline(merge(self.KEY_CLS, key_cls))
        self.desc_style = inline(merge(self.DESC_CLS, desc_cls))
        self._tw_init(cls)

    def on_mount(self) -> None:
        check_inline(self, self.key_style, self.desc_style)
        if self.hints is None:
            self.screen.bindings_updated_signal.subscribe(self, self._bindings_changed)

    def _bindings_changed(self, screen: Screen) -> None:
        self.refresh()

    def current_hints(self) -> list[tuple[str, str]]:
        """(key, description) pairs currently shown."""
        if self.hints is not None:
            return self.hints
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for active in self.screen.active_bindings.values():
            binding = active.binding
            if not binding.show or not active.enabled or binding.action in seen:
                continue
            seen.add(binding.action)
            out.append((self.app.get_key_display(binding), binding.description or binding.action))
        return out

    def render(self) -> RenderResult:
        parts: list[Content] = []
        for key, desc in self.current_hints():
            if parts:
                parts.append(Content(self.SEPARATOR))
            parts.append(Content(apply_transforms(key, self.key_style.transforms)).stylize(self.key_style.style))
            parts.append(Content(" " + apply_transforms(desc, self.desc_style.transforms)).stylize(self.desc_style.style))
        return Content("").join(parts)
