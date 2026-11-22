"""`TwApp`: a Textual App that understands utility classes."""

from __future__ import annotations

from typing import ClassVar

from textual.app import App
from textual.css.stylesheet import CssSource
from textual.dom import DOMNode
from textual.widget import Widget

from . import registry
from .engine import BREAKPOINTS, TailError
from .theme import THEME_NAMES, THEMES, fill_extra_tokens

SOURCE_KEY = ("tui_z", "utilities")


class TwApp(App):
    """Base class for tui_z apps.

    - registers the tui_z themes and selects `TW_THEME`
    - compiles every `cls=` string it sees into the stylesheet, just before the
      widgets using it are styled (no unstyled first frame)
    - sets screen breakpoint classes so `sm: md: lg: xl:` variants work
    """

    TW_THEME: ClassVar[str] = "terminal"
    TW_MAX_CHUNKS: ClassVar[int] = 32
    TW_THEMES: ClassVar[tuple[str, ...]] = THEME_NAMES
    """Themes cycled by `action_next_theme` / `action_prev_theme`."""

    HORIZONTAL_BREAKPOINTS = [(0, "-tw-base")] + [
        (width, f"-tw-{name}") for name, width in BREAKPOINTS.items()
    ]

    def __init__(self, *args, **kwargs) -> None:
        self._tw_version = 0
        self._tw_chunks = 0
        super().__init__(*args, **kwargs)
        for theme in THEMES:
            self.register_theme(theme)
        self.theme = self.TW_THEME

    # -- themes -------------------------------------------------------------
    def cycle_theme(self, step: int = 1) -> str:
        names = list(self.TW_THEMES)
        index = names.index(self.theme) if self.theme in names else -step
        self.theme = names[(index + step) % len(names)]
        return self.theme

    def action_next_theme(self) -> None:
        self.cycle_theme(1)

    def action_prev_theme(self) -> None:
        self.cycle_theme(-1)

    # -- theme variables ---------------------------------------------------
    def get_css_variables(self) -> dict[str, str]:
        variables = fill_extra_tokens(super().get_css_variables())
        self.theme_variables = variables
        return variables

    # -- utility stylesheet -------------------------------------------------
    def tw_flush(self) -> None:
        """Push newly registered utility classes into the stylesheet.

        Incremental: only the new rules are parsed and appended (Textual's
        `reparse()` would re-parse every widget's CSS, ~20 ms). Each flush is a
        small source chunk; chunks are consolidated when they pile up.
        """
        new = registry.since(self._tw_version)
        if not new:
            return
        variables = self.theme_variables or self.get_css_variables()
        for compiled in new:
            for var, utility in compiled.variables:
                if var not in variables:
                    registry.discard(compiled.name)
                    known = ", ".join(sorted(k for k in variables if "-" not in k))
                    raise TailError(
                        f"unknown color '{var}' in utility '{utility}'. "
                        f"Theme colors: {known} (plus -lighten-N / -darken-N / -muted variants)"
                    )
        self._tw_version = registry.version()
        css = "\n".join(c.css for c in new if c.css)
        if css:
            self._tw_add_css(css)

    def _tw_add_css(self, css: str) -> None:
        stylesheet = self.stylesheet
        if self._tw_chunks >= self.TW_MAX_CHUNKS:  # consolidate into one source
            for key in [k for k in stylesheet.source if k[0] == SOURCE_KEY[0]]:
                del stylesheet.source[key]
            self._tw_chunks = 0
            css = registry.stylesheet()
            stylesheet.add_source(css, read_from=(SOURCE_KEY[0], "utilities-0"), is_default_css=False)
            self._tw_chunks = 1
            stylesheet.reparse()
            return
        key = (SOURCE_KEY[0], f"utilities-{self._tw_chunks}")
        self._tw_chunks += 1
        try:
            # Fast path (Textual internals): parse just this chunk and append.
            if stylesheet._require_parse or stylesheet._rules is None:
                raise LookupError  # a full parse is pending anyway
            rules = stylesheet._parse_rules(css, key)
            stylesheet.source[key] = CssSource(css, False, 0, "")
            stylesheet._rules.extend(rules)
            stylesheet._rules_map = None
        except (AttributeError, LookupError, TypeError):
            stylesheet.add_source(css, read_from=key, is_default_css=False)
            stylesheet.parse()

    def _register(self, parent: DOMNode, *widgets: Widget, **kwargs) -> list[Widget]:
        # Widgets created in compose() have registered their classes by now;
        # compile them all in one reparse before Textual applies styles.
        self.tw_flush()
        return super()._register(parent, *widgets, **kwargs)
