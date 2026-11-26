"""Data components: tables, logs and feeds.

`Table` and `LogView` are line-based: one widget, virtualized rendering,
cached lines.

`Table` and `LogView` draw every row/line inside a single widget (Textual's
Line API) instead of mounting widgets per row or cell:

- only visible lines are rendered (10k-line logs cost the same as 10),
- each rendered line is cached until its data, width or the theme changes,
- adding a row is a list append + refresh, not a mount + layout.

Styling still uses class strings; per-cell/per-line `cls` is interpreted as an
inline text style (see `tui_z.styling.inline`).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Hashable, Iterable, Sequence
from datetime import datetime
from itertools import count
from typing import ClassVar

from textual import events
from textual.app import RenderResult
from textual.content import Content
from textual.geometry import Size
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.visual import Visual
from textual.widget import Widget

from ..core.tw import Tw, transform_markup
from ..styling.engine import apply_transforms, merge
from ..styling.errors import TailError
from ..styling.inline import Inline, column, inline, layout_columns, row_variants

type Cell = str | tuple[str, str]
"""A table cell: plain text/markup, or (text, cls) to style that cell."""

_ids = count()


def _fit(content: Content, width: int, align: str) -> Content:
    """Truncate (with ellipsis) and pad a single-line Content to exactly `width`."""
    if width <= 0:
        return Content("")
    if content.cell_length > width:
        content = content.truncate(width, ellipsis=True)
    gap = width - content.cell_length
    if gap <= 0:
        return content
    if align == "right":
        return content.pad_left(gap)
    if align == "center":
        left = gap // 2
        return content.pad_left(left).pad_right(gap - left)
    return content.pad_right(gap)


def _markup(text: str, transforms: tuple[str, ...]) -> Content:
    if transforms:
        text = transform_markup(text, transforms)
    return Content.from_markup(text)


class LineView(Tw, ScrollView):
    """Base for virtualized, line-cached components. Subclasses implement
    `line_count`, `line_key` and `build_line`."""

    DEFAULT_CLS = "w-full h-auto"

    def __init__(self, cls: str = "", *, id: str | None = None) -> None:
        super().__init__(id=id)
        self._strips: dict[Hashable, Strip] = {}
        self._tw_init(cls)

    # -- subclass API --------------------------------------------------------
    def line_count(self) -> int:
        raise NotImplementedError

    def line_key(self, index: int) -> Hashable:
        """Identity of what line `index` shows; same key -> cached strip reused."""
        raise NotImplementedError

    def build_line(self, index: int, width: int) -> Content:
        raise NotImplementedError

    # -- plumbing ------------------------------------------------------------
    def _check_inline(self, *styles: Inline) -> None:
        """Validate theme colors used by inline styles (once the app is known)."""
        if not self.is_attached:
            return
        variables = getattr(self.app, "theme_variables", None) or {}
        for style in styles:
            for var in style.variables:
                if var not in variables:
                    raise TailError(f"unknown color '{var}' in {type(self).__name__} cls")

    def lines_changed(self) -> None:
        """Call after mutating data: resizes the virtual canvas and repaints."""
        self.virtual_size = Size(1, self.line_count())
        if len(self._strips) > 4 * self.line_count() + 256:
            self._strips.clear()
        self.refresh()

    def on_mount(self) -> None:
        self.virtual_size = Size(1, self.line_count())

    def notify_style_update(self) -> None:
        super().notify_style_update()
        self._strips.clear()  # theme / class change -> colors may differ

    def render_line(self, y: int) -> Strip:
        scroll_x, scroll_y = self.scroll_offset
        index = scroll_y + y
        width = self.scrollable_content_region.width
        rich_style = self.rich_style
        if index >= self.line_count() or width <= 0:
            return Strip.blank(width, rich_style)
        key = (self.line_key(index), width)
        strip = self._strips.get(key)
        if strip is None:
            content = self.build_line(index, width)
            strips = Visual.to_strips(self, content, width, 1, self.visual_style, pad=True)
            strip = strips[0] if strips else Strip.blank(width, rich_style)
            self._strips[key] = strip
        return strip.crop_extend(scroll_x, scroll_x + width, rich_style).apply_offsets(scroll_x, index)


# --------------------------------------------------------------------------- #
# LogView
# --------------------------------------------------------------------------- #

class LogView(LineView):
    """Tail-style log: time · tag · message. Keeps the newest `max_lines`.

    log.write("SELL landed [$muted]slot 371,911[/]", tag="EXIT", tag_cls="bg-error/20 text-error")

    Messages are Textual markup; `tag_cls` / `msg_cls` are inline class strings
    (text-*, bg-*, bold, uppercase ...).
    """

    DEFAULT_CLS = "w-full h-fr scrollbar-thin"
    TIME_CLS: ClassVar[str] = "text-muted"
    TAG_CLS: ClassVar[str] = "bold uppercase bg-primary/15 text-primary"

    def __init__(self, cls: str = "", *, max_lines: int = 1000, time_format: str = "%H:%M:%S",
                 tag_width: int = 7, id: str | None = None) -> None:
        self._lines: deque[tuple[int, Content]] = deque(maxlen=max_lines)
        self.time_format = time_format
        self.tag_width = tag_width
        self._time_style = inline(self.TIME_CLS)
        super().__init__(cls, id=id)

    @property
    def max_lines(self) -> int:
        return self._lines.maxlen or 0

    def write(self, message: str, *, tag: str | None = None, tag_cls: str = "",
              msg_cls: str = "", time: datetime | None = None) -> None:
        parts = [Content((time or datetime.now()).strftime(self.time_format)).stylize(self._time_style.style), Content(" ")]
        if tag is not None:
            tag_style = inline(merge(self.TAG_CLS, tag_cls))
            self._check_inline(tag_style)
            pill = _fit(Content(apply_transforms(tag, tag_style.transforms)), self.tag_width, "center")
            parts += [pill.stylize(tag_style.style), Content(" ")]
        msg_style = inline(msg_cls)
        self._check_inline(msg_style)
        body = _markup(message, msg_style.transforms)
        parts.append(body.stylize_before(msg_style.style) if msg_style.style else body)

        at_end = self.scroll_offset.y >= self.max_scroll_y
        self._lines.append((next(_ids), Content("").join(parts)))
        self.lines_changed()
        if at_end:
            self.scroll_end(animate=False, immediate=False)

    def clear(self) -> None:
        self._lines.clear()
        self._strips.clear()
        self.lines_changed()

    def line_count(self) -> int:
        return len(self._lines)

    def line_key(self, index: int) -> Hashable:
        return self._lines[index][0]

    def build_line(self, index: int, width: int) -> Content:
        return _fit(self._lines[index][1], width, "left")


# --------------------------------------------------------------------------- #
# Table
# --------------------------------------------------------------------------- #

class Table(LineView):
    """A light, fast table. Columns carry width/alignment/style cls.

    Table(
        [("#", "w-4 text-muted"), ("Wallet", "w-14 text-info"), ("PnL", "w-fr text-right text-success")],
        [["#1", "0x87cc…aa20", ("+$312k", "bold")], ...],
        row_cls="hover:bg-boost odd:bg-panel/40",
    )

    Column cls: `w-N` / `w-fr` / `w-Nfr`, `text-left/center/right`, plus inline
    styles. Cells may be markup or `(text, cls)`. Row cls supports `odd:`,
    `even:` and `hover:`. Rows render virtually, so thousands are fine.
    """

    DEFAULT_CLS = "w-full h-auto"
    HEADER_CLS: ClassVar[str] = "text-muted uppercase"
    RULE_CLS: ClassVar[str] = "text-line"
    GAP: ClassVar[int] = 1

    def __init__(self, columns: Sequence[tuple[str, str]], rows: Iterable[Sequence[Cell]] = (),
                 cls: str = "", *, row_cls: str = "", header_cls: str = "", header: bool = True,
                 max_rows: int | None = None, id: str | None = None) -> None:
        self.titles = [title for title, _ in columns]
        self.specs = [column(col_cls) for _, col_cls in columns]
        self.header_style = inline(merge(self.HEADER_CLS, header_cls))
        self.rule_style = inline(self.RULE_CLS)
        self.row_styles = row_variants(row_cls)
        self.show_header = header
        self.max_rows = max_rows
        self._rows: list[tuple[int, tuple[tuple[str, Inline], ...]]] = []
        self._hover: int | None = None
        super().__init__(cls, id=id)
        self.set_rows(rows)

    # -- data API --------------------------------------------------------------
    def _make(self, cells: Sequence[Cell]) -> tuple[int, tuple[tuple[str, Inline], ...]]:
        out = []
        for cell in cells[: len(self.specs)]:
            text, cell_cls = (cell, "") if isinstance(cell, str) else cell
            style = inline(cell_cls)
            self._check_inline(style)
            out.append((text, style))
        return next(_ids), tuple(out)

    @property
    def row_count(self) -> int:
        return len(self._rows)

    def add_row(self, cells: Sequence[Cell], *, top: bool = False) -> None:
        row = self._make(cells)
        if top:
            self._rows.insert(0, row)
        else:
            self._rows.append(row)
        if self.max_rows is not None and len(self._rows) > self.max_rows:
            if top:
                del self._rows[self.max_rows:]
            else:
                del self._rows[: len(self._rows) - self.max_rows]
        self.lines_changed()

    def set_rows(self, rows: Iterable[Sequence[Cell]]) -> None:
        self._rows = [self._make(r) for r in rows]
        if self.max_rows is not None:
            del self._rows[self.max_rows:]
        self.lines_changed()

    def update_row(self, index: int, cells: Sequence[Cell]) -> None:
        self._rows[index] = self._make(cells)
        self.lines_changed()

    def clear(self) -> None:
        self.set_rows([])

    # -- lines -----------------------------------------------------------------
    @property
    def _head(self) -> int:
        return 2 if self.show_header else 0

    def line_count(self) -> int:
        return self._head + len(self._rows)

    def line_key(self, index: int) -> Hashable:
        if index < self._head:
            return ("header", index)
        r = index - self._head
        return (self._rows[r][0], r % 2, r == self._hover)

    def build_line(self, index: int, width: int) -> Content:
        if index < self._head:
            if index == 1:
                return Content("─" * width).stylize(self.rule_style.style)
            cells = [(title, self.header_style) for title in self.titles]
            return self._join(cells, width, header=True)
        r = index - self._head
        line = self._join(self._rows[r][1], width)
        styles = [self.row_styles.get(""), self.row_styles.get("odd" if r % 2 == 0 else "even")]
        if r == self._hover:
            styles.append(self.row_styles.get("hover"))
        for style in styles:
            if style and style.style:
                line = line.stylize_before(style.style)
        return line

    def _join(self, cells: Sequence[tuple[str, Inline]], width: int, header: bool = False) -> Content:
        widths = layout_columns(self.specs, width, self.GAP)
        parts: list[Content] = []
        for i, (spec, w) in enumerate(zip(self.specs, widths)):
            if i:
                parts.append(Content(" " * self.GAP))
            if i < len(cells):
                text, cell_style = cells[i]
                transforms = spec.style.transforms + cell_style.transforms
                content = _markup(text, transforms)
                style = f"{spec.style.style} {cell_style.style}".strip()
                if header:
                    style = cell_style.style  # header color/style wins over column color
                if style:
                    content = content.stylize_before(style)
            else:
                content = Content("")
            parts.append(_fit(content, w, spec.align))
        line = Content("").join(parts)
        return _fit(line, width, "left")

    # -- hover -----------------------------------------------------------------
    def _set_hover(self, row: int | None) -> None:
        if row != self._hover and "hover" in self.row_styles:
            self._hover = row
            self.refresh()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        r = event.y + self.scroll_offset.y - self._head
        self._set_hover(r if 0 <= r < len(self._rows) else None)

    def on_leave(self, event: events.Leave) -> None:
        self._set_hover(None)


# --------------------------------------------------------------------------- #
# Ticker
# --------------------------------------------------------------------------- #

class Ticker(Tw, Widget):
    """A scrolling one-line feed. Items are Textual markup (`[$success]+8%[/]`).

    Ticker(["[b $error]LIVE FEED[/]", "VETO $NOVAKIT", ...], "bg-surface")
    """

    DEFAULT_CLS = "w-full h-1"

    def __init__(self, items: Sequence[str] = (), cls: str = "", *, separator: str = "   ·   ",
                 speed: float = 0.12, id: str | None = None) -> None:
        super().__init__(id=id)
        self.separator = separator
        self.speed = speed
        self._offset = 0
        self._tw_init(cls)
        self.set_items(items)

    def set_items(self, items: Sequence[str]) -> None:
        sep = Content.from_markup(f"[$line]{self.separator}[/]")
        self._content = sep.join([Content.from_markup(i) for i in items]) + sep if items else Content("")
        self._loop: Content | None = None  # rebuilt lazily for the current width
        self._loop_width = -1
        self.refresh()

    def on_mount(self) -> None:
        self.set_interval(self.speed, self._advance)

    def _advance(self) -> None:
        if self._content.cell_length:
            self._offset = (self._offset + 1) % len(self._content)
            self.refresh()

    def render(self) -> RenderResult:
        width = self.content_region.width
        if not len(self._content):
            return ""
        if self._loop is None or self._loop_width != width:
            repeats = -(-(width + len(self._content)) // len(self._content))  # ceil
            self._loop = Content("").join([self._content] * repeats)
            self._loop_width = width
        return self._loop[self._offset: self._offset + width]

