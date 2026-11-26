"""`LineChart`: a braille line / area chart with extra series and marks."""

from __future__ import annotations

from collections.abc import Sequence

from textual.app import RenderResult
from textual.content import Content
from textual.widget import Widget

from ...core.tw import Tw
from ._scale import Range, Series, fmt, resample, runs, token_style

# Braille: each cell is a 2x4 dot grid. _DOTS[y][x] is the bit for that dot.
_DOTS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))
_BRAILLE = tuple(" " if i == 0 else chr(0x2800 + i) for i in range(256))  # 0 -> blank cell


class LineChart(Tw, Widget):
    """Braille line / area chart with optional extra series, marks and a y axis.

    Two modes:

    - ``mode="stream"`` (default): a live chart. Every point gets a fixed slot
      of ``step`` dot-columns (a cell is 2 dots wide), the newest point sits on
      the right edge, and ``push()`` scrolls what is already drawn to the left
      without changing its shape. The y-range is sticky (see ``lo``/``hi`` to
      freeze it).
    - ``mode="fit"``: the whole series is stretched to the width (static data).

    LineChart(pnl, "h-10 text-success", fill=True)
    chart = LineChart(price, series=[(path_a, "purple"), (path_b, "cyan")],
                      marks=[(1.4, "success", "TP"), (0.8, "error", "SL")], lo=0.5, hi=1.6)
    chart.push(new_price, new_a, new_b)   # advance every series together

    The main series uses the widget's `text-*` color; extra series and marks
    take theme color tokens.
    """

    DEFAULT_CLS = "w-full h-8 text-primary"

    def __init__(
        self,
        data: Sequence[float] = (),
        cls: str = "",
        *,
        series: Sequence[tuple[Sequence[float], str]] = (),
        marks: Sequence[tuple[float, str, str]] = (),
        fill: bool = False,
        axis: bool = True,
        mode: str = "stream",
        step: int = 1,
        lo: float | None = None,
        hi: float | None = None,
        keep: int = 2000,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        if mode not in ("stream", "fit"):
            raise ValueError("mode must be 'stream' or 'fit'")
        self.mode = mode
        self.step = max(1, step)
        self.keep = keep
        self._data = Series(data, keep)
        self.series: list[tuple[Series, str]] = [(Series(d, keep), color) for d, color in series]
        self.marks = list(marks)
        self.fill = fill
        self.axis = axis
        self.range = Range(lo, hi, sticky=(mode == "stream"))
        self._gutter = 0  # last axis width; avoids a second layout pass
        self._tw_init(cls)

    # -- data ------------------------------------------------------------------
    @property
    def data(self) -> Sequence[float]:
        """The main series (read-only view; use `push` / assign to change)."""
        return self._data

    @data.setter
    def data(self, values: Sequence[float]) -> None:
        self._data = Series(values, self.keep)
        self.refresh()

    def push(self, value: float, *series_values: float) -> None:
        """Append one point to the main series and, in order, to each extra series."""
        self._data.push(value)
        for (values, _), v in zip(self.series, series_values):
            values.push(v)
        self.refresh()

    def set_series(self, series: Sequence[tuple[Sequence[float], str]]) -> None:
        self.series = [(Series(d, self.keep), color) for d, color in series]
        self.refresh()

    # -- rendering -------------------------------------------------------------
    def _layout(self, values: Series, px_w: int) -> list[tuple[int, float]]:
        """(x, value) pairs for one series."""
        if self.mode == "fit":
            return list(enumerate(resample(values, px_w)))
        # points that fit (newest on the right edge) + one off-screen on the left,
        # so the segment entering the left edge is drawn and nothing "pops"
        visible = values.tail((px_w - 1) // self.step + 2)
        right = px_w - 1
        last = len(visible) - 1
        step = self.step
        return [(right - (last - i) * step, v) for i, v in enumerate(visible)]

    def _lay_out_all(self, cols: int) -> tuple[list, float, float]:
        px_w = cols * 2
        all_series = [*self.series, (self._data, "")]
        layouts = [(self._layout(s, px_w), token) for s, token in all_series]
        values = [v for lay, _ in layouts for x, v in lay if x >= 0]
        values += [m[0] for m in self.marks]
        lo, hi = self.range(values) if values else (0.0, 1.0)
        return layouts, lo, hi

    def render(self) -> RenderResult:
        width, height = self.content_region.width, self.content_region.height
        if width < 4 or height < 1 or not (self._data or any(s for s, _ in self.series)):
            return ""

        # The y-axis width depends on the labels, which depend on the range,
        # which depends on how many points fit: lay out once with last frame's
        # gutter and only redo it if the label width actually changed.
        gutter = self._gutter if self.axis else 0
        layouts, lo, hi = self._lay_out_all(width - gutter)
        labels = [fmt(hi), fmt((hi + lo) / 2), fmt(lo)] if self.axis else []
        if self.axis:
            needed = max(map(len, labels)) + 1
            if needed != gutter:
                gutter = self._gutter = needed
                layouts, lo, hi = self._lay_out_all(width - gutter)
                labels = [fmt(hi), fmt((hi + lo) / 2), fmt(lo)]

        cols = width - gutter
        px_w, px_h = cols * 2, height * 4
        bits = [[0] * cols for _ in range(height)]
        color: list[list[str]] = [[""] * cols for _ in range(height)]
        scale = (px_h - 1) / (hi - lo)

        dots = _DOTS
        last_px = px_h - 1
        for layout, token in layouts:
            style = token_style(token)
            area = self.fill and not token
            prev_x: int | None = None
            prev_y = 0.0
            for x, v in layout:
                y = (hi - v) * scale
                if prev_x is None or x - prev_x == 1:
                    # fast path: one point per dot column, segment from prev_y to y
                    spans = ((x, y, y if prev_x is None else prev_y),)
                else:
                    dx = x - prev_x
                    spans = tuple((xi, prev_y + (y - prev_y) * (xi - prev_x) / dx,
                                   prev_y + (y - prev_y) * (xi - 1 - prev_x) / dx)
                                  for xi in range(prev_x + 1, x + 1))
                prev_x, prev_y = x, y
                for xi, y_now, y_before in spans:
                    if xi < 0 or xi >= px_w:
                        continue
                    a, b = round(y_now), round(y_before)
                    top, bottom = (a, b) if a <= b else (b, a)
                    if area:
                        bottom = last_px
                    top = max(top, 0)
                    bottom = min(bottom, last_px)
                    cx, bit_col = xi >> 1, xi & 1
                    for py_ in range(top, bottom + 1):
                        cy = py_ >> 2
                        bits[cy][cx] |= dots[py_ & 3][bit_col]
                        color[cy][cx] = style

        mark_rows: dict[int, tuple[str, str]] = {}
        for value, token, label in self.marks:
            if lo <= value <= hi:
                mark_rows[round((hi - value) * scale) // 4] = (token_style(token), label)

        lines = []
        for row in range(height):
            cells: list[tuple[str, str]] = []
            if gutter:
                label = ""
                if row == 0:
                    label = labels[0]
                elif row == height - 1:
                    label = labels[2]
                elif row == height // 2 and height > 4:
                    label = labels[1]
                cells.append((label.rjust(gutter - 1) + " ", "$muted"))
            mark = mark_rows.get(row)
            mark_label = mark[1][: cols // 3] if mark else ""
            label_from = cols - len(mark_label)
            row_bits, row_color = bits[row], color[row]
            if mark:
                for col in range(cols):
                    b = row_bits[col]
                    if col >= label_from:
                        cells.append((mark_label[col - label_from], f"bold {mark[0]}"))
                    elif b:
                        cells.append((_BRAILLE[b], row_color[col]))
                    else:
                        cells.append(("╌", mark[0]))
            else:
                cells.extend(zip(map(_BRAILLE.__getitem__, row_bits), row_color))
            lines.append(Content.assemble(*runs(cells)))
        return Content("\n").join(lines)

