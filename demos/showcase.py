"""tui-z showcase — every component, most utilities, every theme.

    uv run python demos/showcase.py

Keys: 1-7 switch tab · [ / ] previous/next theme · b themes sidebar ·
i inbox · t send a toast · d open a dialog · q quit
Click a theme in the sidebar to switch.
"""

from __future__ import annotations

import math
import random
from datetime import datetime

from textual import widgets as tx
from textual.app import ComposeResult
from textual.binding import Binding
from textual.theme import Theme

from tui_z import (
    PALETTE,
    Alert,
    Badge,
    Bar,
    BarChart,
    Box,
    Button,
    Checkbox,
    Col,
    Dialog,
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
    NotificationCenter,
    Panel,
    Progress,
    RadioGroup,
    Row,
    Scroll,
    Select,
    Sidebar,
    Spacer,
    Sparkline,
    Spinner,
    Stat,
    Switch,
    Table,
    TabPane,
    Tabs,
    TabView,
    Text,
    ThemeSwitcher,
    Ticker,
    TwApp,
    tw,
)
from tui_z.styling.themes import SEMANTIC, SURFACES
from tui_z.styling.utilities import BORDER_TYPES

# --------------------------------------------------------------------------- #
# Shared class strings — this is how you build a design system with tui-z:
# name the strings you repeat.
# --------------------------------------------------------------------------- #
SECTION = "text-muted bold uppercase mt-1 mb-1"
CARD = "border border-line bg-panel/40 px-1"
NUM = "text-right bold"
UP, DOWN = "text-success", "text-error"
EXIT_COLORS = ("purple", "cyan")  # 2 simulated paths + the live price = 3 lines
TAGS = {  # log tag -> color token
    "EXIT": "error", "LAND": "info", "BUY": "success", "SKIP": "warning",
    "ATA": "purple", "TAPE": "teal", "VETO": "pink",
}


def walk(n: int, start: float = 0.0, drift: float = 0.0, vol: float = 1.0) -> list[float]:
    out, v = [], start
    for _ in range(n):
        v += random.gauss(drift, vol)
        out.append(v)
    return out


def revert(n: int, start: float, mean: float, vol: float, pull: float = 0.05) -> list[float]:
    """Mean-reverting walk: stays in a band, good for streaming demos."""
    out, v = [], start
    for _ in range(n):
        v += (mean - v) * pull + random.gauss(0, vol)
        out.append(v)
    return out


def tag(name: str) -> str:
    c = TAGS.get(name, "muted")
    return f"bg-{c}/20 text-{c}"


# --------------------------------------------------------------------------- #
# Dashboard pieces
# --------------------------------------------------------------------------- #

class DecisionCard(Row):
    """A card with a colored left edge and a big score — the 'decision stack'."""

    DEFAULT_CLS = "h-auto mb-1 border-l border-tall pl-1 pr-1"

    def __init__(self, kind: str, token: str, note: str, score: int, color: str) -> None:
        super().__init__(
            Col(
                Row(Badge(kind, cls=f"bg-{color}/20 text-{color} mr-1"), Text(token, "bold")),
                Text(note, "text-muted truncate"),
                cls="w-fr",
            ),
            Text(str(score), f"w-4 {NUM} text-{color} content-middle h-2"),
            cls=f"border-{color} bg-{color}/5",
        )


# md+ (120+ columns): the panel grid fills the screen, panels stretch to their
# grid row and charts / tables grow inside them. lg+ (160+) also fits the agent
# log on screen; on md it sits just below. Under 120 columns the single column
# scrolls at fixed heights. A minimum height keeps short terminals scrolling
# instead of squashing the panels.
FILL = "md:h-full"  # stretch a panel to its grid row

DECISIONS = [  # (kind, note, color)
    ("Skip · QNT", "Costs 4.1% over the 4% cap", "warning"),
    ("Label · SL", "-38% first at 22 min · training", "success"),
    ("Block · GRD", "14 wallets bought 48% in slot 0", "error"),
    ("Trade entry", "Passed QNT + GRD · 0.61 SOL", "info"),
    ("Label · TP", "+68% first at 47 min · training", "purple"),
]
DECISION_TOKENS = ["$ORCHID", "$QUARTZ", "$TANGLE", "$MAPLE", "$LUMEN", "$CINDER", "$HARBOR", "$WILLOW"]
MAX_DECISIONS = 12  # enough cards to fill a tall panel; older ones are dropped


def decision(i: int, token: int, score: int) -> DecisionCard:
    kind, note, color = DECISIONS[i % len(DECISIONS)]
    return DecisionCard(kind, DECISION_TOKENS[token % len(DECISION_TOKENS)], note, score, color)


LEADERS = [(f"0x{a}…{b}", pnl, tx) for a, b, pnl, tx in [
    ("87cc", "aa20", 312.0, 847), ("3f4a", "c91e", 199.8, 1204), ("5e80", "3c99", 184.2, 432),
    ("a12b", "5f3d", 97.4, 2891), ("1d9e", "b47a", 44.1, 318), ("c241", "e054", 38.6, 129),
    ("f03c", "217b", 31.2, 2210), ("5e80", "3c19", 24.9, 77), ("9b1a", "0d42", 18.3, 640),
    ("44e7", "c3a8", 12.7, 955), ("7d02", "e9f1", 9.4, 213), ("b6c5", "18aa", 5.1, 48),
]]


def dashboard() -> ComposeResult:
    # lg+: the dashboard fills the screen; panels stretch to their row, and charts,
    # tables and the log grow to fill their panel. Smaller screens scroll instead.
    with Grid(cls="grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-1 h-auto "
                  "md:h-full md:grid-rows-[4fr_3fr_3fr] md:min-h-40 lg:h-fr lg:grid-rows-[5fr_3fr] lg:min-h-30"):
        # -- core model: big number + area chart ---------------------------
        yield Panel(
            Row(
                Col(Label("Labels · measured today"),
                    tw(tx.Digits("1,292", id="labels"), "w-auto text-success"),
                    Row(Text("▲ TP 23%", "text-success mr-2"), Text("SL 51%", "text-error mr-2"),
                        Text("TIME 26%", "text-warning")),
                    cls="w-30 mr-2"),
                Sparkline(revert(60, 12, 12, 2), "h-5 text-success", lo=0, id="labels-spark"),
            ),
            LineChart(revert(200, 60, 60, 2.5), "h-8 md:h-fr text-success mt-1", fill=True, id="core-chart"),
            title="Core model", subtitle="in training",
            badge=Badge("Research", cls="bg-info/20 text-info"), cls=FILL,
        )
        # -- exit simulator: many paths + marks -----------------------------
        # live price (foreground) + two simulated paths, all streamed in lock-step
        paths = [(revert(240, 1.0, 1.05, 0.035, 0.02), c) for c in EXIT_COLORS]
        yield Panel(
            LineChart(revert(240, 1.0, 1.05, 0.025, 0.02), "h-12 md:h-fr text-foreground", id="exit-chart",
                      series=paths, marks=[(1.4, "success", " TP +40%"), (0.7, "error", " STOP -30%")],
                      lo=0.5, hi=1.6),
            Row(Stat("P(TP)", "0.37", cls="w-10", value_cls="text-success"),
                Stat("P(SL)", "0.33", cls="w-10", value_cls="text-error"),
                Stat("P(TIME)", "0.31", cls="w-10", value_cls="text-warning"),
                Stat("EV", "+15.5%", cls="w-10", value_cls="text-success"),
                Stat("Median exit", "41 MIN", cls="w-14", value_cls="text-info"),
                cls="mt-1"),
            title="Exit simulator", subtitle="monte carlo · three barriers",
            badge=Badge("3 paths", cls="bg-purple/20 text-purple"), cls=FILL,
        )
        # -- decision stack --------------------------------------------------
        yield Panel(
            Col(*[decision(i, i, score) for i, score in enumerate([50, 39, 7, 93, 92, 61, 18, 77, 44, 85])],
                id="decisions", cls="h-15 md:h-fr overflow-hidden"),
            title="Decision stack", subtitle="newest on top",
            badge=Badge("● Live", cls="bg-error/20 text-error"), cls=FILL,
        )
        # -- leaderboard -----------------------------------------------------
        yield Panel(
            Table(
                [("#", "w-4 text-muted"), ("Wallet", "w-14 text-info"),
                 ("PnL", "w-fr text-right text-success bold"), ("Tx", "w-8 text-right text-muted")],
                [[(f"#{i}", "text-warning bold") if i == 1 else f"#{i}", wallet, f"+${pnl:.1f}k", str(tx)]
                 for i, (wallet, pnl, tx) in enumerate(LEADERS, 1)],
                "h-7 md:h-fr scrollbar-none", row_cls="hover:bg-boost odd:bg-panel/40",
            ),
            title="Arber leaderboard", badge=Badge("30D"), cls=FILL,
        )
        # -- trade tape -----------------------------------------------------
        yield Panel(
            Table(
                [("Time", "w-9 text-muted"), ("Side", "w-5"), ("SOL", "w-7 text-right"),
                 ("Price", "w-fr text-right")],
                [], "h-9 md:h-fr scrollbar-none", row_cls="hover:bg-boost", max_rows=40, id="tape",
            ),
            title="Trade tape", subtitle="time & sales", cls=FILL,
        )
        # -- slot river: column chart ------------------------------------------
        yield Panel(
            Sparkline([abs(math.sin(i / 3)) * 10 + random.random() * 5 for i in range(200)],
                      "h-7 md:h-fr text-blue", lo=0, hi=15, id="river"),
            Row(Badge("Mainnet", cls="bg-success/20 text-success mr-1"),
                Text("SLOT 371,911,229 · 400 MS · BUILDING 26%", "text-muted truncate")),
            title="Slot river", cls=FILL,
        )
    yield Panel(
        LogView(cls="h-12 lg:h-fr", id="log"),
        title="Agent log", subtitle="tail -f · six agents",
        badge=Badge("1 / s", cls="bg-teal/20 text-teal"),
        cls="mt-1 lg:h-[25%] lg:min-h-8",
    )


# --------------------------------------------------------------------------- #
# Components gallery
# --------------------------------------------------------------------------- #

def components() -> ComposeResult:
    yield Text("Badges — semantic", SECTION)
    yield Row(*[Badge(c, cls=f"bg-{c}/20 text-{c} mr-1") for c in SEMANTIC])
    yield Text("Badges — palette (themeable: names map to each theme's own hues)", SECTION)
    yield Row(*[Badge(c, cls=f"bg-{c}/20 text-{c} mr-1") for c in PALETTE])
    yield Text("Badges — solid / outline-ish / muted", SECTION)
    yield Row(
        Badge("Solid", cls="bg-primary text-background mr-1"),
        Badge("Solid err", cls="bg-error text-background mr-1"),
        Badge("Underline", cls="bg-transparent text-warning underline mr-1"),
        Badge("Reverse", cls="bg-transparent text-info reverse mr-1"),
        Badge("Muted", cls="bg-panel text-muted mr-1"),
        Badge("tracking", cls="bg-purple/20 text-purple tracking-wide"),
    )

    yield Text("Buttons — focus with tab, press with enter/space or click", SECTION)
    yield Row(
        Button("Default", "mr-1"),
        Button("Buy yes", "text-success border-success mr-1"),
        Button("Sell", "text-error border-error mr-1"),
        Button("Primary", "bg-primary text-background border-primary hover:bg-primary/80 mr-1"),
        Button("Round", "border-round border-info text-info mr-1"),
        Button("Heavy", "border-heavy border-warning text-warning mr-1"),
        Button("Ghost", "border-none text-muted hover:text-foreground py-1 mr-1"),
        Button("Tall", "border-tall border-purple text-purple bg-purple/10"),
    )

    yield Text("Stats", SECTION)
    yield Row(
        Stat("Net PnL", "+$10 554", cls="w-14", value_cls="text-success"),
        Stat("Open", "4", cls="w-8", value_cls="text-warning"),
        Stat("Win%", "64.4%", cls="w-10", value_cls="text-info"),
        Stat("Blocked", "7,131", cls="w-10", value_cls="text-error"),
        tw(tx.Digits("21:06"), "w-auto text-purple"),
    )

    yield Text("Bars", SECTION)
    yield Grid(*[Row(Text(c, "w-8 text-muted"), Bar(0.15 + i * 0.1, f"w-fr text-{c}"), cls="h-1")
                 for i, c in enumerate(PALETTE)], cls="grid-cols-1 md:grid-cols-3 gap-x-2")

    yield Text("Sparklines & line charts", SECTION)
    yield Row(
        Sparkline(walk(100, 0, 0.1), "w-fr h-3 text-cyan mr-2"),
        Sparkline(walk(100, 0, -0.1), "w-fr h-3 text-pink mr-2"),
        LineChart(walk(80, 0, 0.2), "w-fr h-3 text-green", axis=False, fill=True, mode="fit"),
    )
    yield LineChart(walk(150, 100, 0.3, 2), "h-8 text-blue mt-1", mode="fit",
                    series=[(walk(150, 100, 0.1, 2), "muted")],
                    marks=[(110, "warning", " target")])

    yield Text("Panels", SECTION)
    yield Grid(
        Panel(Text("Default panel: border-line, bg-surface"), title="Default"),
        Panel(Text("cls='border-round border-primary'"), title="Rounded",
              badge=Badge("New"), cls="border-round border-primary"),
        Panel(Text("cls='border-heavy border-error bg-error/5'"), title="Alert",
              badge=Badge("3", cls="bg-error text-background"), cls="border-heavy border-error bg-error/5"),
        Panel(Text("hover me → hover:border-purple"), title="Hover",
              cls="hover:border-purple hover:bg-purple/5"),
        cls="grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-1",
    )

    yield Text("Divider & ticker", SECTION)
    yield Divider("text-line")
    yield Divider("text-primary", char="━")
    yield Ticker(["[b $success]▲ BTC +2.1%[/]", "[b $error]▼ ETH -0.8%[/]", "[$muted]volume[/] 1.2B",
                  "[b $warning]VETO[/] $NOVAKIT"], "bg-panel mt-1")

    yield Text("Table — striped (odd:) + hover:", SECTION)
    yield Table(
        [("Market", "w-fr"), ("Yes", "w-6 text-right text-success"),
         ("No", "w-6 text-right text-error"), ("24h", "w-8 text-right")],
        [["Rates cut in Q1?", "67¢", "33¢", ("▲0.4%", UP)],
         ["BTC above $120k by EOY?", "54¢", "46¢", ("▼1.9%", DOWN)],
         ["Ceasefire holds 30d?", "42¢", "58¢", ("▼2.6%", DOWN)],
         ["Orbital launch by Q4?", "79¢", "21¢", ("▲2.2%", UP)]],
        row_cls="odd:bg-panel/50 hover:bg-primary/10",
    )



    yield Text("Keys & details — Kbd, KeyValue", SECTION)
    yield Row(
        Col(Row(Kbd("ctrl+s", "mr-1"), Text("save", "text-muted mr-3"), Kbd("[", "mr-1"), Kbd("]", "mr-1"),
                Text("theme", "text-muted")),
            Row(Kbd("t", "mr-1"), Text("toast", "text-muted mr-3"), Kbd("d", "mr-1"), Text("dialog", "text-muted"),
                cls="mt-1"),
            cls="w-auto mr-4"),
        KeyValue([("Status", "● Live", "text-success"), ("Latency", "12 ms"), ("Region", "eu-west"),
                  ("Fee", "0.25%", "text-warning")], "w-40", key_cls="uppercase"),
    )

    yield Text("Bar charts — values, colors per bar, histogram", SECTION)
    yield Row(
        BarChart([("Mon", 12), ("Tue", 18), ("Wed", 7, "error"), ("Thu", 22), ("Fri", 15), ("Sat", 4, "muted"),
                  ("Sun", 9)], "w-fr h-8 text-info mr-2", values=True),
        BarChart.histogram([random.gauss(0, 1) for _ in range(500)], bins=16, cls="w-fr h-8 text-purple"),
    )

    yield Text("Heatmap — activity by hour, shaded in a theme color", SECTION)
    yield Heatmap([[max(0.0, math.sin((h - 6) / 24 * math.pi * 2) * 5 + random.random() * 4 - d % 3)
                    for h in range(24)] for d in range(7)],
                  color="success", row_labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                  col_labels=["0h", "", "", "", "", "", "6h", "", "", "", "", "", "12h", "", "", "", "", "",
                              "18h", "", "", "", "", ""])

    yield Text("Tabs on their own — left/right when focused", SECTION)
    yield Tabs(["Day", "Week", "Month", "Year"], active=1, cls="w-50")


# --------------------------------------------------------------------------- #
# Controls: an order ticket whose state is mirrored live
# --------------------------------------------------------------------------- #

MARKETS = [("Rates cut in Q1?", "rates"), ("BTC above $120k?", "btc"), ("Ceasefire holds 30d?", "ceasefire")]
SIZING = ["Kelly", "Fixed", "Off"]


def controls() -> ComposeResult:
    yield Grid(
        Panel(
            Label("Market"), Select(MARKETS, value="rates", prompt="Market", id="ticket-market", cls="mb-1"),
            Label("Amount (SOL)"), Input("0.5", placeholder="0.5", restrict=r"[0-9.]*", id="ticket-amount",
                                         cls="mb-1"),
            Row(Col(Label("Sizing"), RadioGroup(SIZING, 0, id="ticket-sizing"), cls="w-20"),
                Col(Label("Options"),
                    Checkbox("Copy top wallets", True, id="ticket-copy"),
                    Checkbox("Paper trade", id="ticket-paper"),
                    Switch("Live data", True, id="live"),
                    cls="w-fr"),
                cls="h-auto mb-1"),
            Row(Spacer(), Button("Clear", "mr-1", name="ticket-clear"),
                Button("Buy yes", "text-success border-success", name="ticket-submit"), cls="h-auto"),
            title="Order ticket", subtitle="Input · Select · RadioGroup · Checkbox · Switch",
        ),
        Panel(
            KeyValue([("Market", "rates"), ("Amount", "0.5 SOL"), ("Sizing", "Kelly"),
                      ("Copy wallets", "yes", "text-success"), ("Paper", "no", "text-muted"),
                      ("Live data", "on", "text-success")], id="ticket-state", key_cls="uppercase"),
            Divider("mt-1"),
            Text("Every control posts a Changed message; the app updates this KeyValue from them. "
                 "Live data pauses the dashboard.", "w-full text-muted mt-1"),
            title="State", subtitle="KeyValue", badge=Badge("live", cls="bg-success/20 text-success"),
        ),
        cls="grid-cols-1 md:grid-cols-2 gap-1",
    )


# --------------------------------------------------------------------------- #
# Notifications & feedback
# --------------------------------------------------------------------------- #

VARIANTS = ["success", "info", "warning", "error", "neutral"]
TIMEOUTS = [("2 seconds", 2.0), ("4 seconds", 4.0), ("8 seconds", 8.0), ("Until dismissed", 0.0)]


def notifications() -> ComposeResult:
    yield Grid(
        Panel(
            Label("Message"), Input("Order filled · 0.61 SOL", id="toast-message", cls="mb-1"),
            Row(Col(Label("Variant"), RadioGroup(VARIANTS, 0, id="toast-variant"), cls="w-16"),
                Col(Label("Timeout"), Select(TIMEOUTS, value=4.0, allow_blank=False, id="toast-timeout", cls="mb-1"),
                    Checkbox("Add a Retry action", id="toast-action"), cls="w-fr"),
                cls="h-auto mb-1"),
            Row(Button("Send", "text-primary border-primary mr-1", name="toast-send"),
                Button("Burst ×5", "mr-1", name="toast-burst"),
                Button("Repeat", name="toast-repeat"), cls="h-auto"),
            Text("Hover a toast to pause it, click it to dismiss. Repeats merge into ×N.", "w-full text-muted mt-1"),
            title="Toasts", subtitle="app.toast()", badge=Badge("press t", cls="bg-info/20 text-info"),
        ),
        Panel(
            Row(Progress(0, 100, "w-fr text-success", label="Backfill", id="job-backfill"),
                Spinner("", "w-3 ml-1", id="spin-backfill"), cls="h-1 mb-1"),
            Row(Progress(0, 100, "w-fr text-info", label="Index   ", id="job-index"),
                Spinner("", "w-3 ml-1 text-info", id="spin-index"), cls="h-1 mb-1"),
            Progress(total=None, cls="text-purple mb-1", label="Waiting ", show_percentage=False),
            Spinner("Watching 47 markets", "text-warning mb-1"),
            Text("Finished jobs send a toast and restart.", "w-full text-muted"),
            title="Background jobs", subtitle="Progress · Spinner",
        ),
        Panel(
            Col(id="alerts", cls="h-auto"),
            Row(Spacer(), Button("Restore", name="alerts-restore"), cls="h-auto mt-1"),
            title="Alerts", subtitle="dismiss with ✕",
        ),
        Panel(
            Text("A Dialog is a modal screen. It returns the pressed button's result to a callback.", "w-full mb-1"),
            Row(Button("Confirm", "mr-1", name="dialog-confirm"),
                Button("Delete…", "text-error border-error", name="dialog-delete"), cls="h-auto"),
            Text("The inbox (press i) keeps every toast: a NotificationCenter in a right Sidebar.",
                 "w-full text-muted mt-1"),
            title="Dialogs & inbox", subtitle="Dialog · NotificationCenter",
        ),
        cls="grid-cols-1 md:grid-cols-2 gap-1",
    )


def alerts() -> list[Alert]:
    return [
        Alert("Prices from Polygon are delayed by 15 minutes.", title="Market closed", variant="warning",
              dismissible=True, cls="mb-1"),
        Alert("3 orders filled while you were away.", title="Filled", variant="success", dismissible=True,
              cls="mb-1"),
        Alert("Copy trading follows the top 20 wallets.", variant="info", dismissible=True, cls="mb-1"),
        Alert("RPC node unreachable, using the fallback.", title="Degraded", variant="error", dismissible=True),
    ]


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #

def utilities() -> ComposeResult:
    yield Text("Breakpoints — resize the terminal (sm:80 md:120 lg:160 xl:200 cols)", SECTION)
    yield Row(
        Badge("base < 80", cls="bg-muted/30 text-foreground sm:hidden"),
        Badge("sm ≥ 80", cls="hidden sm:block md:hidden bg-info/20 text-info"),
        Badge("md ≥ 120", cls="hidden md:block lg:hidden bg-success/20 text-success"),
        Badge("lg ≥ 160", cls="hidden lg:block xl:hidden bg-warning/20 text-warning"),
        Badge("xl ≥ 200", cls="hidden xl:block bg-purple/20 text-purple"),
        Text("  ← exactly one badge is visible", "text-muted"),
    )

    yield Text("Border types — border-{type} border-{color}", SECTION)
    colors = list(PALETTE)
    yield Grid(*[Box(Text(t, "w-full text-center"), cls=f"border-{t} border-{colors[i % len(colors)]} h-3")
                 for i, t in enumerate(sorted(BORDER_TYPES - {'hidden', 'blank'}))],
               cls="grid-cols-3 md:grid-cols-6 lg:grid-cols-8 gap-1")

    yield Text("Border sides — border-t / border-b / border-l / border-x / border-y", SECTION)
    yield Row(*[Box(Text(s, "w-full text-center"), cls=f"{s} border-heavy border-primary w-14 h-3 mr-2 content-middle")
                for s in ("border-t", "border-b", "border-l", "border-r", "border-x", "border-y")])

    yield Text("Text styles", SECTION)
    yield Row(*[Text(s, f"{s} mr-3") for s in ("bold", "italic", "underline", "strike", "reverse", "dim")])
    yield Text("Content transforms", SECTION)
    yield Row(Text("uppercase", "uppercase mr-3"), Text("CAPITALIZE ME", "lowercase capitalize mr-3"),
              Text("tracking", "tracking-wide mr-3"), Text("wider", "tracking-wider uppercase text-primary"))

    yield Text("Color opacity — bg-primary/{n}", SECTION)
    yield Row(*[Text(f"/{n}", f"bg-primary/{n} w-8 text-center") for n in (5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)])
    yield Text("Text opacity — text-opacity-{n}", SECTION)
    yield Row(*[Text(f"{n}%", f"text-opacity-{n} w-8 bold") for n in (20, 40, 60, 80, 100)])

    yield Text("Alignment — content-* inside a fixed box", SECTION)
    yield Grid(*[Box(Text(f"{h} {v}", "w-auto text-muted"), cls=f"border border-line h-5 justify-{h} items-{v}")
                 for v in ("start", "center", "end") for h in ("start", "center", "end")],
               cls="grid-cols-3 grid-rows-[5] gap-1 w-60")

    yield Text("Spacing — p-0 · p-1 · px-4 · py-1 px-2", SECTION)
    yield Row(*[Box(Text(p, "bg-primary/30"), cls=f"{p} bg-panel w-auto mr-2") for p in ("p-0", "p-1", "px-4", "py-1 px-2")])

    yield Text("Grid — grid-cols-[1fr_2fr_1fr] + col-span-2", SECTION)
    yield Grid(
        Text("1fr", "bg-blue/20 text-center w-full"), Text("2fr", "bg-purple/20 text-center w-full"), Text("1fr", "bg-teal/20 text-center w-full"),
        Text("col-span-2", "bg-pink/20 text-center col-span-2 w-full"), Text("1", "bg-orange/20 text-center w-full"),
        cls="grid-cols-[1fr_2fr_1fr] gap-1",
    )

    yield Text("Variants — hover: · focus: · focus-within: · odd:", SECTION)
    yield Row(
        Box(Text("hover:bg-primary/20"), cls="border border-line px-1 w-26 hover:bg-primary/20 hover:border-primary mr-2"),
        Box(tw(Input(placeholder="focus inside me"), "border-none h-1 bg-transparent"),
            cls="border border-line w-30 h-3 focus-within:border-success focus-within:bg-success/5"),
    )


# --------------------------------------------------------------------------- #
# Palette (verify each theme) + native Textual widgets
# --------------------------------------------------------------------------- #

class Swatch(Row):
    def __init__(self, token: str) -> None:
        self.token = token
        self.hex = Text("", "w-12 text-muted")
        super().__init__(Text("", f"bg-{token} w-6 mr-1"), Text(token, "w-12"), self.hex, cls="h-1 mb-0")


def palette() -> ComposeResult:
    for title, tokens in (("Semantic", SEMANTIC), ("Palette", PALETTE), ("Surfaces & text", SURFACES)):
        yield Text(title, SECTION)
        yield Grid(*[Swatch(t) for t in tokens], cls="grid-cols-2 md:grid-cols-3 lg:grid-cols-4")
    yield Text("Text on surfaces", SECTION)
    yield Grid(*[Box(Text(f"bg-{s}", "bold"), Text("muted text", "text-muted"),
                     Text("[$success]success[/] [$error]error[/] [$warning]warn[/] [$info]info[/]"),
                     cls=f"bg-{s} p-1") for s in ("background", "surface", "panel")],
               cls="grid-cols-1 md:grid-cols-3 gap-1")



def native() -> ComposeResult:
    yield Text("Any Textual widget can take class strings with tw(widget, cls), and follows the theme.",
               "text-muted mb-1")
    yield Grid(
        Panel(tw(tx.Input(placeholder="Textual's Input…"), "mb-1"),
              tw(tx.Select([(t, t) for t in ("Macro", "Crypto", "Tech")], prompt="Textual's Select"), "mb-1"),
              title="Inputs"),
        Panel(Row(tw(tx.Switch(value=True), "mr-1"), Text("Textual's Switch", "content-middle h-3")),
              tw(tx.Checkbox("Textual's Checkbox", True), "mb-1"),
              tx.RadioSet(tx.RadioButton("Kelly", value=True), tx.RadioButton("Fixed"), tx.RadioButton("Off")),
              title="Toggles"),
        Panel(tw(tx.ProgressBar(total=100, show_eta=False, id="progress"), "mb-1"),
              tw(tx.DataTable(id="dt"), "h-8"),
              title="Progress & DataTable"),
        cls="grid-cols-1 md:grid-cols-3 gap-1",
    )


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #

TABS = (
    ("dashboard", "Dashboard", dashboard), ("components", "Components", components),
    ("controls", "Controls", controls), ("notifications", "Notifications", notifications),
    ("utilities", "Utilities", utilities), ("palette", "Palette", palette), ("native", "Native", native),
)
TOAST_IDEAS = [
    ("Order filled · 0.61 SOL", "Fill", "success"), ("Feed lag 2.1 s", "Feed", "warning"),
    ("$NOVAKIT vetoed: creator has 49 launches", "Veto", "error"), ("Model retrained · AUC 0.71", "Research", "info"),
    ("Wallet 0x87cc…aa20 is copying you", "", "neutral"),
]


class Showcase(TwApp):
    TITLE = "tui-z showcase"
    TW_TOAST_MAX = 4
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("[", "prev_theme", "Prev theme"),
        Binding("]", "next_theme", "Next theme"),
        Binding("b", "toggle_sidebar", "Themes"),
        Binding("i", "toggle_inbox", "Inbox"),
        Binding("t", "random_toast", "Toast"),
        Binding("d", "dialog", "Dialog"),
        *[Binding(str(i + 1), f"tab('{tab_id}')", title, show=False) for i, (tab_id, title, _) in enumerate(TABS)],
    ]

    live = True  # "Live data" switch in the Controls tab
    on_dashboard = True  # live updates only run while their tab is visible
    on_notifications = False

    def compose(self) -> ComposeResult:
        # -- header ------------------------------------------------------------
        yield Row(
            Badge("Z", cls="bg-primary text-background mr-1 h-2 w-4 content-center content-middle"),
            Col(Text("TUI-Z [$muted]//[/] SHOWCASE", "bold text-primary tracking-wide"),
                Text("utility classes · components · themes", "text-muted"), cls="w-auto"),
            Spacer(),
            Stat("Launches", "10,064", cls="w-12 hidden md:block", id="launches"),
            Stat("Blocked", "7,131", cls="w-11 hidden md:block", value_cls="text-error"),
            Stat("Signals", "44", cls="w-10 hidden md:block", value_cls="text-success"),
            Stat("Theme", self.theme, cls="w-22", value_cls="text-primary", id="theme-stat"),
            Stat("Inbox", "0", cls="w-8", value_cls="text-muted", id="inbox-stat"),
            Text("", "w-10 text-right bold text-foreground h-2 content-middle", id="clock"),
            cls="h-3 px-1 items-center bg-surface border-b border-line",
        )
        yield Ticker([
            "[b $background on $error] LIVE FEED [/]", "$FERNLY · 50m", "[b $error]VETO[/] $NOVAKIT",
            "31 wallets bought 60% in slot 0", "[b $warning]ENTRY[/] $BRIGHT · net EV [$success]+8.8%[/]",
            "0.59 SOL", "[b $error]VETO[/] $PEBBLE · creator 49 launches", "[b $success]TP[/] $LUMEN +68%",
        ], "bg-panel/60")

        # -- body: themes sidebar + tabs + inbox sidebar -----------------------------
        with Row(cls="h-fr"):
            with Sidebar(title="Themes", width="w-26", id="sidebar"):
                yield ThemeSwitcher()
                yield Divider("mt-1")
                yield KeyValue([("1-7", "tabs"), ("[ ]", "theme"), ("b / i", "sidebars"), ("t", "toast"),
                                ("d", "dialog"), ("q", "quit")], "px-1 mt-1", key_cls="text-primary bold")
                yield Spacer("h-fr")
                yield Text("Palette", "text-muted bold uppercase tracking-wide px-1")
                yield Row(*[Text("  ", f"bg-{c}") for c in PALETTE], cls="px-1 mb-1")
            with TabView(id="tabs", cls="w-fr h-full"):
                for tab_id, title, builder in TABS:
                    with TabPane(title, id=tab_id, cls="h-full"):
                        with Scroll(cls="px-1"):
                            yield from builder()
            with Sidebar(title="Inbox", width="w-44", side="right", collapsed=True, id="inbox"):
                yield NotificationCenter("Toasts so far", "h-fr px-1", id="center")
        yield KeyHints()

    # -- live data -------------------------------------------------------------
    def on_mount(self) -> None:
        # Look widgets up once: timers keep working on these references even
        # while the app is tearing the DOM down on quit.
        self.w_clock = self.query_one("#clock", Text)
        self.w_theme = self.query_one("#theme-stat", Stat)
        self.w_inbox = self.query_one("#inbox-stat", Stat)
        self.w_core = self.query_one("#core-chart", LineChart)
        self.w_river = self.query_one("#river", Sparkline)
        self.w_spark = self.query_one("#labels-spark", Sparkline)
        self.w_exit = self.query_one("#exit-chart", LineChart)
        self.w_progress = self.query_one("#progress", tx.ProgressBar)
        self.w_log = self.query_one("#log", LogView)
        self.w_tape = self.query_one("#tape", Table)
        self.w_decisions = self.query_one("#decisions", Col)
        self.w_labels = self.query_one("#labels", tx.Digits)
        self.w_swatches = list(self.query(Swatch))
        self.w_state = self.query_one("#ticket-state", KeyValue)
        self.w_jobs = [(self.query_one("#job-backfill", Progress), self.query_one("#spin-backfill", Spinner), 3.0),
                       (self.query_one("#job-index", Progress), self.query_one("#spin-index", Spinner), 1.2)]
        self.last_toast: tuple[str, str, str] = TOAST_IDEAS[0]

        self.theme_changed_signal.subscribe(self, self._on_theme)
        self._on_theme(self.current_theme)
        self.watch(self.query_one("#center", NotificationCenter), "unread", self._on_unread)
        self.query_one("#alerts", Col).mount_all(alerts())
        dt = self.query_one("#dt", tx.DataTable)
        dt.add_columns("Wallet", "Side", "Size")
        for _ in range(8):
            dt.add_row(f"0x{random.randrange(16**4):04x}…", random.choice(["BUY", "SELL"]), f"{random.uniform(.1, 3):.2f}")
        self.set_interval(1.0, self._tick_clock)
        self.set_interval(0.25, self._tick_fast)
        self.set_interval(0.9, self._tick_log)
        self.set_interval(2.5, self._tick_decision)
        self.set_interval(0.2, self._tick_jobs)
        self._tick_clock()

    @property
    def running(self) -> bool:
        return self.live and self.on_dashboard

    def _on_theme(self, theme: Theme) -> None:
        self.w_theme.update(theme.name)
        for swatch in self.w_swatches:
            swatch.hex.update(str(self.theme_variables.get(swatch.token, ""))[:9])

    def _on_unread(self, unread: int) -> None:
        self.w_inbox.update(str(unread), "text-error" if unread else "text-muted")

    def _tick_clock(self) -> None:
        self.w_clock.update(datetime.now().strftime("%H:%M:%S"))

    def _tick_fast(self) -> None:
        if self.live:  # the native ProgressBar lives in another tab
            self.w_progress.advance(1)
            if self.w_progress.percentage == 1:
                self.w_progress.progress = 0
        if not self.running:
            return
        last = self.w_core.data[-1]
        self.w_core.push(last + (60 - last) * 0.05 + random.gauss(0, 2.5))
        self.w_river.push(abs(math.sin(len(self.w_river.data) / 3)) * 10 + random.random() * 5)
        self.w_spark.push(random.gauss(12, 3))

        def step(v: float, vol: float) -> float:
            return min(1.58, max(0.52, v + (1.05 - v) * 0.02 + random.gauss(0, vol)))

        self.w_exit.push(step(self.w_exit.data[-1], 0.025),
                         *[step(values[-1], 0.035) for values, _ in self.w_exit.series])

    def _tick_decision(self) -> None:
        """Newest decision on top; the oldest falls off the bottom. Big scores toast."""
        if not self.running:
            return
        kind, token, score = random.randrange(5), random.randrange(8), random.randrange(3, 99)
        self.w_decisions.mount(decision(kind, token, score), before=0)
        for old in self.w_decisions.children[MAX_DECISIONS:]:
            old.remove()
        if score >= 90:
            self.toast(f"{DECISION_TOKENS[token]} scored {score}", title="High confidence", variant="success")

    def _tick_log(self) -> None:
        if not self.running:
            return
        name = random.choice(list(TAGS))
        coin = random.choice(["$CINDER", "$HARBOR", "$WILLOW", "$EMBER", "$LUMEN"])
        sol = random.uniform(0.05, 3)
        self.w_log.write(
            f"{coin} {random.choice(['SELL landed', 'BUY landed', 'token account closed', 'EV +1.8% after costs'])}"
            f" · [$muted]{sol:.2f} SOL · slot 371,911,{random.randrange(999):03d}[/]",
            tag=name, tag_cls=tag(name),
        )
        side = random.choice(["BUY", "SELL"])
        self.w_tape.add_row(
            [datetime.now().strftime("%H:%M:%S"), (side, UP if side == "BUY" else DOWN),
             f"{sol:.2f}", f"{random.uniform(0.0001, 0.01):.5f}"], top=True)
        self.w_labels.update(f"{int(self.w_labels.value.replace(',', '')) + random.randrange(3):,}")
        if random.random() < 0.05:  # the same warning again merges into ×N
            self.toast("RPC answered in 2.1 s", title="Feed lag", variant="warning")

    def _tick_jobs(self) -> None:
        if not self.on_notifications:
            return
        for progress, spinner, rate in self.w_jobs:
            if progress.percentage == 1:
                continue
            progress.advance(rate * random.random())
            if progress.percentage == 1:
                spinner.stop()
                self.toast(f"{progress.label.strip()} finished", title="Job done", variant="info", timeout=3)
                self.set_timer(3, lambda p=progress, s=spinner: (p.update(value=0), s.start()))

    # -- controls ----------------------------------------------------------------
    def on_tab_view_changed(self, event: TabView.Changed) -> None:
        self.on_dashboard = event.pane.id == "dashboard"
        self.on_notifications = event.pane.id == "notifications"

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "ticket-market":
            self.w_state.set("Market", str(event.value))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "ticket-amount":
            self.w_state.set("Amount", f"{event.value or '0'} SOL")

    def on_radio_group_changed(self, event: RadioGroup.Changed) -> None:
        if event.group.id == "ticket-sizing":
            self.w_state.set("Sizing", event.value)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        key = {"ticket-copy": "Copy wallets", "ticket-paper": "Paper"}.get(event.control.id or "")
        if key:
            self.w_state.set(key, "yes" if event.value else "no", "text-success" if event.value else "text-muted")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.control.id == "live":
            self.live = event.value
            self.w_state.set("Live data", "on" if event.value else "paused",
                             "text-success" if event.value else "text-warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        handler = getattr(self, f"_press_{(event.button.name or '').replace('-', '_')}", None)
        if handler is not None:
            handler()

    def _press_ticket_submit(self) -> None:
        amount = self.w_state.get("Amount")
        paper = self.w_state.get("Paper") == "yes"
        self.toast(f"{self.w_state.get('Market')} · {amount} · {self.w_state.get('Sizing')}",
                   title="Paper order placed" if paper else "Order placed", variant="info" if paper else "success")

    def _press_ticket_clear(self) -> None:
        self.query_one("#ticket-amount", Input).value = ""
        self.toast("Ticket cleared", variant="neutral", timeout=2)

    def _toast_from_form(self) -> None:
        message = self.query_one("#toast-message", Input).value or "Hello from tui-z"
        variant = self.query_one("#toast-variant", RadioGroup).value
        timeout = self.query_one("#toast-timeout", Select).value
        action = ("Retry", lambda: self.toast("Retried", variant="info", timeout=2)) \
            if self.query_one("#toast-action", Checkbox).value else None
        self.last_toast = (message, "", variant)
        self.toast(message, variant=variant, timeout=float(timeout) or None, action=action)  # type: ignore[arg-type]

    def _press_toast_send(self) -> None:
        self._toast_from_form()

    def _press_toast_repeat(self) -> None:
        message, title, variant = self.last_toast
        self.toast(message, title=title, variant=variant)

    def _press_toast_burst(self) -> None:
        for message, title, variant in TOAST_IDEAS:
            self.toast(message, title=title, variant=variant)

    def _press_alerts_restore(self) -> None:
        box = self.query_one("#alerts", Col)
        box.remove_children()
        box.mount_all(alerts())

    def _press_dialog_confirm(self) -> None:
        self.action_dialog()

    def _press_dialog_delete(self) -> None:
        def done(result: str | None) -> None:
            if result == "delete":
                self.toast("3 orders deleted", title="Deleted", variant="error")
            else:
                self.toast("Nothing deleted", variant="neutral", timeout=2)

        self.push_screen(Dialog("Delete the 3 open orders? This can't be undone.", title="Delete orders",
                                buttons=[("Keep", "keep"), ("Delete", "delete", "text-error border-error")],
                                cls="border-error"), done)

    # -- actions -------------------------------------------------------------------
    def action_toggle_sidebar(self) -> None:
        self.query_one("#sidebar", Sidebar).toggle()

    def action_toggle_inbox(self) -> None:
        inbox = self.query_one("#inbox", Sidebar)
        inbox.toggle()
        if not inbox.collapsed:
            self.query_one("#center", NotificationCenter).mark_read()

    def action_tab(self, tab: str) -> None:
        self.query_one("#tabs", TabView).active = tab

    def action_random_toast(self) -> None:
        self.last_toast = random.choice(TOAST_IDEAS)
        message, title, variant = self.last_toast
        self.toast(message, title=title, variant=variant)

    def action_dialog(self) -> None:
        def done(result: str | None) -> None:
            self.toast(f"Dialog returned {result!r}", variant="info" if result else "neutral", timeout=3)

        self.push_screen(Dialog("Rebalance the portfolio to the model weights?", title="Rebalance",
                                buttons=[("Cancel", "cancel"), ("Rebalance", "rebalance", Dialog.PRIMARY_CLS)]),
                         done)


if __name__ == "__main__":
    Showcase().run()
