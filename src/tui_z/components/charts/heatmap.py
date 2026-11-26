"""`Heatmap`: a grid of values shaded by one theme color."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from textual.app import RenderResult
from textual.content import Content
from textual.widget import Widget

from ...core.tw import Tw, check_inline
from ...styling.inline import inline


class Heatmap(Tw, Widget):
    """Values shaded from faint to full `color` (a theme token), so it follows
    theme switches.

    Heatmap(activity, color="success", row_labels=["Mon", "Tue", ...], col_labels=["0h", "", "", "3h"])

    `cell` is the width of one cell in columns; `steps` how many shades.
    """

    DEFAULT_CLS = "w-auto h-auto"
    EMPTY_CLS: ClassVar[str] = "bg-panel"
    LABEL_CLS: ClassVar[str] = "text-muted"

    def __init__(self, data: Sequence[Sequence[float]] = (), cls: str = "", *, color: str = "primary",
                 row_labels: Sequence[str] = (), col_labels: Sequence[str] = (), cell: int = 2, steps: int = 5,
                 lo: float | None = None, hi: float | None = None, id: str | None = None) -> None:
        super().__init__(id=id)
        if steps < 1 or cell < 1:
            raise ValueError("cell and steps must be at least 1")
        self.cell = cell
        self.lo, self.hi = lo, hi
        self.row_labels = list(row_labels)
        self.col_labels = list(col_labels)
        self.empty_style = inline(self.EMPTY_CLS)
        self.label_style = inline(self.LABEL_CLS)
        self.set_color(color, steps)
        self._data: list[list[float]] = [list(r) for r in data]
        self._tw_init(cls)

    def on_mount(self) -> None:
        check_inline(self, self.empty_style, self.label_style, *self.shades)

    def set_color(self, color: str, steps: int | None = None) -> None:
        """Shade with another theme color (`steps` shades from faint to full)."""
        steps = steps or len(self.shades)
        self.color = color
        self.shades = [inline(f"bg-{color}/{round(100 * (i + 1) / steps)}") for i in range(steps)]
        check_inline(self, *self.shades)
        self.refresh()

    @property
    def data(self) -> list[list[float]]:
        return [list(r) for r in self._data]

    @data.setter
    def data(self, rows: Sequence[Sequence[float]]) -> None:
        self._data = [list(r) for r in rows]
        self.refresh(layout=True)

    def shade(self, value: float, lo: float, hi: float) -> int:
        """Index into `shades` for a value (-1 = empty)."""
        if value <= lo:
            return -1
        frac = (value - lo) / ((hi - lo) or 1.0)
        return min(len(self.shades) - 1, max(0, round(frac * len(self.shades)) - 1))

    def render(self) -> RenderResult:
        values = [v for row in self._data for v in row]
        if not values:
            return ""
        lo = self.lo if self.lo is not None else min(0.0, *values)
        hi = self.hi if self.hi is not None else max(values)
        gutter = max((len(label) for label in self.row_labels), default=0)
        gutter += 1 if gutter else 0
        lines = []
        if self.col_labels:
            cols = "".join(label[: self.cell].ljust(self.cell) for label in self.col_labels)
            lines.append(Content(" " * gutter + cols).stylize(self.label_style.style))
        blank = " " * self.cell
        for r, row in enumerate(self._data):
            label = self.row_labels[r] if r < len(self.row_labels) else ""
            parts = [Content(label.ljust(gutter)).stylize(self.label_style.style)] if gutter else []
            for value in row:
                i = self.shade(value, lo, hi)
                parts.append(Content(blank).stylize((self.shades[i] if i >= 0 else self.empty_style).style))
            lines.append(Content("").join(parts))
        return Content("\n").join(lines)
