"""Every use of Textual's private API, in one place.

tui-z reaches into a few Textual internals for speed (incremental stylesheet
updates, the named-color table). Keeping them here means a Textual upgrade can
only break this file, and `tests/core/test_textual_compat.py` says exactly
which internal moved. Each helper has a slower public fallback.

Any module may import this one; it imports nothing from tui-z.
"""

from __future__ import annotations

import threading
from typing import Any

from textual.color import Color, ColorParseError
from textual.css.stylesheet import CssSource, Stylesheet

try:  # Textual's table of named colors (red, ansi_bright_green, ...)
    from textual._color_constants import COLOR_NAME_TO_RGB as NAMED_COLORS
except ImportError:  # pragma: no cover - fall back to a parse probe
    NAMED_COLORS = None


def is_named_color(name: str) -> bool:
    """True for a CSS / ANSI color name Textual knows (`red`, `ansi_bright_green`)."""
    if NAMED_COLORS is not None:
        return name in NAMED_COLORS
    # NB: a failed parse runs a fuzzy "did you mean" search (~0.8 ms), which is
    # why the table above is preferred.
    try:  # pragma: no cover - only without the private table
        Color.parse(name)
    except ColorParseError:  # pragma: no cover
        return False
    return True  # pragma: no cover


def can_append_rules(stylesheet: Stylesheet) -> bool:
    """True when `append_rules` can take the fast path on this stylesheet."""
    return (
        hasattr(stylesheet, "_parse_rules")
        and getattr(stylesheet, "_require_parse", True) is False
        and isinstance(getattr(stylesheet, "_rules", None), list)
    )


def append_rules(stylesheet: Stylesheet, css: str, key: tuple[str, str]) -> None:
    """Add a chunk of CSS to a parsed stylesheet.

    Fast path: parse only this chunk and append its rules (~0.4 ms), instead of
    `Stylesheet.parse()` re-parsing every source (~20 ms on a real app).
    Falls back to the public API when the internals aren't as expected.
    """
    if can_append_rules(stylesheet):
        try:
            rules = stylesheet._parse_rules(css, key)
            stylesheet.source[key] = CssSource(css, False, 0, "")
            stylesheet._rules.extend(rules)
            stylesheet._rules_map = None
            return
        except (AttributeError, LookupError, TypeError):  # pragma: no cover - internals changed
            pass
    stylesheet.add_source(css, read_from=key, is_default_css=False)
    stylesheet.parse()


def on_app_thread(app: Any) -> bool:
    """True when called from the thread running `app`'s event loop."""
    thread_id = getattr(app, "_thread_id", None)
    return thread_id is None or thread_id == threading.get_ident()
