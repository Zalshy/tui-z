"""Keeps one app's stylesheet in sync with the process-wide class registry."""

from __future__ import annotations

from collections.abc import Mapping

from textual.css.stylesheet import Stylesheet

from .._textual import append_rules
from ..styling.errors import TailError
from . import registry

SOURCE_PREFIX = "tui_z"


class UtilityStylesheet:
    """Incrementally pushes newly compiled class strings into a stylesheet.

    Each flush adds a small source chunk (only the new rules are parsed). Once
    `max_chunks` pile up they are consolidated into a single source.
    """

    def __init__(self, max_chunks: int = 32) -> None:
        self.max_chunks = max_chunks
        self.version = 0  # how far into the registry this stylesheet has flushed
        self.chunks = 0

    def flush(self, stylesheet: Stylesheet, variables: Mapping[str, str]) -> None:
        """Add every class string registered since the last flush.

        Raises `TailError` if one uses a theme color missing from `variables`.
        """
        new = registry.since(self.version)
        if not new:
            return
        for compiled in new:
            for var, utility in compiled.variables:
                if var not in variables:
                    registry.discard(compiled.name)
                    known = ", ".join(sorted(k for k in variables if "-" not in k))
                    raise TailError(
                        f"unknown color '{var}' in utility '{utility}'. "
                        f"Theme colors: {known} (plus -lighten-N / -darken-N / -muted variants)"
                    )
        self.version = registry.version()
        css = "\n".join(c.css for c in new if c.css)
        if css:
            self._add(stylesheet, css)

    def _add(self, stylesheet: Stylesheet, css: str) -> None:
        if self.chunks >= self.max_chunks:  # consolidate into one source
            for key in [k for k in stylesheet.source if k[0] == SOURCE_PREFIX]:
                del stylesheet.source[key]
            stylesheet.add_source(registry.stylesheet(), read_from=(SOURCE_PREFIX, "utilities-0"),
                                  is_default_css=False)
            self.chunks = 1
            stylesheet.reparse()
            return
        key = (SOURCE_PREFIX, f"utilities-{self.chunks}")
        self.chunks += 1
        append_rules(stylesheet, css, key)
