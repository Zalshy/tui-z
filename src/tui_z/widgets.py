"""tui_z components.

Every component takes `cls=` (a utility class string). Components ship their
look as `DEFAULT_CLS`; your `cls` is merged after it, so for any property you
set, yours wins:

    Badge("LIVE")                                  # default: primary pill
    Badge("BOT", cls="bg-warning/20 text-warning") # same badge, amber

Use `tw(widget, cls)` to put utility classes on any Textual widget.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import ClassVar

from textual.app import RenderResult, active_app
from textual.containers import VerticalScroll
from textual.content import Content
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from . import registry
from .engine import Compiled, apply_transforms, compile_cls, merge

# --------------------------------------------------------------------------- #
# Core plumbing
# --------------------------------------------------------------------------- #

def _attach(widget: Widget, cls: str, previous: Compiled | None) -> Compiled:
    compiled = compile_cls(cls)
    registry.add(compiled)
    if widget.is_attached:  # changing cls on a live widget: compile now
        try:
            app = active_app.get()
        except LookupError:
            app = None
        if app is not None and hasattr(app, "tw_flush"):
            app.tw_flush()
    if not widget.is_attached:
        # Not mounted yet: Textual styles the widget when it is registered, so
        # an immediate restyle here would be wasted work (~0.4 ms per widget).
        if previous is not None and previous.name != compiled.name:
            widget.remove_class(previous.name, update=False)
        widget.add_class(compiled.name, update=False)
    elif previous is None:
        widget.add_class(compiled.name)
    elif previous.name != compiled.name:
        # swap in ONE class update (remove + add would restyle the node twice)
        widget.set_classes([c for c in widget.classes if c != previous.name] + [compiled.name])
    return compiled


def tw[W: Widget](widget: W, cls: str) -> W:
    """Apply utility classes to any Textual widget: `tw(DataTable(), "h-fr border")`."""
    widget._tw_compiled = _attach(widget, cls, getattr(widget, "_tw_compiled", None))  # type: ignore[attr-defined]
    return widget


class Tw:
    """Mixin giving a widget `cls=` support. Put it before the Widget base."""

    DEFAULT_CLS: ClassVar[str] = ""
    _tw_compiled: Compiled | None = None
    _tw_cls: str = ""

    def _tw_init(self, cls: str | None) -> None:
        self.set_cls(cls or "")

    @classmethod
    def base_cls(cls) -> str:
        """DEFAULT_CLS of the whole class hierarchy, parents first.

        Subclasses *extend* their parent's look: `class Card(Row): DEFAULT_CLS
        = "border"` keeps Row's `row w-full h-auto` and adds `border`.
        """
        cached = cls.__dict__.get("_tw_base_cls")
        if cached is None:
            cached = merge(*[k.__dict__["DEFAULT_CLS"] for k in reversed(cls.__mro__) if "DEFAULT_CLS" in k.__dict__])
            cls._tw_base_cls = cached
        return cached

    @property
    def cls(self) -> str:
        """The user part of the class string (without DEFAULT_CLS)."""
        return self._tw_cls

    def set_cls(self, cls: str) -> None:
        """Replace the user class string; DEFAULT_CLS still applies underneath."""
        if cls == self._tw_cls and self._tw_compiled is not None:
            return  # unchanged: skip compile lookup + class churn
        self._tw_cls = cls
        self._tw_compiled = _attach(self, merge(self.base_cls(), cls), self._tw_compiled)  # type: ignore[arg-type]
        self._tw_changed()

    def add_cls(self, cls: str) -> None:
        """Append utilities (they win over existing ones)."""
        self.set_cls(merge(self._tw_cls, cls))

    def _tw_changed(self) -> None:
        """Hook for components that render content transforms."""

    @property
    def transforms(self) -> tuple[str, ...]:
        return self._tw_compiled.transforms if self._tw_compiled else ()


_MARKUP_TAG = re.compile(r"(\[[^\[\]]*\])")


def _transform_markup(text: str, transforms: tuple[str, ...]) -> str:
    """Apply content transforms to text but not to [markup] tags."""
    if not transforms:
        return text
    parts = _MARKUP_TAG.split(text)
    return "".join(p if _MARKUP_TAG.fullmatch(p) else apply_transforms(p, transforms) for p in parts)


# --------------------------------------------------------------------------- #
# Layout
# --------------------------------------------------------------------------- #

class Box(Tw, Widget):
    """A container. Vertical by default; `row` / `grid` change the layout."""

    DEFAULT_CLS = "w-full h-auto"

    def __init__(self, *children: Widget, cls: str = "", id: str | None = None,
                 name: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(*children, id=id, name=name, classes=classes, disabled=disabled)
        self._tw_init(cls)


class Row(Box):
    """Horizontal container."""

    DEFAULT_CLS = "row w-full h-auto"


class Col(Box):
    """Vertical container (same as Box, reads better next to Row)."""

    DEFAULT_CLS = "col w-full h-auto"


class Grid(Box):
    """Grid container: `Grid(..., cls="grid-cols-3 gap-1")`."""

    DEFAULT_CLS = "grid w-full h-auto grid-rows-[auto]"


class Scroll(Tw, VerticalScroll):
    """Vertically scrolling container."""

    DEFAULT_CLS = "w-full h-fr scrollbar-thin"

    def __init__(self, *children: Widget, cls: str = "", id: str | None = None,
                 classes: str | None = None) -> None:
        super().__init__(*children, id=id, classes=classes)
        self._tw_init(cls)


class Spacer(Tw, Widget):
    """Takes up the remaining space in a Row."""

    DEFAULT_CLS = "w-fr h-1"

    def __init__(self, cls: str = "") -> None:
        super().__init__()
        self._tw_init(cls)

    def render(self) -> RenderResult:
        return ""


class Divider(Tw, Widget):
    """A horizontal rule; color = `text-*`, style via `CHAR`."""

    DEFAULT_CLS = "w-full h-1 text-line"
    CHAR: ClassVar[str] = "─"

    def __init__(self, cls: str = "", char: str | None = None) -> None:
        super().__init__()
        self.char = char or self.CHAR
        self._tw_init(cls)

    def render(self) -> RenderResult:
        return self.char * self.content_region.width


# --------------------------------------------------------------------------- #
# Content
# --------------------------------------------------------------------------- #

class Text(Tw, Static):
    """Text with utility classes. Supports Textual markup (`[$success]x[/]`) and
    content transforms (`uppercase`, `lowercase`, `capitalize`, `tracking-wide`)."""

    DEFAULT_CLS = "w-auto h-auto"

    def __init__(self, content: str = "", cls: str = "", *, markup: bool = True,
                 id: str | None = None, classes: str | None = None) -> None:
        self._raw = content
        self._markup = markup
        super().__init__("", markup=markup, id=id, classes=classes)
        self._tw_init(cls)

    def _tw_changed(self) -> None:
        self._render_text()

    def _render_text(self) -> None:
        text = self._raw
        if self.transforms:
            text = _transform_markup(text, self.transforms) if self._markup else apply_transforms(text, self.transforms)
        super().update(text, layout=self._auto_sized())

    def _auto_sized(self) -> bool:
        """Only an auto-sized widget needs a layout pass when its text changes."""
        width, height = self.styles.width, self.styles.height
        return width is None or height is None or width.is_auto or height.is_auto

    def update(self, content: str = "") -> None:  # type: ignore[override]
        if content == self._raw:
            return
        self._raw = content
        self._render_text()

    @property
    def text(self) -> str:
        return self._raw


class Badge(Text):
    """A one-line pill: `Badge("WHALE", cls="bg-info/20 text-info")`."""

    DEFAULT_CLS = "w-auto h-1 px-1 bg-primary/15 text-primary bold uppercase"


class Label(Text):
    """Small caption text, as in `MKT PRICE` / `FAIR VALUE`."""

    DEFAULT_CLS = "w-auto h-auto text-muted uppercase"


class Stat(Tw, Widget):
    """Label over a value: the KPI tile.

    Stat("NET PNL", "+$10 554", cls="w-16", value_cls="text-success")
    """

    DEFAULT_CLS = "w-auto h-auto"
    LABEL_CLS: ClassVar[str] = "text-muted uppercase"
    VALUE_CLS: ClassVar[str] = "text-foreground bold"

    def __init__(self, label: str, value: str = "", cls: str = "", *,
                 label_cls: str = "", value_cls: str = "", id: str | None = None) -> None:
        self.label = Text(label, merge(self.LABEL_CLS, label_cls))
        self.value = Text(value, merge(self.VALUE_CLS, value_cls))
        super().__init__(self.label, self.value, id=id)
        self._tw_init(cls)

    def update(self, value: str, value_cls: str | None = None) -> None:
        self.value.update(value)
        if value_cls is not None:
            self.value.set_cls(merge(self.VALUE_CLS, value_cls))


class Panel(Tw, Widget):
    """A bordered section with a `// TITLE` header and optional right-side badge.

    Panel(*children, title="Live markets", badge=Badge("WATCHING 47"), cls="h-fr")
    """

    DEFAULT_CLS = "w-full h-auto border border-line bg-surface px-1"
    HEADER_CLS: ClassVar[str] = "h-1 mb-1"
    TITLE_CLS: ClassVar[str] = "text-muted bold uppercase tracking-wide"
    PREFIX: ClassVar[str] = "//"

    def __init__(self, *children: Widget, title: str = "", badge: Widget | None = None,
                 subtitle: str = "", cls: str = "", title_cls: str = "", header_cls: str = "",
                 id: str | None = None) -> None:
        header: list[Widget] = []
        if title or badge:
            parts: list[Widget] = []
            if title:
                if self.PREFIX:
                    parts.append(Text(f"{self.PREFIX} ", "text-line bold", markup=False))
                parts.append(Text(title, merge(self.TITLE_CLS, title_cls), markup=False))
            if subtitle:
                parts.append(Text(f"  {subtitle}", "text-muted truncate", markup=False))
            parts.append(Spacer())
            if badge is not None:
                parts.append(badge)
            header.append(Row(*parts, cls=merge(self.HEADER_CLS, header_cls)))
        super().__init__(*header, *children, id=id)
        self._tw_init(cls)


# --------------------------------------------------------------------------- #
# Data (Table / LogView live in tui_z.lines)
# --------------------------------------------------------------------------- #

class Ticker(Tw, Widget):
    """A scrolling one-line feed. Items are Textual markup (`[$success]+8%[/]`).

    Ticker(["[b $error]LIVE FEED[/]", "VETO $NOVAKIT", ...], "bg-surface")
    """

    DEFAULT_CLS = "w-full h-1"

    def __init__(self, items: Sequence[str] = (), cls: str = "", *, separator: str = "   ·   ",
                 speed: float = 0.12, id: str | None = None) -> None:
        super().__init__(id=id)
        self.separator = separator
        self.speed = speed
        self._offset = 0
        self._tw_init(cls)
        self.set_items(items)

    def set_items(self, items: Sequence[str]) -> None:
        sep = Content.from_markup(f"[$line]{self.separator}[/]")
        self._content = sep.join([Content.from_markup(i) for i in items]) + sep if items else Content("")
        self._loop: Content | None = None  # rebuilt lazily for the current width
        self._loop_width = -1
        self.refresh()

    def on_mount(self) -> None:
        self.set_interval(self.speed, self._advance)

    def _advance(self) -> None:
        if self._content.cell_length:
            self._offset = (self._offset + 1) % len(self._content)
            self.refresh()

    def render(self) -> RenderResult:
        width = self.content_region.width
        if not len(self._content):
            return ""
        if self._loop is None or self._loop_width != width:
            repeats = -(-(width + len(self._content)) // len(self._content))  # ceil
            self._loop = Content("").join([self._content] * repeats)
            self._loop_width = width
        return self._loop[self._offset: self._offset + width]


# --------------------------------------------------------------------------- #
# Interaction
# --------------------------------------------------------------------------- #

class Button(Tw, Static, can_focus=True):
    """Clickable / focusable button. Posts `Button.Pressed`.

    Button("BUY YES", "text-success border-success")
    """

    DEFAULT_CLS = (
        "w-auto h-auto px-2 border border-line text-foreground bold uppercase content-center cursor-pointer "
        "hover:bg-boost hover:border-muted focus:border-primary focus:text-primary"
    )

    class Pressed(Message):
        def __init__(self, button: Button) -> None:
            super().__init__()
            self.button = button

        @property
        def control(self) -> Button:
            return self.button

    BINDINGS = [("enter", "press", "Press"), ("space", "press", "Press")]

    def __init__(self, label: str, cls: str = "", *, id: str | None = None, name: str | None = None) -> None:
        self._label = label
        super().__init__("", id=id, name=name)
        self._tw_init(cls)

    def _tw_changed(self) -> None:
        self.update(apply_transforms(self._label, self.transforms))

    @property
    def label(self) -> str:
        return self._label

    def on_click(self) -> None:
        self.action_press()

    def action_press(self) -> None:
        self.post_message(self.Pressed(self))
