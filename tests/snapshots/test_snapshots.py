"""Visual regression tests: one gallery per component family, in three themes.

Snapshots live in `__snapshots__/` next to this file. After an intended visual
change, review the diff report and update them:

    uv run pytest tests/snapshots --snapshot-update
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime

import pytest
from textual.widget import Widget

from tui_z import (
    Alert,
    Badge,
    Bar,
    BarChart,
    Button,
    Checkbox,
    Col,
    Divider,
    Grid,
    Heatmap,
    Input,
    Kbd,
    KeyHints,
    KeyValue,
    Label,
    LineChart,
    LogView,
    Notification,
    NotificationCenter,
    Panel,
    Progress,
    RadioGroup,
    Row,
    Select,
    Sidebar,
    Spacer,
    Sparkline,
    Spinner,
    Stat,
    Switch,
    Table,
    TabPane,
    TabView,
    Text,
    ThemeSwitcher,
    Ticker,
    Toast,
    TwApp,
)

THEMES = ["tokyo-night", "catppuccin-latte", "terminal"]  # dark, light, ANSI-ish
WAVE = [3 + 3 * ((i * 7) % 11) / 10 for i in range(80)]  # deterministic data


def layout() -> Iterable[Widget]:
    yield Grid(
        Panel(Text("Default panel"), title="Default"),
        Panel(Text("Rounded, primary"), title="Rounded", badge=Badge("new"), cls="border-round border-primary"),
        Panel(Text("Heavy error"), title="Alert", subtitle="3 open", cls="border-heavy border-error bg-error/5"),
        cls="grid-cols-3 gap-1",
    )
    yield Row(Text("left"), Spacer(), Text("right"), cls="mt-1 bg-panel")
    yield Divider("mt-1")
    yield Divider("text-primary", char="━")


def content() -> Iterable[Widget]:
    yield Row(*[Badge(c, cls=f"bg-{c}/20 text-{c} mr-1") for c in ("success", "warning", "error", "info")])
    yield Row(Label("Fair value", cls="mr-2"), Text("[b $success]+12%[/] markup", "mr-2"),
              Text("tracking", "tracking-wide uppercase text-primary"), cls="mt-1")
    yield Row(Stat("Net PnL", "+$10 554", cls="w-14", value_cls="text-success"),
              Stat("Open", "4", cls="w-8", value_cls="text-warning"), cls="mt-1")
    yield Row(Kbd("ctrl+s", "mr-1"), Kbd("q", "mr-1"), Text("keys", "text-muted"), cls="mt-1")
    yield KeyValue([("Status", "Live", "text-success"), ("Latency", "12 ms"), ("Region", "eu-west")], "mt-1")


def data() -> Iterable[Widget]:
    yield Table([("#", "w-3 text-muted"), ("Market", "w-fr"), ("Yes", "w-6 text-right text-success")],
                [["1", "Rates cut in Q1?", "67¢"], ["2", "BTC above 120k?", ("54¢", "text-warning")],
                 ["3", "Ceasefire holds?", "42¢"]],
                row_cls="odd:bg-panel/50")
    log = LogView(cls="h-4 mt-1", id="log")
    yield log
    yield Ticker(["[b $success]▲ BTC +2.1%[/]", "[b $error]▼ ETH -0.8%[/]"], "mt-1 bg-panel", speed=3600)


def charts() -> Iterable[Widget]:
    yield Row(Bar(0.3, "w-fr text-success mr-2"), Bar(0.8, "w-fr text-error"))
    yield Sparkline(WAVE, "h-3 text-info mt-1", lo=0)
    yield LineChart(WAVE, "h-8 text-primary mt-1", mode="fit", series=[(WAVE[::-1], "purple")],
                    marks=[(5.0, "warning", " target")])
    yield Row(
        BarChart([("Mon", 3), ("Tue", 5), ("Wed", 2, "error"), ("Thu", 4)], "w-fr h-6 text-info mr-2", values=True),
        Heatmap([[(r * 3 + c) % 7 for c in range(12)] for r in range(4)], "mt-1", color="success",
                row_labels=["Mon", "Tue", "Wed", "Thu"]),
        cls="h-auto mt-1",
    )


def controls() -> Iterable[Widget]:
    yield Row(Button("Default", "mr-1"), Button("Buy", "text-success border-success mr-1"),
              Button("Ghost", "border-none text-muted"))
    yield Row(Col(Checkbox("Copy trades", True), Checkbox("Paper mode"), Switch("Live", True), Switch("Alerts"),
                  cls="w-24"),
              RadioGroup(["Kelly", "Fixed", "Off"], 1, "w-14"),
              Col(Input("", placeholder="Search markets…"), Select([("Macro", 1), ("Crypto", 2)], value=2),
                  cls="w-fr"),
              cls="h-auto mt-1")
    yield Row(Sidebar(ThemeSwitcher(), title="Themes", width="w-24"),
              Sidebar(Text("hidden"), title="Rail", collapsed=True), cls="h-14 mt-1")


def navigation() -> Iterable[Widget]:
    yield TabView(TabPane("Dashboard", Text("dashboard pane")), TabPane("Logs", Text("logs pane")),
                  TabPane("Settings", Text("settings pane")), cls="h-6")
    yield KeyHints([("q", "quit"), ("[ ]", "theme"), ("b", "sidebar")], "mt-1")


def feedback() -> Iterable[Widget]:
    for variant in ("success", "info", "warning", "error"):
        yield Alert(f"A {variant} alert", title=variant.capitalize(), variant=variant, dismissible=True, cls="mb-1")
    yield Progress(40, 100, "text-success", label="Sync")
    spinner = Spinner("Loading", "mt-1")
    spinner.stop("Loaded")
    yield spinner
    yield Row(Toast("Order filled · 0.61 SOL", title="Fill", variant="success", timeout=None),
              Toast("Feed lag 2.1 s", variant="warning", timeout=None, action=("Retry", lambda: None), cls="ml-2"),
              cls="h-auto")
    yield NotificationCenter(cls="h-6 mt-1", id="center")


GALLERIES: dict[str, Callable[[], Iterable[Widget]]] = {
    "layout": layout, "content": content, "data": data, "charts": charts, "controls": controls,
    "navigation": navigation, "feedback": feedback,
}


def gallery_app(builder: Callable[[], Iterable[Widget]], theme: str) -> TwApp:
    class Gallery(TwApp):
        TW_THEME = theme
        AUTO_FOCUS = None  # no blinking cursor in the snapshots

        def compose(self):
            yield Col(*builder(), cls="p-1")

        def on_mount(self) -> None:
            if self.query("#center"):
                for i, (title, variant) in enumerate([("Fill", "success"), ("Lag", "warning")]):
                    self.query_one("#center", NotificationCenter).add(
                        Notification(f"note {i}", title, variant, datetime(2026, 1, 1, 9, 0, i)))
            if self.query("#log"):
                log = self.query_one("#log", LogView)
                for i, (tag, color) in enumerate([("buy", "success"), ("exit", "error"), ("skip", "warning")]):
                    log.write(f"message {i} [$muted]· detail[/]", tag=tag, tag_cls=f"bg-{color}/20 text-{color}",
                              time=datetime(2026, 1, 1, 12, 0, i))

    return Gallery()


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("family", list(GALLERIES))
def test_gallery(family, theme, snap_compare):
    assert snap_compare(gallery_app(GALLERIES[family], theme), terminal_size=(110, 36))
