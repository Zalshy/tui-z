"""tui-z — utility-class styling and components for Textual terminal UIs."""

from .app import TwApp
from .charts import Bar, LineChart, Sparkline
from .engine import TailError, compile_cls, merge
from .inline import inline
from .lines import LineView, LogView, Table
from .sidebar import Sidebar
from .theme import PALETTE, THEME_NAMES, THEMES, make_theme
from .theming import ThemeSwitcher
from .widgets import (
    Badge,
    Box,
    Button,
    Col,
    Divider,
    Grid,
    Label,
    Panel,
    Row,
    Scroll,
    Spacer,
    Stat,
    Text,
    Ticker,
    Tw,
    tw,
)

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
