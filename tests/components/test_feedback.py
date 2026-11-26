import threading

import pytest
from helpers import plain

from tui_z import (
    Alert,
    Button,
    Dialog,
    NotificationCenter,
    Progress,
    Spinner,
    Text,
    Toast,
    ToastStack,
    TwApp,
)
from tui_z.components.feedback import variant_color


class Toasts(TwApp):
    TW_TOAST_TIMEOUT = 0.3

    def __init__(self) -> None:
        super().__init__()
        self.dismissed: list[tuple[str, str]] = []

    def compose(self):
        yield Text("body", id="body")

    def on_toast_dismissed(self, event: Toast.Dismissed) -> None:
        self.dismissed.append((event.toast.message, event.reason))


def stack(app) -> ToastStack:
    return app.screen.query_one(ToastStack)


async def slid_in(pilot, app) -> None:
    """Wait until every toast has slid into place (the slide starts a refresh after mounting)."""
    for _ in range(200):
        await pilot.wait_for_animation()
        if all(t.styles.offset.x.value == 0 for t in stack(app).toasts):
            return
        await pilot.pause(0.02)
    raise AssertionError("toasts never slid in")


# -- variants -------------------------------------------------------------------

def test_unknown_variant_is_an_error():
    assert variant_color("warning") == "warning" and variant_color("neutral") == "muted"
    with pytest.raises(ValueError, match="variant"):
        Toast("x", variant="loud")
    with pytest.raises(ValueError, match="variant"):
        Alert("x", variant="loud")


# -- Toast ----------------------------------------------------------------------

async def test_toast_shows_and_times_out():
    app = Toasts()
    async with app.run_test() as pilot:
        toast = app.toast("Order filled", title="Fill", variant="success")
        await pilot.pause()
        assert toast in stack(app).toasts
        texts = [plain(t) for t in toast.query(Text)]
        assert "Fill" in texts and "Order filled" in texts and "✓" in texts
        assert "border-success" in toast.applied_cls
        await pilot.pause(0.6)
        assert toast.dismissed and app.dismissed == [("Order filled", "timeout")]


async def test_toast_without_timeout_stays_until_clicked():
    app = Toasts()
    async with app.run_test() as pilot:
        toast = app.toast("Sticky", timeout=None)
        await pilot.pause(0.5)
        await slid_in(pilot, app)
        assert not toast.dismissed and toast.countdown is None
        await pilot.click(toast)
        await pilot.pause()
        assert app.dismissed == [("Sticky", "clicked")]


async def test_toast_close_button_and_action():
    app = Toasts()
    ran = []
    async with app.run_test(size=(100, 30)) as pilot:
        closable = app.toast("one", timeout=None)
        acting = app.toast("two", timeout=None, action=("Retry", lambda: ran.append(1)))
        await pilot.pause()
        await slid_in(pilot, app)  # clicks land once they've slid in
        await pilot.click(closable.query_one("_Close"))
        await pilot.click(acting.query_one(Button))
        await pilot.pause()
        assert ran == [1]
        assert app.dismissed == [("one", "closed"), ("two", "action")]


async def test_hover_pauses_the_countdown():
    app = Toasts()
    async with app.run_test() as pilot:
        toast = app.toast("hover me", timeout=0.8)
        await pilot.pause()
        await slid_in(pilot, app)  # let it slide in under the pointer
        await pilot.hover(toast)
        await pilot.pause(1.0)
        assert not toast.dismissed
        await pilot.hover("#body")
        await pilot.pause(1.0)
        assert toast.dismissed


async def test_same_message_bumps_a_counter_and_restarts_the_timer():
    app = Toasts()
    async with app.run_test() as pilot:
        first = app.toast("Feed lag", variant="warning")
        await pilot.pause(0.2)
        again = app.toast("Feed lag", variant="warning")
        assert first.remaining == first.timeout  # restarted (checked before a tick can land)
        await pilot.pause()
        assert again is first and first.count == 2
        assert plain(first.counter) == "×2" and first.counter.display
        assert len(stack(app).toasts) == 1
        assert len(app.tw_notifications) == 2  # both are remembered


async def test_stack_keeps_at_most_max_toasts():
    app = Toasts()
    app.TW_TOAST_MAX = 2
    async with app.run_test(size=(100, 40)) as pilot:
        for i in range(4):
            app.toast(f"m{i}", timeout=None)
            await pilot.pause()
        assert [t.message for t in stack(app).toasts] == ["m3", "m2"]  # top-right: newest first
        assert ("m0", "replaced") in app.dismissed


@pytest.mark.parametrize("position", ["bottom-right", "top-right"])
async def test_stack_fills_up_to_the_default_max(position):
    class App(Toasts):
        TW_TOASTS = position

    app = App()
    async with app.run_test(size=(100, 40)) as pilot:
        for i in range(6):
            app.toast(f"m{i}", timeout=None)
        await pilot.pause()
        messages = [t.message for t in stack(app).toasts]
        assert sorted(messages) == ["m2", "m3", "m4", "m5"]  # TW_TOAST_MAX = 4: the two oldest went
        assert [m for m, reason in app.dismissed if reason == "replaced"] == ["m0", "m1"]


async def test_top_positions_put_the_newest_first():
    class Top(Toasts):
        TW_TOASTS = "top-left"

    app = Top()
    async with app.run_test(size=(100, 40)) as pilot:
        app.toast("old", timeout=None)
        await pilot.pause()
        app.toast("new", timeout=None)
        await pilot.pause()
        s = stack(app)
        assert [t.message for t in s.toasts] == ["new", "old"]
        assert "dock-top" in s.applied_cls and "justify-start" in s.applied_cls
        assert s.styles.dock == "top"


@pytest.mark.parametrize(("position", "side"), [("top-right", 1), ("bottom-left", -1)])
async def test_toasts_slide_in_from_their_side(position, side):
    class App(Toasts):
        TW_TOASTS = position

    app = App()
    async with app.run_test(size=(100, 30)) as pilot:
        toast = app.toast("slide", timeout=None)
        await pilot.pause(0.05)
        start = toast.styles.offset.x.value
        assert start * side > 0  # starts off to that side
        await slid_in(pilot, app)
        assert toast.region.right == 99 if side > 0 else toast.region.x == 1


async def test_no_slide_when_centered_or_animations_are_off():
    class Center(Toasts):
        TW_TOASTS = "top-center"

    app = Center()
    async with app.run_test() as pilot:
        toast = app.toast("still", timeout=None)
        await pilot.pause()
        assert toast.slide_from is None and toast.styles.offset.x.value == 0
    app = Toasts()
    app.animation_level = "none"
    async with app.run_test() as pilot:
        toast = app.toast("still", timeout=None)
        await pilot.pause()
        assert toast.slide_from == "right" and toast.styles.offset.x.value == 0


def test_stack_rejects_unknown_position():
    with pytest.raises(ValueError, match="position"):
        ToastStack(position="middle")


async def test_notify_goes_through_toasts():
    class App(Toasts):
        TW_TOAST_TIMEOUT = 30.0  # no expiry on a slow runner

    app = App()
    async with app.run_test() as pilot:
        app.notify("Saved", title="Disk", severity="information")
        app.notify("Disk full", severity="error", timeout=10)
        await pilot.pause()
        toasts = stack(app).toasts
        assert [(t.variant, t.title, t.timeout) for t in toasts] == [("error", "", 10), ("info", "Disk", 30.0)]
        assert not app._notifications  # Textual's own notifications are unused


async def test_textual_notifications_when_toasts_are_off():
    class Native(Toasts):
        TW_TOASTS = None

    app = Native()
    async with app.run_test() as pilot:
        app.notify("native")
        await pilot.pause()
        assert not app.screen.query(ToastStack)
        assert [n.message for n in app._notifications] == ["native"]


async def test_toast_from_a_worker_thread():
    app = Toasts()
    async with app.run_test() as pilot:
        results = []
        thread = threading.Thread(target=lambda: results.append(app.toast("from thread", timeout=None)))
        thread.start()
        while thread.is_alive():
            await pilot.pause(0.05)
        await pilot.pause()
        assert results == [None]
        assert [t.message for t in stack(app).toasts] == ["from thread"]


async def test_toasts_follow_the_active_screen():
    app = Toasts()
    async with app.run_test() as pilot:
        app.push_screen(Dialog("modal"))
        await pilot.pause()
        app.toast("on the dialog", timeout=None)
        await pilot.pause()
        assert app.screen.query_one(ToastStack).toasts[0].message == "on the dialog"


# -- NotificationCenter -----------------------------------------------------------

async def test_notification_center_records_history_and_unread():
    app = Toasts()
    async with app.run_test(size=(100, 30)) as pilot:
        app.toast("before mount", variant="error")
        center = NotificationCenter(cls="h-8")
        await app.mount(center)
        await pilot.pause()
        assert center.history.line_count() == 1 and center.unread == 0
        app.toast("Order filled", title="Fill", variant="success")
        app.toast("Lag", variant="warning")
        await pilot.pause()
        assert center.history.line_count() == 3 and center.unread == 2
        assert plain(center.badge) == "2" and center.badge.display
        await pilot.click(center)
        await pilot.pause()
        assert center.unread == 0 and not center.badge.display
        center.clear()
        assert center.history.line_count() == 0


# -- Alert ----------------------------------------------------------------------

async def test_alert_variant_title_update_and_dismiss(mount):
    alert = Alert("Prices delayed", title="Market closed", variant="warning", dismissible=True, id="a")
    dismissed = []

    class App(TwApp):
        def compose(self):
            yield alert

        def on_alert_dismissed(self, event: Alert.Dismissed) -> None:
            dismissed.append(event.reason)

    app = App()
    async with app.run_test() as pilot:
        assert "border-warning" in alert.applied_cls and "bg-warning/10" in alert.applied_cls
        texts = [plain(t) for t in alert.query(Text)]
        assert texts[:3] == ["!", "Market closed", "Prices delayed"]
        alert.update("Back at 9:30")
        assert plain(alert.message_text) == "Back at 9:30"
        await pilot.click(alert.query_one("_Close"))
        await pilot.pause()
        assert dismissed == ["closed"] and not app.query("#a")


# -- Progress -------------------------------------------------------------------

async def test_progress_renders_label_bar_and_percentage(mount):
    p = Progress(25, 100, "w-30", label="Sync")
    async with mount(p) as (app, pilot):
        text = plain(p)
        assert text.startswith("Sync ") and text.endswith(" 25%") and len(text) == 30
        p.advance(25)
        assert p.percentage == 0.5 and plain(p).endswith(" 50%")
        p.update(value=200)
        assert p.percentage == 1.0
        p.update(total=0)
        assert p.percentage == 1.0
        p.update(label="Done", total=10, value=5)
        assert plain(p).startswith("Done ") and p.percentage == 0.5


async def test_progress_indeterminate_sweeps(mount):
    p = Progress(total=None, cls="w-20", show_percentage=False)
    async with mount(p) as (app, pilot):
        assert p.percentage is None
        before = p.render()
        await pilot.pause(0.3)
        assert p.render().spans != before.spans


async def test_progress_sweeps_only_while_indeterminate_and_visible(mount):
    p = Progress(10, 100, "w-20")
    async with mount(p) as (app, pilot):
        await pilot.pause(0.25)
        assert p._sweep == 0  # determinate: the sweep timer is paused
        p.update(total=None)
        await pilot.pause(0.25)
        assert p._sweep > 0
        p.display = False
        await pilot.pause()
        hidden_at = p._sweep
        await pilot.pause(0.25)
        assert p._sweep == hidden_at  # not on screen: no redraws


# -- Spinner --------------------------------------------------------------------

async def test_spinner_spins_and_stops(mount):
    s = Spinner("Syncing", "w-20")
    async with mount(s) as (app, pilot):
        first = plain(s)
        assert first.endswith(" Syncing") and first[0] in Spinner.FRAMES
        await pilot.pause(0.3)
        assert plain(s) != first
        s.stop("Synced")
        assert plain(s) == "✓ Synced"
        frame = s.frame
        await pilot.pause(0.2)
        assert s.frame == frame
        s.start("Again")
        assert plain(s).endswith(" Again")
        s.display = False
        await pilot.pause()
        frame = s.frame
        await pilot.pause(0.25)
        assert s.frame == frame  # not on screen: no redraws
        assert plain(Spinner()) in Spinner.FRAMES


# -- Dialog ---------------------------------------------------------------------

async def test_dialog_returns_the_pressed_button():
    app = Toasts()
    results = []
    async with app.run_test(size=(100, 30)) as pilot:
        dialog = Dialog("Delete 3 orders?", title="Confirm",
                        buttons=[("Cancel", "cancel"), ("Delete", "delete", "text-error border-error")])
        app.push_screen(dialog, results.append)
        await pilot.pause()
        buttons = list(dialog.query(Button))
        assert [b.name for b in buttons] == ["cancel", "delete"]
        assert app.focused is buttons[-1]  # the main action
        await pilot.press("enter")
        await pilot.pause()
        app.push_screen(Dialog("Sure?"), results.append)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert results == ["delete", None]
