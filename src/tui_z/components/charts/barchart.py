"""`BarChart`: vertical bars for categories, and histograms."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from textual.app import RenderResult
from textual.content import Content
from textual.widget import Widget

from ...core.tw import Tw
from ._scale import fmt, runs, token_style

type BarItem = float | tuple[str, float] | tuple[str, float, str]
"""A bar: a value, (label, value) or (label, value, color token)."""


class BarChart(Tw, Widget):
    """Vertical bars with labels under them. Bar color = `text-*`.

    BarChart([("Mon", 3), ("Tue", 5), ("Wed", 2, "error")], "h-8 text-primary")
    BarChart.histogram(latencies, bins=12, cls="h-6 text-info")

    Bars share the width (`bar_width=` fixes it); one bar is drawn with eighth
    blocks, so heights are precise to 1/8 of a cell.
    """

    DEFAULT_CLS = "w-full h-8 text-primary"
    BLOCKS: ClassVar[str] = " ▁▂▃▄▅▆▇█"
    MAX_BAR: ClassVar[int] = 8

    def __init__(self, data: Sequence[BarItem] = (), cls: str = "", *, bar_width: int | None = None,
                 gap: int = 1, labels: bool = True, values: bool = False, lo: float = 0.0,
                 hi: float | None = None, id: str | None = None) -> None:
        super().__init__(id=id)
        self.bar_width = bar_width
        self.gap = max(0, gap)
        self.show_labels = labels
        self.show_values = values
        self.lo, self.hi = lo, hi
        self._items: list[tuple[str, float, str]] = []
        self.set_data(data)
        self._tw_init(cls)

    @classmethod
    def histogram(cls, values: Sequence[float], bins: int = 10, *, lo: float | None = None,
                  hi: float | None = None, **kwargs) -> BarChart:
        """Count `values` into `bins` equal-width bins, labelled by their start."""
        if bins < 1:
            raise ValueError("bins must be at least 1")
        if not values:
            return cls([], **kwargs)
        start = min(values) if lo is None else lo
        end = max(values) if hi is None else hi
        width = (end - start) / bins or 1.0
        counts = [0] * bins
        for v in values:
            if start <= v <= end:
                counts[min(bins - 1, int((v - start) / width))] += 1
        return cls([(fmt(start + i * width), float(c)) for i, c in enumerate(counts)], **kwargs)

    @property
    def data(self) -> list[tuple[str, float, str]]:
        return list(self._items)

    def set_data(self, data: Sequence[BarItem]) -> None:
        items = []
        for item in data:
            if isinstance(item, int | float):
                items.append(("", float(item), ""))
            elif len(item) == 2:
                items.append((item[0], float(item[1]), ""))
            else:
                items.append((item[0], float(item[1]), item[2]))  # type: ignore[misc]
        self._items = items
        self.refresh()

    def _widths(self, width: int) -> tuple[int, int]:
        n = len(self._items)
        if self.bar_width is not None:
            return max(1, self.bar_width), self.gap
        bar = (width - self.gap * (n - 1)) // n if n else 0
        return max(1, min(self.MAX_BAR, bar)), self.gap

    def render(self) -> RenderResult:
        width, height = self.content_region.width, self.content_region.height
        if not self._items or width < 1 or height < 1:
            return ""
        bar_w, gap = self._widths(width)
        label_rows = int(self.show_labels and height > 1)
        rows = height - label_rows
        n = min(len(self._items), max(1, (width + gap) // (bar_w + gap)))  # bars that fit
        items = self._items[:n]
        hi = self.hi if self.hi is not None else max(v for _, v, _ in items)
        span = (hi - self.lo) or 1.0
        levels = [round(max(0.0, min(1.0, (v - self.lo) / span)) * rows * 8) for _, v, _ in items]

        lines = []
        for row in range(rows - 1, -1, -1):
            cells: list[tuple[str, str]] = []
            for i, ((_, value, token), level) in enumerate(zip(items, levels)):
                if i:
                    cells.append((" " * gap, ""))
                fill = max(0, min(8, level - row * 8))
                text = self.BLOCKS[fill] * bar_w
                top = (level - 1) // 8  # row holding the bar's top block (-1: empty bar)
                if self.show_values and row == top + 1:
                    text = fmt(value)[:bar_w].center(bar_w)  # value sits just above its bar
                cells.append((text, token_style(token)))
            lines.append(Content.assemble(*runs(cells)))
        if label_rows:
            cells = []
            for i, (label, _, _) in enumerate(items):
                if i:
                    cells.append((" " * gap, ""))
                cells.append((label[:bar_w].center(bar_w), "$muted"))
            lines.append(Content.assemble(*runs(cells)))
        return Content("\n").join(lines)
