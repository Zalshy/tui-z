"""`TwApp`: a Textual App that understands utility classes.

This is the top layer: it may use anything in tui-z (components included).
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import App
from textual.dom import DOMNode
from textual.widget import Widget

from .core.stylesheet import UtilityStylesheet
from .styling.themes import THEME_NAMES, THEMES, fill_extra_tokens
from .styling.utilities import BREAKPOINTS


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
        self._tw_sheet = UtilityStylesheet(self.TW_MAX_CHUNKS)
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
        `reparse()` would re-parse every widget's CSS, ~20 ms).
        """
        self._tw_sheet.flush(self.stylesheet, self.theme_variables or self.get_css_variables())

    def _register(self, parent: DOMNode, *widgets: Widget, **kwargs) -> list[Widget]:
        # Widgets created in compose() have registered their classes by now;
        # compile them all in one reparse before Textual applies styles.
        self.tw_flush()
        return super()._register(parent, *widgets, **kwargs)
