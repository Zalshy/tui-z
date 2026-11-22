"""A live markets dashboard built only from tui_z components + class strings.

    uv run python demos/markets.py      (q quits, t cycles themes)
"""

from __future__ import annotations

import random

from textual.app import ComposeResult
from textual.binding import Binding

from tui_z import (
    Badge,
    Bar,
    Button,
    Col,
    Grid,
    Label,
    Panel,
    Row,
    Scroll,
    Spacer,
    Sparkline,
    Stat,
    Text,
    TwApp,
)

MARKETS = [
    ("Rates cut in Q1?", "MACRO", 5.4, 0.67),
    ("BTC above $120k by EOY?", "CRYPTO", 8.9, 0.54),
    ("Ceasefire holds 30d?", "GEO", 1.3, 0.42),
    ("Orbital launch by Q4?", "TECH", 3.2, 0.79),
    ("Recession by Q3?", "MACRO", 6.1, 0.29),
    ("Assistant v2 ships?", "TECH", 1.8, 0.62),
]
WALLETS = [("0x3f4a…c91e", "ARB", "info"), ("0xa12b…5f3d", "BOT", "warning"),
           ("0x87cc…aa20", "WHALE", "secondary"), ("0x1d9e…b47a", "ARB", "info")]

# Reusable class strings: this is the "design system" of the app.
NUM = "w-7 text-right bold"
UP = "text-success"
DOWN = "text-error"


def delta(change: float) -> tuple[str, str]:
    return (f"▲{change:.1f}%", UP) if change >= 0 else (f"▼{abs(change):.1f}%", DOWN)


class MarketRow(Col):
    DEFAULT_CLS = "h-auto pb-1 border-b border-line mb-1"

    def __init__(self, question: str, tag: str, volume: float, yes: float) -> None:
        self.yes = yes
        self.yes_text = Text("", f"{NUM} {UP}")
        self.no_text = Text("", f"{NUM} {DOWN}")
        self.delta_text = Text("", "w-8 text-right")
        self.bar = Bar(yes, "w-20 text-success")
        super().__init__(
            Row(
                Col(Text(question, "bold truncate"),
                    Text(f"{tag} · ${volume}M", "text-muted"), cls="grow"),
                self.yes_text, self.no_text, self.delta_text,
            ),
            self.bar,
        )
        self.tick(0.0)

    def tick(self, change: float) -> None:
        self.yes = min(0.99, max(0.01, self.yes + change / 100))
        self.yes_text.update(f"{self.yes * 100:.0f}¢")
        self.no_text.update(f"{(1 - self.yes) * 100:.0f}¢")
        text, color = delta(change)
        self.delta_text.update(text)
        self.delta_text.set_cls(f"w-8 text-right {color}")
        self.bar.value = self.yes


class EdgeCard(Col):
    DEFAULT_CLS = "h-auto border border-line bg-panel px-1 mb-1"

    def __init__(self, question: str, edge: float, price: int, fair: float, vol: float) -> None:
        tone = "success" if edge > 5 else "warning"
        super().__init__(
            Row(Text(question, "bold grow"),
                Badge(f"+{edge:.2f}% EDGE", cls=f"bg-{tone}/15 text-{tone}")),
            Row(Stat("Mkt price", f"{price}¢", cls="w-18"),
                Stat("Fair value", f"{fair}¢", cls="w-18", value_cls="text-success"),
                Stat("Volume", f"${vol}M", cls="w-18", value_cls="text-warning"),
                cls="my-1"),
            Row(Button("Buy yes", "text-success border-success mr-1"),
                Button("Copy trade", "mr-1"),
                Button("Ignore", "text-muted")),
        )


class Markets(TwApp):
    TITLE = "edge terminal"
    BINDINGS = [Binding("q", "quit", "Quit"), Binding("t", "next_theme", "Theme")]

    def compose(self) -> ComposeResult:
        self.pnl = Stat("Net PnL", "+$10 554", cls="w-18", value_cls="text-success")
        self.winrate = Stat("Win%", "64.4%", cls="w-10", value_cls="text-info")
        self.rows = [MarketRow(*m) for m in MARKETS]
        self.spark = Sparkline([random.gauss(0, 1) for _ in range(300)], "h-4 text-success")

        # -- header bar -----------------------------------------------------
        yield Row(
            Text("EDGE[$muted]//[/]TERMINAL", "text-primary bold tracking-wide w-30"),
            self.pnl,
            Stat("Open", "4", cls="w-8", value_cls="text-warning"),
            self.winrate,
            Stat("Wallets", "7", cls="w-16"),
            Spacer(),
            Badge("● LIVE", cls="bg-success/15 text-success mr-1"),
            Badge("DEMO COPY", cls="bg-warning/15 text-warning"),
            cls="h-3 px-1 items-center border-b border-line bg-surface",
        )

        # -- main grid: 3 columns on wide terminals, 1 on narrow ---------------
        yield Grid(
            Panel(
                Scroll(
                    EdgeCard("Rates cut in Q1?", 8.42, 67, 75.4, 5.4),
                    EdgeCard("BTC $120k by EOY?", 5.29, 54, 59.1, 8.9),
                    EdgeCard("Orbital launch by Q4?", 6.63, 78, 84.7, 3.2),
                    EdgeCard("Assistant v2 ships?", 4.72, 62, 65.9, 1.8),
                ),
                title="Mispricing scanner",
                badge=Badge("4 edges found", cls="bg-error/15 text-error"),
                cls="h-full",
            ),
            Panel(
                Label("Address", cls="mb-1"),
                *[Col(Text(addr, "text-info"),
                      Badge(kind, cls=f"bg-{tone}/15 text-{tone} mb-1"),
                      cls="h-auto")
                  for addr, kind, tone in WALLETS],
                title="Wallet tracker",
                badge=Badge("7 tracked", cls="bg-info/15 text-info"),
                cls="h-full",
            ),
            Panel(
                Row(Label("Market", cls="grow"), Label("Yes", cls="w-7 text-right"),
                    Label("No", cls="w-7 text-right"), Label("24h", cls="w-8 text-right"),
                    cls="mb-1"),
                Scroll(*self.rows),
                title="Live markets",
                badge=Badge("Watching 47"),
                cls="h-full",
            ),
            Panel(
                Row(Stat("Total", "+$10 554", cls="w-18", value_cls="text-success"),
                    Stat("Today", "+$412", cls="w-14", value_cls="text-success")),
                self.spark,
                title="PnL curve",
                cls="h-full md:col-span-3",
            ),
            cls="h-fr grid-cols-1 md:grid-cols-[2fr_1fr_2fr] md:grid-rows-[1fr_9] gap-1 p-1",
        )

    def on_mount(self) -> None:
        self.set_interval(0.5, self.tick)

    def tick(self) -> None:
        for row in random.sample(self.rows, 2):
            row.tick(random.uniform(-2.5, 2.5))
        self.spark.push(self.spark.data[-1] + random.gauss(0.15, 1))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.notify(f"{event.button.label} pressed")



if __name__ == "__main__":
    Markets().run()
