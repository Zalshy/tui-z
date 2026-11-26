"""Content components: text, badges, labels and KPI tiles."""

from __future__ import annotations

from typing import ClassVar

from textual.widget import Widget
from textual.widgets import Static

from ..core.tw import Tw, transform_markup
from ..styling.engine import apply_transforms, merge


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

