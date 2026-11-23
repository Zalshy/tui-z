"""tui-z showcase — every component, most utilities, every theme.

    uv run python demos/showcase.py

Keys: b toggle sidebar · [ / ] previous/next theme · 1-5 switch tab · q quit
Click a theme in the sidebar to switch.
"""

from __future__ import annotations

import math
import random
from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.theme import Theme
from textual.widgets import (
    Checkbox,
    DataTable,
    Digits,
    Footer,
    Input,
    ProgressBar,
    RadioButton,
    RadioSet,
    Select,
    Switch,
    TabbedContent,
    TabPane,
)

from tui_z import (
    PALETTE,
    Badge,
    Bar,
    Box,
    Button,
    Col,
    Divider,
    Grid,
    Label,
    LineChart,
    LogView,
    Panel,
    Row,
    Scroll,
    Sidebar,
    Spacer,
    Sparkline,
    Stat,
    Table,
    Text,
    ThemeSwitcher,
    Ticker,
    TwApp,
    tw,
)
from tui_z.engine import BORDER_TYPES
from tui_z.theme import SEMANTIC, SURFACES

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


FILL = "lg:h-full"  # stretch a panel to its grid row


def dashboard() -> ComposeResult:
    # lg+: the dashboard fills the screen; panels stretch to their row, and charts,
    # tables and the log grow to fill their panel. Smaller screens scroll instead.
    with Grid(cls="grid-cols-1 lg:grid-cols-3 gap-1 h-auto lg:h-fr lg:grid-rows-[5fr_3fr]"):
        # -- core model: big number + area chart ---------------------------
        yield Panel(
            Row(
                Col(Label("Labels · measured today"),
                    tw(Digits("1,292", id="labels"), "w-auto text-success"),
                    Row(Text("▲ TP 23%", "text-success mr-2"), Text("SL 51%", "text-error mr-2"),
                        Text("TIME 26%", "text-warning")),
                    cls="w-30 mr-2"),
                Sparkline(revert(60, 12, 12, 2), "h-5 text-success", lo=0, id="labels-spark"),
            ),
            LineChart(revert(200, 60, 60, 2.5), "h-8 lg:h-fr text-success mt-1", fill=True, id="core-chart"),
            title="Core model", subtitle="in training",
            badge=Badge("Research", cls="bg-info/20 text-info"), cls=FILL,
        )
        # -- exit simulator: many paths + marks -----------------------------
        # live price (foreground) + two simulated paths, all streamed in lock-step
        paths = [(revert(240, 1.0, 1.05, 0.035, 0.02), c) for c in EXIT_COLORS]
        yield Panel(
            LineChart(revert(240, 1.0, 1.05, 0.025, 0.02), "h-12 lg:h-fr text-foreground", id="exit-chart",
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
            DecisionCard("Skip · QNT", "$ORCHID", "Costs 4.1% over the 4% cap", 50, "warning"),
            DecisionCard("Label · SL", "$QUARTZ", "-38% first at 22 min · training", 39, "success"),
            DecisionCard("Block · GRD", "$TANGLE", "14 wallets bought 48% in slot 0", 7, "error"),
            DecisionCard("Trade entry", "$MAPLE", "Passed QNT + GRD · 0.61 SOL", 93, "info"),
            DecisionCard("Label · TP", "$LUMEN", "+68% first at 47 min · training", 92, "purple"),
            title="Decision stack", subtitle="newest on top",
            badge=Badge("● Live", cls="bg-error/20 text-error"), cls=FILL,
        )
        # -- leaderboard -----------------------------------------------------
        yield Panel(
            Table(
                [("#", "w-4 text-muted"), ("Wallet", "w-14 text-info"),
                 ("PnL", "w-fr text-right text-success bold"), ("Tx", "w-8 text-right text-muted")],
                [[("#1", "text-warning bold"), "0x87cc…aa20", "+$312.0k", "847"],
                 ["#2", "0x3f4a…c91e", "+$184.2k", "1204"],
                 ["#3", "0x5e80…3c99", "+$199.8k", "432"],
                 ["#4", "0xa12b…5f3d", "+$97.4k", "2891"],
                 ["#5", "0x1d9e…b47a", "+$44.1k", "318"]],
                row_cls="hover:bg-boost odd:bg-panel/40",
            ),
            title="Arber leaderboard", badge=Badge("30D"), cls=FILL,
        )
        # -- trade tape -----------------------------------------------------
        yield Panel(
            Table(
                [("Time", "w-9 text-muted"), ("Side", "w-5"), ("SOL", "w-7 text-right"),
                 ("Price", "w-fr text-right")],
                [], "lg:h-fr scrollbar-none", row_cls="hover:bg-boost", max_rows=40, id="tape",
            ),
            title="Trade tape", subtitle="time & sales", cls=FILL,
        )
        # -- slot river: column chart ------------------------------------------
        yield Panel(
            Sparkline([abs(math.sin(i / 3)) * 10 + random.random() * 5 for i in range(200)],
                      "h-7 lg:h-fr text-blue", lo=0, hi=15, id="river"),
            Row(Badge("Mainnet", cls="bg-success/20 text-success mr-1"),
                Text("SLOT 371,911,229 · 400 MS · BUILDING 26%", "text-muted truncate")),
            title="Slot river", cls=FILL,
        )
    yield Panel(
        LogView(cls="h-12 lg:h-fr", id="log"),
        title="Agent log", subtitle="tail -f · six agents",
        badge=Badge("1 / s", cls="bg-teal/20 text-teal"),
        cls="mt-1 lg:h-[25%] lg:min-h-7",
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
        tw(Digits("21:06"), "w-auto text-purple"),
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
    yield Text("Textual widgets follow the theme too; style them with tw(widget, cls)", "text-muted mb-1")
    yield Grid(
        Panel(tw(Input(placeholder="Search markets…"), "mb-1"),
              tw(Select([(t, t) for t in ("Macro", "Crypto", "Tech")], prompt="Category"), "mb-1"),
              title="Inputs"),
        Panel(Row(tw(Switch(value=True), "mr-1"), Text("Live mode", "content-middle h-3")),
              tw(Checkbox("Copy trades", True), "mb-1"),
              RadioSet(RadioButton("Kelly", value=True), RadioButton("Fixed"), RadioButton("Off")),
              title="Toggles"),
        Panel(tw(ProgressBar(total=100, show_eta=False, id="progress"), "mb-1"),
              tw(DataTable(id="dt"), "h-8"),
              title="Progress & DataTable"),
        cls="grid-cols-1 md:grid-cols-3 gap-1",
    )


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #

class Showcase(TwApp):
    TITLE = "tui-z showcase"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("[", "prev_theme", "Prev theme"),
        Binding("]", "next_theme", "Next theme"),
        Binding("b", "toggle_sidebar", "Sidebar"),
        *[Binding(str(i + 1), f"tab('{t}')", t.title(), show=False)
          for i, t in enumerate(("dashboard", "components", "utilities", "palette", "native"))],
    ]

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
            Text("", "w-10 text-right bold text-foreground h-2 content-middle", id="clock"),
            cls="h-3 px-1 items-center bg-surface border-b border-line",
        )
        yield Ticker([
            "[b $background on $error] LIVE FEED [/]", "$FERNLY · 50m", "[b $error]VETO[/] $NOVAKIT",
            "31 wallets bought 60% in slot 0", "[b $warning]ENTRY[/] $BRIGHT · net EV [$success]+8.8%[/]",
            "0.59 SOL", "[b $error]VETO[/] $PEBBLE · creator 49 launches", "[b $success]TP[/] $LUMEN +68%",
        ], "bg-panel/60")

        # -- body: sidebar + tabs --------------------------------------------------
        with Row(cls="h-fr"):
            with Sidebar(title="Themes", width="w-26", id="sidebar"):
                yield ThemeSwitcher()
                yield Divider("mt-1")
                yield Text("b      sidebar\n[ / ]  cycle theme\n1-5    switch tab\ntab    focus\nq      quit",
                           "text-muted px-1 mt-1", markup=False)
                yield Spacer("h-fr")
                yield Text("Palette", "text-muted bold uppercase tracking-wide px-1")
                yield Row(*[Text("  ", f"bg-{c}") for c in PALETTE], cls="px-1 mb-1")
            with tw(TabbedContent(id="tabs"), "w-fr h-full"):
                for tab_id, title, builder in (
                    ("dashboard", "Dashboard", dashboard), ("components", "Components", components),
                    ("utilities", "Utilities", utilities), ("palette", "Palette", palette),
                    ("native", "Native", native),
                ):
                    with TabPane(title, id=tab_id):
                        with Scroll(cls="px-1"):
                            yield from builder()
        yield Footer()

    # -- live data -------------------------------------------------------------
    def on_mount(self) -> None:
        # Look widgets up once: timers keep working on these references even
        # while the app is tearing the DOM down on quit.
        self.w_clock = self.query_one("#clock", Text)
        self.w_theme = self.query_one("#theme-stat", Stat)
        self.w_core = self.query_one("#core-chart", LineChart)
        self.w_river = self.query_one("#river", Sparkline)
        self.w_spark = self.query_one("#labels-spark", Sparkline)
        self.w_exit = self.query_one("#exit-chart", LineChart)
        self.w_progress = self.query_one("#progress", ProgressBar)
        self.w_log = self.query_one("#log", LogView)
        self.w_tape = self.query_one("#tape", Table)
        self.w_labels = self.query_one("#labels", Digits)
        self.w_swatches = list(self.query(Swatch))

        self.theme_changed_signal.subscribe(self, self._on_theme)
        self._on_theme(self.current_theme)
        dt = self.query_one("#dt", DataTable)
        dt.add_columns("Wallet", "Side", "Size")
        for _ in range(8):
            dt.add_row(f"0x{random.randrange(16**4):04x}…", random.choice(["BUY", "SELL"]), f"{random.uniform(.1, 3):.2f}")
        self.set_interval(1.0, self._tick_clock)
        self.set_interval(0.25, self._tick_fast)
        self.set_interval(0.9, self._tick_log)
        self._tick_clock()

    def _on_theme(self, theme: Theme) -> None:
        self.w_theme.update(theme.name)
        for swatch in self.w_swatches:
            swatch.hex.update(str(self.theme_variables.get(swatch.token, ""))[:9])

    def _tick_clock(self) -> None:
        self.w_clock.update(datetime.now().strftime("%H:%M:%S"))

    def _tick_fast(self) -> None:
        last = self.w_core.data[-1]
        self.w_core.push(last + (60 - last) * 0.05 + random.gauss(0, 2.5))
        self.w_river.push(abs(math.sin(len(self.w_river.data) / 3)) * 10 + random.random() * 5)
        self.w_spark.push(random.gauss(12, 3))

        def step(v: float, vol: float) -> float:
            return min(1.58, max(0.52, v + (1.05 - v) * 0.02 + random.gauss(0, vol)))

        self.w_exit.push(step(self.w_exit.data[-1], 0.025),
                         *[step(values[-1], 0.035) for values, _ in self.w_exit.series])
        self.w_progress.advance(1)
        if self.w_progress.percentage == 1:
            self.w_progress.progress = 0

    def _tick_log(self) -> None:
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

    def action_toggle_sidebar(self) -> None:
        self.query_one("#sidebar", Sidebar).toggle()

    def action_tab(self, tab: str) -> None:
        self.query_one("#tabs", TabbedContent).active = tab


if __name__ == "__main__":
    Showcase().run()
