"""`Tw`: the mixin that gives any widget a `cls=` class string.

Every component takes `cls=` (a utility class string). Components ship their
look as `DEFAULT_CLS`; your `cls` is merged after it, so for any property you
set, yours wins:

    Badge("LIVE")                                  # default: primary pill
    Badge("BOT", cls="bg-warning/20 text-warning") # same badge, amber

Use `tw(widget, cls)` to put utility classes on any Textual widget.
"""

from __future__ import annotations

import re
from typing import ClassVar

from textual.app import active_app
from textual.widget import Widget

from ..styling.engine import Compiled, apply_transforms, compile_cls, merge
from . import registry


def _attach(widget: Widget, cls: str, previous: Compiled | None) -> Compiled:
    compiled = compile_cls(cls)
    registry.add(compiled)
    if widget.is_attached:  # changing cls on a live widget: compile now
        try:
            app = active_app.get()
        except LookupError:  # pragma: no cover - attached widgets always have an app
            app = None
        if app is not None and hasattr(app, "tw_flush"):
            app.tw_flush()
    if not widget.is_attached:
        # Not mounted yet: Textual styles the widget when it is registered, so
        # an immediate restyle here would be wasted work (~0.4 ms per widget).
        if previous is not None and previous.name != compiled.name:
            widget.remove_class(previous.name, update=False)
        widget.add_class(compiled.name, update=False)
    elif previous is None:
        widget.add_class(compiled.name)
    elif previous.name != compiled.name:
        # swap in ONE class update (remove + add would restyle the node twice)
        widget.set_classes([c for c in widget.classes if c != previous.name] + [compiled.name])
    return compiled


def tw[W: Widget](widget: W, cls: str) -> W:
    """Apply utility classes to any Textual widget: `tw(DataTable(), "h-fr border")`."""
    widget._tw_compiled = _attach(widget, cls, getattr(widget, "_tw_compiled", None))  # type: ignore[attr-defined]
    return widget


class Tw:
    """Mixin giving a widget `cls=` support. Put it before the Widget base."""

    DEFAULT_CLS: ClassVar[str] = ""
    _tw_compiled: Compiled | None = None
    _tw_cls: str = ""

    def _tw_init(self, cls: str | None) -> None:
        self.set_cls(cls or "")

    @classmethod
    def base_cls(cls) -> str:
        """DEFAULT_CLS of the whole class hierarchy, parents first.

        Subclasses *extend* their parent's look: `class Card(Row): DEFAULT_CLS
        = "border"` keeps Row's `row w-full h-auto` and adds `border`.
        """
        cached = cls.__dict__.get("_tw_base_cls")
        if cached is None:
            cached = merge(*[k.__dict__["DEFAULT_CLS"] for k in reversed(cls.__mro__) if "DEFAULT_CLS" in k.__dict__])
            cls._tw_base_cls = cached
        return cached

    @property
    def cls(self) -> str:
        """The user part of the class string (without DEFAULT_CLS)."""
        return self._tw_cls

    @property
    def tw_class(self) -> str:
        """The generated CSS class (`tw-<hash>`) currently on the widget."""
        return self._tw_compiled.name if self._tw_compiled else ""

    def set_cls(self, cls: str) -> None:
        """Replace the user class string; DEFAULT_CLS still applies underneath."""
        if cls == self._tw_cls and self._tw_compiled is not None:
            return  # unchanged: skip compile lookup + class churn
        self._tw_cls = cls
        self._tw_compiled = _attach(self, merge(self.base_cls(), cls), self._tw_compiled)  # type: ignore[arg-type]
        self._tw_changed()

    def add_cls(self, cls: str) -> None:
        """Append utilities (they win over existing ones)."""
        self.set_cls(merge(self._tw_cls, cls))

    def _tw_changed(self) -> None:
        """Hook for components that render content transforms."""

    @property
    def transforms(self) -> tuple[str, ...]:
        return self._tw_compiled.transforms if self._tw_compiled else ()


_MARKUP_TAG = re.compile(r"(\[[^\[\]]*\])")


def transform_markup(text: str, transforms: tuple[str, ...]) -> str:
    """Apply content transforms to text but not to [markup] tags."""
    if not transforms:
        return text
    parts = _MARKUP_TAG.split(text)
    return "".join(p if _MARKUP_TAG.fullmatch(p) else apply_transforms(p, transforms) for p in parts)
