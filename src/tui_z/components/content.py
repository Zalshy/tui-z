"""Content components: text, badges, labels, keys and KPI tiles."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from textual.app import RenderResult
from textual.content import Content
from textual.widget import Widget
from textual.widgets import Static

from ..core.tw import Tw, check_inline, transform_markup
from ..styling.engine import apply_transforms, merge
from ..styling.inline import Inline, inline


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
            text = transform_markup(text, self.transforms) if self._markup else apply_transforms(text, self.transforms)
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


class Kbd(Text):
    """A keyboard key: `Kbd("ctrl+s")`."""

    DEFAULT_CLS = "w-auto h-1 px-1 bg-boost text-foreground bold"

    def __init__(self, key: str, cls: str = "", *, id: str | None = None) -> None:
        super().__init__(key, cls, markup=False, id=id)


type Pair = tuple[str, str] | tuple[str, str, str]
"""A KeyValue row: (key, value) or (key, value, value_cls)."""


class KeyValue(Tw, Widget):
    """Aligned key / value rows, for detail panels.

    KeyValue([("Status", "Live", "text-success"), ("Latency", "12 ms")])
    kv.set("Latency", "18 ms", "text-warning")

    Values are Textual markup. `key_cls` / `value_cls` (and the per-row cls)
    are inline styles: text-*, bg-*, bold, uppercase ...
    """

    DEFAULT_CLS = "w-full h-auto"
    KEY_CLS: ClassVar[str] = "text-muted"
    VALUE_CLS: ClassVar[str] = "text-foreground"
    GAP: ClassVar[int] = 2

    def __init__(self, items: Sequence[Pair] = (), cls: str = "", *, key_cls: str = "",
                 value_cls: str = "", id: str | None = None) -> None:
        super().__init__(id=id)
        self.key_style = inline(merge(self.KEY_CLS, key_cls))
        self.value_style = inline(merge(self.VALUE_CLS, value_cls))
        self._rows: dict[str, tuple[str, Inline]] = {}
        for item in items:
            self.set(*item)
        self._tw_init(cls)

    def on_mount(self) -> None:
        check_inline(self, self.key_style, self.value_style, *(style for _, style in self._rows.values()))

    def set(self, key: str, value: str, cls: str = "") -> None:
        """Add a row, or change the value (and its cls) of an existing one."""
        style = inline(cls)
        check_inline(self, style)
        is_new = key not in self._rows
        self._rows[key] = (value, style)
        self.refresh(layout=is_new)

    def remove_key(self, key: str) -> None:
        self._rows.pop(key, None)
        self.refresh(layout=True)

    def get(self, key: str) -> str | None:
        row = self._rows.get(key)
        return row[0] if row else None

    def render(self) -> RenderResult:
        if not self._rows:
            return ""
        width = max(len(apply_transforms(k, self.key_style.transforms)) for k in self._rows) + self.GAP
        lines = []
        for key, (value, style) in self._rows.items():
            k = Content(apply_transforms(key, self.key_style.transforms)).stylize(self.key_style.style)
            v = Content.from_markup(transform_markup(value, self.value_style.transforms + style.transforms))
            v = v.stylize_before(f"{self.value_style.style} {style.style}".strip()) if (self.value_style.style or style.style) else v
            lines.append(k + Content(" " * (width - k.cell_length)) + v)
        return Content("\n").join(lines)
