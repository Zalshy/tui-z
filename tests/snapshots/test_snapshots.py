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
    Badge,
    Bar,
    Button,
    Col,
    Divider,
    Grid,
    Label,
    LineChart,
    LogView,
    Panel,
    Row,
    Sidebar,
    Spacer,
    Sparkline,
    Stat,
    Table,
    Text,
    ThemeSwitcher,
    Ticker,
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


def controls() -> Iterable[Widget]:
    yield Row(Button("Default", "mr-1"), Button("Buy", "text-success border-success mr-1"),
              Button("Ghost", "border-none text-muted"))
    yield Row(Sidebar(ThemeSwitcher(), title="Themes", width="w-24"),
              Sidebar(Text("hidden"), title="Rail", collapsed=True), cls="h-14 mt-1")


GALLERIES: dict[str, Callable[[], Iterable[Widget]]] = {
    "layout": layout, "content": content, "data": data, "charts": charts, "controls": controls,
}


def gallery_app(builder: Callable[[], Iterable[Widget]], theme: str) -> TwApp:
    class Gallery(TwApp):
        TW_THEME = theme

        def compose(self):
            yield Col(*builder(), cls="p-1")

        def on_mount(self) -> None:
            if self.query("#log"):
                log = self.query_one("#log", LogView)
                for i, (tag, color) in enumerate([("buy", "success"), ("exit", "error"), ("skip", "warning")]):
                    log.write(f"message {i} [$muted]· detail[/]", tag=tag, tag_cls=f"bg-{color}/20 text-{color}",
                              time=datetime(2026, 1, 1, 12, 0, i))

    return Gallery()


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("family", list(GALLERIES))
def test_gallery(family, theme, snap_compare):
    assert snap_compare(gallery_app(GALLERIES[family], theme), terminal_size=(100, 30))
