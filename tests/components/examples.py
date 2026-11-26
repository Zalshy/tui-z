"""One minimal example of every exported component.

`test_contract.py` runs the shared checks over this table, and fails if an
exported component has no entry, so a new component gets them by adding a
line here. Each factory takes the user `cls`.
"""

from __future__ import annotations

from collections.abc import Callable

from textual.widget import Widget

import tui_z
from tui_z import (
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
    Toast,
    ToastStack,
    Tw,
)

WAVE = [float(i % 7) for i in range(60)]

EXAMPLES: dict[type, Callable[[str], Widget]] = {
    # layout
    Box: lambda cls: Box(Text("box"), cls=cls),
    Row: lambda cls: Row(Text("a"), Text("b"), cls=cls),
    Col: lambda cls: Col(Text("a"), Text("b"), cls=cls),
    Grid: lambda cls: Grid(Text("a"), Text("b"), cls=cls),
    Scroll: lambda cls: Scroll(*[Text(f"line {i}") for i in range(20)], cls=cls),
    Spacer: Spacer,
    Divider: Divider,
    Panel: lambda cls: Panel(Text("body"), title="Title", badge=Badge("new"), cls=cls),
    # content
    Text: lambda cls: Text("text", cls),
    Badge: lambda cls: Badge("live", cls=cls),
    Label: lambda cls: Label("label", cls=cls),
    Stat: lambda cls: Stat("PnL", "+12", cls=cls),
    Kbd: lambda cls: Kbd("ctrl+s", cls),
    KeyValue: lambda cls: KeyValue([("Status", "Live", "text-success"), ("Latency", "12 ms")], cls),
    # data
    Table: lambda cls: Table([("A", "w-4"), ("B", "w-fr")], [["1", "x"], ["2", "y"]], cls),
    LogView: LogView,
    Ticker: lambda cls: Ticker(["one", "two"], cls, speed=60),
    # charts
    Bar: lambda cls: Bar(0.5, cls),
    Sparkline: lambda cls: Sparkline(WAVE, cls),
    LineChart: lambda cls: LineChart(WAVE, cls),
    BarChart: lambda cls: BarChart([("a", 1), ("b", 3), ("c", 2, "error")], cls),
    Heatmap: lambda cls: Heatmap([[0, 1, 2], [3, 4, 5]], cls, row_labels=["x", "y"]),
    # controls
    Button: lambda cls: Button("go", cls),
    ThemeSwitcher: lambda cls: ThemeSwitcher(cls=cls),
    Checkbox: lambda cls: Checkbox("copy", True, cls),
    Switch: lambda cls: Switch("live", False, cls),
    RadioGroup: lambda cls: RadioGroup(["a", "b", "c"], 1, cls),
    Input: lambda cls: Input("", cls, placeholder="type"),  # Textual can't set a value outside an app
    Select: lambda cls: Select([("One", 1), ("Two", 2)], cls, value=1),
    # navigation
    Sidebar: lambda cls: Sidebar(Text("inside"), title="Menu", cls=cls, width="w-7"),
    Tabs: lambda cls: Tabs(["one", "two"], 1, cls),
    TabPane: lambda cls: TabPane("one", Text("x"), cls=cls),
    TabView: lambda cls: TabView(TabPane("one", Text("x")), TabPane("two", Text("y")), cls=cls),
    KeyHints: lambda cls: KeyHints([("q", "quit"), ("?", "help")], cls),
    # feedback
    Toast: lambda cls: Toast("Order filled", title="Fill", variant="success", timeout=None, cls=cls),
    ToastStack: lambda cls: ToastStack(Toast("hi", timeout=None), cls=cls),
    Alert: lambda cls: Alert("Prices delayed", title="Market", variant="warning", dismissible=True, cls=cls),
    Progress: lambda cls: Progress(40, 100, cls, label="sync"),
    Spinner: lambda cls: Spinner("loading", cls),
    NotificationCenter: lambda cls: NotificationCenter(cls=cls),
}

# Components whose width comes from a parameter, not the user cls
# (Sidebar: `width=` / `rail=`, so collapsing keeps working).
WIDTH_FROM_PARAMS = {Sidebar}

# Invisible containers (only their children are drawn): Textual gives them no
# region, so the contract checks their resolved styles instead of their size.
INVISIBLE = {ToastStack}

# Exported Tw classes that are bases or screens, not widgets you mount
# (Dialog is a screen: tests/components/test_feedback.py covers it).
ABSTRACT = {tui_z.LineView, Dialog}


def exported_components() -> set[type]:
    out = set()
    for name in tui_z.__all__:
        obj = getattr(tui_z, name)
        if isinstance(obj, type) and issubclass(obj, Tw) and obj is not Tw and obj not in ABSTRACT:
            out.add(obj)
    return out
