"""Inline styles: class strings applied to *spans of text* instead of widgets.

Line-based components (Table, LogView) draw many cells in one widget, so their
per-cell / per-line `cls` can't become CSS classes. This module interprets the
text-level subset of utilities into Textual `Content` style strings:

    text-{c} bg-{c}[/NN]  bold italic underline strike reverse dim
    uppercase lowercase capitalize tracking-wide tracking-wider

plus, for column specs, `w-N` `w-fr` `w-Nfr` `w-auto` and `text-left/center/right`,
and for rows, the `odd:` `even:` `hover:` variants.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .engine import split_variants
from .errors import TailError
from .utilities import TEXT_STYLES, TRANSFORMS, add_transform, color_value

_ALIGN = {"text-left": "left", "text-center": "center", "text-right": "right"}


@dataclass(frozen=True)
class Inline:
    style: str  # Textual Content style, e.g. "bold $success on $success 20%"
    transforms: tuple[str, ...]
    variables: tuple[str, ...]  # theme variables used (for validation)


@lru_cache(maxsize=2048)
def inline(cls: str) -> Inline:
    """Interpret a class string as an inline text style. Last utility wins."""
    fg = bg = None
    flags: dict[str, bool] = {}
    transforms: dict[str, None] = {}
    sources: dict[str, str] = {}
    for util in cls.split():
        if util in TRANSFORMS:
            add_transform(transforms, util)
        elif util in TEXT_STYLES:
            flags[util] = True
        elif util == "font-normal":
            flags["bold"] = False
        elif util == "truncate":
            pass  # cells always truncate
        elif util.startswith("text-") and util not in _ALIGN:
            fg = color_value(util[5:], sources, util)
        elif util.startswith("bg-"):
            bg = color_value(util[3:], sources, util)
        else:
            raise TailError(f"'{util}' can't style a span of text (in cls={cls!r})")
    parts = [f for f, on in flags.items() if on]
    if fg:
        parts.append(fg)
    if bg:
        parts.append(f"on {bg}")
    return Inline(" ".join(parts), tuple(transforms), tuple(sources))


@dataclass(frozen=True)
class ColumnSpec:
    width: int | None  # fixed cells, or None for fractional
    fr: int  # fraction weight when width is None
    align: str
    style: Inline


@lru_cache(maxsize=512)
def column(cls: str) -> ColumnSpec:
    """`"w-14 text-right text-success bold"` -> width/align + inline style."""
    width: int | None = None
    fr = 1
    align = "left"
    rest = []
    for util in cls.split():
        if util in _ALIGN:
            align = _ALIGN[util]
        elif util in ("w-fr", "grow"):
            width, fr = None, 1
        elif util.startswith("w-"):
            raw = util[2:]
            if raw.isdigit():
                width = int(raw)
            elif raw.endswith("fr") and raw[:-2].isdigit():
                width, fr = None, int(raw[:-2])
            else:
                raise TailError(f"column width must be w-N, w-fr or w-Nfr, got '{util}'")
        else:
            rest.append(util)
    return ColumnSpec(width, fr, align, inline(" ".join(rest)))


@lru_cache(maxsize=512)
def row_variants(cls: str) -> dict[str, Inline]:
    """`"odd:bg-panel/40 hover:bg-boost text-muted"` -> {"": ..., "odd": ..., "hover": ...}."""
    groups: dict[str, list[str]] = {}
    for token in cls.split():
        variants, util = split_variants(token)
        key = ":".join(variants)
        if key not in ("", "odd", "even", "hover"):
            raise TailError(f"row variants are odd:, even:, hover: — got '{token}'")
        groups.setdefault(key, []).append(util)
    return {key: inline(" ".join(utils)) for key, utils in groups.items()}


def layout_columns(specs: list[ColumnSpec], width: int, gap: int = 1) -> list[int]:
    """Resolve column widths for a total width (fixed first, fr share the rest)."""
    fixed = sum(s.width for s in specs if s.width is not None)
    gaps = gap * max(0, len(specs) - 1)
    frs = [s.fr for s in specs if s.width is None]
    free = max(0, width - fixed - gaps)
    out: list[int] = []
    total_fr = sum(frs) or 1
    given = 0
    fr_seen = 0
    for s in specs:
        if s.width is not None:
            out.append(s.width)
        else:
            fr_seen += s.fr
            share = free * fr_seen // total_fr - given  # exact split, no rounding drift
            given += share
            out.append(share)
    return out
