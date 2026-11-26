"""`Sparkline`: a block column chart that streams."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from textual.app import RenderResult
from textual.widget import Widget

from ...core.tw import Tw
from ._scale import Range, Series, resample


class Sparkline(Tw, Widget):
    """Block sparkline / column chart. Color = `text-*`. Any height (`h-6`).

    Streams by default: one column per value, newest on the right; `push()`
    scrolls existing columns left unchanged. `stretch=True` instead fits the
    whole series to the width (for static data).

    Sparkline(values, "h-4 text-success", lo=0)
    """

    DEFAULT_CLS = "w-full h-1 text-primary"
    BLOCKS: ClassVar[str] = " ▁▂▃▄▅▆▇█"

    def __init__(self, data: Sequence[float] = (), cls: str = "", *, stretch: bool = False,
                 lo: float | None = None, hi: float | None = None, keep: int = 1000,
                 id: str | None = None) -> None:
        super().__init__(id=id)
        self.stretch = stretch
        self.range = Range(lo, hi, sticky=not stretch, headroom=0.0)
        self._data = Series(data, keep)
        self._tw_init(cls)

    @property
    def data(self) -> Sequence[float]:
        """The series (read-only view; use `push` / assign to change)."""
        return self._data

    @data.setter
    def data(self, values: Sequence[float]) -> None:
        self._data = Series(values, self._data.keep)
        self.refresh()

    def push(self, value: float) -> None:
        self._data.push(value)
        self.refresh()

    def render(self) -> RenderResult:
        width, height = self.content_region.width, max(1, self.content_region.height)
        if not self.data or not width:
            return ""
        values = resample(self._data, width) if self.stretch else self._data.tail(width)
        lo, hi = self.range(values)
        span = hi - lo
        levels = height * 8
        heights = [round((min(hi, max(lo, v)) - lo) / span * (levels - 1)) + 1 for v in values]
        rows = []
        for row in range(height - 1, -1, -1):
            rows.append("".join(self.BLOCKS[max(0, min(8, h - row * 8))] for h in heights).rjust(width))
        return "\n".join(rows)
