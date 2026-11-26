"""Shared chart maths: series buffers, y-ranges, resampling, run merging.

Pure functions and small classes with no widget code, so they are unit-tested
directly (see tests/components/charts/test_scale.py).
"""

from __future__ import annotations

from collections.abc import Sequence


class Series(list):
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


def runs(cells: list[tuple[str, str]]) -> list[tuple[str, str]]:
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


def token_style(token: str | None) -> str:
    return f"${token}" if token else ""


def resample(values: Sequence[float], n: int) -> list[float]:
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


def fmt(value: float) -> str:
    a = abs(value)
    if a >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if a >= 10_000:
        return f"{value / 1000:.0f}k"
    if a >= 100:
        return f"{value:.0f}"
    return f"{value:.2f}".rstrip("0").rstrip(".") if a < 10 else f"{value:.1f}"



class Range:
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
