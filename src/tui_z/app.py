"""`TwApp`: a Textual App that understands utility classes.

This is the top layer: it may use anything in tui-z (components included).
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import App
from textual.dom import DOMNode
from textual.notifications import SeverityLevel
from textual.signal import Signal
from textual.widget import Widget

from ._textual import on_app_thread
from .components.feedback import Notification, Toast, ToastAction, ToastStack
from .core.stylesheet import UtilityStylesheet
from .styling.themes import THEME_NAMES, THEMES, fill_extra_tokens
from .styling.utilities import BREAKPOINTS

DEFAULT = object()  # "use TW_TOAST_TIMEOUT" (None already means "until dismissed")


class TwApp(App):
    """Base class for tui_z apps.

    - registers the tui_z themes and selects `TW_THEME`
    - compiles every `cls=` string it sees into the stylesheet, just before the
      widgets using it are styled (no unstyled first frame)
    - sets screen breakpoint classes so `sm: md: lg: xl:` variants work
    - shows notifications as tui-z toasts: `app.toast(...)`, and Textual's
      `app.notify(...)` too (set `TW_TOASTS = None` to keep Textual's)
    """

    TW_THEME: ClassVar[str] = "terminal"
    TW_MAX_CHUNKS: ClassVar[int] = 32
    TW_THEMES: ClassVar[tuple[str, ...]] = THEME_NAMES
    """Themes cycled by `action_next_theme` / `action_prev_theme`."""
    TW_TOASTS: ClassVar[str | None] = "top-right"
    """Where toasts appear (`top-left` ... `bottom-right`); None keeps Textual's notify()."""
    TW_TOAST_MAX: ClassVar[int] = 4
    """Most toasts on screen at once; the oldest is dismissed for a new one."""
    TW_TOAST_TIMEOUT: ClassVar[float] = 4.0

    HORIZONTAL_BREAKPOINTS = [(0, "-tw-base")] + [
        (width, f"-tw-{name}") for name, width in BREAKPOINTS.items()
    ]

    def __init__(self, *args, **kwargs) -> None:
        self._tw_sheet = UtilityStylesheet(self.TW_MAX_CHUNKS)
        super().__init__(*args, **kwargs)
        self.tw_notifications: list[Notification] = []
        """Every toast shown so far (see `NotificationCenter`)."""
        self.tw_notification_signal: Signal[Notification] = Signal(self, "tw-notification")
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

    # -- notifications -------------------------------------------------------
    def toast(self, message: str, *, title: str = "", variant: str = "info", timeout: float | object | None = DEFAULT,
              action: ToastAction | None = None, markup: bool = True, cls: str = "") -> Toast | None:
        """Show a toast on the current screen.

        app.toast("Order filled", variant="success")
        app.toast("Feed lost", title="Connection", variant="error", timeout=None,
                  action=("Retry", self.reconnect))

        `variant`: success, info, warning, error or neutral. `timeout` in
        seconds (default `TW_TOAST_TIMEOUT`, None = until dismissed). Safe to
        call from a worker thread (it then returns None).
        """
        if not on_app_thread(self):
            self.call_from_thread(self.toast, message, title=title, variant=variant, timeout=timeout,
                                  action=action, markup=markup, cls=cls)
            return None
        if timeout is DEFAULT:
            timeout = self.TW_TOAST_TIMEOUT
        toast = Toast(message, title=title, variant=variant, timeout=timeout, action=action, markup=markup, cls=cls)
        note = Notification(message, title, variant)
        self.tw_notifications.append(note)
        self.tw_notification_signal.publish(note)
        stacks = self.screen.query_children(ToastStack)
        if stacks:
            stack = stacks.first()
        else:
            stack = ToastStack(position=self.TW_TOASTS or "top-right", max_toasts=self.TW_TOAST_MAX)
            self.screen.mount(stack)
        return stack.push(toast)

    def notify(self, message: str, *, title: str = "", severity: SeverityLevel = "information",
               timeout: float | None = None, markup: bool = True) -> None:
        """Textual's notify(), shown as a tui-z toast (unless `TW_TOASTS` is None)."""
        if self.TW_TOASTS is None:
            super().notify(message, title=title, severity=severity, timeout=timeout, markup=markup)
            return
        variant = {"information": "info"}.get(severity, severity)
        self.toast(message, title=title, variant=variant, timeout=DEFAULT if timeout is None else timeout,
                   markup=markup)

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
