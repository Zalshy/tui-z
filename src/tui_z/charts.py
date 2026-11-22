"""Charts drawn with text cells: bars, sparklines, braille line/area charts.

All charts use the widget's text color (`text-*`) for the main series and
theme tokens (`"success"`, `"muted"` ...) for anything extra, so they follow
theme switches.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from textual.app import RenderResult
from textual.content import Content
from textual.reactive import reactive
from textual.widget import Widget

from .widgets import Tw


class _Series(list):
    """A list that trims itself to the newest `keep` items in amortized O(1)
    (trims in bulk once it reaches 2x keep, instead of shifting on every push)."""

    __slots__ = ("keep",)

    def __init__(self, values: Sequence[float] = (), keep: int = 2000) -> None:
        super().__init__(list(values)[-keep:])
        self.keep = keep

    def push(self, value: float) -> None:
        self.append(value)
        if len(self) >= 2 * self.keep:
            del self[: -self.keep]

    def tail(self, n: int) -> list[float]:
        return self[-n:] if n > 0 else []


def _runs(cells: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Merge adjacent cells with the same style into one span (far fewer spans)."""
    out: list[tuple[str, str]] = []
    buf: list[str] = []
    style: str | None = None
    for ch, st in cells:
        if st != style and buf:
            out.append(("".join(buf), style or ""))
            buf = []
        style = st
        buf.append(ch)
    if buf:
        out.append(("".join(buf), style or ""))
    return out


def _style(token: str | None) -> str:
    return f"${token}" if token else ""


def _resample(values: Sequence[float], n: int) -> list[float]:
    """Fit a series into n points (linear interpolation either way)."""
    if n <= 0 or not values:
        return []
    if len(values) == 1:
        return [values[0]] * n
    out = []
    scale = (len(values) - 1) / max(1, n - 1)
    for i in range(n):
        x = i * scale
        lo = int(x)
        hi = min(lo + 1, len(values) - 1)
        frac = x - lo
        out.append(values[lo] * (1 - frac) + values[hi] * frac)
    return out


def _fmt(value: float) -> str:
    a = abs(value)
    if a >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if a >= 10_000:
        return f"{value / 1000:.0f}k"
    if a >= 100:
        return f"{value:.0f}"
    return f"{value:.2f}".rstrip("0").rstrip(".") if a < 10 else f"{value:.1f}"


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


class _Range:
    """Y-range for streaming charts.

    `lo`/`hi` given -> fixed. Otherwise *sticky*: it grows (with a little
    headroom) when a new extreme arrives and only shrinks once the visible data
    uses less than `shrink_below` of it, so already-drawn data keeps its shape
    instead of re-scaling on every new point.
    """

    def __init__(self, lo: float | None, hi: float | None, *, sticky: bool = True,
                 headroom: float = 0.08, shrink_below: float = 0.4) -> None:
        self.fixed_lo, self.fixed_hi = lo, hi
        self.sticky = sticky
        self.headroom = headroom
        self.shrink_below = shrink_below
        self._lo: float | None = None
        self._hi: float | None = None

    def reset(self) -> None:
        self._lo = self._hi = None

    def __call__(self, values: Sequence[float]) -> tuple[float, float]:
        if not values:
            return (self.fixed_lo or 0.0, self.fixed_hi or 1.0)
        vlo, vhi = min(values), max(values)
        if self.sticky:
            span = (vhi - vlo) or abs(vhi) or 1.0
            pad = span * self.headroom
            cur_lo, cur_hi = self._lo, self._hi
            if cur_lo is None or cur_hi is None:
                cur_lo, cur_hi = vlo - pad, vhi + pad
            if vlo < cur_lo:
                cur_lo = vlo - pad
            if vhi > cur_hi:
                cur_hi = vhi + pad
            if (vhi - vlo) < (cur_hi - cur_lo) * self.shrink_below:
                cur_lo, cur_hi = vlo - pad, vhi + pad
            self._lo, self._hi = cur_lo, cur_hi
            lo, hi = cur_lo, cur_hi
        else:
            lo, hi = vlo, vhi
        lo = self.fixed_lo if self.fixed_lo is not None else lo
        hi = self.fixed_hi if self.fixed_hi is not None else hi
        if hi <= lo:
            hi, lo = lo + 1, lo - 1
        return lo, hi


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
        self.range = _Range(lo, hi, sticky=not stretch, headroom=0.0)
        self._data = _Series(data, keep)
        self._tw_init(cls)

    @property
    def data(self) -> Sequence[float]:
        """The series (read-only view; use `push` / assign to change)."""
        return self._data

    @data.setter
    def data(self, values: Sequence[float]) -> None:
        self._data = _Series(values, self._data.keep)
        self.refresh()

    def push(self, value: float) -> None:
        self._data.push(value)
        self.refresh()

    def render(self) -> RenderResult:
        width, height = self.content_region.width, max(1, self.content_region.height)
        if not self.data or not width:
            return ""
        values = _resample(self._data, width) if self.stretch else self._data.tail(width)
        lo, hi = self.range(values)
        span = hi - lo
        levels = height * 8
        heights = [round((min(hi, max(lo, v)) - lo) / span * (levels - 1)) + 1 for v in values]
        rows = []
        for row in range(height - 1, -1, -1):
            rows.append("".join(self.BLOCKS[max(0, min(8, h - row * 8))] for h in heights).rjust(width))
        return "\n".join(rows)


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
        self._data = _Series(data, keep)
        self.series: list[tuple[_Series, str]] = [(_Series(d, keep), color) for d, color in series]
        self.marks = list(marks)
        self.fill = fill
        self.axis = axis
        self.range = _Range(lo, hi, sticky=(mode == "stream"))
        self._gutter = 0  # last axis width; avoids a second layout pass
        self._tw_init(cls)

    # -- data ------------------------------------------------------------------
    @property
    def data(self) -> Sequence[float]:
        """The main series (read-only view; use `push` / assign to change)."""
        return self._data

    @data.setter
    def data(self, values: Sequence[float]) -> None:
        self._data = _Series(values, self.keep)
        self.refresh()

    def push(self, value: float, *series_values: float) -> None:
        """Append one point to the main series and, in order, to each extra series."""
        self._data.push(value)
        for (values, _), v in zip(self.series, series_values):
            values.push(v)
        self.refresh()

    def set_series(self, series: Sequence[tuple[Sequence[float], str]]) -> None:
        self.series = [(_Series(d, self.keep), color) for d, color in series]
        self.refresh()

    # -- rendering -------------------------------------------------------------
    def _layout(self, values: _Series, px_w: int) -> list[tuple[int, float]]:
        """(x, value) pairs for one series."""
        if self.mode == "fit":
            return list(enumerate(_resample(values, px_w)))
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
        labels = [_fmt(hi), _fmt((hi + lo) / 2), _fmt(lo)] if self.axis else []
        if self.axis:
            needed = max(map(len, labels)) + 1
            if needed != gutter:
                gutter = self._gutter = needed
                layouts, lo, hi = self._lay_out_all(width - gutter)
                labels = [_fmt(hi), _fmt((hi + lo) / 2), _fmt(lo)]

        cols = width - gutter
        px_w, px_h = cols * 2, height * 4
        bits = [[0] * cols for _ in range(height)]
        color: list[list[str]] = [[""] * cols for _ in range(height)]
        scale = (px_h - 1) / (hi - lo)

        dots = _DOTS
        last_px = px_h - 1
        for layout, token in layouts:
            style = _style(token)
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
                mark_rows[round((hi - value) * scale) // 4] = (_style(token), label)

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
            lines.append(Content.assemble(*_runs(cells)))
        return Content("\n").join(lines)
