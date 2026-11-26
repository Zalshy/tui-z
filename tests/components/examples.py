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
    # data
    Table: lambda cls: Table([("A", "w-4"), ("B", "w-fr")], [["1", "x"], ["2", "y"]], cls),
    LogView: LogView,
    Ticker: lambda cls: Ticker(["one", "two"], cls, speed=60),
    # charts
    Bar: lambda cls: Bar(0.5, cls),
    Sparkline: lambda cls: Sparkline(WAVE, cls),
    LineChart: lambda cls: LineChart(WAVE, cls),
    # controls
    Button: lambda cls: Button("go", cls),
    ThemeSwitcher: lambda cls: ThemeSwitcher(cls=cls),
    # navigation
    Sidebar: lambda cls: Sidebar(Text("inside"), title="Menu", cls=cls, width="w-7"),
}

# Components whose width comes from a parameter, not the user cls
# (Sidebar: `width=` / `rail=`, so collapsing keeps working).
WIDTH_FROM_PARAMS = {Sidebar}

# Exported Tw classes that are bases, not components you mount.
ABSTRACT = {tui_z.LineView}


def exported_components() -> set[type]:
    out = set()
    for name in tui_z.__all__:
        obj = getattr(tui_z, name)
        if isinstance(obj, type) and issubclass(obj, Tw) and obj is not Tw and obj not in ABSTRACT:
            out.add(obj)
    return out
