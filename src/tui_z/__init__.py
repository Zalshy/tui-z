"""tui-z — utility-class styling and components for Textual terminal UIs.

Layers (each may import only from the ones above it):

    styling/     class strings -> CSS, inline styles, themes   (pure)
    core/        Tw mixin, class registry, stylesheet sync
    components/  every widget
    app.py       TwApp, which ties it all together
"""

from .app import TwApp
from .components import (
    Badge,
    Bar,
    Box,
    Button,
    Col,
    Divider,
    Grid,
    Label,
    LineChart,
    LineView,
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
)
from .core import Tw, tw
from .styling import PALETTE, THEME_NAMES, THEMES, TailError, compile_cls, inline, make_theme, merge

__all__ = [
    "PALETTE",
    "THEMES",
    "THEME_NAMES",
    "Badge",
    "Bar",
    "Box",
    "Button",
    "Col",
    "Divider",
    "Grid",
    "Label",
    "LineChart",
    "LineView",
    "LogView",
    "Panel",
    "Row",
    "Scroll",
    "Sidebar",
    "Spacer",
    "Sparkline",
    "Stat",
    "Table",
    "TailError",
    "Text",
    "ThemeSwitcher",
    "Ticker",
    "Tw",
    "TwApp",
    "compile_cls",
    "inline",
    "make_theme",
    "merge",
    "tw",
]
