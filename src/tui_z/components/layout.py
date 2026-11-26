"""Layout components: containers, spacing and panels."""

from __future__ import annotations

from typing import ClassVar

from textual.app import RenderResult
from textual.containers import VerticalScroll
from textual.widget import Widget

from ..core.tw import Tw
from ..styling.engine import merge
from .content import Text


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

