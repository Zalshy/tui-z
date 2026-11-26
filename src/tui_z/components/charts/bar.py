"""`Bar`: a horizontal 0..1 meter."""

from __future__ import annotations

from typing import ClassVar

from textual.app import RenderResult
from textual.content import Content
from textual.reactive import reactive
from textual.widget import Widget

from ...core.tw import Tw


class Bar(Tw, Widget):
    """Horizontal meter, 0..1. Fill color = `text-*`; track = theme `line`.

    Bar(0.67, "w-16 text-success")
    """

    DEFAULT_CLS = "w-full h-1 text-primary"
    FILL: ClassVar[str] = "━"
    TRACK: ClassVar[str] = "━"

    value: reactive[float] = reactive(0.0)

    def __init__(self, value: float = 0.0, cls: str = "", *, track: bool = True, id: str | None = None) -> None:
        super().__init__(id=id)
        self.show_track = track
        self._tw_init(cls)
        self.value = value

    def validate_value(self, value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def render(self) -> RenderResult:
        width = self.content_region.width
        filled = round(self.value * width)
        parts: list[tuple[str, str]] = [(self.FILL * filled, "")]
        if self.show_track:
            parts.append((self.TRACK * (width - filled), "$line"))
        return Content.assemble(*parts)
