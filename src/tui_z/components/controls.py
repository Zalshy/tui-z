"""Interactive controls: buttons, toggles, inputs and the theme switcher."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, ClassVar

from textual import events
from textual.app import RenderResult
from textual.content import Content
from textual.message import Message
from textual.reactive import reactive
from textual.theme import Theme
from textual.widget import Widget
from textual.widgets import Input as TextualInput
from textual.widgets import Select as TextualSelect
from textual.widgets import Static

from ..core.tw import Tw, check_inline, tw
from ..styling.engine import apply_transforms, merge
from ..styling.inline import inline
from ..styling.themes import THEME_NAMES
from .content import Text
from .layout import Box


class Button(Tw, Static, can_focus=True):
    """Clickable / focusable button. Posts `Button.Pressed`.

    Button("BUY YES", "text-success border-success")
    """

    DEFAULT_CLS = (
        "w-auto h-auto px-2 border border-line text-foreground bold uppercase content-center cursor-pointer "
        "hover:bg-boost hover:border-muted focus:border-primary focus:text-primary "
        "bg-transparent min-w-0"  # reset what Textual's `Button { }` CSS would add (+ line_pad below)
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
        # Textual CSS can't set `line-pad: 0` (it only takes 1+), so reset what
        # Textual's `Button { }` CSS adds with an inline style instead.
        self.styles.line_pad = 0
        self._tw_init(cls)

    def _tw_changed(self) -> None:
        self.update(apply_transforms(self._label, self.transforms))

    @property
    def label(self) -> str:
        return self._label

    def on_click(self, event: events.Click) -> None:
        event.stop()  # a press is not also a click on whatever contains the button
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


# --------------------------------------------------------------------------- #
# Toggles
# --------------------------------------------------------------------------- #

class _Toggle(Tw, Widget, can_focus=True):
    """Base for Checkbox / Switch: a focusable on/off control with a label."""

    # border/padding/background reset what Textual's `Switch { }` CSS would add
    DEFAULT_CLS = "w-auto h-1 border-none p-0 bg-transparent cursor-pointer focus:bg-boost disabled:text-opacity-50"
    ON_CLS: ClassVar[str] = "text-primary bold"
    OFF_CLS: ClassVar[str] = "text-muted"
    ON: ClassVar[str] = ""
    OFF: ClassVar[str] = ""

    BINDINGS = [("enter", "toggle", "Toggle"), ("space", "toggle", "Toggle")]

    value: reactive[bool] = reactive(False, init=False)

    class Changed(Message):
        def __init__(self, toggle: _Toggle, value: bool) -> None:
            super().__init__()
            self.toggle = toggle
            self.value = value

        @property
        def control(self) -> _Toggle:
            return self.toggle

    def __init__(self, label: str = "", value: bool = False, cls: str = "", *, on_cls: str = "",
                 off_cls: str = "", id: str | None = None, disabled: bool = False) -> None:
        super().__init__(id=id, disabled=disabled)
        self.label = label
        self.on_style = inline(merge(self.ON_CLS, on_cls))
        self.off_style = inline(merge(self.OFF_CLS, off_cls))
        self.set_reactive(type(self).value, value)
        self._tw_init(cls)

    def on_mount(self) -> None:
        check_inline(self, self.on_style, self.off_style)

    def toggle(self) -> None:
        self.value = not self.value

    def action_toggle(self) -> None:
        self.toggle()

    def on_click(self, event: events.Click) -> None:
        event.stop()
        self.toggle()

    def watch_value(self, value: bool) -> None:
        self.post_message(self.Changed(self, value))

    def render(self) -> RenderResult:
        mark = Content(self.ON if self.value else self.OFF).stylize(
            (self.on_style if self.value else self.off_style).style)
        if not self.label:
            return mark
        return mark + Content(" ") + Content.from_markup(apply_transforms(self.label, self.transforms))


class Checkbox(_Toggle):
    """A checkbox with a label. Posts `Checkbox.Changed` (`.value`).

    Checkbox("Copy trades", True, on_cls="text-success")
    """

    ON: ClassVar[str] = "[✓]"
    OFF: ClassVar[str] = "[ ]"

    class Changed(_Toggle.Changed):
        """Handled by `on_checkbox_changed`."""


class Switch(_Toggle):
    """An on/off switch with an optional label. Posts `Switch.Changed` (`.value`).

    Switch("Live mode", True)
    """

    ON: ClassVar[str] = "━━●"
    OFF: ClassVar[str] = "○━━"

    class Changed(_Toggle.Changed):
        """Handled by `on_switch_changed`."""


class RadioGroup(Tw, Widget, can_focus=True):
    """One choice out of a few, one per line. Arrows or a click select.

    RadioGroup(["Kelly", "Fixed", "Off"], value=0)    # posts RadioGroup.Changed
    """

    DEFAULT_CLS = "w-auto h-auto cursor-pointer focus:bg-boost/50"
    ON_CLS: ClassVar[str] = "text-primary bold"
    OFF_CLS: ClassVar[str] = "text-muted"
    ON: ClassVar[str] = "◉"
    OFF: ClassVar[str] = "○"

    BINDINGS = [("up,left", "move(-1)", "Previous"), ("down,right", "move(1)", "Next")]

    index: reactive[int] = reactive(0, init=False)

    class Changed(Message):
        def __init__(self, group: RadioGroup, index: int) -> None:
            super().__init__()
            self.group = group
            self.index = index

        @property
        def value(self) -> str:
            return self.group.options[self.index]

        @property
        def control(self) -> RadioGroup:
            return self.group

    def __init__(self, options: Sequence[str], value: int = 0, cls: str = "", *, on_cls: str = "",
                 off_cls: str = "", id: str | None = None) -> None:
        if not options:
            raise ValueError("RadioGroup needs at least one option")
        super().__init__(id=id)
        self.options = list(options)
        self.on_style = inline(merge(self.ON_CLS, on_cls))
        self.off_style = inline(merge(self.OFF_CLS, off_cls))
        self.set_reactive(RadioGroup.index, self.validate_index(value))
        self._tw_init(cls)

    @property
    def value(self) -> str:
        return self.options[self.index]

    def validate_index(self, index: int) -> int:
        return max(0, min(len(self.options) - 1, index))

    def on_mount(self) -> None:
        check_inline(self, self.on_style, self.off_style)

    def watch_index(self, index: int) -> None:
        self.post_message(self.Changed(self, index))

    def action_move(self, step: int) -> None:
        self.index = (self.index + step) % len(self.options)

    def on_click(self, event: events.Click) -> None:
        event.stop()
        if 0 <= event.y < len(self.options):
            self.index = event.y

    def render(self) -> RenderResult:
        lines = []
        for i, option in enumerate(self.options):
            on = i == self.index
            style = (self.on_style if on else self.off_style).style
            lines.append(Content(self.ON if on else self.OFF).stylize(style) + Content(" ")
                         + Content(option).stylize(style if on else ""))
        return Content("\n").join(lines)


# --------------------------------------------------------------------------- #
# Text entry (Textual's widgets, restyled)
# --------------------------------------------------------------------------- #

class Input(Tw, TextualInput):
    """Textual's `Input`, styled with class strings. Same events (`Input.Changed`,
    `Input.Submitted`) and options (`validators=`, `restrict=` ...).

    Input(placeholder="Search markets…", cls="w-40")
    """

    DEFAULT_CLS = "w-full h-3 px-1 border-round border-line bg-surface text-foreground focus:border-primary"

    def __init__(self, value: str = "", cls: str = "", *, placeholder: str = "", password: bool = False,
                 id: str | None = None, **kwargs: Any) -> None:
        super().__init__(value, placeholder, password=password, id=id, **kwargs)
        self._tw_init(cls)


class Select(Tw, TextualSelect):
    """Textual's `Select`, styled with class strings. Posts `Select.Changed`.

    Select([("Macro", "macro"), ("Crypto", "crypto")], prompt="Category")

    `cls` styles the outer widget; `current_cls` the closed box and
    `overlay_cls` the open list. `group-focus:` in `current_cls` follows the
    Select's focus.
    """

    DEFAULT_CLS = "w-full h-auto"
    CURRENT_CLS: ClassVar[str] = "border-round border-line bg-surface text-foreground group-focus:border-primary"
    OVERLAY_CLS: ClassVar[str] = "border-round border-primary bg-surface"

    def __init__(self, options: Iterable[tuple[str, Any]], cls: str = "", *, prompt: str = "Select",
                 value: Any = TextualSelect.NULL, allow_blank: bool = True, current_cls: str = "",
                 overlay_cls: str = "", id: str | None = None, **kwargs: Any) -> None:
        super().__init__(options, prompt=prompt, value=value, allow_blank=allow_blank, id=id, **kwargs)
        self.add_class("group")  # so `group-focus:` in current_cls follows the Select's focus
        self.current_cls = merge(self.CURRENT_CLS, current_cls)
        self.overlay_cls = merge(self.OVERLAY_CLS, overlay_cls)
        self._tw_init(cls)

    def on_mount(self) -> None:
        # Select builds its parts in compose(); style them once they exist.
        tw(self.query_one("SelectCurrent"), self.current_cls)
        tw(self.query_one("SelectOverlay"), self.overlay_cls)
