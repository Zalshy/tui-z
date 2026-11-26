"""Interactive controls: buttons, toggles, inputs and the theme switcher."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from textual import events
from textual.message import Message
from textual.theme import Theme
from textual.widgets import Static

from ..core.tw import Tw
from ..styling.engine import apply_transforms, merge
from ..styling.themes import THEME_NAMES
from .content import Text
from .layout import Box


class Button(Tw, Static, can_focus=True):
    """Clickable / focusable button. Posts `Button.Pressed`.

    Button("BUY YES", "text-success border-success")
    """

    DEFAULT_CLS = (
        "w-auto h-auto px-2 border border-line text-foreground bold uppercase content-center cursor-pointer "
        "hover:bg-boost hover:border-muted focus:border-primary focus:text-primary"
    )

    class Pressed(Message):
        def __init__(self, button: Button) -> None:
            super().__init__()
            self.button = button

        @property
        def control(self) -> Button:
            return self.button

    BINDINGS = [("enter", "press", "Press"), ("space", "press", "Press")]

    def __init__(self, label: str, cls: str = "", *, id: str | None = None, name: str | None = None) -> None:
        self._label = label
        super().__init__("", id=id, name=name)
        self._tw_init(cls)

    def _tw_changed(self) -> None:
        self.update(apply_transforms(self._label, self.transforms))

    @property
    def label(self) -> str:
        return self._label

    def on_click(self) -> None:
        self.action_press()

    def action_press(self) -> None:
        self.post_message(self.Pressed(self))


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
