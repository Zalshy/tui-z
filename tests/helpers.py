"""Small helpers for reading what widgets render (import: `from helpers import plain`)."""

from __future__ import annotations


def plain_line(widget, y: int) -> str:
    """Text of one rendered line of a Line API widget (Table, LogView...)."""
    return "".join(seg.text for seg in widget.render_line(y))


def plain(widget) -> str:
    """Text a widget renders, without styles."""
    rendered = widget.render()
    return getattr(rendered, "plain", None) or str(rendered)
