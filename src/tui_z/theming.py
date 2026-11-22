"""Theme switching UI."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from textual import events
from textual.theme import Theme

from .engine import merge
from .theme import THEME_NAMES
from .widgets import Box, Text


class _ThemeItem(Text):
    def __init__(self, theme: str, cls: str) -> None:
        self.theme_name = theme
        super().__init__(theme, cls, markup=False)

    def on_click(self, event: events.Click) -> None:
        event.stop()
        self.app.theme = self.theme_name


class ThemeSwitcher(Box):
    """Clickable list of themes; highlights the active one and follows
    `app.theme` changes made elsewhere (key bindings, command palette).

    ThemeSwitcher()                          # every tui-z theme, vertical
    ThemeSwitcher(["tokyo-night", "catppuccin-mocha"], cls="row")
    """

    DEFAULT_CLS = "w-full h-auto"
    ITEM_CLS: ClassVar[str] = "w-full h-1 px-1 text-muted cursor-pointer hover:bg-boost hover:text-foreground"
    ACTIVE_CLS: ClassVar[str] = "bg-primary/20 text-primary bold"

    def __init__(self, themes: Sequence[str] = THEME_NAMES, cls: str = "", *,
                 item_cls: str = "", active_cls: str = "", id: str | None = None) -> None:
        self.item_cls = merge(self.ITEM_CLS, item_cls)
        self.active_cls = merge(self.item_cls, self.ACTIVE_CLS, active_cls)
        self.items = [_ThemeItem(name, self.item_cls) for name in themes]
        super().__init__(*self.items, cls=cls, id=id)

    def on_mount(self) -> None:
        self.app.theme_changed_signal.subscribe(self, self._on_theme)
        self._highlight(self.app.theme)

    def _on_theme(self, theme: Theme) -> None:
        self._highlight(theme.name)

    def _highlight(self, name: str) -> None:
        for item in self.items:
            item.set_cls(self.active_cls if item.theme_name == name else self.item_cls)
            item.update(f"● {item.theme_name}" if item.theme_name == name else f"  {item.theme_name}")
