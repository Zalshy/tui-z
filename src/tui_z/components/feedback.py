"""Feedback components: notifications, alerts, progress, spinners and dialogs.

Toast and Alert share the same variants (success, info, warning, error,
neutral), each a theme color plus an icon:

    app.toast("Order filled", variant="success")       # see TwApp.toast
    Alert("Prices delayed 15 min", title="Market closed", variant="warning")
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar

from textual import events
from textual.app import ComposeResult, RenderResult
from textual.content import Content
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widget import Widget

from ..core.tw import Tw, check_inline
from ..styling.engine import merge
from ..styling.inline import inline
from .charts.bar import Bar
from .content import Badge, Text
from .controls import Button
from .data import LogView
from .layout import Col, Panel, Row, Spacer

# --------------------------------------------------------------------------- #
# Variants
# --------------------------------------------------------------------------- #

VARIANTS: dict[str, tuple[str, str]] = {
    # variant: (theme color, icon)
    "success": ("success", "✓"),
    "info": ("info", "i"),
    "warning": ("warning", "!"),
    "error": ("error", "✗"),
    "neutral": ("muted", "•"),
}


def variant_color(variant: str) -> str:
    """Theme color token of a variant; raises ValueError for an unknown one."""
    try:
        return VARIANTS[variant][0]
    except KeyError:
        raise ValueError(f"unknown variant {variant!r}; use one of {', '.join(VARIANTS)}") from None


def variant_icon(variant: str) -> str:
    variant_color(variant)
    return VARIANTS[variant][1]


class _Close(Text):
    """The ✕ that dismisses a toast or alert."""

    def on_click(self, event: events.Click) -> None:
        event.stop()
        owner = next((a for a in self.ancestors if isinstance(a, Toast | Alert)), None)
        if owner is not None:
            owner.dismiss("closed")


# --------------------------------------------------------------------------- #
# Toast
# --------------------------------------------------------------------------- #

type ToastAction = tuple[str, Callable[[], object]]
"""(button label, callback) for a toast's action button."""


class Toast(Tw, Widget):
    """A short-lived notification. Usually created with `app.toast(...)`.

    - disappears after `timeout` seconds (None: stays until dismissed), with a
      countdown bar; hovering pauses it
    - a click dismisses it; `action=("Retry", callback)` adds a button
    - the same message again bumps a ×N counter instead of stacking

    Posts `Toast.Dismissed(toast, reason)` with reason "timeout", "closed",
    "clicked", "action", "replaced" or "dismissed".
    """

    # p-0 resets the padding Textual's `Toast { }` CSS would add
    DEFAULT_CLS = "w-48 max-w-full h-auto mt-1 p-0 pl-1 bg-surface border-l border-heavy visible cursor-pointer"
    TITLE_CLS: ClassVar[str] = "bold w-fr truncate"
    MESSAGE_CLS: ClassVar[str] = "text-foreground w-full"
    TICK: ClassVar[float] = 0.1

    class Dismissed(Message):
        def __init__(self, toast: Toast, reason: str) -> None:
            super().__init__()
            self.toast = toast
            self.reason = reason

        @property
        def control(self) -> Toast:
            return self.toast

    def __init__(self, message: str, *, title: str = "", variant: str = "info", timeout: float | None = 4.0,
                 action: ToastAction | None = None, markup: bool = True, cls: str = "",
                 id: str | None = None) -> None:
        self.variant = variant
        self.color = variant_color(variant)
        self.message = message
        self.title = title
        self.timeout = timeout
        self.action = action
        self.remaining = timeout or 0.0
        self.count = 1
        self.dismissed = False
        c = self.color
        self.counter = Text("", f"text-{c} bold w-auto ml-1 hidden", markup=False)
        header = Row(
            Text(variant_icon(variant), f"text-{c} bold w-2"),
            Text(title or variant.capitalize(), merge(self.TITLE_CLS, f"text-{c}"), markup=False),
            self.counter,
            _Close("✕", "w-3 text-muted text-center hover:text-foreground", markup=False),
            cls="h-1",
        )
        parts: list[Widget] = [header, Text(message, merge(self.MESSAGE_CLS, "pl-2 pr-1"), markup=markup)]
        if action is not None:
            parts.append(Row(Spacer(), Button(action[0], f"text-{c} border-{c} mr-1"), cls="h-auto"))
        self.countdown = Bar(1.0, f"text-{c}/60 mt-1 mr-1", track=False) if timeout else None
        if self.countdown is not None:
            parts.append(self.countdown)
        super().__init__(*parts, id=id)
        self._tw_init(cls)

    def _tw_defaults(self) -> str:
        return merge(self.base_cls(), f"border-{self.color}")

    @property
    def key(self) -> tuple[str, str, str]:
        """Toasts with the same key are merged (`×N`) instead of stacked."""
        return (self.variant, self.title, self.message)

    def on_mount(self) -> None:
        if self.timeout:
            self.set_interval(self.TICK, self._tick)

    def _tick(self) -> None:
        if self.dismissed or self.is_mouse_over:
            return  # hovering pauses the countdown
        self.remaining = max(0.0, self.remaining - self.TICK)
        if self.countdown is not None and self.timeout:
            self.countdown.value = self.remaining / self.timeout
        if self.remaining <= 0:
            self.dismiss("timeout")

    def bump(self) -> None:
        """The same message arrived again: count it and restart the timer."""
        self.count += 1
        self.counter.update(f"×{self.count}")
        self.counter.set_cls(self.counter.cls.replace(" hidden", ""))
        self.remaining = self.timeout or 0.0
        if self.countdown is not None:
            self.countdown.value = 1.0

    def dismiss(self, reason: str = "dismissed") -> None:
        if self.dismissed:
            return
        self.dismissed = True
        self.post_message(self.Dismissed(self, reason))
        self.remove()

    def on_click(self, event: events.Click) -> None:
        event.stop()
        self.dismiss("clicked")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if self.action is not None:
            self.action[1]()
        self.dismiss("action")


TOAST_POSITIONS: dict[str, str] = {
    "bottom-right": "dock-bottom justify-end",
    "bottom-left": "dock-bottom justify-start",
    "bottom-center": "dock-bottom justify-center",
    "top-right": "dock-top justify-end",
    "top-left": "dock-top justify-start",
    "top-center": "dock-top justify-center",
}


class ToastStack(Tw, Widget):
    """Holds the toasts of one screen, docked to a corner. `TwApp` creates it.

    The stack itself is invisible (clicks go through to the widgets under it);
    only its toasts are drawn.
    """

    DEFAULT_CLS = "w-full h-auto px-1 pb-1 invisible"

    def __init__(self, *toasts: Toast, position: str = "bottom-right", max_toasts: int = 4,
                 cls: str = "", id: str | None = None) -> None:
        if position not in TOAST_POSITIONS:
            raise ValueError(f"unknown toast position {position!r}; use one of {', '.join(TOAST_POSITIONS)}")
        self.position = position
        self.max_toasts = max_toasts
        super().__init__(*toasts, id=id)
        self._tw_init(cls)

    def _tw_defaults(self) -> str:
        return merge(self.base_cls(), TOAST_POSITIONS[self.position])

    LAYER: ClassVar[str] = "tw-toasts"

    def on_mount(self) -> None:
        # Docked widgets only push aside widgets on their own layer, so the stack
        # gets a layer of its own (above the screen's content) and floats.
        screen = self.screen
        if self.LAYER not in screen.layers:
            own = screen.styles.layers if screen.styles.has_rule("layers") else ("default",)
            screen.styles.layers = (*own, self.LAYER)
        self.styles.layer = self.LAYER

    @property
    def toasts(self) -> list[Toast]:
        return [t for t in self.children if isinstance(t, Toast) and not t.dismissed]

    def find(self, key: tuple[str, str, str]) -> Toast | None:
        return next((t for t in self.toasts if t.key == key), None)

    def push(self, toast: Toast) -> Toast:
        """Show a toast, or bump the live one with the same message."""
        same = self.find(toast.key)
        if same is not None:
            same.bump()
            return same
        top = self.position.startswith("top")
        live = self.toasts
        excess = max(0, len(live) - self.max_toasts + 1)  # make room for the new one
        for old in (live[len(live) - excess:] if top else live[:excess]):  # the oldest go
            old.dismiss("replaced")
        if top and live:  # newest nearest the edge
            self.mount(toast, before=0)
        else:
            self.mount(toast)
        return toast


# --------------------------------------------------------------------------- #
# Notification history
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Notification:
    """One toast, as remembered by `TwApp.tw_notifications`."""

    message: str
    title: str = ""
    variant: str = "info"
    time: datetime = field(default_factory=datetime.now)


class NotificationCenter(Tw, Widget):
    """Every toast the app has shown, newest at the bottom, with an unread count.

    NotificationCenter(cls="h-12")   # follows TwApp.toast() / notify()

    `unread` counts toasts since the last `mark_read()` (clicking it marks
    everything read).
    """

    DEFAULT_CLS = "col w-full h-10"
    HEADER_CLS: ClassVar[str] = "h-1 mb-1"
    UNREAD_CLS: ClassVar[str] = "bg-error text-background"

    unread: reactive[int] = reactive(0, init=False)

    def __init__(self, title: str = "Notifications", cls: str = "", *, max_items: int = 200,
                 id: str | None = None) -> None:
        self.badge = Badge("", cls=merge(self.UNREAD_CLS, "hidden"))
        self.history = LogView("h-fr", max_lines=max_items, tag_width=9)  # fits "warning" with room
        header = Row(Text(title, "text-muted bold uppercase tracking-wide w-fr truncate", markup=False),
                     self.badge, cls=self.HEADER_CLS)
        super().__init__(header, self.history, id=id)
        self._tw_init(cls)

    def on_mount(self) -> None:
        signal = getattr(self.app, "tw_notification_signal", None)
        for note in getattr(self.app, "tw_notifications", ()):
            self._write(note)
        if signal is not None:
            signal.subscribe(self, self.add)

    def _write(self, note: Notification) -> None:
        c = variant_color(note.variant)
        text = f"[b]{Content(note.title).markup}[/b] {note.message}" if note.title else note.message
        self.history.write(text, tag=note.variant, tag_cls=f"bg-{c}/20 text-{c}", time=note.time)

    def add(self, note: Notification) -> None:
        """Record one notification (called for every app toast)."""
        self._write(note)
        self.unread += 1

    def watch_unread(self, unread: int) -> None:
        self.badge.update(str(unread))
        self.badge.set_cls(self.UNREAD_CLS if unread else merge(self.UNREAD_CLS, "hidden"))

    def mark_read(self) -> None:
        self.unread = 0

    def clear(self) -> None:
        self.history.clear()
        self.mark_read()

    def on_click(self) -> None:
        self.mark_read()


# --------------------------------------------------------------------------- #
# Alert
# --------------------------------------------------------------------------- #

class Alert(Tw, Widget):
    """A banner that stays in the layout: `Alert("Prices delayed", variant="warning")`.

    `dismissible=True` adds a ✕ that removes it and posts `Alert.Dismissed`.
    """

    DEFAULT_CLS = "w-full h-auto px-1 border-l border-tall"
    TITLE_CLS: ClassVar[str] = "bold"

    class Dismissed(Message):
        def __init__(self, alert: Alert, reason: str) -> None:
            super().__init__()
            self.alert = alert
            self.reason = reason

        @property
        def control(self) -> Alert:
            return self.alert

    def __init__(self, message: str, *, title: str = "", variant: str = "info", dismissible: bool = False,
                 markup: bool = True, cls: str = "", id: str | None = None) -> None:
        self.variant = variant
        self.color = c = variant_color(variant)
        self.message_text = Text(message, "w-full", markup=markup)
        body: list[Widget] = []
        if title:
            body.append(Text(title, merge(self.TITLE_CLS, f"text-{c}"), markup=False))
        body.append(self.message_text)
        parts: list[Widget] = [Text(variant_icon(variant), f"text-{c} bold w-2"), Col(*body, cls="w-fr")]
        if dismissible:
            parts.append(_Close("✕", "w-3 text-muted text-center cursor-pointer hover:text-foreground", markup=False))
        super().__init__(Row(*parts, cls="h-auto"), id=id)
        self._tw_init(cls)

    def _tw_defaults(self) -> str:
        return merge(self.base_cls(), f"border-{self.color} bg-{self.color}/10")

    def update(self, message: str) -> None:
        self.message_text.update(message)

    def dismiss(self, reason: str = "dismissed") -> None:
        self.post_message(self.Dismissed(self, reason))
        self.remove()


# --------------------------------------------------------------------------- #
# Progress / Spinner
# --------------------------------------------------------------------------- #

_KEEP = object()  # "argument not given" for Progress.update(total=...)


class Progress(Tw, Widget):
    """A labelled progress bar with a percentage. Fill color = `text-*`.

    Progress(total=100, label="Sync", cls="text-success")
    progress.advance(5)          # or progress.update(value=40)

    `total=None` is indeterminate: a segment sweeps back and forth.
    """

    DEFAULT_CLS = "w-full h-1 text-primary"
    LABEL_CLS: ClassVar[str] = "text-muted"
    FILL: ClassVar[str] = "━"
    SWEEP: ClassVar[float] = 0.08

    value: reactive[float] = reactive(0.0)
    total: reactive[float | None] = reactive(100.0)

    def __init__(self, value: float = 0.0, total: float | None = 100.0, cls: str = "", *, label: str = "",
                 show_percentage: bool = True, id: str | None = None) -> None:
        super().__init__(id=id)
        self.label = label
        self.show_percentage = show_percentage
        self.label_style = inline(self.LABEL_CLS)
        self._sweep = 0
        self.set_reactive(Progress.total, total)
        self.set_reactive(Progress.value, value)
        self._tw_init(cls)

    def on_mount(self) -> None:
        check_inline(self, self.label_style)
        # the sweep only runs while indeterminate
        self._sweep_timer = self.set_interval(self.SWEEP, self._step, pause=self.total is not None)

    def watch_total(self, total: float | None) -> None:
        timer = getattr(self, "_sweep_timer", None)
        if timer is None:
            return
        if total is None:
            timer.resume()
        else:
            timer.pause()

    def _step(self) -> None:
        if self.is_on_screen:  # no redraws on a hidden tab
            self._sweep += 1
            self.refresh()

    @property
    def percentage(self) -> float | None:
        """0..1, or None while indeterminate."""
        if self.total is None:
            return None
        return max(0.0, min(1.0, self.value / self.total)) if self.total else 1.0

    def advance(self, amount: float = 1.0) -> None:
        self.value += amount

    def update(self, *, value: float | None = None, total: float | object | None = _KEEP,
               label: str | None = None) -> None:
        """Change any of value, total (None = indeterminate) and label."""
        if total is not _KEEP:
            self.total = total  # type: ignore[assignment]
        if value is not None:
            self.value = value
        if label is not None:
            self.label = label
            self.refresh()

    def render(self) -> RenderResult:
        width = self.content_region.width
        parts: list[Content] = []
        if self.label:
            parts.append(Content(self.label + " ").stylize(self.label_style.style))
        pct = self.percentage
        suffix = f" {pct * 100:3.0f}%" if self.show_percentage and pct is not None else ""
        bar_w = max(0, width - sum(p.cell_length for p in parts) - len(suffix))
        if pct is None:
            seg = max(1, bar_w // 4)
            travel = max(1, bar_w - seg)
            pos = self._sweep % (2 * travel)
            start = pos if pos <= travel else 2 * travel - pos
            parts += [Content(self.FILL * start).stylize("$line"), Content(self.FILL * seg),
                      Content(self.FILL * (bar_w - start - seg)).stylize("$line")]
        else:
            filled = round(pct * bar_w)
            parts += [Content(self.FILL * filled), Content(self.FILL * (bar_w - filled)).stylize("$line")]
        if suffix:
            parts.append(Content(suffix).stylize("$foreground"))
        return Content("").join(parts)


class Spinner(Tw, Widget):
    """An animated spinner with a label. Color = `text-*`.

    Spinner("Syncing wallets", cls="text-primary")
    spinner.stop("Synced")       # freezes on a ✓ and the new label
    """

    DEFAULT_CLS = "w-auto h-1 text-primary"
    FRAMES: ClassVar[Sequence[str]] = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
    DONE: ClassVar[str] = "✓"
    SPEED: ClassVar[float] = 0.08

    def __init__(self, label: str = "", cls: str = "", *, id: str | None = None) -> None:
        super().__init__(id=id)
        self.label = label
        self.frame = 0
        self.spinning = True
        self._tw_init(cls)

    def on_mount(self) -> None:
        self._timer = self.set_interval(self.SPEED, self._advance)

    def _advance(self) -> None:
        if self.spinning and self.is_on_screen:  # no redraws on a hidden tab
            self.frame = (self.frame + 1) % len(self.FRAMES)
            self.refresh()

    def start(self, label: str | None = None) -> None:
        if label is not None:
            self.label = label
        self.spinning = True
        self.refresh(layout=label is not None)

    def stop(self, label: str | None = None) -> None:
        if label is not None:
            self.label = label
        self.spinning = False
        self.refresh(layout=label is not None)

    def render(self) -> RenderResult:
        mark = self.FRAMES[self.frame] if self.spinning else self.DONE
        if not self.label:
            return mark
        return Content(mark) + Content(" " + self.label).stylize("$foreground")


# --------------------------------------------------------------------------- #
# Dialog
# --------------------------------------------------------------------------- #

type DialogButton = tuple[str, str] | tuple[str, str, str]
"""(label, result) or (label, result, button cls)."""


class Dialog(Tw, ModalScreen[str | None]):
    """A modal dialog. Dismisses with the pressed button's result (None on escape).

    def on_delete(result: str | None) -> None: ...
    app.push_screen(Dialog("Delete 3 orders?", title="Confirm",
                           buttons=[("Cancel", "cancel"), ("Delete", "delete", "text-error border-error")]),
                    on_delete)

    `cls` styles the panel; the screen behind it is dimmed.
    """

    DEFAULT_CLS = "place-center bg-background/60"
    PANEL_CLS: ClassVar[str] = "w-60 max-w-full h-auto border-round border-primary bg-surface px-2 py-1"
    PRIMARY_CLS: ClassVar[str] = "text-primary border-primary"

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, message: str, *, title: str = "", buttons: Sequence[DialogButton] = (),
                 cls: str = "", id: str | None = None) -> None:
        super().__init__(id=id)
        self.message = message
        self.title_text = title
        self.buttons = list(buttons) or [("Cancel", "cancel"), ("OK", "ok", self.PRIMARY_CLS)]
        self.panel_cls = merge(self.PANEL_CLS, cls)
        self._tw_init("")

    def compose(self) -> ComposeResult:
        buttons = [Button(b[0], merge("ml-1", b[2] if len(b) > 2 else ""), name=b[1])  # type: ignore[misc]
                   for b in self.buttons]
        yield Panel(Text(self.message, "w-full mb-1"), Row(Spacer(), *buttons, cls="h-auto"),
                    title=self.title_text, cls=self.panel_cls)

    def on_mount(self) -> None:
        self.query(Button).last().focus()  # the last button is the main action

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(event.button.name)

    def action_cancel(self) -> None:
        self.dismiss(None)
